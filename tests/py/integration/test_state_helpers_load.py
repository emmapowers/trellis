"""Integration tests for trellis.state.load()."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

from trellis import component, load
from trellis.state import Failed, Load, Loading, Ready

if TYPE_CHECKING:
    from tests.conftest import PatchCapture


async def _wait_for(event: asyncio.Event) -> None:
    await asyncio.wait_for(event.wait(), timeout=1.0)


def _snapshot(result: Load[object]) -> tuple[type[Load[object]], object | None]:
    if isinstance(result, Ready):
        return (Ready, result.value)
    if isinstance(result, Failed):
        return (Failed, str(result.error))
    return (Loading, None)


class TestLoadHelper:
    def test_initial_state_is_loading(self, capture_patches: "type[PatchCapture]") -> None:
        """load() returns Loading on the initial render."""
        started = asyncio.Event()
        observed: list[Load[int]] = []

        async def fetch_value() -> int:
            started.set()
            await asyncio.Event().wait()
            return 1

        @component
        def App() -> None:
            observed.append(load(fetch_value))

        capture = capture_patches(App)

        async def test() -> None:
            capture.render()
            await _wait_for(started)

        asyncio.run(test())

        assert isinstance(observed[0], Loading)
        assert observed[0].loading is True
        assert observed[0].ready is False
        assert observed[0].failed is False
        assert observed[0].get(9) == 9

    def test_successful_completion_yields_ready(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """A successful loader transitions from Loading to Ready."""
        release = asyncio.Event()
        observed: list[Load[str]] = []

        async def fetch_value() -> str:
            await release.wait()
            return "ready"

        @component
        def App() -> None:
            observed.append(load(fetch_value))

        capture = capture_patches(App)

        async def test() -> None:
            capture.render()
            release.set()
            await asyncio.sleep(0)
            capture.render()

        asyncio.run(test())

        assert isinstance(observed[0], Loading)
        assert isinstance(observed[1], Ready)
        assert observed[1].ready is True
        assert observed[1].get("fallback") == "ready"
        assert observed[1].value == "ready"

    def test_failure_yields_failed(self, capture_patches: "type[PatchCapture]") -> None:
        """A failing loader transitions from Loading to Failed."""
        release = asyncio.Event()
        observed: list[Load[int]] = []

        async def fetch_value() -> int:
            await release.wait()
            raise RuntimeError("boom")

        @component
        def App() -> None:
            observed.append(load(fetch_value))

        capture = capture_patches(App)

        async def test() -> None:
            capture.render()
            release.set()
            await asyncio.sleep(0)
            capture.render()

        asyncio.run(test())

        assert isinstance(observed[0], Loading)
        assert isinstance(observed[1], Failed)
        assert observed[1].failed is True
        assert observed[1].get(11) == 11
        assert str(observed[1].error) == "boom"

    def test_reload_forces_a_fresh_fetch(self, capture_patches: "type[PatchCapture]") -> None:
        """reload() starts a fresh request for the same slot."""
        release_events = [asyncio.Event(), asyncio.Event()]
        started_events = [asyncio.Event(), asyncio.Event()]
        snapshots: list[tuple[type[Load[object]], object | None]] = []
        latest: list[Load[int]] = []
        call_count = 0

        async def fetch_value() -> int:
            nonlocal call_count
            idx = call_count
            call_count += 1
            started_events[idx].set()
            await release_events[idx].wait()
            return idx + 1

        @component
        def App() -> None:
            result = load(fetch_value)
            latest[:] = [result]
            snapshots.append(_snapshot(result))

        capture = capture_patches(App)

        async def test() -> None:
            capture.render()
            await _wait_for(started_events[0])

            release_events[0].set()
            await asyncio.sleep(0)
            capture.render()

            latest[-1].reload()
            capture.render()
            await _wait_for(started_events[1])

            release_events[1].set()
            await asyncio.sleep(0)
            capture.render()

        asyncio.run(test())

        assert snapshots == [
            (Loading, None),
            (Ready, 1),
            (Loading, None),
            (Ready, 2),
        ]

    def test_arg_and_kwarg_changes_restart_load_without_key(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Changing explicit args/kwargs restarts the load when key is omitted."""
        query = {"value": 2, "multiplier": 3}
        releases: dict[tuple[int, int], asyncio.Event] = {}
        started: dict[tuple[int, int], asyncio.Event] = {}
        snapshots: list[tuple[type[Load[object]], object | None]] = []
        calls: list[tuple[int, int]] = []

        async def fetch_value(value: int, *, multiplier: int) -> int:
            identity = (value, multiplier)
            calls.append(identity)
            started.setdefault(identity, asyncio.Event()).set()
            await releases.setdefault(identity, asyncio.Event()).wait()
            return value * multiplier

        @component
        def App() -> None:
            snapshots.append(
                _snapshot(load(fetch_value, query["value"], multiplier=query["multiplier"]))
            )

        capture = capture_patches(App)

        async def test() -> None:
            capture.render()
            await asyncio.sleep(0)
            await _wait_for(started[(2, 3)])
            releases[(2, 3)].set()
            await asyncio.sleep(0)
            capture.render()

            query["value"] = 4
            query["multiplier"] = 5
            capture.session.dirty.mark(capture.session.root_element.id)
            capture.render()
            await asyncio.sleep(0)
            await _wait_for(started[(4, 5)])

            releases[(4, 5)].set()
            await asyncio.sleep(0)
            capture.render()

        asyncio.run(test())

        assert calls == [(2, 3), (4, 5)]
        assert snapshots == [
            (Loading, None),
            (Ready, 6),
            (Loading, None),
            (Ready, 20),
        ]

    def test_key_overrides_arg_comparison_semantics(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """When key is set, only the key controls automatic reload semantics."""
        value = {"current": 1}
        release_events = [asyncio.Event(), asyncio.Event()]
        started_events = [asyncio.Event(), asyncio.Event()]
        snapshots: list[tuple[type[Load[object]], object | None]] = []
        latest: list[Load[int]] = []
        calls: list[int] = []

        async def fetch_value(current: int) -> int:
            idx = len(calls)
            calls.append(current)
            started_events[idx].set()
            await release_events[idx].wait()
            return current

        @component
        def App() -> None:
            result = load(fetch_value, value["current"], key="stable")
            latest[:] = [result]
            snapshots.append(_snapshot(result))

        capture = capture_patches(App)

        async def test() -> None:
            capture.render()
            await _wait_for(started_events[0])
            release_events[0].set()
            await asyncio.sleep(0)
            capture.render()

            value["current"] = 2
            capture.session.dirty.mark(capture.session.root_element.id)
            capture.render()

            latest[-1].reload()
            capture.render()
            await _wait_for(started_events[1])
            release_events[1].set()
            await asyncio.sleep(0)
            capture.render()

        asyncio.run(test())

        assert calls == [1, 2]
        assert snapshots == [
            (Loading, None),
            (Ready, 1),
            (Ready, 1),
            (Loading, None),
            (Ready, 2),
        ]

    def test_equality_comparison_exceptions_raise_clear_type_error(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Comparison failures instruct the caller to provide key=... explicitly."""

        class Uncomparable:
            def __eq__(self, other: object) -> bool:
                raise RuntimeError("cannot compare")

        current = {"value": Uncomparable()}

        async def fetch_value(_arg: Uncomparable) -> str:
            return "done"

        @component
        def App() -> None:
            load(fetch_value, current["value"])

        capture = capture_patches(App)

        async def test() -> None:
            capture.render()
            await asyncio.sleep(0)
            capture.render()

            current["value"] = Uncomparable()
            capture.session.dirty.mark(capture.session.root_element.id)
            with pytest.raises(TypeError, match="provide key="):
                capture.render()

        asyncio.run(test())

    def test_stale_completions_do_not_overwrite_newer_results(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Older completions are ignored after reload or identity changes."""
        query = {"value": "slow"}
        started = {"slow": asyncio.Event(), "fast": asyncio.Event()}
        release = {"slow": asyncio.Event(), "fast": asyncio.Event()}
        snapshots: list[tuple[type[Load[object]], object | None]] = []

        async def fetch_value(name: str) -> str:
            started[name].set()
            try:
                await release[name].wait()
            except asyncio.CancelledError:
                await release[name].wait()
            return name

        @component
        def App() -> None:
            snapshots.append(_snapshot(load(fetch_value, query["value"])))

        capture = capture_patches(App)

        async def test() -> None:
            capture.render()
            await asyncio.sleep(0)
            await _wait_for(started["slow"])

            query["value"] = "fast"
            capture.session.dirty.mark(capture.session.root_element.id)
            capture.render()
            await asyncio.sleep(0)
            await _wait_for(started["fast"])

            release["fast"].set()
            await asyncio.sleep(0)
            capture.render()

            release["slow"].set()
            await asyncio.sleep(0)
            capture.render()

        asyncio.run(test())

        assert snapshots == [
            (Loading, None),
            (Loading, None),
            (Ready, "fast"),
        ]

    def test_load_is_reexported_from_root_and_package(self, rendered) -> None:
        """trellis reexports load, and trellis.state exports the helper types."""
        from trellis import load as root_load
        from trellis.state import Failed as package_failed
        from trellis.state import Load as package_load_type
        from trellis.state import Loading as package_loading
        from trellis.state import Ready as package_ready
        from trellis.state import load as package_load

        observed: list[Load[int]] = []

        async def fetch_value() -> int:
            await asyncio.Event().wait()
            return 1

        @component
        def App() -> None:
            observed.append(root_load(fetch_value))

        async def test() -> None:
            rendered(App)
            await asyncio.sleep(0)

        asyncio.run(test())

        assert root_load is package_load
        assert package_load_type is Load
        assert package_loading is Loading
        assert package_ready is Ready
        assert package_failed is Failed
        assert isinstance(observed[0], Loading)
