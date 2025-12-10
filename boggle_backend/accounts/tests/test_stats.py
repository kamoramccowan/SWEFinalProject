from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from game.models import Challenge, GameSession


class UserStatsTests(APITestCase):
    def setUp(self):
        self.UserModel = get_user_model()
        self.user = self.UserModel.objects.create_user(username="u1", password="pw", firebase_uid="uid-1")
        self.other = self.UserModel.objects.create_user(username="u2", password="pw", firebase_uid="uid-2")
        self.challenge = Challenge.objects.create(
            creator_user_id=str(self.user.id),
            title="Challenge",
            description="",
            grid=[["A"]],
            difficulty="easy",
            valid_words=["A"],
        )
        self.stats_url = "/api/stats/"

    @mock.patch("accounts.authentication.verify_firebase_id_token")
    def test_stats_with_sessions(self, mock_verify):
        mock_verify.return_value = {"uid": self.user.firebase_uid}
        today = timezone.now()
        yesterday = today - timedelta(days=1)

        GameSession.objects.create(
            challenge=self.challenge,
            player_user_id=str(self.user.id),
            mode=GameSession.MODE_CHALLENGE,
            score=10,
            end_time=today,
            submissions=[
                {"word": "A", "is_valid": True},
                {"word": "B", "is_valid": False},
            ],
        )
        GameSession.objects.create(
            challenge=self.challenge,
            player_user_id=str(self.user.id),
            mode=GameSession.MODE_CHALLENGE,
            score=20,
            end_time=yesterday,
            submissions=[
                {"word": "C", "is_valid": True},
            ],
        )
        # Another user's session should not affect stats
        GameSession.objects.create(
            challenge=self.challenge,
            player_user_id=str(self.other.id),
            mode=GameSession.MODE_CHALLENGE,
            score=99,
            end_time=today,
            submissions=[{"word": "Z", "is_valid": True}],
        )

        resp = self.client.get(self.stats_url, HTTP_AUTHORIZATION="Bearer token")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        stats = resp.data["stats"]
        self.assertEqual(stats["games_played"], 2)
        self.assertEqual(stats["best_score"], 20)
        self.assertEqual(stats["average_score"], 15)
        self.assertEqual(stats["total_valid_words_found"], 2)
        self.assertEqual(stats["total_submissions"], 3)
        self.assertEqual(stats["correct_submissions"], 2)
        self.assertEqual(stats["incorrect_submissions"], 1)
        self.assertAlmostEqual(stats["accuracy"], 0.667, places=3)
        self.assertEqual(stats["days_played"], 2)
        self.assertEqual(stats["current_streak"], 2)
        self.assertGreaterEqual(stats["longest_streak"], 2)

    def test_stats_requires_auth(self):
        resp = self.client.get(self.stats_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch("accounts.authentication.verify_firebase_id_token")
    def test_stats_empty_defaults(self, mock_verify):
        mock_verify.return_value = {"uid": self.user.firebase_uid}
        resp = self.client.get(self.stats_url, HTTP_AUTHORIZATION="Bearer token")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        stats = resp.data["stats"]
        self.assertEqual(stats["games_played"], 0)
        self.assertEqual(stats["average_score"], 0)
        self.assertEqual(stats["best_score"], 0)
        self.assertEqual(stats["total_valid_words_found"], 0)
        self.assertEqual(stats["total_submissions"], 0)
        self.assertEqual(stats["correct_submissions"], 0)
        self.assertEqual(stats["incorrect_submissions"], 0)
        self.assertEqual(stats["accuracy"], 0)
        self.assertEqual(stats["days_played"], 0)
        self.assertEqual(stats["current_streak"], 0)
        self.assertEqual(stats["longest_streak"], 0)
