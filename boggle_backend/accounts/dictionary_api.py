import os
import json
import urllib.request
import urllib.error


class WordNotFound(Exception):
    pass


class DictionaryAPIError(Exception):
    pass


def lookup_word_meaning(word: str) -> dict:
    """
    Call an external dictionary API and normalize the response.
    Uses a public dictionary API by default; configurable via env `DICTIONARY_API_URL`.
    """
    word_norm = word.strip().lower()
    if not word_norm:
        raise WordNotFound("Word is empty.")

    base_url = os.getenv("DICTIONARY_API_URL", "https://api.dictionaryapi.dev/api/v2/entries/en")
    url = f"{base_url}/{word_norm}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            status = resp.getcode()
            body = resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise WordNotFound(f"Word '{word_norm}' not found.")
        raise DictionaryAPIError(f"Dictionary API error ({exc.code}).")
    except Exception as exc:
        raise DictionaryAPIError(f"Dictionary lookup failed: {exc}")

    if status != 200:
        raise DictionaryAPIError(f"Dictionary API error ({status}).")

    try:
        data = json.loads(body.decode("utf-8"))
    except Exception:
        raise DictionaryAPIError("Dictionary API returned invalid JSON.")

    # Normalize definitions
    definitions = []
    if isinstance(data, list):
        for entry in data:
            meanings = entry.get("meanings") or []
            for meaning in meanings:
                part = meaning.get("partOfSpeech") or ""
                defs = meaning.get("definitions") or []
                for d in defs:
                    definitions.append(
                        {
                            "part_of_speech": part,
                            "definition": d.get("definition", ""),
                            "example": d.get("example") or "",
                        }
                    )
    payload = {
        "word": word_norm.upper(),
        "definitions": definitions,
    }
    return payload
