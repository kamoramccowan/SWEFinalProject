from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from game.models import Challenge, GameSession

# Dev A tests for FR-06: one-word submission, timeout, and end session.


class SessionSubmitAndEndTests(APITestCase):
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
        )
        self.submit_url = reverse('game_sessions_submit_word', args=[self.session.id])
        self.end_url = reverse('game_sessions_end', args=[self.session.id])

    def test_submit_before_timeout(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.submit_url, {"word": "test"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.session.refresh_from_db()
        self.assertEqual(len(self.session.submissions), 1)
        self.assertEqual(self.session.submissions[0]["word"], "TEST")
        self.assertTrue(self.session.submissions[0]["is_valid"])
        self.assertGreater(self.session.score, 0)
        self.assertEqual(self.session.challenge.difficulty, "easy")

    def test_submit_after_timeout(self):
        self.session.start_time = timezone.now() - timedelta(seconds=600)
        self.session.duration_seconds = 1
        self.session.save(update_fields=['start_time', 'duration_seconds'])

        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.submit_url, {"word": "late"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get("error_code"), "TIME_UP")

    def test_submit_after_end(self):
        self.session.end_time = timezone.now()
        self.session.save(update_fields=['end_time'])

        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.submit_url, {"word": "late"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get("error_code"), "TIME_UP")

    def test_end_session_and_block_further_submissions(self):
        self.client.force_authenticate(user=self.user)
        end_resp = self.client.post(self.end_url, {}, format='json')
        self.assertEqual(end_resp.status_code, status.HTTP_200_OK)

        submit_resp = self.client.post(self.submit_url, {"word": "after"}, format='json')
        self.assertEqual(submit_resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(submit_resp.data.get("error_code"), "TIME_UP")

    def test_invalid_word_does_not_increase_score(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.submit_url, {"word": "zz"}, format='json')  # below min length for easy is 3
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.session.refresh_from_db()
        self.assertEqual(self.session.score, 0)
        self.assertFalse(self.session.submissions[0]["is_valid"])
