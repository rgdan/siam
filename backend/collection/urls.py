from django.urls import path
from . import views


urlpatterns = [
    path('pieces/<int:piece_id>/reactivate/', views.reactivate, name='piece-reactivate'),
    path('pieces/<int:piece_id>/recover/', views.recover, name='piece-recover'),
    path('pieces/<int:piece_id>/decommission/', views.decommission, name='piece-decommission'),
    path('pieces/<int:piece_id>/missing/', views.missing, name='piece-missing'),
    path('pieces/<int:piece_id>/loan/', views.loan, name='piece-loan'),
    path('pieces/<int:piece_id>/return/', views.return_loan, name='piece-return'),
    path('collection/report/', views.collection_report, name='collection-report'),
    path('pieces/', views.pieces, name='pieces'),
    path('pieces/<int:piece_id>/', views.piece_detail, name='piece-detail'),
    path('pieces/<int:piece_id>/photos/', views.upload_photos, name='piece-photos'),
    path('pieces/<int:piece_id>/photos/order/', views.reorder_photos, name='piece-photo-order'),
]
