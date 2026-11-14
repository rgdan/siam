from django.urls import path
from . import consolidated, exports


urlpatterns = [
    path('reports/consolidated/', consolidated.consolidated_report, name='consolidated-report'),
    path('reports/export/<str:tipo>/<str:formato>/', exports.export_report, name='report-export'),
]
