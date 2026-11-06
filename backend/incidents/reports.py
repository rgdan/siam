from django.db.models import Count

from .models import Incident


def incident_report_data(fecha_inicio=None, fecha_fin=None):
    incidents = Incident.objects.all()
    if fecha_inicio is not None:
        incidents = incidents.filter(timestamp__date__gte=fecha_inicio)
    if fecha_fin is not None:
        incidents = incidents.filter(timestamp__date__lte=fecha_fin)
    counts = {category: 0 for category in Incident.Category.values}
    counts.update({row["category"]: row["total"] for row in
                   incidents.values("category").annotate(total=Count("pk"))})
    return {"total": sum(counts.values()), "por_categoria": counts}
