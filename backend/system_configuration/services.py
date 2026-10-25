from audit.models import AuditEntry
from audit.services import record
from django.db import transaction

from .defaults import DEFAULTS, default_for
from .models import Parameter
from .serializers import ConfigurationSerializer


def current_configuration():
    values = {key: default_for(key) for key in DEFAULTS}
    values.update(
        Parameter.objects.filter(key__in=DEFAULTS).values_list("key", "value")
    )
    return values


@transaction.atomic
def update_configuration(*, user, values):
    validated = ConfigurationSerializer(data=values, partial=True)
    validated.is_valid(raise_exception=True)
    for key, value in validated.validated_data.items():
        parameter, _ = Parameter.objects.select_for_update().get_or_create(
            key=key, defaults={"value": default_for(key)}
        )
        old = parameter.value
        if old == value:
            continue
        parameter.value = value
        parameter.save(update_fields=["value"])
        record(
            user=user,
            action_type=AuditEntry.Action.MODIFY,
            entity="system_parameter",
            entity_id=key,
            old={key: old},
            new={key: value},
        )
    return current_configuration()
