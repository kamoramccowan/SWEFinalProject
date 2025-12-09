from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from game.models import Challenge, GameSession


class ChallengeShuffleLimitTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='alice', password='pw123456')
        self.challenge = Challenge.objects.create(
            creator_user_id=str(self.user.id),
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
        self.session = GameSession.objects.create(
            challenge=self.challenge,
            player_user_id=str(self.user.id),
            mode=GameSession.MODE_CHALLENGE,
        )
        self.url = reverse('game_challenges_shuffle', args=[self.challenge.id])

    def test_shuffle_limit_twice(self):
        self.client.force_authenticate(user=self.user)
        payload = {"session_id": self.session.id}
        resp1 = self.client.post(self.url, payload, format='json')
        resp2 = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        resp3 = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp3.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(resp3.data.get("error_code"), "SHUFFLE_LIMIT_REACHED")
