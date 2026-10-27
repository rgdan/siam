from api.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone
from incidents.models import Incident


class IncidentModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.guard = User.objects.create_user(
            email="incident-guard@test.cr", full_name="Guard", role=User.Role.GUARDA
        )

    def test_each_category_preserves_description_actor_and_automatic_time(self):
        before = timezone.now()
        for category in Incident.Category.values:
            with self.subTest(category=category):
                incident = Incident(
                    description="  Objeto encontrado junto a la entrada.  ",
                    category=category, user=self.guard,
                )
                incident.full_clean()
                incident.save()
                incident.refresh_from_db()
                self.assertEqual(incident.description, "Objeto encontrado junto a la entrada.")
                self.assertEqual((incident.category, incident.user_id), (category, self.guard.pk))
                self.assertLessEqual(before, incident.timestamp)
                self.assertLessEqual(incident.timestamp, timezone.now())
        self.assertEqual(Incident.objects.count(), 5)

    def test_description_minimum_counts_trimmed_characters(self):
        for description in ("", "123456789", " " * 10, " 123456789 ", "\t\n" * 10):
            with self.subTest(description=description):
                incident = Incident(description=description, category="otro", user=self.guard)
                with self.assertRaisesMessage(ValidationError, "10 caracteres"):
                    incident.full_clean()
        incident = Incident(description=" 1234567890 ", category="otro", user=self.guard)
        incident.full_clean()
        incident.save()
        self.assertEqual(incident.description, "1234567890")

    def test_database_rejects_invalid_description_category_and_missing_actor(self):
        valid = {"description": "1234567890", "category": "otro", "user": self.guard}
        for values in (
            {"description": ""}, {"description": "123456789"},
            {"description": " 123456789 "}, {"description": None},
            {"category": "invalid"}, {"category": ""}, {"category": None},
            {"user": None},
        ):
            with self.subTest(values=values):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    Incident.objects.create(**{**valid, **values})
        self.assertFalse(Incident.objects.exists())

    def test_registering_account_cannot_be_deleted(self):
        incident = Incident.objects.create(
            description="1234567890", category="otro", user=self.guard,
        )
        self.assertTrue(self.guard.has_related_records())
        with self.assertRaises(ProtectedError):
            self.guard.delete()
        self.assertTrue(Incident.objects.filter(pk=incident.pk).exists())
