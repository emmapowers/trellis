"""Integration tests for trellis.state.mount()."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import pytest

from trellis import component, mount, state

if TYPE_CHECKING:
    from tests.conftest import PatchCapture


class TestMountHelper:
    def test_sync_function_runs_once_on_mount(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """mount(sync_fn) runs once after the first mount."""
        calls: list[str] = []

        def start() -> None:
            calls.append("mounted")

        @component
        def App() -> None:
            mount(start)

        capture = capture_patches(App)
        capture.render()

        assert calls == ["mounted"]

    def test_async_function_runs_on_mount_and_can_update_state_later(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """mount(async_fn) can update state after the initial render."""
        done = asyncio.Event()
        observed: list[str] = []

        @component
        def App() -> None:
            status = state("idle")
            observed.append(status.value)

            async def start() -> None:
                await asyncio.sleep(0)
                status.set("ready")
                done.set()

            mount(start)

        capture = capture_patches(App)

        async def test() -> None:
            capture.render()
            await asyncio.wait_for(done.wait(), timeout=1.0)
            capture.render()

        asyncio.run(test())

        assert observed == ["idle", "ready"]

    def test_sync_generator_runs_setup_and_cleanup_on_unmount(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """mount(sync_generator) runs setup on mount and cleanup on unmount."""
        show_child = [True]
        events: list[str] = []

        def lifecycle():
            events.append("setup")
            yield
            events.append("cleanup")

        @component
        def Child() -> None:
            mount(lifecycle)

        @component
        def App() -> None:
            if show_child[0]:
                Child()

        capture = capture_patches(App)
        capture.render()

        show_child[0] = False
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        assert events == ["setup", "cleanup"]

    def test_async_generator_runs_setup_and_cleanup_on_unmount(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """mount(async_generator) runs async setup and cleanup once each."""
        show_child = [True]
        events: list[str] = []
        setup_done = asyncio.Event()
        cleanup_done = asyncio.Event()

        async def lifecycle():
            events.append("setup")
            setup_done.set()
            yield
            events.append("cleanup")
            cleanup_done.set()

        @component
        def Child() -> None:
            mount(lifecycle)

        @component
        def App() -> None:
            if show_child[0]:
                Child()

        capture = capture_patches(App)

        async def test() -> None:
            capture.render()
            await asyncio.wait_for(setup_done.wait(), timeout=1.0)

            show_child[0] = False
            capture.session.dirty.mark(capture.session.root_element.id)
            capture.render()

            await asyncio.wait_for(cleanup_done.wait(), timeout=1.0)

        asyncio.run(test())

        assert events == ["setup", "cleanup"]

    def test_rerender_does_not_rerun_mount_logic_for_same_slot(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """A mounted slot keeps its first callable and does not rerun on rerender."""
        calls: list[str] = []
        current_label = ["first"]
        counter_cell = []

        def run_current() -> None:
            calls.append(current_label[0])

        @component
        def App() -> None:
            counter = state(0)
            counter_cell[:] = [counter]
            mount(run_current)

        capture = capture_patches(App)
        capture.render()

        current_label[0] = "second"
        counter_cell[0].set(1)
        capture.render()

        assert calls == ["first"]

    def test_remount_creates_a_fresh_lifecycle_run(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Unmounting and remounting a slot captures a fresh callable."""
        show_child = [True]
        current_label = ["first"]
        calls: list[str] = []

        def start() -> None:
            calls.append(current_label[0])

        @component
        def Child() -> None:
            mount(start)

        @component
        def App() -> None:
            if show_child[0]:
                Child()

        capture = capture_patches(App)
        capture.render()

        show_child[0] = False
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        current_label[0] = "second"
        show_child[0] = True
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        assert calls == ["first", "second"]

    def test_generator_without_yield_logs_error_and_does_not_leak_cleanup(
        self,
        capture_patches: "type[PatchCapture]",
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A generator that never yields logs an error and stores no cleanup."""
        show_child = [True]
        events: list[str] = []

        def broken():
            events.append("setup")
            if False:
                yield

        @component
        def Child() -> None:
            mount(broken)

        @component
        def App() -> None:
            if show_child[0]:
                Child()

        capture = capture_patches(App)
        with caplog.at_level(logging.ERROR):
            capture.render()

        show_child[0] = False
        capture.session.dirty.mark(capture.session.root_element.id)
        with caplog.at_level(logging.ERROR):
            capture.render()

        assert events == ["setup"]
        assert "yield exactly once" in caplog.text

    def test_generator_with_multiple_yields_logs_error(
        self,
        capture_patches: "type[PatchCapture]",
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A generator that yields twice logs an error during cleanup."""
        show_child = [True]
        events: list[str] = []

        def broken():
            events.append("setup")
            yield
            events.append("cleanup")
            yield
            events.append("after")

        @component
        def Child() -> None:
            mount(broken)

        @component
        def App() -> None:
            if show_child[0]:
                Child()

        capture = capture_patches(App)
        capture.render()

        show_child[0] = False
        capture.session.dirty.mark(capture.session.root_element.id)
        with caplog.at_level(logging.ERROR):
            capture.render()

        assert events == ["setup", "cleanup"]
        assert "yield exactly once" in caplog.text

    def test_mount_is_reexported_from_root_and_package(self, rendered) -> None:
        """trellis and trellis.state both export mount()."""
        from trellis import mount as root_mount
        from trellis.state import mount as package_mount

        calls: list[str] = []

        @component
        def App() -> None:
            root_mount(lambda: calls.append("mounted"))

        rendered(App)

        assert root_mount is package_mount
        assert calls == ["mounted"]
