from datetime import datetime
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from api.models import User
from .models import Piece
from .reports import collection_report_data


class CollectionReportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="museum@example.com", full_name="Museum", role=User.Role.MUSEOLOGO,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.displayed = Piece.objects.create(title="Display", state="displayed", location="Room 1", object_type="Painting", collection="Art")
        Piece.objects.create(title="Storage", object_type="Sculpture", collection="Art")
        Piece.objects.create(title="History", object_type="Painting", collection="History")
        Piece.objects.create(title="Inactive storage", decommissioned=True, object_type="Painting", collection="Art")
        Piece.objects.create(title="Inactive display", state="displayed", location="Room 2", decommissioned=True, object_type="Sculpture", collection="History")
        Piece.objects.create(title="Unassigned")

    def test_counts_composition_and_legacy_decommissions(self):
        data = collection_report_data()
        self.assertEqual(data["total"], 6)
        self.assertEqual(data["active"], 4)
        self.assertEqual(data["by_state"], {"displayed": 1, "stored": 3, "loaned": 0, "missing": 0, "decommissioned": 2})
        self.assertEqual(data["by_object_type"], {"": 1, "Painting": 3, "Sculpture": 2})
        self.assertEqual(data["by_collection"], {"": 1, "Art": 3, "History": 2})
        for key in ["by_state", "by_object_type", "by_collection"]:
            self.assertEqual(sum(data[key].values()), data["total"])

    def test_state_type_collection_and_combined_filters(self):
        self.assertEqual(collection_report_data(state="displayed")["total"], 1)
        self.assertEqual(collection_report_data(state="stored")["total"], 3)
        self.assertEqual(collection_report_data(state="decommissioned")["total"], 2)
        self.assertEqual(collection_report_data(collection="Art")["total"], 3)
        self.assertEqual(collection_report_data(object_type="Painting")["total"], 3)
        filtered = collection_report_data(state="decommissioned", object_type="Painting", collection="Art")
        self.assertEqual(filtered["total"], 1)
        self.assertEqual(filtered["filters"], {"state": "decommissioned", "object_type": "Painting", "collection": "Art"})
        self.assertEqual(collection_report_data(state="stored", object_type="Painting", collection="Art")["total"], 0)

    def test_unassigned_is_distinct_from_all(self):
        self.assertEqual(collection_report_data(collection="")["total"], 1)
        self.assertEqual(collection_report_data(object_type="")["total"], 1)
        self.assertEqual(collection_report_data(collection=None)["total"], 6)
        self.assertEqual(self.client.get("/api/collection/report/?collection=").json()["total"], 1)

    def test_future_lifecycle_states_have_zero_counts_without_other_prs(self):
        for state in ["loaned", "stolen", "lost", "missing"]:
            with self.subTest(state=state):
                response = self.client.get("/api/collection/report/", {"state": state})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["total"], 0)
                self.assertTrue(all(count == 0 for count in response.json()["by_state"].values()))

    def test_all_lifecycle_categories_and_missing_filters(self):
        # SIAM-21/25/26 introduce these states in separate PRs. Test their grouped
        # records without importing their schema or endpoints into this PR.
        groups = [
            {"state": state, "decommissioned": False, "object_type": "Painting", "collection": "Art", "count": count}
            for state, count in [("displayed", 1), ("stored", 2), ("loaned", 3), ("stolen", 4), ("lost", 5), ("decommissioned", 6)]
        ]
        groups.append({"state": "loaned", "decommissioned": True, "object_type": "Sculpture", "collection": "History", "count": 7})
        with patch("collection_integrity.reports.Piece.objects.values") as values:
            values.return_value.annotate.return_value.order_by.return_value = groups
            data = collection_report_data()
            self.assertEqual(data["total"], 28)
            self.assertEqual(data["active"], 6)
            self.assertEqual(data["by_state"], {"displayed": 1, "stored": 2, "loaned": 3, "missing": 9, "decommissioned": 13})
            self.assertEqual(data["missing_breakdown"], {"stolen": 4, "lost": 5})
            self.assertEqual(collection_report_data(state="missing")["total"], 9)
            self.assertEqual(collection_report_data(state="stolen")["total"], 4)
            self.assertEqual(collection_report_data(state="lost")["total"], 5)
            self.assertEqual(collection_report_data(state="loaned")["total"], 3)

    def test_endpoint_and_consolidated_function_return_same_figures(self):
        expected = collection_report_data(collection="Art")
        response = self.client.get("/api/collection/report/", {"collection": "Art"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        actual = response.json()
        expected.pop("generated_at")
        actual.pop("generated_at")
        self.assertEqual(actual, expected)

    def test_one_query_and_generation_time_without_cache(self):
        before = timezone.now()
        with self.assertNumQueries(1):
            initial = collection_report_data()
        generated = datetime.fromisoformat(initial["generated_at"])
        self.assertGreaterEqual(generated, before)
        self.assertLessEqual(generated, timezone.now())
        self.displayed.decommissioned = True
        self.displayed.save()
        current = collection_report_data()
        self.assertEqual(current["by_state"]["displayed"], 0)
        self.assertEqual(current["by_state"]["decommissioned"], 3)
        self.assertEqual(current["total"], initial["total"])

    def test_empty_dataset_and_no_matches(self):
        empty = collection_report_data(collection="No matches")
        self.assertEqual(empty["total"], 0)
        self.assertEqual(empty["by_object_type"], {})
        self.assertEqual(empty["by_collection"], {})
        self.assertEqual(empty["available_filters"]["collections"], ["", "Art", "History"])
        Piece.objects.all().delete()
        empty = collection_report_data()
        self.assertEqual(empty["total"], 0)
        self.assertEqual(empty["available_filters"], {"object_types": [], "collections": []})
        self.assertEqual(len(empty["by_state"]), 5)

    def test_invalid_filters_are_rejected(self):
        self.assertEqual(self.client.get("/api/collection/report/?state=invalid").status_code, 400)
        with self.assertRaises(ValidationError):
            collection_report_data(state="invalid")
        with self.assertRaises(ValidationError):
            collection_report_data(collection="x" * 201)

    def test_only_museologist_can_generate_report(self):
        for role in User.Role.values:
            if role != User.Role.MUSEOLOGO:
                with self.subTest(role=role):
                    self.user.role = role
                    self.user.save()
                    self.assertEqual(self.client.get("/api/collection/report/").status_code, 403)

    def test_collection_can_be_edited_or_cleared_without_losing_other_data(self):
        url = f"/api/pieces/{self.displayed.pk}/"
        self.assertEqual(self.client.patch(url, {"collection": "New collection"}, format="json").status_code, 200)
        self.displayed.refresh_from_db()
        self.assertEqual((self.displayed.collection, self.displayed.title), ("New collection", "Display"))
        self.assertEqual(collection_report_data(collection="New collection")["total"], 1)
        self.assertEqual(self.client.patch(url, {"collection": "x" * 201}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(url, {"collection": ""}, format="json").status_code, 200)
        self.assertEqual(collection_report_data(collection="")["total"], 2)

    def test_session_and_active_account_are_required(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get("/api/collection/report/").status_code, 401)
        self.user.is_active = False
        self.user.save()
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get("/api/collection/report/").status_code, 403)

    def test_collection_is_optional_on_registration_and_available_to_report(self):
        payload = {
            "title": "New", "object_type": "Painting", "materials_techniques": "Oil",
            "measurement_value": 1, "measurement_unit": "cm", "inscriptions_marks": "Mark",
            "distinguishing_features": "Detail", "subject": "Portrait", "date_period": "1900", "author_maker": "Artist",
        }
        response = self.client.post("/api/pieces/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["collection"], "")
        response = self.client.post("/api/pieces/", payload | {"collection": "New collection"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(collection_report_data(collection="New collection")["total"], 1)
