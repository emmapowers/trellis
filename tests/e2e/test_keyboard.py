"""E2E tests for keyboard handling — runs in a headless browser via Playwright."""

from playwright.sync_api import Page, expect


def _log_entry(text: str) -> str:
    """Build the locator text for a log entry."""
    return f"\u2192 {text}"


def _defocus(page: Page) -> None:
    """Move focus away from any input by clicking a non-interactive element."""
    page.evaluate("() => { document.activeElement?.blur(); }")
    page.wait_for_timeout(100)


class TestFocusScoped:
    """Focus-scoped .on_key() handlers."""

    def test_enter_submits_when_input_focused(self, keyboard_page: Page) -> None:
        keyboard_page.locator("input[placeholder='Enter to submit']").focus()
        keyboard_page.keyboard.press("Enter")
        expect(keyboard_page.locator(f"text={_log_entry('submit')}").first).to_be_visible()

    def test_escape_fires_in_input(self, keyboard_page: Page) -> None:
        keyboard_page.locator("input[placeholder='Escape to cancel']").focus()
        keyboard_page.keyboard.press("Escape")
        expect(keyboard_page.locator(f"text={_log_entry('cancel')}").first).to_be_visible()

    def test_shift_enter_does_not_trigger_enter(self, keyboard_page: Page) -> None:
        keyboard_page.locator("input[placeholder='Shift+Enter test']").focus()
        keyboard_page.keyboard.press("Shift+Enter")
        expect(keyboard_page.locator(f"text={_log_entry('submit-shift-test')}")).not_to_be_visible()


class TestMountScoped:
    """Mount-scoped HotKey() global shortcuts."""

    def test_mod_s_fires_globally(self, keyboard_page: Page) -> None:
        _defocus(keyboard_page)
        keyboard_page.keyboard.press("Meta+s")
        expect(keyboard_page.locator(f"text={_log_entry('save')}").first).to_be_visible()

    def test_bare_key_ignored_in_input(self, keyboard_page: Page) -> None:
        keyboard_page.locator("input[placeholder='K should NOT fire here']").focus()
        keyboard_page.keyboard.press("k")
        expect(keyboard_page.locator(f"text={_log_entry('search')}")).not_to_be_visible()

    def test_bare_key_fires_outside_input(self, keyboard_page: Page) -> None:
        _defocus(keyboard_page)
        keyboard_page.keyboard.press("k")
        expect(keyboard_page.locator(f"text={_log_entry('search')}").first).to_be_visible()


class TestConflictResolution:
    """Deeper HotKey wins; pass falls through to shallower."""

    def test_inner_passes_outer_handles(self, keyboard_page: Page) -> None:
        _defocus(keyboard_page)
        keyboard_page.keyboard.press("Escape")
        expect(keyboard_page.locator(f"text={_log_entry('inner: passing')}").first).to_be_visible()
        expect(keyboard_page.locator(f"text={_log_entry('outer escape')}").first).to_be_visible()


class TestEnabledToggle:
    """HotKey with enabled= toggle."""

    def test_disabled_does_not_fire(self, keyboard_page: Page) -> None:
        _defocus(keyboard_page)
        keyboard_page.keyboard.press("Meta+d")
        expect(keyboard_page.locator(f"text={_log_entry('mod+d fired')}")).not_to_be_visible()

    def test_toggle_on_fires(self, keyboard_page: Page) -> None:
        keyboard_page.locator("text=Enable Mod+D").click()
        keyboard_page.wait_for_timeout(1000)  # Wait for re-render with enabled HotKey
        _defocus(keyboard_page)
        keyboard_page.keyboard.press("Meta+d")
        expect(keyboard_page.locator(f"text={_log_entry('mod+d fired')}").first).to_be_visible()


class TestSequences:
    """Key sequences and chords."""

    def test_gg_sequence(self, keyboard_page: Page) -> None:
        _defocus(keyboard_page)
        keyboard_page.keyboard.press("g")
        expect(keyboard_page.locator(f"text={_log_entry('gg: go to top')}")).not_to_be_visible()
        keyboard_page.keyboard.press("g")
        expect(keyboard_page.locator(f"text={_log_entry('gg: go to top')}").first).to_be_visible()

    def test_chord_sequence(self, keyboard_page: Page) -> None:
        _defocus(keyboard_page)
        keyboard_page.keyboard.press("Meta+k")
        keyboard_page.wait_for_timeout(200)
        keyboard_page.keyboard.press("Meta+s")
        expect(
            keyboard_page.locator(f"text={_log_entry('chord: special save')}").first
        ).to_be_visible()
