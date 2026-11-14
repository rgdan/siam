from django.test import TestCase
from rest_framework.test import APIClient

from .models import User


class AccountTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            email="admin@example.com", password="Admin12345", full_name="Admin",
            role=User.Role.ADMINISTRADOR_SISTEMA,
        )

    def test_login_rotates_csrf_and_logout_ends_session(self):
        client = APIClient(enforce_csrf_checks=True)
        credentials = {"email": self.admin.email, "password": "Admin12345"}
        self.assertEqual(client.post("/api/auth/login/", credentials).status_code, 403)
        token = client.get("/api/auth/csrf/").json()["csrfToken"]
        response = client.post(
            "/api/auth/login/", credentials, format="json", HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()["csrfToken"], token)
        account = client.get("/api/auth/me/").json()
        self.assertEqual(account["id"], self.admin.pk)
        self.assertIn("sistema.configurar", account["permissions"])
        self.assertNotIn("password", account)
        token = response.json()["csrfToken"]
        self.assertEqual(client.post("/api/auth/logout/", HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertEqual(client.get("/api/auth/me/").status_code, 401)

    def test_user_creation_hashes_password_and_rejects_duplicate_email(self):
        client = APIClient()
        client.force_authenticate(self.admin)
        data = {
            "email": "guard@example.com", "full_name": "Guard",
            "role": User.Role.GUARDA, "password": "Guard12345",
        }
        response = client.post("/api/users/", data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.json())
        self.assertTrue(User.objects.get(pk=response.json()["id"]).check_password(data["password"]))
        self.assertEqual(client.post("/api/users/", data, format="json").status_code, 400)

    def test_last_administrator_cannot_be_demoted(self):
        client = APIClient()
        client.force_authenticate(self.admin)
        response = client.patch(
            f"/api/users/{self.admin.pk}/", {"role": User.Role.GUARDA}, format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, User.Role.ADMINISTRADOR_SISTEMA)
