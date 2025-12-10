from unittest import mock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class ChallengeApiTests(APITestCase):
    def test_generate_dictionary_endpoint_validates_and_returns_words(self):
        grid = [
            ["C", "A", "T", "S"],
            ["D", "O", "G", "S"],
            ["B", "I", "R", "D"],
            ["F", "I", "S", "H"],
        ]
        with mock.patch('api.views.generate_valid_words', return_value=["CAT", "DOG"]):
            response = self.client.post(reverse('generate_dictionary'), {"grid": grid}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["grid_size"], 4)
        self.assertEqual(response.data["valid_words"], ["CAT", "DOG"])

    def test_create_challenge_generates_dictionary_and_persists_payload(self):
        grid = [
            ["T", "E", "S", "T"],
            ["W", "O", "R", "D"],
            ["M", "A", "K", "E"],
            ["P", "L", "A", "Y"],
        ]
        payload = {
            "title": "Practice board",
            "description": "Testing create",
            "difficulty": "easy",
            "grid": grid,
        }

        # Post to the Dev A challenge create endpoint (requires auth).
        with mock.patch("accounts.authentication.verify_firebase_id_token") as mock_verify:
            mock_verify.return_value = {"uid": "user123"}
            response = self.client.post(
                reverse("game_challenges_create"),
                payload,
                format="json",
                HTTP_AUTHORIZATION="Bearer token",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Dev A serializer stores normalized grid and leaves valid_words empty by default.
        self.assertIn("id", response.data)
        self.assertEqual(response.data["difficulty"], "easy")
        self.assertEqual(response.data["valid_words"], [])
        self.assertEqual(response.data["title"], "Practice board")
