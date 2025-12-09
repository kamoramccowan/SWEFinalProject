from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# Contract tests to keep API shapes stable for frontend integration.


class ChallengeApiContractTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='alice', password='pw123456')
        self.create_url = reverse('game_challenges_create')
        self.mine_url = reverse('game_challenges_mine')

    def test_create_response_shape(self):
        payload = {
            "title": "Contract Board",
            "description": "Doc",
            "grid": [
                ["A", "B", "C", "D"],
                ["E", "F", "G", "H"],
                ["I", "J", "K", "L"],
                ["M", "N", "O", "P"],
            ],
            "difficulty": "easy",
            "recipients": ["friend@example.com"],
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.create_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected_keys = {
            "id",
            "creator_user_id",
            "title",
            "description",
            "grid",
            "difficulty",
            "valid_words",
            "recipients",
            "status",
            "created_at",
            "updated_at",
        }
        self.assertTrue(expected_keys.issubset(set(response.data.keys())))
        self.assertEqual(response.data["status"], "active")
        self.assertEqual(response.data["creator_user_id"], str(self.user.id))

    def test_list_mine_response_shape(self):
        # create one challenge
        payload = {
            "title": "Contract Board",
            "description": "Doc",
            "grid": [
                ["A", "B", "C", "D"],
                ["E", "F", "G", "H"],
                ["I", "J", "K", "L"],
                ["M", "N", "O", "P"],
            ],
            "difficulty": "easy",
        }
        self.client.force_authenticate(user=self.user)
        self.client.post(self.create_url, payload, format='json')

        response = self.client.get(self.mine_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        if response.data:
            item = response.data[0]
            expected_keys = {
                "id",
                "title",
                "description",
                "difficulty",
                "recipients",
                "status",
                "created_at",
            }
            self.assertTrue(expected_keys.issubset(set(item.keys())))

    def test_validation_error_shape(self):
        bad_payload = {
            "title": "Bad",
            "grid": [["A"], []],  # not square
            "difficulty": "easy",
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.create_url, bad_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get("error_code"), "VALIDATION_ERROR")
        self.assertIn("details", response.data)
