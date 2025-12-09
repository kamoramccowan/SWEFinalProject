from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from game.models import Challenge, GameSession


class SessionResultsAndHintTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='alice', password='pw123456')
        self.challenge = Challenge.objects.create(
            creator_user_id=str(self.user.id),
            title="Playable",
            description="",
            grid=[["T", "E"], ["S", "T"]],
            difficulty="easy",
        )
        self.challenge.valid_words = ["TEST", "WORD"]
        self.challenge.save(update_fields=['valid_words'])
        self.session = GameSession.objects.create(
            challenge=self.challenge,
            player_user_id=str(self.user.id),
            mode=GameSession.MODE_CHALLENGE,
            start_time=timezone.now(),
            duration_seconds=300,
            hint_uses=0,
            submissions=[
                {"word": "TEST", "is_valid": True, "score_delta": 4, "timestamp": timezone.now().isoformat()}
            ],
            score=4,
        )
        self.results_url = reverse('game_sessions_results', args=[self.session.id])
        self.hint_url = reverse('game_sessions_hint', args=[self.session.id])

    def test_results_after_end(self):
        self.session.end_time = timezone.now()
        self.session.save(update_fields=['end_time'])

        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.results_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("all_valid_words", resp.data)
        self.assertIn("found_words", resp.data)
        self.assertEqual(resp.data["found_words"], ["TEST"])
        self.assertIn("WORD", resp.data["all_valid_words"])
        self.assertEqual(resp.data["score"], 4)

    def test_results_block_if_active(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.results_url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data.get("error_code"), "SESSION_ACTIVE")

    def test_hint_only_unfound_and_active(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.hint_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("WORD", self.challenge.valid_words)
        self.assertEqual(resp.data["hint"]["first_letter"], "W")
        self.assertEqual(resp.data["hint"]["length"], 4)
        self.assertEqual(resp.data["remaining"], 2)

    def test_hint_limit(self):
        self.client.force_authenticate(user=self.user)
        for _ in range(3):
            resp = self.client.get(self.hint_url)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self.client.get(self.hint_url)
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(resp.data.get("error_code"), "HINT_LIMIT_REACHED")

    def test_hint_blocks_after_time_up(self):
        self.session.start_time = timezone.now() - timedelta(seconds=600)
        self.session.duration_seconds = 1
        self.session.save(update_fields=['start_time', 'duration_seconds'])

        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.hint_url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data.get("error_code"), "TIME_UP")
