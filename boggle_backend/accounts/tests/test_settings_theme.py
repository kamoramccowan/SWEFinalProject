from unittest import mock

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


class UserSettingsThemeTests(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username="themeuser", password="pw", firebase_uid="uid-theme")
        self.url = "/api/settings/"

    @mock.patch("accounts.authentication.verify_firebase_id_token")
    def test_default_theme(self, mock_verify):
        mock_verify.return_value = {"uid": self.user.firebase_uid}
        resp = self.client.get(self.url, HTTP_AUTHORIZATION="Bearer token")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get("theme"), "light")

    @mock.patch("accounts.authentication.verify_firebase_id_token")
    def test_update_theme(self, mock_verify):
        mock_verify.return_value = {"uid": self.user.firebase_uid}
        resp = self.client.patch(
            self.url,
            {"theme": "dark"},
            format="json",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get("theme"), "dark")
        resp2 = self.client.get(self.url, HTTP_AUTHORIZATION="Bearer token")
        self.assertEqual(resp2.data.get("theme"), "dark")

    @mock.patch("accounts.authentication.verify_firebase_id_token")
    def test_reject_invalid_theme(self, mock_verify):
        mock_verify.return_value = {"uid": self.user.firebase_uid}
        resp = self.client.patch(
            self.url,
            {"theme": "ultra"},
            format="json",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
