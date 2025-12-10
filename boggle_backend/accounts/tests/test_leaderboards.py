from datetime import date, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import DailyChallenge
from game.models import Challenge, GameSession


class LeaderboardTests(APITestCase):
    def setUp(self):
        self.UserModel = get_user_model()
        self.user1 = self.UserModel.objects.create_user(username='u1', password='pw', firebase_uid='uid1')
        self.user2 = self.UserModel.objects.create_user(username='u2', password='pw', firebase_uid='uid2')
        self.challenge = Challenge.objects.create(
            creator_user_id=str(self.user1.id),
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
        self.daily = DailyChallenge.objects.create(date=date.today(), challenge=self.challenge, source="random")
        self.daily_url = reverse('daily_leaderboard')
        self.challenge_url = reverse('challenge_leaderboard', args=[self.challenge.id])
        self.rank_url_template = reverse('session_rank', args=[0]).replace("0/", "{}/")

        now = timezone.now()
        GameSession.objects.create(
            challenge=self.challenge,
            player_user_id=str(self.user1.id),
            mode=GameSession.MODE_CHALLENGE,
            end_time=now - timedelta(minutes=2),
            score=15,
        )
        GameSession.objects.create(
            challenge=self.challenge,
            player_user_id=str(self.user2.id),
            mode=GameSession.MODE_CHALLENGE,
            end_time=now - timedelta(minutes=1),
            score=15,
        )

    @mock.patch("accounts.authentication.verify_firebase_id_token")
    def test_daily_leaderboard_sorted(self, mock_verify):
        mock_verify.return_value = {"uid": "uid1"}
        resp = self.client.get(self.daily_url, HTTP_AUTHORIZATION="Bearer token")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        entries = resp.data["entries"]
        self.assertEqual(len(entries), 2)
        # same score; earlier end_time ranks higher -> user1 first
        self.assertEqual(entries[0]["player_user_id"], str(self.user1.id))
        self.assertLessEqual(entries[0]["rank"], entries[1]["rank"])

    @mock.patch("accounts.authentication.verify_firebase_id_token")
    def test_challenge_leaderboard(self, mock_verify):
        mock_verify.return_value = {"uid": "uid1"}
        resp = self.client.get(self.challenge_url, HTTP_AUTHORIZATION="Bearer token")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["challenge_id"], self.challenge.id)

    def test_session_rank(self):
        session = GameSession.objects.filter(player_user_id=str(self.user2.id)).first()
        resp = self.client.get(self.rank_url_template.format(session.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("rank", resp.data)
        self.assertIn("total_players", resp.data)
        self.assertLessEqual(resp.data["rank"], resp.data["total_players"])
