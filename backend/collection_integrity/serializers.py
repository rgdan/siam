import base64
import binascii
from io import BytesIO

from PIL import Image, UnidentifiedImageError
from rest_framework import serializers
from django.utils import timezone

from .models import Photo, Piece

OBJECT_FIELDS = [
    "object_type",
    "materials_techniques",
    "measurement_value",
    "measurement_unit",
    "inscriptions_marks",
    "distinguishing_features",
    "title",
    "subject",
    "date_period",
    "author_maker",
]


class PieceSerializer(serializers.ModelSerializer):
    decommissioned_user = serializers.CharField(source="decommissioned_by.full_name", read_only=True, default=None)
    class Meta:
        model = Piece
        fields = [
            "id",
            "identifier",
            *OBJECT_FIELDS,
            "collection", "event_date", "event_observations", "loan_to", "loan_start", "loan_end",
            "state",
            "location",
            "decommissioned", "decommissioned_at", "decommission_reason", "decommissioned_by", "decommissioned_user",
        ]
        read_only_fields = ["id", "identifier", "decommissioned", "decommissioned_at", "decommission_reason", "decommissioned_by", "decommissioned_user", "event_date", "event_observations", "loan_to", "loan_start", "loan_end"]
        extra_kwargs = {
            key: {"required": True, "allow_blank": False}
            for key in OBJECT_FIELDS
            if key != "measurement_value"
        }
        extra_kwargs["measurement_value"] = {"required": True, "allow_null": False}

    def validate_measurement_unit(self, value):
        if value not in ["mm", "cm", "m", "g", "kg"]:
            raise serializers.ValidationError("invalid_unit")
        return value

    def validate(self, attrs):
        errors = {}
        for key in ["id", "identifier", "decommissioned", "decommissioned_at", "decommission_reason", "decommissioned_by", "decommissioned_user", "event_date", "event_observations", "loan_to", "loan_start", "loan_end"]:
            if key in self.initial_data:
                errors[key] = "immutable"
        if self.instance is None:
            if "state" in self.initial_data and attrs.get("state") != "stored":
                errors["state"] = "initial_storage"
            attrs["state"] = "stored"
        state = attrs.get("state", self.instance.state if self.instance else "stored")
        if "state" in attrs and state not in ["stored", "displayed"]:
            errors["state"] = "invalid_state"
        location = attrs.get(
            "location", self.instance.location if self.instance else ""
        )
        if self.instance and self.instance.state in ["stolen", "lost", "loaned"]:
            if "state" in attrs or "location" in attrs:
                errors["state"] = "unavailable_piece"
        if state == "displayed" and not location.strip():
            errors["location"] = "required"
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class PhotoOrderSerializer(serializers.Serializer):
    photos = serializers.ListField(child=serializers.IntegerField(min_value=1))


class PhotoSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = ["id", "name", "data"]

    def get_data(self, photo) -> str:
        return (
            "data:"
            + photo.mime_type
            + ";base64,"
            + base64.b64encode(bytes(photo.content)).decode()
        )


MAX_PHOTO_BYTES = 5 * 1024 * 1024


class UploadSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    content = serializers.CharField(
        max_length=7 * 1024 * 1024,
        trim_whitespace=False,
        error_messages={"max_length": "too_large"},
    )

    def validate(self, attrs):
        try:
            content = base64.b64decode(attrs["content"], validate=True)
        except (binascii.Error, ValueError):
            raise serializers.ValidationError("invalid_image")
        if len(content) > MAX_PHOTO_BYTES:
            raise serializers.ValidationError("too_large")
        try:
            with Image.open(BytesIO(content)) as image:
                fmt = image.format
                if fmt not in ["JPEG", "PNG", "WEBP"]:
                    raise serializers.ValidationError("invalid_format")
                image.verify()
            with Image.open(BytesIO(content)) as image:
                image.load()
        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
            Image.DecompressionBombError,
        ):
            raise serializers.ValidationError("invalid_image")
        attrs["content"] = content
        attrs["mime_type"] = {
            "JPEG": "image/jpeg",
            "PNG": "image/png",
            "WEBP": "image/webp",
        }[fmt]
        return attrs


class DecommissionSerializer(serializers.Serializer):
    reason = serializers.CharField()
    confirmed = serializers.BooleanField()

    def validate_confirmed(self, value):
        if not value:
            raise serializers.ValidationError("confirmation_required")
        return value


class MissingPieceSerializer(serializers.Serializer):
    state = serializers.ChoiceField(
        choices=["stolen", "lost"],
        error_messages={"required": "required", "invalid_choice": "invalid_state"},
    )
    event_date = serializers.DateField(
        error_messages={"required": "required", "invalid": "invalid_date"},
    )
    observations = serializers.CharField(required=False, allow_blank=True, default="")
    confirmed = serializers.BooleanField(error_messages={"required": "confirmation_required"})

    def validate_confirmed(self, value):
        if not value:
            raise serializers.ValidationError("confirmation_required")
        return value

    def validate_event_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("future_date")
        return value


class LoanSerializer(serializers.Serializer):
    recipient = serializers.CharField(
        max_length=200,
        error_messages={"required": "required", "blank": "required", "max_length": "recipient_too_long"},
    )
    start_date = serializers.DateField(error_messages={"required": "required", "invalid": "invalid_date"})
    end_date = serializers.DateField(error_messages={"required": "required", "invalid": "invalid_date"})

    def validate(self, attrs):
        if attrs["end_date"] < attrs["start_date"]:
            raise serializers.ValidationError({"end_date": "invalid_loan_period"})
        return attrs
