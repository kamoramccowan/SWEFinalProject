from datetime import date
from unittest import mock

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from game.models import Challenge
from accounts.models import DailyChallenge


class DailyChallengeTests(APITestCase):
    def setUp(self):
        self.UserModel = get_user_model()
        self.url = reverse('daily_challenge')
        self.challenge = Challenge.objects.create(
            creator_user_id="1",
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

    def test_get_creates_daily_when_absent(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["challenge_id"], self.challenge.id)
        self.assertEqual(resp.data["date"], str(date.today()))
        self.assertEqual(DailyChallenge.objects.count(), 1)

    def test_get_reuses_existing(self):
        DailyChallenge.objects.create(date=date.today(), challenge=self.challenge, source="random")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["challenge_id"], self.challenge.id)
        self.assertEqual(DailyChallenge.objects.count(), 1)

    @mock.patch("accounts.daily.pick_active_challenge")
    def test_no_active_challenges(self, mock_pick):
        mock_pick.side_effect = ValueError("No active challenges available to serve as daily challenge.")
        Challenge.objects.all().delete()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data.get("error_code"), "NO_ACTIVE_CHALLENGES")
