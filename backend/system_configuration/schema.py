from drf_spectacular.utils import inline_serializer
from rest_framework import serializers as s
from core.schema import ERRORS
from .serializers import ConfigurationSerializer


CONFIGURATION = inline_serializer("ConfigurationResult", {
    "values": ConfigurationSerializer(), "defaults": ConfigurationSerializer(),
})

