# Changelog (Dev A – Game & Challenges)

## [Unreleased]
- Docs: Added `API.md` documenting challenge endpoints and error shapes.
- FR-02/FR-03: Challenge creation and "my challenges" listing in `game/` app, with recipients/status fields and structured errors.
- Tests: Response-shape tests for creation/listing to guard contracts.
- FR-04: Soft delete for challenges with DELETE /api/challenges/{id}/, active-only listings, and ownership checks.
- FR-05: Session creation for playing active challenges (POST /api/sessions/) with GameSession model.
- FR-06: Timed play scaffolding with session submission and end endpoints (`POST /sessions/{id}/submit-word/`, `POST /sessions/{id}/end/`), time-up handling, and owner checks.
- FR-08: Session results (all valid vs found words, score) and hint endpoint for active sessions.
- Hint limits: Added per-session hint counter (3 max) and 429 response when exceeded.
- FR-11: Shareable challenge slugs and by-slug lookup; session shuffle limits; rotation angles.
- FR-13: Difficulty-driven grid sizes, timers, min word lengths; hard-mode rare letters for practice.
- FR-10 (Dev B): Guest vs registered rules, registered-only challenge actions, optional Firebase auth for mixed endpoints.
- FR-14 (Dev B): DailyChallenge model, lazy daily selection, and GET /api/daily-challenge/ endpoint returning today's challenge.
- FR-14 extension: DailyChallengeResult model with per-user daily scores recorded on session end.
