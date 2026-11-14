from drf_spectacular.utils import inline_serializer
from rest_framework import serializers as s
from core.schema import ERRORS, DETAIL, CONFIRM
from .serializers import UserSerializer


CSRF = inline_serializer("CSRFToken", {"csrfToken": s.CharField()})


LOGIN_RESULT = inline_serializer("LoginResult", {"detail": s.CharField(), "csrfToken": s.CharField()})


class SessionUserSerializer(UserSerializer):
    permissions = s.ListField(child=s.CharField())

    class Meta(UserSerializer.Meta):
        fields = ["id", "full_name", "email", "role", "permissions"]


DELETE_USER = inline_serializer("DeleteUserResult", {
    "detail": s.CharField(), "action": s.ChoiceField(choices=["deleted", "deactivated"]),
})

