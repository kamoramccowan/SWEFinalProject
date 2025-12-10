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
            "creator": "user123",
            "difficulty": "easy",
            "grid_size": 4,
            "grid": grid,
            "clues": ["Animals", "Sports"],
            "description": "Practice board",
        }

        with mock.patch('api.serializers.generate_valid_words', return_value=["WORD", "PLAY"]):
            response = self.client.post(reverse('challenges'), payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["valid_words"], ["WORD", "PLAY"])
        self.assertEqual(response.data["grid_size"], 4)
        self.assertEqual(response.data["clues"], ["Animals", "Sports"])
