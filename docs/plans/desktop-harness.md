# Desktop E2E Test Harness — Future Plan

## What Exists Today

The branch added a desktop E2E testing system split across three layers:

### 1. Probe engine (`src/trellis/platforms/desktop/e2e.py`)
A closed `DesktopE2EScenario` enum, env-var-driven config, and hardcoded JS probe
scripts. The markdown-link probe is a JS IIFE that clicks the "Typography" tab,
traverses into a shadow DOM Markdown host, and dispatches a click on the first anchor.

### 2. In-process instrumentation (`DesktopPlatform` in `platform.py`)
Seven `_e2e_*` instance variables and three methods baked into the production platform
class. On every instantiation the platform checks `TRELLIS_DESKTOP_E2E_SCENARIO` from
the environment. When set it: injects the probe JS after connection, intercepts
`trellis_open_external` (recording the URL instead of opening a browser), emits a
`TRELLIS_DESKTOP_E2E_RESULT={json}` line to stdout, and terminates with exit code 0/1.

### 3. Subprocess runner (`tests/e2e/desktop_harness.py`)
Spawns the trellis CLI as a child process with E2E env vars, captures stdout, and
parses the result payload. Tests call `run_desktop_e2e_scenario()` and assert on the
returned `DesktopE2ERunResult`.

### Communication flow

```
test  →  subprocess  →  env vars
                          ↓
                  production code reads env
                          ↓
                  injects JS probe into webview
                          ↓
                  intercepts side effect (open_external)
                          ↓
                  prints JSON to stdout
                          ↓
test  ←  parses stdout  ←  exit code
```

## Problems

- **Test logic in production code.** `DesktopPlatform` carries E2E state on every
  instantiation. If an env var is accidentally set, external links silently fail.
- **Closed scenario enum.** Adding a new E2E test requires editing production source
  files (`e2e.py`, `platform.py`).
- **Hardcoded probes.** The JS probe string is specific to the showcase app layout
  ("Typography" button text, shadow DOM structure).
- **Single observation point.** Only `trellis_open_external` is observable — no way to
  assert on state changes, rendered output, or other commands.
- **Stdout parsing.** Fragile line-based protocol with no framing or versioning.

## Design Direction

The underlying capability — inject JS into a running Trellis webview and observe
Python-side effects — is valuable for both manual testing and agent-driven workflows.
A proper implementation would:

1. **Accept arbitrary JS probes** from the caller, not a closed enum.
2. **Provide general observation hooks** — intercept any command, state change, or
   render output, not just `open_external`.
3. **Use structured IPC** — a control socket or dedicated channel rather than stdout.
4. **Keep production code clean** — test instrumentation via middleware or a subclass,
   not mixed into the base `DesktopPlatform`.

### Sketch API

```python
from trellis.testing import DesktopTestHarness

async with DesktopTestHarness(app_root=Path("examples/widget_showcase")) as harness:
    # Inject arbitrary JS
    await harness.inject_js('document.querySelector("button").click()')

    # Observe any command the frontend sends to the backend
    result = await harness.wait_for_command("trellis_open_external")
    assert result.url == "https://example.com"

    # Or query rendered state
    tree = await harness.get_render_tree()
    assert tree.find("Label", text="Hello") is not None
```

This would live under `trellis.testing` (a new public module) and import nothing from
the desktop platform internals. The `DesktopPlatform` would expose a hook point (e.g.
command middleware) that the harness plugs into at test time.

## Status

Removed from the branch for now. To be re-implemented as a standalone testing module.
