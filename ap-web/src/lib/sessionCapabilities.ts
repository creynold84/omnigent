/** UI-only session capability gates, derived from snapshot labels. */

const CLAUDE_NATIVE_WRAPPER = "claude-code-native-ui";
const CODEX_NATIVE_WRAPPER = "codex-native-ui";

/**
 * Fail-closed gate for Web UI reasoning-effort controls.
 *
 * :param session: Session or sidebar row carrying labels. ``null`` or missing
 *     labels fail closed.
 * :returns: True only for native sessions with Web UI effort controls.
 */
export function supportsEffortControl(
  session: { labels?: Record<string, string | null> | null } | null | undefined,
): boolean {
  const wrapper = session?.labels?.["omnigent.wrapper"];
  return wrapper === CLAUDE_NATIVE_WRAPPER || wrapper === CODEX_NATIVE_WRAPPER;
}

/**
 * Fail-closed gate for the Web UI Tasks (plan/TODO) panel.
 *
 * True only for harnesses that feed the panel via ``external_session_todos``:
 * claude-native (TodoWrite/task hooks) and codex-native (structured
 * ``turn/plan/updated`` plan steps). A narrow allowlist — other native
 * wrappers (Cursor, Pi) don't emit todos.
 *
 * :param session: Session or sidebar row carrying labels. ``null`` or missing
 *     labels fail closed.
 * :returns: True only for native sessions that populate the Tasks panel.
 */
export function supportsTasksPanel(
  session: { labels?: Record<string, string | null> | null } | null | undefined,
): boolean {
  const wrapper = session?.labels?.["omnigent.wrapper"];
  return wrapper === CLAUDE_NATIVE_WRAPPER || wrapper === CODEX_NATIVE_WRAPPER;
}
