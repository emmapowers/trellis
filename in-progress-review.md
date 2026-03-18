# PR #51 Review Comments

## Actionable — can fix now

1. **`steps.py:729`** (emma) — Add docstring to `SSRBundleBuildStep` explaining it builds a Node-targeted bundle for the SSR sidecar (Bun), not shipped to the client.
   → **Action:** Update class docstring.

2. **`steps.py:842`** (coderabbit) — Put `renderer.start()` inside the `try` block so `renderer.stop()` runs if `start()` raises.
   → **Action:** Move `renderer.start()` inside the try.

3. **`steps.py:854`** (coderabbit) — Don't mark SSR enabled when renderer returns no HTML.
   → **Action:** Only set `ssr_enabled = True` if `ssr_html` is non-empty.

4. **`handler.py:330`** (emma) — Extract resumed vs new-session logic into separate functions.
   → **Action:** Refactor `handle_hello` into `_resume_session` and `_create_session` helpers.

5. **`handler.py:338`** (emma) — `_setup_router_callbacks` was supposed to be removed on main.
   → **Known tech debt** — router callbacks still use the old pattern because the send-queue refactor isn't merged yet.

6. **`handler.py:370,383`** (emma) — Add `_ssr_resumed` flag, skip `initial_render` when SSR; don't call `initial_render` in SSR context.
   → **Action:** Have `handle_hello` set an `_ssr_resumed` flag; `run()` skips `initial_render` when set.

7. **`handler.py:376`** (coderabbit) — Restore router callback setup in non-SSR initial render path.
   → **Action:** Call `_setup_router_callbacks()` after initial render in the non-SSR path too.

8. **`ssr_utils.py:4`** (emma) — Update module docstring; used by all platforms now, not just server.
   → **Action:** Update docstring.

9. **`ssr_utils.py:59`** (emma) — Is the `<` escaping in dehydration JSON robust enough?
   → **Action:** Verify and add a comment explaining the escaping.

10. **`serve_platform.py:127`** (coderabbit) — Respect `config.ssr` when composing app-mode steps.
    → **Action:** Only include `SSRBundleBuildStep`/`SSRPreRenderStep` when `config.ssr` is True.

11. **`platform.py:134`** (emma) — Move server platform lazy imports to the top.
    → **Action:** Move imports to module level.

12. **`platform.py:155`** (emma) — Extract SSR setup into its own function.
    → **Action:** Create `_setup_ssr()` helper in server platform.

13. **`ssr-entry.tsx:1`** (emma) — Verify SSR entry code isn't shipped to the client bundle.
    → **Action:** Verify esbuild config separates SSR bundle from client bundle. Add comment if needed.

14. **`subprocess.py:24`** (coderabbit) — Fix `Popen[bytes]` return type.
    → ✅ **Already fixed** — changed to `Popen[tp.Any]`.

15. **`config.py:269`** (coderabbit) — Document `ssr` and `session_ttl` fields in Config docstring.
    → ✅ **Already fixed** — docstring updated externally.

16. **`config.py:127`** (coderabbit) — Validate `session_ttl` as positive value.
    → ✅ **Already fixed** — `validate_positive_int` wired up externally.

17. **`desktop/index.html.j2`** (coderabbit) — Template removal code unreachable.
    → ✅ **Already fixed** — removed `<template>` approach entirely, SSR HTML is inline now.

## Needs discussion

18. **`steps.py:801`** (emma) — Should `SSRBundleBuildStep` move out of `bundler/steps.py`? It's used by all 3 platforms now.

19. **`steps.py:828`** (emma) — Same for `SSRPreRenderStep`. Both are build steps used by all platforms. Keeping in `bundler/` seems right since they're build steps, not runtime code.

20. **`main.tsx:48`** (emma) — Audit platform JS, move shared SSR/hydration code to common. How much can realistically be shared given platform-specific transports?

21. **`routes.py:74`** + **`ssr.py:55`** (emma) — Drop theme from server SSR? CSS variables make it unnecessary, and it halves the cache.

22. **`subprocess.py:110`** (emma) — Make `stop_child_process` async to avoid blocking the event loop.

23. **`ssr_renderer.py:28`** (emma) — Make SSRRenderer fully async (related to #22).

## Already resolved

24. **`ssr.py` cache never populated** (coderabbit) — Emma confirmed `_get_ssr_html()` has `self._cache.put()`.
25. **`desktop/main.tsx:89`** keep desktop loading fallback (coderabbit) — SSR is the loading fallback.
26. **`subprocess.py` Popen[bytes] type** (coderabbit) — Fixed this session.
27. **`desktop/index.html.j2` template removal unreachable** (coderabbit) — Removed template approach.
28. **`handler.py` _background_tasks** (emma) — Removed stale SSR branch artifacts.

## Low priority / noise

29. **`steps.py:754`** (coderabbit) — Include `output_name` in SSR bundle cache key. Minor edge case.
30. **`routes.py:53`** (coderabbit) — Don't run SSR for every 404. Already guarded by `_is_document_request`.
31. **`routes.py:87`** (coderabbit) — Advertise theme-dependent HTML with Vary header. Already done.
32. **`session_store.py:62`** (coderabbit) — Session cleanup/expiry. Already has TTL-based cleanup.
33. **`ssr_cache.py`** (coderabbit) — Bound cache key space / validate max_entries. Nice-to-have.
34. **`ssr_renderer.py:60,file`** (coderabbit) — PIPE draining, lock protection, restart safety. Subsumed by #23.
35. **`ssr.py:file`** (coderabbit) — Include theme_mode in cache key. Moot if we drop themes (#21).
36. **`ssr.py:file`** (coderabbit) — Escape dehydration payload. Already handled by `ssr_utils.py`.
37. **`check_hydration.js`** (coderabbit) — Minor test cleanup.
38. **`test_ssr_hydration.py`** (coderabbit) — Don't skip on exit code 2. Test robustness.
39. **`test_ssr_orchestrator.py:132`** (coderabbit) — Test doesn't verify cache reuse. Nice-to-have.
40. **`test_subprocess_utils.py:81`** (coderabbit) — Mock kernel32 in Windows tests. Nice-to-have.
41. **`ssr.py:107`** (emma) — Return None on SSR failure for CSR fallback. Already happens in `routes.py`.
42. **`platform.py:115`** (coderabbit) — Server platform setup suggestion. Overlaps with #12.
43. **`session_store.py:62`** (coderabbit, 2nd) — Expire entries without leaking session. Overlaps with #32.
