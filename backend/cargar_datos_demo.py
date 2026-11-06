import os
from datetime import datetime, timedelta
from io import BytesIO
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo

import django

INICIO_DEMO = datetime(2026, 11, 23, 9, tzinfo=ZoneInfo("America/Costa_Rica"))


def _crear_demo(model, *, user, entity, lookup, defaults=None):
    from audit.services import audited_create

    existing = model.objects.filter(**lookup).first()
    if existing is not None:
        return existing

    def guardar():
        instance = model(**{**(defaults or {}), **lookup})
        instance.full_clean()
        instance.save()
        # auto_now_add uses the execution date; these fixtures need their scenario date.
        if "timestamp" in lookup:
            model.objects.filter(pk=instance.pk).update(timestamp=lookup["timestamp"])
            instance.timestamp = lookup["timestamp"]
        return instance

    return audited_create(user=user, entity=entity, create=guardar)


def _foto_demo(numero, vista):
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (640, 480), "#f4f0e6")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 640, 72), fill="#00243e")
    font = ImageFont.load_default(size=22)
    draw.text((24, 22), "SIAM / DEMO", fill="white", font=font)
    color = ["#b10c00", "#315168", "#7b5a34"][numero % 3]
    if vista == 0:
        draw.ellipse((230, 120, 410, 350), fill=color)
        draw.rectangle((270, 110, 370, 145), fill=color)
    else:
        draw.rounded_rectangle((180, 140, 460, 320), radius=12, fill=color)
    draw.text((24, 395), f"SAMPLE {numero:02d} / VIEW {vista + 1}", fill="#00243e", font=font)
    draw.text((24, 435), "Illustration, not an actual museum object", fill="#00243e", font=font)
    content = BytesIO()
    image.save(content, format="PNG")
    return {"name": f"demo-{numero}-{vista + 1}.png", "mime_type": "image/png", "content": content.getvalue()}


