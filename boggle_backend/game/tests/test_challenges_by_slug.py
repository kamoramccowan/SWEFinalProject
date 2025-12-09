from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from game.models import Challenge


class ChallengeBySlugTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='alice', password='pw123456')
        self.challenge = Challenge.objects.create(
            creator_user_id=str(self.user.id),
            title="Slug Challenge",
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
        self.url = reverse('game_challenges_by_slug', args=[self.challenge.share_slug])

    def test_get_by_slug(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], self.challenge.id)
        self.assertEqual(resp.data["share_slug"], self.challenge.share_slug)

    def test_deleted_returns_404(self):
        self.challenge.status = Challenge.STATUS_DELETED
        self.challenge.save(update_fields=['status'])
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_unknown_slug_returns_404(self):
        resp = self.client.get(reverse('game_challenges_by_slug', args=['unknown']))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
