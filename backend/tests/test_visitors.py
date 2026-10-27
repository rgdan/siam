from itertools import product

from api.models import User
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone
from visitors.models import VisitorEntry


class VisitorEntryModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.guard = User.objects.create_user(
            email="guard@test.cr", full_name="Guard", role=User.Role.GUARDA
        )

    def test_each_combination_preserves_categories_time_and_guard(self):
        before = timezone.now()
        for age_group, nationality, sex in product(
            VisitorEntry.AgeGroup.values,
            VisitorEntry.Nationality.values,
            VisitorEntry.Sex.values,
        ):
            with self.subTest(age_group=age_group, nationality=nationality, sex=sex):
                entry = VisitorEntry.objects.create(
                    age_group=age_group,
                    nationality=nationality,
                    sex=sex,
                    user=self.guard,
                )
                entry.refresh_from_db()
                self.assertEqual(
                    (entry.age_group, entry.nationality, entry.sex, entry.user_id),
                    (age_group, nationality, sex, self.guard.pk),
                )
                self.assertLessEqual(before, entry.timestamp)
                self.assertLessEqual(entry.timestamp, timezone.now())
        self.assertEqual(VisitorEntry.objects.count(), 8)

    def test_database_rejects_invalid_or_missing_categories_and_guard(self):
        valid = {
            "age_group": "mayor",
            "nationality": "nacional",
            "sex": "femenino",
            "user": self.guard,
        }
        for field in ("age_group", "nationality", "sex", "user"):
            invalid_values = (None,) if field == "user" else ("invalid", "", None)
            for value in invalid_values:
                with self.subTest(field=field, value=value):
                    with self.assertRaises(IntegrityError), transaction.atomic():
                        VisitorEntry.objects.create(**{**valid, field: value})
        self.assertEqual(VisitorEntry.objects.count(), 0)

    def test_entry_prevents_deleting_registering_guard(self):
        entry = VisitorEntry.objects.create(
            age_group="menor", nationality="extranjero", sex="masculino",
            user=self.guard,
        )
        self.assertTrue(self.guard.has_related_records())
        with self.assertRaises(ProtectedError):
            self.guard.delete()
        self.assertTrue(VisitorEntry.objects.filter(pk=entry.pk).exists())
