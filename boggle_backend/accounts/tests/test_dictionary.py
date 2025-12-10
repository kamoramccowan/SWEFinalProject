from unittest import mock

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import WordDefinitionCache


class WordDefinitionTests(APITestCase):
    def setUp(self):
        self.url = "/api/words/{}/definition/"

    @mock.patch("accounts.views.lookup_word_meaning")
    def test_word_found(self, mock_lookup):
        mock_lookup.return_value = {
            "word": "CAT",
            "definitions": [{"part_of_speech": "noun", "definition": "a cat", "example": ""}],
        }
        resp = self.client.get(self.url.format("cat"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["word"], "CAT")
        # cache created
        self.assertTrue(WordDefinitionCache.objects.filter(word="cat").exists())

    @mock.patch("accounts.views.lookup_word_meaning")
    def test_word_not_found(self, mock_lookup):
        from accounts.dictionary_api import WordNotFound

        mock_lookup.side_effect = WordNotFound("Word 'zzz' not found.")
        resp = self.client.get(self.url.format("zzz"))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data["error_code"], "WORD_NOT_FOUND")

    @mock.patch("accounts.views.lookup_word_meaning")
    def test_external_error(self, mock_lookup):
        from accounts.dictionary_api import DictionaryAPIError

        mock_lookup.side_effect = DictionaryAPIError("fail")
        resp = self.client.get(self.url.format("cat"))
        self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(resp.data["error_code"], "DICTIONARY_UNAVAILABLE")

    def test_cache_used(self):
        WordDefinitionCache.objects.create(
            word="dog",
            payload={"word": "DOG", "definitions": [{"part_of_speech": "noun", "definition": "dog", "example": ""}]},
        )
        with mock.patch("accounts.views.lookup_word_meaning", side_effect=AssertionError("Should not call")):
            resp = self.client.get(self.url.format("dog"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["word"], "DOG")
