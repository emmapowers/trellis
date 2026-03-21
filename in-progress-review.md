# PR #51 Review Comments

## Actionable — can fix now

1. **`steps.py:729`** (emma) — Add docstring to `SSRBundleBuildStep`.
   → ✅ **Fixed** — Updated docstring clarifying it's for the Bun sidecar, not shipped to client.

2. **`steps.py:842`** (coderabbit) — Put `renderer.start()` inside the `try` block.
   → ✅ **Fixed** — `renderer.start()` now inside `try`.

3. **`steps.py:854`** (coderabbit) — Don't mark SSR enabled when renderer returns no HTML.
   → ✅ **Fixed** — `ssr_enabled` only set when HTML is non-empty.

4. **`handler.py:330`** (emma) — Extract resumed vs new-session logic into separate functions.
   → ✅ **Fixed** — Refactored into `_try_resume_session()` and `_create_session()`.

5. **`handler.py:338`** (emma) — `_setup_router_callbacks` was supposed to be removed on main.
   → ✅ **Resolved** — Known tech debt; send-queue refactor branch not merged yet.

6. **`handler.py:370,383`** (emma) — Add `_ssr_resumed` flag, skip `initial_render` when SSR.
   → ✅ **Fixed** — `_ssr_resumed` flag set in `_try_resume_session()`; `run()` skips `initial_render` when set.

7. **`handler.py:376`** (coderabbit) — Restore router callback setup in non-SSR initial render path.
   → ✅ **Fixed** — `_setup_router_callbacks()` called after `initial_render()` in non-SSR path.

8. **`ssr_utils.py:4`** (emma) — Update module docstring; used by all platforms now.
   → ✅ **Fixed** — Docstring updated.

9. **`ssr_utils.py:59`** (emma) — Is the `<` escaping robust enough?
   → ✅ **Fixed** — Added comment documenting the standard approach (OWASP, used by Next.js/Remix).

10. **`serve_platform.py:127`** (coderabbit) — Respect `config.ssr` when composing app-mode steps.
    → ✅ **Fixed** — SSR steps gated on `config.ssr`.

11. **`platform.py:134`** (emma) — Move server platform lazy imports to the top.
    → ✅ **Fixed** — Imports moved to module level.

12. **`platform.py:155`** (emma) — Extract SSR setup into its own function.
    → ✅ **Fixed** — Extracted `_setup_ssr()` helper.

13. **`ssr-entry.tsx:1`** (emma) — Verify SSR entry code isn't shipped to the client bundle.
    → ✅ **Fixed** — Added documentation; SSR uses `--platform=node`, client uses `--platform=browser`.

14. **`subprocess.py:24`** (coderabbit) — Fix `Popen[bytes]` return type.
    → ✅ **Previously fixed** — changed to `Popen[tp.Any]`.

15. **`config.py:269`** (coderabbit) — Document `ssr` and `session_ttl` fields in Config docstring.
    → ✅ **Previously fixed** — docstring updated.

16. **`config.py:127`** (coderabbit) — Validate `session_ttl` as positive value.
    → ✅ **Previously fixed** — `validate_positive_int` wired up.

17. **`desktop/index.html.j2`** (coderabbit) — Template removal code unreachable.
    → ✅ **Previously fixed** — removed `<template>` approach entirely.

## Needs discussion

18. **`steps.py:801`** (emma) — Should `SSRBundleBuildStep` move out of `bundler/steps.py`?
    → ✅ **Resolved** — Keeping in `bundler/`. It's a build step used by all 3 platforms, and that's where build steps live.

19. **`steps.py:828`** (emma) — Same for `SSRPreRenderStep`.
    → ✅ **Resolved** — Same reasoning.

20. **`main.tsx:48`** (emma) — Audit platform JS, move shared SSR/hydration code to common.
    → ✅ **Fixed** — Extracted `init.ts`, `ssr.ts` (types + `mountApp()`), `ClientApp.tsx` (shared wrapper) to common. All 3 entry points simplified.

21. **`routes.py:74`** + **`ssr.py:55`** (emma) — Drop theme from server SSR.
    → ✅ **Fixed** — Removed theme detection, params, and cache dimension. Cache keyed by route only.

22. **`subprocess.py:110`** (emma) — Make `stop_child_process` async.
    → ✅ **Fixed** — Added `start_child_process_async()`/`stop_child_process_async()` using `asyncio.create_subprocess_exec`.

23. **`ssr_renderer.py:28`** (emma) — Make SSRRenderer fully async.
    → ✅ **Fixed** — Full async rewrite: `httpx.AsyncClient`, `asyncio.create_subprocess_exec`, `asyncio.Lock`. Build pipeline (`BuildStep.run()`, `build()`, `AppLoader.bundle()`) made async too.

## Already resolved

24. **`ssr.py` cache never populated** (coderabbit) — Emma confirmed `_get_ssr_html()` has `self._cache.put()`.
25. **`desktop/main.tsx:89`** keep desktop loading fallback (coderabbit) — SSR is the loading fallback.
26. **`subprocess.py` Popen[bytes] type** (coderabbit) — Fixed this session.
27. **`desktop/index.html.j2` template removal unreachable** (coderabbit) — Removed template approach.
28. **`handler.py` _background_tasks** (emma) — Removed stale SSR branch artifacts.

## Low priority / noise

29. **`steps.py:754`** (coderabbit) — Include `output_name` in SSR bundle cache key. Minor edge case.
30. **`routes.py:53`** (coderabbit) — Don't run SSR for every 404. Already guarded by `_is_document_request`.
31. **`routes.py:87`** (coderabbit) — Vary header. Moot — theme removed from SSR.
32. **`session_store.py:62`** (coderabbit) — Session cleanup/expiry. Already has TTL-based cleanup.
33. **`ssr_cache.py`** (coderabbit) — Bound cache key space / validate max_entries. Nice-to-have.
34. **`ssr_renderer.py:60,file`** (coderabbit) — PIPE draining, lock protection, restart safety. Subsumed by #23.
35. **`ssr.py:file`** (coderabbit) — Include theme_mode in cache key. Moot — theme removed from SSR.
36. **`ssr.py:file`** (coderabbit) — Escape dehydration payload. Already handled by `ssr_utils.py`.
37. **`check_hydration.js`** (coderabbit) — Minor test cleanup.
38. **`test_ssr_hydration.py`** (coderabbit) — Don't skip on exit code 2. Test robustness.
39. **`test_ssr_orchestrator.py:132`** (coderabbit) — Test doesn't verify cache reuse. Nice-to-have.
40. **`test_subprocess_utils.py:81`** (coderabbit) — Mock kernel32 in Windows tests. Nice-to-have.
41. **`ssr.py:107`** (emma) — Return None on SSR failure for CSR fallback. Already happens in `routes.py`.
42. **`platform.py:115`** (coderabbit) — Server platform setup suggestion. Overlaps with #12.
43. **`session_store.py:62`** (coderabbit, 2nd) — Expire entries without leaking session. Overlaps with #32.
