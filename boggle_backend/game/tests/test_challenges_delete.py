from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from game.models import Challenge

# Dev A tests for FR-04: ensure creators can soft-delete their challenges and others cannot.


class ChallengeDeleteTests(APITestCase):
    def setUp(self):
        self.user_a = get_user_model().objects.create_user(username='alice', password='pw123456')
        self.user_b = get_user_model().objects.create_user(username='bob', password='pw123456')
        self.challenge = Challenge.objects.create(
            creator_user_id=str(self.user_a.id),
            title="To Delete",
            description="",
            grid=[["A", "B"], ["C", "D"]],
            difficulty="easy",
        )
        self.delete_url = reverse('game_challenges_delete', args=[self.challenge.id])
        self.mine_url = reverse('game_challenges_mine')

    def test_creator_can_delete(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.delete(self.delete_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.challenge.refresh_from_db()
        self.assertEqual(self.challenge.status, Challenge.STATUS_DELETED)

        # Should not appear in mine list
        mine_resp = self.client.get(self.mine_url)
        self.assertEqual(mine_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(mine_resp.data, [])

    def test_other_user_cannot_delete(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.delete(self.delete_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.challenge.refresh_from_db()
        self.assertEqual(self.challenge.status, Challenge.STATUS_ACTIVE)

    def test_deleted_is_not_found(self):
        self.challenge.status = Challenge.STATUS_DELETED
        self.challenge.save(update_fields=['status'])

        self.client.force_authenticate(user=self.user_a)
        response = self.client.delete(self.delete_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
