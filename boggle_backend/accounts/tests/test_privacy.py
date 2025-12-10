from unittest import mock

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.privacy import can_receive_challenge
from game.models import Challenge


class PrivacyTests(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.alice = self.User.objects.create_user(
            username="alice", password="pw", firebase_uid="uid-a", email="alice@example.com"
        )
        self.settings_url = "/api/settings/"
        self.challenge = Challenge.objects.create(
            creator_user_id=str(self.alice.id),
            title="c1",
            description="",
            grid=[["A"]],
            difficulty="easy",
            valid_words=["A"],
        )
        self.send_url = f"/api/challenges/{self.challenge.id}/send/"

    @mock.patch("accounts.authentication.verify_firebase_id_token")
    def test_default_allows_incoming(self, mock_verify):
        mock_verify.return_value = {"uid": self.alice.firebase_uid}
        resp = self.client.get(self.settings_url, HTTP_AUTHORIZATION="Bearer token")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(can_receive_challenge(self.alice))

    @mock.patch("accounts.authentication.verify_firebase_id_token")
    def test_block_incoming(self, mock_verify):
        mock_verify.return_value = {"uid": self.alice.firebase_uid}
        resp = self.client.patch(
            self.settings_url,
            {"challenge_visibility": "no-one", "allow_incoming_challenges": False},
            format="json",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.alice.refresh_from_db()
        self.assertFalse(can_receive_challenge(self.alice))

    def test_requires_auth(self):
        resp = self.client.get(self.settings_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch("accounts.authentication.verify_firebase_id_token")
    def test_send_respects_block(self, mock_verify):
        # Sender is bob, recipient is alice
        bob = self.User.objects.create_user(username="bob", password="pw", firebase_uid="uid-b")
        mock_verify.return_value = {"uid": bob.firebase_uid}
        # Alice blocks incoming
        alice_settings = self.alice.usersettings if hasattr(self.alice, "usersettings") else None
        if not alice_settings:
            alice_settings = self.alice.settings if hasattr(self.alice, "settings") else None
        if not alice_settings:
            from accounts.models import UserSettings
            alice_settings, _ = UserSettings.objects.get_or_create(user=self.alice)
        alice_settings.challenge_visibility = "no-one"
        alice_settings.allow_incoming_challenges = False
        alice_settings.save(update_fields=["challenge_visibility", "allow_incoming_challenges", "updated_at"])

        resp = self.client.post(
            self.send_url,
            {"target_user_id": self.alice.id},
            format="json",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch("accounts.authentication.verify_firebase_id_token")
    def test_send_allowed_when_whitelisted(self, mock_verify):
        bob = self.User.objects.create_user(username="bob", password="pw", firebase_uid="uid-b")
        mock_verify.return_value = {"uid": bob.firebase_uid}
        # Alice allows only bob
        from accounts.models import UserSettings
        settings, _ = UserSettings.objects.get_or_create(user=self.alice)
        settings.allowed_sender_user_ids = [bob.id]
        settings.save(update_fields=["allowed_sender_user_ids", "updated_at"])

        resp = self.client.post(
            self.send_url,
            {"target_user_id": self.alice.id},
            format="json",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("email_sent", resp.data)

    @mock.patch("accounts.authentication.verify_firebase_id_token")
    def test_send_requires_recipient_email(self, mock_verify):
        # Remove alice email
        self.alice.email = ""
        self.alice.save(update_fields=["email"])
        bob = self.User.objects.create_user(username="bob", password="pw", firebase_uid="uid-b")
        mock_verify.return_value = {"uid": bob.firebase_uid}
        resp = self.client.post(
            self.send_url,
            {"target_user_id": self.alice.id},
            format="json",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data.get("error_code"), "RECIPIENT_NO_EMAIL")
