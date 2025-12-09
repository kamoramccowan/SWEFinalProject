from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from game.models import Challenge

# Dev A tests for FR-03: ensure "my challenges" only returns the authenticated user's items.


class ChallengeMineTests(APITestCase):
    def setUp(self):
        self.user_a = get_user_model().objects.create_user(username='alice', password='pw123456')
        self.user_b = get_user_model().objects.create_user(username='bob', password='pw123456')
        self.url = reverse('game_challenges_mine')

    def test_user_sees_only_their_challenges(self):
        c1 = Challenge.objects.create(
            creator_user_id=str(self.user_a.id),
            title="A1",
            description="first",
            grid=[["A", "B"], ["C", "D"]],
            difficulty="easy",
            recipients=["r1@example.com"],
        )
        c2 = Challenge.objects.create(
            creator_user_id=str(self.user_a.id),
            title="A2",
            description="second",
            grid=[["E", "F"], ["G", "H"]],
            difficulty="medium",
        )
        Challenge.objects.create(
            creator_user_id=str(self.user_b.id),
            title="B1",
            description="other user",
            grid=[["I", "J"], ["K", "L"]],
            difficulty="hard",
        )

        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data]
        self.assertEqual(set(ids), {c1.id, c2.id})
        # Ordered by created_at descending (c2 created after c1)
        self.assertEqual(ids[0], c2.id)
        self.assertEqual(ids[1], c1.id)
        # Recipients included
        rec_for_c1 = [item for item in response.data if item["id"] == c1.id][0]["recipients"]
        self.assertEqual(rec_for_c1, ["r1@example.com"])

    def test_other_user_does_not_see_challenges(self):
        Challenge.objects.create(
            creator_user_id=str(self.user_a.id),
            title="A1",
            description="first",
            grid=[["A", "B"], ["C", "D"]],
            difficulty="easy",
        )

        self.client.force_authenticate(user=self.user_b)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_empty_list_when_no_challenges(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_deleted_challenge_not_returned(self):
        Challenge.objects.create(
            creator_user_id=str(self.user_a.id),
            title="A1",
            description="first",
            grid=[["A", "B"], ["C", "D"]],
            difficulty="easy",
            status=Challenge.STATUS_DELETED,
        )

        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