def cargar_datos_demo():
    from django.db import transaction
    from django.utils import timezone
    from api.models import Evento, User
    from audit.models import AuditEntry
    from audit.services import audited_create
    from collection_integrity.models import Piece
    from collection_integrity.services import register_piece
    from incidents.models import Incident
    from system_configuration.defaults import DEFAULTS, default_for
    from system_configuration.models import Parameter
    from visitors.models import VisitorEntry

    with transaction.atomic():
        print("Solo para desarrollo local: estas cuentas usan una contraseña pública.")
        for role, nombre in User.Role.choices:
            email = f"{role}@demo.siam.test"
            if User.objects.filter(email__iexact=email).exists():
                print(f"Ya existe, sin cambios: {email}")
                continue
            audited_create(
                user=None, entity="user",
                create=lambda: User.objects.create_user(
                    email=email, password="Demo12345",
                    full_name=f"Demo {nombre}", role=role,
                ),
            )
            print(f"Creada: {email} ({nombre})")
        users = {role: User.objects.get(email__iexact=f"{role}@demo.siam.test") for role in User.Role.values}
        guarda = users[User.Role.GUARDA]
        coordinador = users[User.Role.COORDINADOR]
        museologo = users[User.Role.MUSEOLOGO]
        administrador = users[User.Role.ADMINISTRADOR_SISTEMA]

        for key in DEFAULTS:
            _crear_demo(Parameter, user=administrador, entity="system_parameter",
                        lookup={"key": key}, defaults={"value": default_for(key)})

        piezas = [
            ("vasija", "Vasija didáctica", "Arqueología", "Cerámica", "displayed", "Arcilla"),
            ("documento", "Documento facsímil", "Historia", "Documento", "displayed", "Papel y tinta"),
            ("fotografia", "Fotografía de referencia", "Fotografía", "Fotografía", "stored", "Papel fotográfico"),
            ("medalla", "Medalla de reproducción", "Historia", "Medalla", "stored", "Metal"),
            ("textil", "Textil didáctico", "Vida cotidiana", "Textil", "loaned", "Algodón"),
            ("placa", "Placa demostrativa", "Historia", "Placa", "decommissioned", "Yeso"),
            ("grabado", "Grabado de reproducción", "Arte", "Grabado", "stolen", "Papel"),
            ("mapa", "Mapa facsímil", "Historia", "Mapa", "lost", "Papel y tinta"),
            ("libro", "Libro de práctica", "", "Libro", "stored", "Papel y cartón"),
        ]
        for numero, (slug, title, collection, object_type, state, material) in enumerate(piezas, 1):
            identifier = uuid5(NAMESPACE_URL, f"https://demo.siam.test/pieces/{slug}")
            if Piece.objects.filter(identifier=identifier).exists():
                continue
            fields = {
                "state": state, "collection": collection, "object_type": object_type,
                "materials_techniques": material, "measurement_value": "24.5000",
                "measurement_unit": "cm", "inscriptions_marks": f"DEMO-{numero:03d}",
                "distinguishing_features": "Reproducción sintética para demostración del sistema.",
                "subject": "Patrimonio e historia de Costa Rica (ejemplo ficticio)",
                "date_period": "Siglo XIX (referencia didáctica)", "author_maker": "Autor de demostración",
                "location": f"Sala {numero}" if state == "displayed" else "",
            }
            if state == "loaned":
                fields.update(loan_to="Institución de ejemplo", loan_start=INICIO_DEMO.date(),
                              loan_end=(INICIO_DEMO + timedelta(days=7)).date())
            elif state == "decommissioned":
                fields.update(decommissioned=True, decommissioned_at=INICIO_DEMO,
                              decommissioned_by=museologo, decommission_reason="[DEMO] Deterioro de una reproducción didáctica.")
            elif state in ("stolen", "lost"):
                fields.update(event_date=INICIO_DEMO.date(),
                              event_observations="[DEMO] Escenario ficticio para practicar el registro y la recuperación.")
            register_piece(user=museologo, identifier=identifier, title=f"[DEMO] {title}",
                           photos=[_foto_demo(numero, vista) for vista in range(2)], **fields)

        eventos = [
            (-20, 10, "Visita escolar de referencia", "publico", 25, 23, "programado"),
            (-19, 10, "Taller de referencia", "publico", 30, 36, "programado"),
            (-19, 14, "Visita sin asistencia registrada", "privado", 15, None, "programado"),
            (-19, 16, "Actividad sin asistentes", "publico", 10, 0, "programado"),
            (-3, 10, "Introducción a la semana cultural", "publico", 40, 32, "programado"),
            (0, 10, "Recorrido por la Campaña Nacional", "publico", 35, 31, "programado"),
            (0, 14, "Reunión de coordinación", "privado", 12, None, "programado"),
            (1, 10, "Taller de patrimonio para escolares", "publico", 30, 28, "programado"),
            (2, 11, "Capacitación en conservación", "privado", 20, 18, "programado"),
            (3, 14, "Conversatorio de historia local", "publico", 50, None, "programado"),
            (4, 9, "Visita guiada accesible", "publico", 25, None, "programado"),
            (5, 10, "Jornada familiar", "publico", 80, None, "programado"),
            (5, 14, "Sesión de inventario cancelada", "privado", 15, None, "cancelado"),
            (6, 11, "Recorrido de cierre", "publico", 40, None, "programado"),
            (7, 9, "Evaluación de la semana cultural", "privado", 8, None, "programado"),
        ]
        for day, hour, title, tipo, expected, actual, estado in eventos:
            description = f"[DEMO] {title}"
            event_id = AuditEntry.objects.filter(
                entity="evento", action_type=AuditEntry.Action.CREATE,
                changes__descripcion__new=description,
            ).values_list("entity_id", flat=True).first()
            if event_id is not None and Evento.objects.filter(pk=event_id).exists():
                continue
            fecha = (INICIO_DEMO + timedelta(days=day)).replace(hour=hour)
            _crear_demo(Evento, user=coordinador, entity="evento", lookup={"descripcion": description},
                        defaults={"fecha": fecha, "tipo": tipo, "estado": estado,
                                  "ubicacion": "Sala de reuniones" if tipo == "privado" else "Sala principal",
                                  "asistentes_esperados": expected,
                                  "asistentes_reales": actual if fecha <= timezone.now() else None,
                                  "creado_por": coordinador})

        for day, total in enumerate([12, 16, 20, 14, 24, 30, 18]):
            for index in range(total):
                _crear_demo(VisitorEntry, user=guarda, entity="visitor_entry", lookup={
                    "timestamp": INICIO_DEMO + timedelta(days=day, minutes=index * 10),
                    "user": guarda,
                    "age_group": VisitorEntry.AgeGroup.values[index % 2],
                    "nationality": VisitorEntry.Nationality.values[(index // 2) % 2],
                    "sex": VisitorEntry.Sex.values[(index // 4) % 2],
                })

        descripciones = [
            "Paraguas de demostración encontrado en el vestíbulo.",
            "Luminaria de ejemplo fuera de servicio en una sala.",
            "Simulación de incumplimiento de normas de acceso.",
            "Simulacro de atención por mareo, sin datos de personas.",
            "Ejercicio de revisión de señalización del recorrido.",
        ]
        for day, (category, description) in enumerate(zip(Incident.Category.values, descripciones)):
            _crear_demo(Incident, user=guarda, entity="incident",
                        lookup={"timestamp": INICIO_DEMO + timedelta(days=day, hours=6),
                                "user": guarda, "category": category},
                        defaults={"description": f"[DEMO] {description}"})

    print("Datos sintéticos: 23–29 de noviembre de 2026; eventos de referencia: 3–4 de noviembre.")
    print("Carga completada. Los registros existentes se conservan sin cambios.")


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    cargar_datos_demo()
