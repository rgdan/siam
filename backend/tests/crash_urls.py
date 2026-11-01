import os
import threading
from pathlib import Path

from api.models import User
from audit.models import AuditEntry
from collection_integrity.models import Photo, Piece
from collection_integrity.services import collection_transaction, register_piece
from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt


def status(request):
    return JsonResponse(
        {
            "titles": list(
                Piece.objects.order_by("pk").values_list("title", flat=True)
            ),
            "counts": [
                model.objects.count()
                for model in (Piece, Photo, AuditEntry)
            ],
            "photos": [bytes(p.content).decode() for p in Photo.objects.order_by("pk")],
        }
    )


@csrf_exempt
def write(request):
    if request.method != "POST":
        return JsonResponse({}, status=405)
    user = User.objects.get(email="crash@test.cr")
    with collection_transaction():
        register_piece(
            user=user,
            title="interrupted",
            photos=[{"name": "partial", "content": b"partial"}],
        )

        Path(os.environ["SIAM_CRASH_MARKER"]).write_text(
            "uncommitted", encoding="utf-8"
        )
        threading.Event().wait(120)
    return JsonResponse({})


urlpatterns = [path("status/", status), path("write/", write)]
