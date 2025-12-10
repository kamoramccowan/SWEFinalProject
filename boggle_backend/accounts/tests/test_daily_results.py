from datetime import date
from unittest import mock

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import DailyChallenge, DailyChallengeResult
from game.models import Challenge, GameSession


class DailyChallengeResultTests(APITestCase):
    def setUp(self):
        self.UserModel = get_user_model()
        self.user = self.UserModel.objects.create_user(username='alice', password='pw', firebase_uid='uid-1')
        self.challenge = Challenge.objects.create(
            creator_user_id=str(self.user.id),
            title="Daily",
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
        self.end_url_template = '/api/sessions/{}/end/'

    @mock.patch("accounts.authentication.verify_firebase_id_token")
    def test_daily_result_recorded_on_session_end(self, mock_verify):
        mock_verify.return_value = {"uid": self.user.firebase_uid}
        session = GameSession.objects.create(
            challenge=self.challenge,
            player_user_id=str(self.user.id),
            mode=GameSession.MODE_CHALLENGE,
            score=10,
        )
        resp = self.client.post(self.end_url_template.format(session.id), {}, format='json',
                                HTTP_AUTHORIZATION="Bearer token")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(DailyChallengeResult.objects.filter(daily_challenge=self.daily).count(), 1)
        result = DailyChallengeResult.objects.filter(daily_challenge=self.daily).first()
        self.assertEqual(result.score, 10)

    @mock.patch("accounts.authentication.verify_firebase_id_token")
    def test_daily_result_updates_if_higher(self, mock_verify):
        mock_verify.return_value = {"uid": self.user.firebase_uid}
        DailyChallengeResult.objects.create(daily_challenge=self.daily, user=self.user, score=5)
        session = GameSession.objects.create(
            challenge=self.challenge,
            player_user_id=str(self.user.id),
            mode=GameSession.MODE_CHALLENGE,
            score=12,
        )
        resp = self.client.post(self.end_url_template.format(session.id), {}, format='json',
                                HTTP_AUTHORIZATION="Bearer token")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        result = DailyChallengeResult.objects.filter(daily_challenge=self.daily).first()
        self.assertEqual(result.score, 12)
