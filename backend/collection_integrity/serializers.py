import base64
import binascii
from io import BytesIO

from PIL import Image, UnidentifiedImageError
from rest_framework import serializers

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
    class Meta:
        model = Piece
        fields = [
            "id",
            "identifier",
            *OBJECT_FIELDS,
            "collection",
            "state",
            "location",
            "decommissioned",
        ]
        read_only_fields = ["id", "identifier", "decommissioned"]
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
        for key in ["id", "identifier", "decommissioned"]:
            if key in self.initial_data:
                errors[key] = "immutable"
        if self.instance is None:
            if "state" in self.initial_data and attrs.get("state") != "stored":
                errors["state"] = "initial_storage"
            attrs["state"] = "stored"
        state = attrs.get("state", self.instance.state if self.instance else "stored")
        if state not in ["stored", "displayed"]:
            errors["state"] = "invalid_state"
        location = attrs.get(
            "location", self.instance.location if self.instance else ""
        )
        if state == "displayed" and not location.strip():
            errors["location"] = "required"
        if state == "stored":
            attrs["location"] = ""
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

    def get_data(self, photo):
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
