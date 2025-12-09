from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from game.models import Challenge, GameSession

# Dev A tests for FR-05: start a session for an active challenge; reject deleted/nonexistent.


class SessionCreateTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='alice', password='pw123456')
        self.challenge = Challenge.objects.create(
            creator_user_id=str(self.user.id),
            title="Playable",
            description="",
            grid=[["A", "B"], ["C", "D"]],
            difficulty="easy",
        )
        self.url = reverse('game_sessions_create')

    def test_start_session_success(self):
        payload = {
            "challenge_id": self.challenge.id,
            "mode": "challenge",
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data
        self.assertEqual(data["challenge"], self.challenge.id)
        self.assertNotIn("challenge_id", data)  # write-only; should not echo back
        self.assertEqual(data["mode"], "challenge")
        session = GameSession.objects.get(pk=data["id"])
        self.assertEqual(session.player_user_id, str(self.user.id))

    def test_start_session_deleted_challenge(self):
        self.challenge.status = Challenge.STATUS_DELETED
        self.challenge.save(update_fields=['status'])

        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"challenge_id": self.challenge.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("challenge_id", response.data.get("details", {}))

    def test_start_session_nonexistent_challenge(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"challenge_id": 9999}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("challenge_id", response.data.get("details", {}))
