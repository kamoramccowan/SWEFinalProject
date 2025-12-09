from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# Dev A tests for FR-02 (Create Challenges): ensure grid validation and server-bound creator_user_id.


class ChallengeCreateTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='alice', password='pw123456')
        self.url = reverse('game_challenges_create')

    def test_create_challenge_success(self):
        payload = {
            "title": "My First Board",
            "description": "Fun practice",
            "grid": [
                ["t", "e", "s", "t"],
                ["w", "o", "r", "d"],
                ["p", "l", "a", "y"],
                ["g", "a", "m", "e"],
            ],
            "difficulty": "easy",
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["creator_user_id"], str(self.user.id))
        self.assertEqual(response.data["title"], payload["title"])
        self.assertEqual(response.data["difficulty"], payload["difficulty"])
        # Grid is uppercased during validation
        self.assertEqual(response.data["grid"][0][0], "T")
        self.assertIn("created_at", response.data)

    def test_reject_non_square_grid(self):
        payload = {
            "title": "Bad Grid",
            "grid": [
                ["A", "B", "C"],
                ["D", "E"],  # shorter row
            ],
            "difficulty": "medium",
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get("error_code"), "VALIDATION_ERROR")
        self.assertIn("grid", response.data.get("details", {}))

    def test_creator_user_id_ignores_client_payload(self):
        payload = {
            "title": "Should Ignore Client Creator",
            "grid": [
                ["A", "B"],
                ["C", "D"],
            ],
            "difficulty": "hard",
            "creator_user_id": "malicious-client",
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["creator_user_id"], str(self.user.id))
        self.assertNotEqual(response.data["creator_user_id"], payload["creator_user_id"])
