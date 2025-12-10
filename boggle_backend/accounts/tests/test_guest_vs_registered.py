from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from game.models import Challenge


class GuestVsRegisteredTests(APITestCase):
    def setUp(self):
        self.UserModel = get_user_model()
        self.challenge_create_url = reverse('game_challenges_create')
        self.session_create_url = reverse('game_sessions_create')

    def _auth_header(self):
        return {"HTTP_AUTHORIZATION": "Bearer token"}

    @patch("accounts.authentication.verify_firebase_id_token")
    def test_registered_can_create_challenge(self, mock_verify):
        mock_verify.return_value = {"uid": "uid-123", "email": "user@example.com", "name": "User"}
        payload = {
            "title": "Registered Challenge",
            "grid": [
                ["A", "B", "C", "D"],
                ["E", "F", "G", "H"],
                ["I", "J", "K", "L"],
                ["M", "N", "O", "P"],
            ],
            "difficulty": "easy",
        }
        resp = self.client.post(self.challenge_create_url, payload, format='json', **self._auth_header())
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_guest_cannot_create_challenge(self):
        payload = {
            "title": "Guest Challenge",
            "grid": [
                ["A", "B", "C", "D"],
                ["E", "F", "G", "H"],
                ["I", "J", "K", "L"],
                ["M", "N", "O", "P"],
            ],
            "difficulty": "easy",
        }
        resp = self.client.post(self.challenge_create_url, payload, format='json')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    @patch("accounts.authentication.verify_firebase_id_token")
    def test_guest_can_start_practice_session(self, mock_verify):
        # No auth header for guest
        resp = self.client.post(self.session_create_url, {"mode": "practice", "difficulty": "easy"}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    @patch("accounts.authentication.verify_firebase_id_token")
    def test_guest_cannot_start_challenge_session(self, mock_verify):
        user = self.UserModel.objects.create_user(username="alice", password="pw", firebase_uid="uid-abc")
        challenge = Challenge.objects.create(
            creator_user_id=str(user.id),
            title="Challenge",
            description="",
            grid=[
                ["A", "B", "C", "D"],
                ["E", "F", "G", "H"],
                ["I", "J", "K", "L"],
                ["M", "N", "O", "P"],
            ],
            difficulty="easy",
            valid_words=["ABCD"],
        )
        # guest: no auth header
        resp = self.client.post(self.session_create_url, {"challenge_id": challenge.id}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("accounts.authentication.verify_firebase_id_token")
    def test_registered_can_start_challenge_session(self, mock_verify):
        mock_verify.return_value = {"uid": "uid-registered"}
        self.client.post(self.challenge_create_url, {
            "title": "Registered Challenge",
            "grid": [
                ["A", "B", "C", "D"],
                ["E", "F", "G", "H"],
                ["I", "J", "K", "L"],
                ["M", "N", "O", "P"],
            ],
            "difficulty": "easy",
        }, format='json', **self._auth_header())

        challenge = Challenge.objects.first()
        resp = self.client.post(self.session_create_url, {"challenge_id": challenge.id}, format='json', **self._auth_header())
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
