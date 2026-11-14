"""Shared collection figures for RF-MUS-07 and the SIAM-27 consolidated report."""
from collections import Counter

from django.db.models import Count
from django.utils import timezone
from rest_framework import serializers

from .models import Piece


REPORT_STATES = ("displayed", "stored", "loaned", "missing", "stolen", "lost", "decommissioned")


class CollectionReportFilters(serializers.Serializer):
    state = serializers.ChoiceField(choices=REPORT_STATES, required=False)
    object_type = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)
    collection = serializers.CharField(required=False, allow_blank=True, max_length=200, trim_whitespace=False)


def collection_report_data(*, state=None, object_type=None, collection=None):
    """Return JSON-ready figures from one grouped database query, without writes.

    Internal callers (including SIAM-27) enforce their own access permissions.
    Filters match exact values. None means all; an empty string selects an
    unassigned collection/type. The 'missing' state groups stolen and lost.
    Both the legacy decommissioned flag and the lifecycle state mean De baja.
    """
    serializer = CollectionReportFilters(data={
        key: value for key, value in {
            "state": state, "object_type": object_type, "collection": collection,
        }.items() if value is not None
    })
    serializer.is_valid(raise_exception=True)
    filters = {key: serializer.validated_data.get(key) for key in ["state", "object_type", "collection"]}

    # All counts and filter options come from this single statement, so concurrent
    # changes cannot cause disagreement between totals and category breakdowns.
    groups = list(Piece.objects.values("state", "decommissioned", "object_type", "collection").annotate(count=Count("pk")).order_by())
    generated_at = timezone.now().isoformat()
    states, types, collections = Counter(), Counter(), Counter()
    for group in groups:
        current = "decommissioned" if group["decommissioned"] or group["state"] == "decommissioned" else group["state"]
        if filters["state"] is not None:
            included_states = ("stolen", "lost") if filters["state"] == "missing" else (filters["state"],)
            if current not in included_states:
                continue
        if filters["object_type"] is not None and group["object_type"] != filters["object_type"]:
            continue
        if filters["collection"] is not None and group["collection"] != filters["collection"]:
            continue
        states[current] += group["count"]
        types[group["object_type"]] += group["count"]
        collections[group["collection"]] += group["count"]

    return {
        "generated_at": generated_at,
        "filters": filters,
        "total": sum(states.values()),
        "active": sum(states[key] for key in ["displayed", "stored", "loaned"]),
        "by_state": {
            "displayed": states["displayed"], "stored": states["stored"], "loaned": states["loaned"],
            "missing": states["stolen"] + states["lost"], "decommissioned": states["decommissioned"],
        },
        "missing_breakdown": {"stolen": states["stolen"], "lost": states["lost"]},
        "by_object_type": dict(sorted(types.items())),
        "by_collection": dict(sorted(collections.items())),
        "available_filters": {
            "object_types": sorted({group["object_type"] for group in groups}),
            "collections": sorted({group["collection"] for group in groups}),
        },
    }
