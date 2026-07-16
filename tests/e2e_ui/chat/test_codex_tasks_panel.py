"""E2E: codex-native sessions render plan/TODO progress in the Tasks panel."""

from __future__ import annotations

import json
import re
from urllib.parse import urlparse

from playwright.sync_api import Page, Route, expect

from tests.e2e_ui.conftest import open_right_rail

# Todos the patched snapshot advertises. Mirrors the ``external_session_todos``
# payload the codex-native forwarder now emits from ``turn/plan/updated``
# (``step`` → ``content``/``activeForm``, camelCase status normalized to
# snake_case). The Tasks panel renders ``content`` per row.
_CODEX_TODOS = [
    {
        "content": "Investigate the failing test",
        "status": "completed",
        "activeForm": "Investigating",
    },
    {"content": "Apply the fix", "status": "in_progress", "activeForm": "Applying the fix"},
    {"content": "Run the suite", "status": "pending", "activeForm": "Running the suite"},
]


def _patch_session_as_codex_native_with_todos(page: Page, session_id: str) -> None:
    """Patch the browser's session snapshot into a codex-native + todos response.

    The server fixture seeds a normal ``hello_world`` session so the page can
    boot against the real app/server. This route patch changes only the
    ``GET /v1/sessions/{session_id}`` response as seen by the browser, stamping
    the ``codex-native-ui`` wrapper label (so the Tasks panel's harness gate
    admits the session) and a ``todos`` list (what the server snapshot builder
    would return from ``_session_todos_cache`` after the forwarder posted a
    plan). No real Codex CLI is needed to exercise the web behavior.

    :param page: Playwright page before navigation.
    :param session_id: Session id to patch, e.g. ``"conv_abc123"``.
    :returns: None.
    """

    def _handle(route: Route) -> None:
        request = route.request
        if urlparse(request.url).path != f"/v1/sessions/{session_id}" or request.method != "GET":
            route.continue_()
            return
        response = route.fetch()
        payload = response.json()
        payload["labels"] = {
            **payload.get("labels", {}),
            "omnigent.wrapper": "codex-native-ui",
        }
        payload["harness"] = "codex"
        payload["todos"] = _CODEX_TODOS
        route.fulfill(
            status=200,
            headers={**response.headers, "content-type": "application/json"},
            body=json.dumps(payload),
        )

    page.route("**/v1/sessions/**", _handle)


def test_codex_native_session_shows_plan_in_tasks_panel(
    page: Page,
    seeded_session: tuple[str, str],
) -> None:
    """A codex-native session surfaces its plan steps in the Tasks panel.

    Covers the harness-gate widening: the Tasks tab (previously claude-native
    only) now admits ``codex-native-ui``, and the shared TodoPanel renders the
    plan steps the forwarder mapped into ``external_session_todos``.

    :param page: Playwright page fixture.
    :param seeded_session: ``(base_url, session_id)`` for a real server-backed
        session; the browser snapshot is patched to codex-native with todos.
    :returns: None.
    """
    base_url, session_id = seeded_session
    _patch_session_as_codex_native_with_todos(page, session_id)

    page.goto(f"{base_url}/c/{session_id}")

    # Scope every lookup to the desktop "Workspace" rail so it never matches the
    # hidden mobile drawer that mirrors the same labels.
    open_right_rail(page)
    rail = page.get_by_role("complementary", name="Workspace")

    tasks_tab = rail.get_by_role("tab", name=re.compile("^Tasks"))
    expect(tasks_tab).to_be_visible(timeout=30_000)
    # Badge shows completed/total (1 of 3 todos completed).
    expect(tasks_tab).to_contain_text("1/3")

    tasks_tab.click()
    # The panel renders each plan step's content.
    for todo in _CODEX_TODOS:
        expect(rail.get_by_text(todo["content"], exact=False)).to_be_visible(timeout=30_000)
