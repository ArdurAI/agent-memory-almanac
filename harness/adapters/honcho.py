"""
Honcho adapter for the Quest harness.

Implements the frozen MemoryAdapter contract for Honcho.
https://github.com/plastic-labs/honcho

Honcho is a user-modeling memory backend (FastAPI + pgvector) that builds
a representation of the user via a dialectic API. It uses an async deriver
queue for profile updates.

SETUP REQUIRED:
1. Install Honcho server: see https://github.com/plastic-labs/honcho
2. Start PostgreSQL with pgvector extension
3. Start Redis (for caching)
4. Start the Honcho FastAPI server
5. Configure the API endpoint below

Note: This is a scaffold. The actual Honcho API calls need to be filled in.
"""

import time
from typing import Optional

from harness.adapter import MemoryAdapter, AdapterResult

# Honcho is imported lazily
try:
    from honcho import Honcho
    HAVE_HONCHO = True
except ImportError:
    HAVE_HONCHO = False


class HonchoAdapter(MemoryAdapter):
    """Quest adapter for Honcho (user-modeling memory)."""

    def __init__(self, api_url: str = "http://localhost:8000",
                 user_id: str = "quest-user", app_id: str = "quest-app"):
        self.api_url = api_url
        self.user_id = user_id
        self.app_id = app_id
        self.client = None
        if HAVE_HONCHO:
            # TODO: Initialize Honcho client
            # self.client = Honcho(base_url=api_url)
            pass
        else:
            raise ImportError(
                "honcho is not installed. See https://github.com/plastic-labs/honcho\n"
                "You also need PostgreSQL + pgvector + Redis running."
            )

    def add(self, conversation_turns: list[dict]) -> AdapterResult:
        t0 = time.perf_counter()
        # TODO: Send conversation turns to Honcho API
        # for turn in conversation_turns:
        #     self.client.create_message(
        #         app_id=self.app_id,
        #         user_id=self.user_id,
        #         content=turn["content"],
        #         # ...
        #     )
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed,
            metadata={"note": "Honcho adapter scaffold — implement API calls"})

    def await_ingest(self, timeout_sec: float = 60.0) -> AdapterResult:
        # Honcho has an async deriver queue — await_ingest measures real lag
        t0 = time.perf_counter()
        # TODO: Poll the deriver queue until processing is complete
        # or check that the user profile has been updated
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed,
            metadata={"note": "Honcho deriver queue — measure async lag"})

    def search(self, query: str, k: int = 5) -> AdapterResult:
        t0 = time.perf_counter()
        # TODO: Query Honcho for user-model context
        # results = self.client.query(
        #     app_id=self.app_id,
        #     user_id=self.user_id,
        #     query=query,
        #     top_k=k
        # )
        excerpts = []
        elapsed = time.perf_counter() - t0
        return AdapterResult(success=True, elapsed_sec=elapsed,
            metadata={"excerpts": excerpts,
                     "note": "Honcho adapter scaffold — implement search"})

    def export(self) -> AdapterResult:
        # TODO: Export user profile and message history
        return AdapterResult(success=True, elapsed_sec=0.0, metadata={
            "note": "Honcho export not yet implemented",
            "user_id": self.user_id,
            "app_id": self.app_id,
        })

    def wipe(self) -> AdapterResult:
        # TODO: Clear all data for this user/app
        # self.client.delete_user(app_id=self.app_id, user_id=self.user_id)
        return AdapterResult(success=True, elapsed_sec=0.0,
            metadata={"note": "Honcho wipe not yet implemented"})
