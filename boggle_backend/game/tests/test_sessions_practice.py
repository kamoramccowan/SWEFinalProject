from unittest import mock

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from game.models import Challenge, GameSession
from game.practice import get_letter_pool


class PracticeSessionTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='alice', password='pw123456')
        self.url = reverse('game_sessions_create')
        self.submit_url_template = '/api/sessions/{}/submit-word/'

    @mock.patch('game.practice.generate_practice_grid')
    @mock.patch('game.practice.load_full_dictionary')
    def test_create_practice_session_and_submit(self, mock_dict, mock_grid):
        mock_grid.return_value = [["T", "E"], ["S", "T"]]
        mock_dict.return_value = ["TEST", "WORD"]

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url, {"mode": "practice", "difficulty": "easy"}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        session_id = resp.data["id"]

        session = GameSession.objects.get(pk=session_id)
        self.assertEqual(session.mode, GameSession.MODE_PRACTICE)
        self.assertEqual(session.challenge.creator_user_id, str(self.user.id))
        self.assertEqual(session.challenge.difficulty, "easy")
        self.assertEqual(session.duration_seconds, 120)
        self.assertTrue("TEST" in session.challenge.valid_words)

        submit_url = self.submit_url_template.format(session_id)
        submit_resp = self.client.post(submit_url, {"word": "test"}, format='json')
        self.assertEqual(submit_resp.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertGreater(session.score, 0)

    def test_challenge_mode_unchanged(self):
        # Create a normal challenge
        challenge = Challenge.objects.create(
            creator_user_id=str(self.user.id),
            title="Challenge",
            description="",
            grid=[["A", "B"], ["C", "D"]],
            difficulty="easy",
            valid_words=["ABCD"],
        )
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url, {"challenge_id": challenge.id}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        session = GameSession.objects.get(pk=resp.data["id"])
        self.assertEqual(session.mode, GameSession.MODE_CHALLENGE)

    def test_hard_letter_pool_has_rare_letters(self):
        pool = get_letter_pool("hard")
        self.assertIn("Q", pool)
        self.assertIn("Z", pool)
        self.assertIn("X", pool)
