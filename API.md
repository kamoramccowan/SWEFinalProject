# Boggle Boost – Game & Challenges API (Dev A)

Scope: Challenge/game endpoints owned by Dev A. Auth is provided by Dev B; every request is assumed to arrive with an authenticated user on `request.user` or `request.user_id`. Client-supplied user ids are ignored.

Base URL
- Local dev: `http://localhost:8000/api/`

Error format
```json
{ "error_code": "VALIDATION_ERROR", "message": "Invalid challenge payload.", "details": { ... } }
```

Endpoints

### POST /challenges/
Create a challenge using the authenticated user as creator.
- Auth: required.
- Body:
```json
{
  "title": "My First Board",
  "description": "Optional text",
  "grid": [["A","B"],["C","D"]],
  "difficulty": "easy|medium|hard",
  "recipients": ["friend@example.com"]  // optional list
}
```
- Success (201):
```json
{
  "id": 1,
  "creator_user_id": "123",
  "title": "My First Board",
  "description": "Optional text",
  "grid": [["A","B"],["C","D"]],
  "difficulty": "easy",
  "valid_words": [],
  "recipients": ["friend@example.com"],
  "status": "active",
  "created_at": "...",
  "updated_at": "..."
}
```
- Errors: 400 with `error_code: "VALIDATION_ERROR"`.

Auth/roles
- Guests: no token; may only start practice sessions.
- Registered: Firebase token; may create challenges and start challenge sessions.
- `POST /api/auth/login/verify/` returns user info plus `role: "registered"` and `is_registered: true` when authenticated.

### GET /challenges/mine/
List challenges created by the authenticated user (active only).
- Auth: required.
- Success (200):
```json
[
  {
    "id": 1,
    "title": "My First Board",
    "description": "Optional text",
    "difficulty": "easy",
    "recipients": ["friend@example.com"],
    "status": "active",
    "created_at": "..."
  }
]
```
- Returns `[]` if none or if filtered user has none.

### DELETE /challenges/{id}/
Soft-delete a challenge you created.
- Auth: required.
- Success (200):
```json
{ "status": "deleted" }
```
- 404 if not found, already deleted, or not owned by the caller.

### POST /sessions/
Start a session on an active challenge (mode=challenge).
- Auth: optional (player_user_id may be null for guests).
- Body:
```json
{
  "challenge_id": 1,
  "mode": "challenge"
}
```
- Success (201):
```json
{
  "id": 10,
  "challenge": 1,
  "player_user_id": "123",      // null for guests
  "mode": "challenge",
  "start_time": "...",
  "end_time": null,
  "duration_seconds": null,
  "score": 0,
  "submissions": []
}
```
- Errors: 400 with `error_code: "VALIDATION_ERROR"` for missing/invalid challenge.

### POST /sessions/{id}/submit-word/
Submit one word to an active session (timed).
- Auth: required if session is owned by a user; guests allowed for guest sessions.
- Body: `{ "word": "TEST" }`
- Success (200): `{ "status": "accepted", "word": "TEST", "session_id": 10, "is_valid": true, "score_delta": 4, "score": 4 }`
- Errors:
  - 400 `error_code: "TIME_UP"` if session is ended or timed out.
  - 400 `error_code: "VALIDATION_ERROR"` for bad payload.
  - 404 if session not found or not owned by caller.

### POST /sessions/{id}/end/
Explicitly end a session.
- Success (200): `{ "status": "ended", "session_id": 10 }`
- Further submissions will return `TIME_UP`.

### GET /sessions/{id}/results/
Return all valid words, found words, and score for an ended session.
- Auth: required if session is owned; guests allowed for guest sessions.
- Errors: 400 `SESSION_ACTIVE` if session not ended; 404 if not owned/not found.
- Success (200):
```json
{
  "all_valid_words": ["TEST", "WORD"],
  "found_words": ["TEST"],
  "score": 4
}
```

### GET /sessions/{id}/hint/
Return a simple hint for an active session (unfound word first letter/length).
- Errors: 400 `TIME_UP` if ended/timed out; 404 if not owned/not found; 429 `HINT_LIMIT_REACHED` after 3 uses.
- Success (200): `{ "hint": { "first_letter": "W", "length": 4, "word": "WORD" }, "remaining": 2 }`

### GET /challenges/by-slug/{share_slug}/
Fetch an active challenge by its shareable slug.
- Success (200): same payload as challenge detail (id, title, description, grid, difficulty, valid_words, recipients, status, share_slug, timestamps)
- 404 if slug not found or challenge is deleted.

### GET /daily-challenge/
Return today's global daily challenge (creates one lazily if missing).
- Success (200):
```json
{
  "date": "2025-12-09",
  "challenge_id": 123,
  "title": "Challenge",
  "difficulty": "easy",
  "grid": [...],
  "share_slug": "abc123",
  "created_at": "..."
}
```
- Errors: 404 with `error_code: "NO_ACTIVE_CHALLENGES"` if no active challenges exist to serve.
- Scores for the daily challenge are recorded separately when authenticated users end a session on that challenge.

### POST /challenges/{id}/send/  (Dev B privacy + targeted send)
Send a challenge invite to a specific registered user, enforcing recipient privacy settings.
- Auth: required.
- Body:
```json
{ "target_user_id": 42 }
```
- Behavior:
  - Blocks if recipient privacy disallows incoming challenges (`403`, `PRIVACY_BLOCKED`).
  - Blocks if recipient has no email on file (`400`, `RECIPIENT_NO_EMAIL`).
  - Records an invite; stubs an email send to the recipient’s email with the share link (configure real mailer later).
- Success (201):
```json
{
  "id": 10,
  "challenge_id": 123,
  "recipient_id": 42,
  "sender_id": 7,
  "created_at": "...",
  "status": "sent",
  "email_sent": true,
  "share_link": "http://localhost:3000/challenges/abc123"
}
```
- Errors:
  - 400 `VALIDATION_ERROR` if target_user_id missing.
  - 400 `RECIPIENT_NO_EMAIL` if recipient has no email.
  - 403 `PRIVACY_BLOCKED` if recipient blocks incoming challenges.
  - 404 `TARGET_NOT_FOUND` or `CHALLENGE_NOT_FOUND`.

### GET /settings/ and PUT/PATCH /settings/  (Dev B privacy)
Read/update privacy settings.
- Auth: required.
- Fields:
  - `challenge_visibility`: `everyone` | `no-one`
  - `allow_incoming_challenges`: boolean
  - `allowed_sender_user_ids`: list of user ids permitted to target you (if non-empty, acts as allowlist)
  - `theme`: `light` | `dark` | `high-contrast` (FR-17)
- Success (200): returns the settings object.
- Errors: 400 `VALIDATION_ERROR` for bad payload.

### GET /words/{word}/definition/  (Dev B dictionary lookup, FR-19)
Lookup the meaning of a word using an external dictionary API with caching.
- Auth: not required.
- Success (200):
```json
{
  "word": "CAT",
  "definitions": [
    { "part_of_speech": "noun", "definition": "...", "example": "..." }
  ]
}
```
- Errors:
  - 404 `WORD_NOT_FOUND` if the word has no entry.
  - 503 `DICTIONARY_UNAVAILABLE` if the external service fails.
  - 400 `VALIDATION_ERROR` if word is empty.

Notes
- Status values: `active`, `deleted` (deleted items are excluded from `/challenges/mine/`).
- Grids must be square and letter-only; cells are uppercased on save.
- Recipients are stored as a list of identifiers (e.g., emails/usernames). Dev B owns the actual addressing/permissions logic.
