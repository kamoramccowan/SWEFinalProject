from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.firebase_auth import FirebaseVerificationError


class FirebaseAuthenticationTests(APITestCase):
    def setUp(self):
        self.verify_url = reverse("auth_login_verify")
        self.logout_url = reverse("auth_logout")
        self.UserModel = get_user_model()

    @patch("accounts.authentication.verify_firebase_id_token")
    def test_login_verify_creates_user(self, mock_verify):
        mock_verify.return_value = {"uid": "uid-123", "email": "user@example.com", "name": "Ada Lovelace"}

        response = self.client.post(self.verify_url, HTTP_AUTHORIZATION="Bearer test-token")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["firebase_uid"], "uid-123")
        self.assertEqual(response.data["email"], "user@example.com")
        self.assertEqual(response.data["display_name"], "Ada Lovelace")
        self.assertTrue(response.data["is_registered"])

        user = self.UserModel.objects.get(firebase_uid="uid-123")
        self.assertEqual(user.email, "user@example.com")
        self.assertEqual(user.display_name, "Ada Lovelace")

    @patch("accounts.authentication.verify_firebase_id_token")
    def test_login_verify_reuses_existing_user(self, mock_verify):
        existing = self.UserModel.objects.create_user(
            username="existing", password="pw123456", firebase_uid="uid-reuse", email="old@example.com"
        )
        mock_verify.return_value = {"uid": "uid-reuse", "email": "new@example.com", "name": "Updated Name"}

        response = self.client.post(self.verify_url, HTTP_AUTHORIZATION="Bearer token")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], existing.id)
        self.assertEqual(self.UserModel.objects.filter(firebase_uid="uid-reuse").count(), 1)

        existing.refresh_from_db()
        self.assertEqual(existing.email, "new@example.com")
        self.assertEqual(existing.display_name, "Updated Name")

    @patch("accounts.authentication.verify_firebase_id_token")
    def test_logout_acknowledged(self, mock_verify):
        mock_verify.return_value = {"uid": "uid-logout"}
        response = self.client.post(self.logout_url, HTTP_AUTHORIZATION="Bearer token")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

    def test_missing_token_returns_structured_error(self):
        response = self.client.post(self.verify_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data.get("error_code"), "AUTH_HEADER_MISSING")

    @patch("accounts.authentication.verify_firebase_id_token")
    def test_invalid_token_returns_structured_error(self, mock_verify):
        mock_verify.side_effect = FirebaseVerificationError("INVALID_ID_TOKEN", "bad token")

        response = self.client.post(self.verify_url, HTTP_AUTHORIZATION="Bearer bad")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data.get("error_code"), "INVALID_ID_TOKEN")
