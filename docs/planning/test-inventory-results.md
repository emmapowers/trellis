# Test Inventory Results

## Progress

| File | Status |
|------|--------|
| tests/test_base.py | Complete |
| tests/test_block_component.py | Complete |
| tests/test_bundler.py | Complete |
| tests/test_composition_component.py | Complete |
| tests/test_context.py | Complete |
| tests/test_deep_trees.py | Complete |
| tests/test_efficient_updates.py | Complete |
| tests/test_event_handling.py | Complete |
| tests/test_fine_grained_classes.py | Complete |
| tests/test_html.py | Complete |
| tests/test_message_handler.py | Complete |
| tests/test_messages.py | Complete |
| tests/test_mutable.py | Complete |
| tests/test_ports.py | Complete |
| tests/test_react_component.py | Complete |
| tests/test_reconciler.py | Complete |
| tests/test_rendering.py | Complete |
| tests/test_routes.py | Complete |
| tests/test_serialization.py | Complete |
| tests/test_serve_platform.py | Complete |
| tests/test_state.py | Complete |
| tests/test_state_edge_cases.py | Complete |
| tests/test_style_props.py | Complete |
| tests/test_tracked.py | Complete |
| tests/test_trellis.py | Complete |
| tests/test_utils.py | Complete |
| tests/test_widgets.py | Complete |
| tests/integration/test_bundler.py | Complete |
| tests/js/ClientMessageHandler.test.ts | Complete |
| tests/js/core/store.test.ts | Complete |
| tests/js/core/types.test.ts | Complete |
| tests/js/core/renderTree.test.tsx | Complete |

---

## tests/test_base.py

**Module Under Test**: `trellis.core.components.base`, `trellis.core.components.composition`, `trellis.core.components.react`, `trellis.html.base`, `trellis.html.text`
**Classification**: Unit
**Test Count**: 9
**Target Location**: `tests/py/unit/core/components/test_base.py`

### Dependencies
- Real: None (all tests use direct instantiation/decoration)
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestElementKind.test_element_kind_explicit_values`

| Field | Value |
|-------|-------|
| **Purpose** | Verify ElementKind enum values are explicit strings for stable wire format serialization |
| **Invariants** | ElementKind enum values must be the exact strings "react_component", "jsx_element", "text" |
| **Assertion Coverage** | Yes - directly asserts the three expected string values |

#### `TestElementKind.test_element_kind_is_str_enum`

| Field | Value |
|-------|-------|
| **Purpose** | Verify ElementKind values are usable as strings without .value accessor |
| **Invariants** | StrEnum members can be used directly in string contexts (str(), f-strings) |
| **Assertion Coverage** | Yes - tests both str() and f-string interpolation |

#### `TestElementKind.test_element_kind_value_property`

| Field | Value |
|-------|-------|
| **Purpose** | Verify ElementKind.value property returns the string value |
| **Invariants** | The .value property returns the underlying string for all enum members |
| **Assertion Coverage** | Yes - checks .value for all three enum members |

#### `TestIComponentProtocolConformance.test_composition_component_has_element_kind`

| Field | Value |
|-------|-------|
| **Purpose** | Verify CompositionComponent implements element_kind property from IComponent protocol |
| **Invariants** | Components created with @component decorator have element_kind = REACT_COMPONENT |
| **Assertion Coverage** | Yes - checks hasattr and value |

#### `TestIComponentProtocolConformance.test_composition_component_has_element_name`

| Field | Value |
|-------|-------|
| **Purpose** | Verify CompositionComponent implements element_name property from IComponent protocol |
| **Invariants** | Components created with @component decorator have element_name = "CompositionComponent" |
| **Assertion Coverage** | Yes - checks hasattr and value |

#### `TestIComponentProtocolConformance.test_composition_component_has_required_methods`

| Field | Value |
|-------|-------|
| **Purpose** | Verify CompositionComponent has methods required by the component protocol |
| **Invariants** | Components must be callable and have execute() and _has_children_param |
| **Assertion Coverage** | Yes - checks callable() and hasattr for execute, _has_children_param |

#### `TestIComponentProtocolConformance.test_html_element_has_jsx_element_kind`

| Field | Value |
|-------|-------|
| **Purpose** | Verify HtmlElement returns JSX_ELEMENT kind for native DOM rendering |
| **Invariants** | HTML elements decorated with @html_element must have element_kind = JSX_ELEMENT |
| **Assertion Coverage** | Yes - accesses _component attribute and checks element_kind |

#### `TestIComponentProtocolConformance.test_text_node_has_text_kind`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TextNode has TEXT kind and special "__text__" element name |
| **Invariants** | TextNode must have element_kind = TEXT and element_name = "__text__" for client-side text handling |
| **Assertion Coverage** | Yes - checks both element_kind and element_name |

#### `TestIComponentProtocolConformance.test_react_component_base_has_react_component_kind`

| Field | Value |
|-------|-------|
| **Purpose** | Verify ReactComponentBase subclasses return REACT_COMPONENT kind |
| **Invariants** | Widget classes extending ReactComponentBase have element_kind = REACT_COMPONENT and element_name matching _element_name |
| **Assertion Coverage** | Yes - checks both element_kind and element_name on subclass instance |

### Quality Issues

- **None identified** - Tests are well-isolated, clearly named, and test public API behavior
- Tests properly verify protocol conformance without depending on implementation details
- Good coverage of the ElementKind contract (wire format stability) and component protocol

---

## tests/test_block_component.py

**Module Under Test**: `trellis.core.components.composition`, `trellis.core.rendering.render`, `trellis.core.rendering.session`
**Classification**: Integration
**Test Count**: 8
**Target Location**: `tests/py/integration/core/test_container_components.py`

### Dependencies
- Real: `RenderSession`, `render()`, `@component` decorator
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestContainerComponent.test_with_statement_collects_children`

| Field | Value |
|-------|-------|
| **Purpose** | Verify that children created inside a `with` block are passed to the container component |
| **Invariants** | Components with `children` parameter receive all elements created in their `with` block; the tree structure reflects parent-child relationships |
| **Assertion Coverage** | Yes - verifies tree structure: Parent→Column→2 Children |

#### `TestContainerComponent.test_nested_containers`

| Field | Value |
|-------|-------|
| **Purpose** | Verify that nested `with` blocks work correctly for deeply nested container hierarchies |
| **Invariants** | Nested containers each collect their own children; tree depth matches nesting level |
| **Assertion Coverage** | Yes - verifies Column→Row→Child structure and component names |

#### `TestContainerComponent.test_container_receives_children_list`

| Field | Value |
|-------|-------|
| **Purpose** | Verify container components receive children as a list of Element descriptors |
| **Invariants** | The `children` parameter is a list of Element objects (descriptors), not rendered nodes |
| **Assertion Coverage** | Yes - captures children list and verifies length and type |

#### `TestContainerComponent.test_component_without_children_param_raises_on_with`

| Field | Value |
|-------|-------|
| **Purpose** | Verify that using `with` on a component that doesn't accept children raises TypeError |
| **Invariants** | Components must explicitly opt-in to children via `children` parameter; using `with` without it is an error |
| **Assertion Coverage** | Yes - uses pytest.raises with match string |

#### `TestContainerComponent.test_cannot_provide_children_prop_and_use_with`

| Field | Value |
|-------|-------|
| **Purpose** | Verify that providing both `children` prop and `with` block raises RuntimeError |
| **Invariants** | Children can only come from one source (prop or with block), not both |
| **Assertion Coverage** | Yes - uses pytest.raises with match string |

#### `TestContainerComponent.test_empty_with_block`

| Field | Value |
|-------|-------|
| **Purpose** | Verify that an empty `with` block results in an empty children list |
| **Invariants** | Empty `with` block passes `children=[]`, not `None` or missing |
| **Assertion Coverage** | Yes - captures children and asserts equals empty list |

#### `TestContainerComponent.test_child_call_mounts_element`

| Field | Value |
|-------|-------|
| **Purpose** | Verify that calling `child()` mounts the element; uncalled children are not mounted |
| **Invariants** | Children are descriptors until `child()` is called; only called children appear in tree |
| **Assertion Coverage** | Yes - verifies only 1 child mounted despite 3 collected |

#### `TestContainerComponent.test_container_can_reorder_children`

| Field | Value |
|-------|-------|
| **Purpose** | Verify containers can mount children in a different order than collected |
| **Invariants** | Order of `child()` calls determines tree order, not order of collection |
| **Assertion Coverage** | Yes - verifies reversed order via props comparison |

### Quality Issues

- **Classification mismatch**: These tests exercise multiple modules working together (component decorator + render pipeline + session management), making them integration tests despite testing "unit" behavior
- Tests are well-structured with clear purposes and good isolation between test cases
- Good coverage of edge cases (empty blocks, error conditions, reordering)

---

## tests/test_bundler.py

**Module Under Test**: `trellis.bundler`
**Classification**: Unit (most tests), Integration (build_bundle test)
**Test Count**: 12
**Target Location**: `tests/py/unit/test_bundler.py` (split build_bundle test to `tests/py/integration/test_bundler.py`)

### Dependencies
- Real: `tarfile`, `pathlib.Path`, `io.BytesIO`
- Mocked: `platform.system`, `platform.machine`, `trellis.bundler.ensure_esbuild`, `trellis.bundler.ensure_packages`, `subprocess.run`

### Fixtures Used
- `tmp_path` (pytest built-in)

### Tests

#### `TestGetPlatform.test_darwin_arm64`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _get_platform returns "darwin-arm64" for macOS ARM |
| **Invariants** | Darwin + arm64 → "darwin-arm64" |
| **Assertion Coverage** | Yes - direct equality check |

#### `TestGetPlatform.test_darwin_x64`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _get_platform returns "darwin-x64" for macOS Intel |
| **Invariants** | Darwin + x86_64 → "darwin-x64" |
| **Assertion Coverage** | Yes - direct equality check |

#### `TestGetPlatform.test_linux_x64`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _get_platform returns "linux-x64" for Linux x86_64 |
| **Invariants** | Linux + x86_64 → "linux-x64" |
| **Assertion Coverage** | Yes - direct equality check |

#### `TestGetPlatform.test_linux_arm64`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _get_platform returns "linux-arm64" for Linux aarch64 |
| **Invariants** | Linux + aarch64 → "linux-arm64" |
| **Assertion Coverage** | Yes - direct equality check |

#### `TestGetPlatform.test_windows_x64`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _get_platform returns "win32-x64" for Windows x64 |
| **Invariants** | Windows + AMD64 → "win32-x64" |
| **Assertion Coverage** | Yes - direct equality check |

#### `TestGetPlatform.test_unsupported_os`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _get_platform raises RuntimeError for unsupported OS |
| **Invariants** | Unknown OS raises RuntimeError with "Unsupported platform" message |
| **Assertion Coverage** | Yes - pytest.raises with match |

#### `TestGetPlatform.test_unsupported_arch`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _get_platform raises RuntimeError for unsupported architecture |
| **Invariants** | Unknown architecture raises RuntimeError with "Unsupported platform" message |
| **Assertion Coverage** | Yes - pytest.raises with match |

#### `TestSafeExtract.test_safe_extract_normal_paths`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _safe_extract correctly extracts normal tarball paths |
| **Invariants** | Normal relative paths extract to expected locations with correct content |
| **Assertion Coverage** | Yes - verifies file contents at expected paths |

#### `TestSafeExtract.test_safe_extract_rejects_parent_traversal`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _safe_extract rejects paths with parent directory traversal (../) |
| **Invariants** | Paths starting with "../" must raise ValueError |
| **Assertion Coverage** | Yes - pytest.raises with "path traversal" match |

#### `TestSafeExtract.test_safe_extract_rejects_hidden_traversal`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _safe_extract rejects paths with hidden traversal in middle |
| **Invariants** | Paths containing "../" anywhere must raise ValueError |
| **Assertion Coverage** | Yes - pytest.raises with "path traversal" match |

#### `TestSafeExtract.test_safe_extract_rejects_absolute_paths`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _safe_extract rejects absolute paths |
| **Invariants** | Absolute paths (starting with /) must raise ValueError |
| **Assertion Coverage** | Yes - pytest.raises with "path traversal" match |

#### `TestBundleConfig.test_static_files_default_is_none`

| Field | Value |
|-------|-------|
| **Purpose** | Verify BundleConfig.static_files defaults to None |
| **Invariants** | Omitting static_files parameter results in None |
| **Assertion Coverage** | Yes - direct equality check |

#### `TestBundleConfig.test_static_files_can_be_set`

| Field | Value |
|-------|-------|
| **Purpose** | Verify BundleConfig.static_files can be configured as dict |
| **Invariants** | static_files parameter is stored correctly |
| **Assertion Coverage** | Yes - direct equality check |

#### `TestBuildBundleStaticFiles.test_copies_static_files_to_dist`

| Field | Value |
|-------|-------|
| **Purpose** | Verify build_bundle copies static files to dist directory |
| **Invariants** | Files specified in static_files are copied to dist with correct content |
| **Assertion Coverage** | Yes - verifies file exists and content matches |

### Quality Issues

- **Good isolation**: Platform detection tests properly mock system calls
- **Security testing**: Good coverage of tarball path traversal attack vectors
- **Integration test mixed in**: `test_copies_static_files_to_dist` is more of an integration test (uses real filesystem, mocks multiple dependencies) - could be cleaner if split out
- Tests are well-named and focused on single behaviors

---

## tests/test_composition_component.py

**Module Under Test**: `trellis.core.components.composition`, `trellis.core.rendering.render`, `trellis.core.rendering.session`
**Classification**: Integration
**Test Count**: 10
**Target Location**: `tests/py/integration/core/test_composition_component.py`

### Dependencies
- Real: `RenderSession`, `render()`, `@component` decorator, `CompositionComponent`
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestCompositionComponent.test_component_decorator`

| Field | Value |
|-------|-------|
| **Purpose** | Verify @component decorator creates a CompositionComponent with correct name |
| **Invariants** | Decorated function becomes CompositionComponent instance with name matching function name |
| **Assertion Coverage** | Yes - checks isinstance and name property |

#### `TestCompositionComponent.test_component_returns_node`

| Field | Value |
|-------|-------|
| **Purpose** | Verify component renders to an Element with correct component reference |
| **Invariants** | RenderSession.root_element is an Element whose component property equals the root component |
| **Assertion Coverage** | Yes - checks root_element exists, is Element, has correct component |

#### `TestCompositionComponent.test_nested_components`

| Field | Value |
|-------|-------|
| **Purpose** | Verify child components are correctly nested in the element tree |
| **Invariants** | Calling a component inside another creates parent-child relationship in tree |
| **Assertion Coverage** | Yes - verifies child_ids length and child's component reference |

#### `TestCompositionComponent.test_component_with_props_via_parent`

| Field | Value |
|-------|-------|
| **Purpose** | Verify props are passed to child component's render function |
| **Invariants** | Props passed when calling component are received in render function |
| **Assertion Coverage** | Yes - captures received props via side effect |

#### `TestCompositionComponent.test_multiple_children`

| Field | Value |
|-------|-------|
| **Purpose** | Verify multiple child components are all collected |
| **Invariants** | N component calls produce N child_ids in parent |
| **Assertion Coverage** | Yes - checks child_ids length equals 3 |

#### `TestCompositionComponent.test_implicit_child_collection`

| Field | Value |
|-------|-------|
| **Purpose** | Verify elements created in component body are auto-collected with correct props |
| **Invariants** | Elements created during execution become children in creation order; props are preserved |
| **Assertion Coverage** | Yes - verifies count and props on each child |

#### `TestCompositionComponent.test_conditional_children`

| Field | Value |
|-------|-------|
| **Purpose** | Verify only created elements are collected (conditional rendering) |
| **Invariants** | Children count reflects actual component calls, not potential calls |
| **Assertion Coverage** | Yes - compares two scenarios (1 child vs 0 children) |

#### `TestCompositionComponent.test_loop_children`

| Field | Value |
|-------|-------|
| **Purpose** | Verify elements created in loops are all collected with correct props |
| **Invariants** | Loop iterations produce corresponding children; props preserve loop values |
| **Assertion Coverage** | Yes - verifies count and props for each iteration |

#### `TestCompositionComponent.test_component_with_explicit_none_key`

| Field | Value |
|-------|-------|
| **Purpose** | Verify key=None results in None, not the string "None" |
| **Invariants** | Explicit key=None and omitted key both result in None; string keys are preserved as strings |
| **Assertion Coverage** | Yes - checks three children: explicit None, omitted, explicit string |

### Quality Issues

- **Classification**: These are integration tests (use RenderSession + render() + component decorator together)
- **Good coverage**: Tests cover basic usage, nesting, props, loops, conditionals, keys
- **Clean structure**: Each test is focused on a single behavior

---

## tests/test_context.py

**Module Under Test**: `trellis.core.state.stateful` (context API: `with state:` and `from_context()`)
**Classification**: Integration
**Test Count**: 15
**Target Location**: `tests/py/integration/core/state/test_context.py`

### Dependencies
- Real: `RenderSession`, `render()`, `@component`, `Stateful`
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestContextAPI.test_context_requires_render_context`

| Field | Value |
|-------|-------|
| **Purpose** | Verify `with state:` raises RuntimeError outside render context |
| **Invariants** | Context API only works during component execution |
| **Assertion Coverage** | Yes - pytest.raises with match |

#### `TestContextAPI.test_from_context_requires_render_context`

| Field | Value |
|-------|-------|
| **Purpose** | Verify `from_context()` raises RuntimeError outside render context |
| **Invariants** | Context API only works during component execution |
| **Assertion Coverage** | Yes - pytest.raises with match |

#### `TestContextAPI.test_context_basic_push_pop`

| Field | Value |
|-------|-------|
| **Purpose** | Verify basic context push/pop with `with` statement inside render |
| **Invariants** | State provided via `with` is retrievable by `from_context()` in descendants |
| **Assertion Coverage** | Yes - captures value and compares |

#### `TestContextAPI.test_context_nested_same_type`

| Field | Value |
|-------|-------|
| **Purpose** | Verify nested contexts - inner shadows outer for child components |
| **Invariants** | Components find the nearest ancestor context of the requested type |
| **Assertion Coverage** | Yes - captures from multiple components, verifies expected values |

#### `TestContextAPI.test_context_different_types`

| Field | Value |
|-------|-------|
| **Purpose** | Verify different state types have separate context stacks |
| **Invariants** | Context lookup is type-specific; multiple types can coexist |
| **Assertion Coverage** | Yes - captures both types' values |

#### `TestContextAPI.test_context_not_found_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify `from_context()` raises LookupError when no context provided |
| **Invariants** | Missing context raises LookupError with descriptive message |
| **Assertion Coverage** | Yes - pytest.raises with match |

#### `TestContextAPI.test_context_with_default_returns_none`

| Field | Value |
|-------|-------|
| **Purpose** | Verify `from_context(default=None)` returns None when no context |
| **Invariants** | With default=None, missing context returns None instead of raising |
| **Assertion Coverage** | Yes - captures and compares to [None] |

#### `TestContextAPI.test_context_with_default_returns_found`

| Field | Value |
|-------|-------|
| **Purpose** | Verify `from_context(default=None)` returns context when available |
| **Invariants** | Default parameter doesn't affect behavior when context exists |
| **Assertion Coverage** | Yes - verifies result is not None and has expected value |

#### `TestContextAPI.test_context_with_render`

| Field | Value |
|-------|-------|
| **Purpose** | Verify context works during component rendering |
| **Invariants** | Context is available throughout render execution |
| **Assertion Coverage** | Yes - captures state value |

#### `TestContextAPI.test_context_deeply_nested_components`

| Field | Value |
|-------|-------|
| **Purpose** | Verify context accessible through deep component nesting |
| **Invariants** | Context walks up entire ancestor chain, not just direct parent |
| **Assertion Coverage** | Yes - captures value from deeply nested component |

#### `TestContextAPI.test_context_as_variable`

| Field | Value |
|-------|-------|
| **Purpose** | Verify `with state as var` pattern works |
| **Invariants** | `__enter__` returns self for use in `with ... as` syntax |
| **Assertion Coverage** | Yes - asserts inline and captures from child |

#### `TestContextAPI.test_context_exception_safety`

| Field | Value |
|-------|-------|
| **Purpose** | Verify context is still accessible in except block during render |
| **Invariants** | Context persists on node, exceptions don't clear it |
| **Assertion Coverage** | Yes - captures identity comparison |

#### `TestContextAPI.test_context_multiple_instances_different_subclasses`

| Field | Value |
|-------|-------|
| **Purpose** | Verify subclasses have their own context stacks |
| **Invariants** | Each Stateful subclass has independent context; inheritance doesn't affect lookup |
| **Assertion Coverage** | Yes - captures values from both base and derived types |

#### `TestContextAPI.test_context_reuse_same_instance`

| Field | Value |
|-------|-------|
| **Purpose** | Verify same instance can be used in context multiple times |
| **Invariants** | Instance identity preserved across multiple `with` blocks |
| **Assertion Coverage** | Yes - captures values from two children, both see same value |

#### `TestContextAPI.test_context_state_modification_during_render_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify modifying state during render raises RuntimeError |
| **Invariants** | State is immutable during render; modifications must happen in callbacks |
| **Assertion Coverage** | Yes - pytest.raises with match |

### Quality Issues

- **Good coverage**: Comprehensive testing of context API edge cases
- **Clear invariants**: Each test verifies a specific aspect of context behavior
- **Classification**: Integration tests (exercise Stateful + components + rendering together)
- **Potential improvement**: `test_context_nested_same_type` uses two different types (OuterState/InnerState) which doesn't actually test "same type" nesting - the test name is misleading

---

## tests/test_deep_trees.py

**Module Under Test**: `trellis.core.components.composition`, `trellis.core.rendering.render`, `trellis.core.rendering.session`, `trellis.core.state.stateful`
**Classification**: Integration
**Test Count**: 15
**Target Location**: `tests/py/integration/core/test_deep_trees.py`

### Dependencies
- Real: `RenderSession`, `render()`, `@component`, `Stateful`
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestDeepTrees.test_50_level_deep_tree`

| Field | Value |
|-------|-------|
| **Purpose** | Verify framework handles deeply nested trees (50 levels) |
| **Invariants** | Tree depth equals DEPTH+1 (for Root); all levels render correctly |
| **Assertion Coverage** | Yes - recursively counts depth and asserts equals 51 |

#### `TestDeepTrees.test_parent_child_relationships_deep_tree`

| Field | Value |
|-------|-------|
| **Purpose** | Verify parent_id is correctly set for each node in deep tree |
| **Invariants** | Every node's state.parent_id matches its actual parent element's id |
| **Assertion Coverage** | Yes - recursively verifies all relationships, collects errors |

#### `TestDeepTrees.test_deep_tree_rerender_preserves_structure`

| Field | Value |
|-------|-------|
| **Purpose** | Verify re-rendering preserves node IDs (stable identity) |
| **Invariants** | Node IDs are deterministic and stable across re-renders |
| **Assertion Coverage** | Yes - collects IDs before/after re-render and compares |

#### `TestDeepTrees.test_deep_tree_with_state`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Stateful instances mount once per level in deep tree |
| **Invariants** | on_mount called once per level; re-render doesn't create new states |
| **Assertion Coverage** | Yes - counts mounts before and after re-render |

#### `TestWideTrees.test_50_siblings`

| Field | Value |
|-------|-------|
| **Purpose** | Verify framework handles wide trees (50 siblings) |
| **Invariants** | Parent's child_ids length equals number of children created |
| **Assertion Coverage** | Yes - asserts child_ids length is 50 |

#### `TestWideTrees.test_wide_tree_rerender`

| Field | Value |
|-------|-------|
| **Purpose** | Verify re-rendering preserves all sibling IDs |
| **Invariants** | Sibling IDs are stable across re-renders |
| **Assertion Coverage** | Yes - compares ID lists before/after |

#### `TestWideTrees.test_add_siblings`

| Field | Value |
|-------|-------|
| **Purpose** | Verify adding siblings mounts new elements |
| **Invariants** | Increasing child count adds new elements to tree |
| **Assertion Coverage** | Yes - checks child_ids length after adding siblings |

#### `TestWideTrees.test_remove_siblings`

| Field | Value |
|-------|-------|
| **Purpose** | Verify removing siblings unmounts old elements |
| **Invariants** | on_unmount called for each removed sibling; only removed indices unmounted |
| **Assertion Coverage** | Yes - verifies unmount count and indices |

#### `TestCombinedDeepAndWide.test_branching_tree`

| Field | Value |
|-------|-------|
| **Purpose** | Verify framework handles trees with branching factor at each level |
| **Invariants** | Total node count matches geometric series formula |
| **Assertion Coverage** | Yes - recursively counts nodes and compares to expected 122 |

#### `TestCombinedDeepAndWide.test_deep_tree_with_wide_leaf_level`

| Field | Value |
|-------|-------|
| **Purpose** | Verify deep tree with many children at leaf level |
| **Invariants** | Leaf level has expected child count; tree structure correct |
| **Assertion Coverage** | Yes - navigates to leaf level and checks child count |

#### `TestMountingOrder.test_deep_tree_mount_order`

| Field | Value |
|-------|-------|
| **Purpose** | Verify mount order is parent-first in deep tree |
| **Invariants** | on_mount called in order 0, 1, 2, ..., DEPTH |
| **Assertion Coverage** | Yes - collects mount order and asserts sequential |

#### `TestMountingOrder.test_wide_tree_unmount_order`

| Field | Value |
|-------|-------|
| **Purpose** | Verify all children unmount when parent removed |
| **Invariants** | Removing container unmounts all its children |
| **Assertion Coverage** | Yes - verifies all 10 children unmounted |

#### `TestTreeTraversal.test_empty_tree`

| Field | Value |
|-------|-------|
| **Purpose** | Verify empty component (no children) works |
| **Invariants** | Root element exists with empty child_ids |
| **Assertion Coverage** | Yes - checks root_element exists and has 0 children |

#### `TestTreeTraversal.test_single_child_chain`

| Field | Value |
|-------|-------|
| **Purpose** | Verify tree where each node has exactly one child |
| **Invariants** | Chain has exactly DEPTH levels; each node has exactly 1 child |
| **Assertion Coverage** | Yes - traverses chain and counts depth |

#### `TestTreeTraversal.test_asymmetric_tree`

| Field | Value |
|-------|-------|
| **Purpose** | Verify tree with different depths in different branches |
| **Invariants** | Each branch has its expected depth; asymmetry preserved |
| **Assertion Coverage** | Yes - measures depth of each branch separately |

### Quality Issues

- **Good stress testing**: Exercises edge cases with large trees (50+ nodes)
- **Clear invariants**: Each test verifies specific structural properties
- **Well-organized**: Logical grouping by tree shape (deep, wide, combined)
- **Integration tests**: Use full render pipeline with RenderSession + render()

---

## tests/test_efficient_updates.py

**Module Under Test**: `trellis.core.components.composition`, `trellis.core.rendering.render`, `trellis.core.rendering.session`, `trellis.core.state.stateful`
**Classification**: Integration
**Test Count**: 14
**Target Location**: `tests/py/integration/core/test_efficient_updates.py`

### Dependencies
- Real: `RenderSession`, `render()`, `@component`, `Stateful`
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestMinimalRerenders.test_state_change_only_rerenders_dependent_component`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state change only re-renders the component that reads it |
| **Invariants** | Components not reading changed state don't re-execute |
| **Assertion Coverage** | Yes - tracks render counts per component |

#### `TestMinimalRerenders.test_fine_grained_property_tracking`

| Field | Value |
|-------|-------|
| **Purpose** | Verify only components reading the changed property re-render |
| **Invariants** | Property-level dependency tracking; different properties are independent |
| **Assertion Coverage** | Yes - tests each property change independently |

#### `TestMinimalRerenders.test_multiple_state_changes_batched`

| Field | Value |
|-------|-------|
| **Purpose** | Verify multiple state changes before render are batched |
| **Invariants** | Components render once per batch, not once per change |
| **Assertion Coverage** | Yes - makes multiple changes then one render() call |

#### `TestPropsUnchangedOptimization.test_unchanged_props_skip_execution`

| Field | Value |
|-------|-------|
| **Purpose** | Verify components with unchanged props don't re-execute |
| **Invariants** | Props comparison determines whether to execute component |
| **Assertion Coverage** | Yes - parent re-renders but child skipped |

#### `TestPropsUnchangedOptimization.test_changed_props_trigger_execution`

| Field | Value |
|-------|-------|
| **Purpose** | Verify components with changed props do re-execute |
| **Invariants** | Changed props force component execution |
| **Assertion Coverage** | Yes - changing value_ref triggers child re-render |

#### `TestPropsUnchangedOptimization.test_deeply_nested_unchanged_props`

| Field | Value |
|-------|-------|
| **Purpose** | Verify deeply nested components with unchanged props skip execution |
| **Invariants** | Props optimization works at all nesting levels |
| **Assertion Coverage** | Yes - only root re-executes, all children skipped |

#### `TestDirtyMarkingBehavior.test_mark_dirty_only_affects_target`

| Field | Value |
|-------|-------|
| **Purpose** | Verify marking element dirty doesn't affect parent or siblings |
| **Invariants** | Dirty marking is element-specific, not inherited |
| **Assertion Coverage** | Yes - only child1 re-renders when marked dirty |

#### `TestDirtyMarkingBehavior.test_dirty_parent_and_child_renders_child_once`

| Field | Value |
|-------|-------|
| **Purpose** | Verify child renders once even if both parent and child are dirty |
| **Invariants** | Parent clears child's dirty flag when re-rendering child |
| **Assertion Coverage** | Yes - child count is 1 not 2 |

#### `TestDirtyMarkingBehavior.test_child_dirty_cleared_by_parent_rerender`

| Field | Value |
|-------|-------|
| **Purpose** | Verify parent re-render handles child's dirty state |
| **Invariants** | Child's props unchanged so it should be skipped |
| **Assertion Coverage** | Yes - child count stays at 1 |

#### `TestDirtyMarkingBehavior.test_dirty_container_preserves_children`

| Field | Value |
|-------|-------|
| **Purpose** | Verify container marked dirty still receives its children |
| **Invariants** | Re-render preserves children passed via `with` block |
| **Assertion Coverage** | Yes - children_received shows 1 both times |

#### `TestDeeplyNestedStateUpdates.test_deep_state_change_only_rerenders_path`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state change in deep component only re-renders the leaf |
| **Invariants** | Intermediate levels don't re-render for leaf state change |
| **Assertion Coverage** | Yes - only leaf counter increases |

#### `TestDeeplyNestedStateUpdates.test_multiple_readers_at_different_depths`

| Field | Value |
|-------|-------|
| **Purpose** | Verify multiple components at different depths reading same state |
| **Invariants** | All readers re-render; non-readers don't |
| **Assertion Coverage** | Yes - root, level1, level3 re-render; level2 doesn't |

#### `TestStateWithMultipleComponents.test_same_state_multiple_readers`

| Field | Value |
|-------|-------|
| **Purpose** | Verify multiple components reading same property all re-render |
| **Invariants** | All dependents notified on property change |
| **Assertion Coverage** | Yes - both readers increment, non-reader doesn't |

#### `TestStateWithMultipleComponents.test_independent_states_independent_updates`

| Field | Value |
|-------|-------|
| **Purpose** | Verify independent state instances trigger independent updates |
| **Invariants** | State instance isolation; changes don't cross-pollinate |
| **Assertion Coverage** | Yes - changing state_a only affects ReaderA |

### Quality Issues

- **Critical tests**: These verify the core fine-grained reactivity system
- **Good coverage**: Tests property-level tracking, props optimization, dirty marking
- **Clear invariants**: Each test verifies a specific optimization or behavior
- **Integration tests**: Exercise the full render pipeline together

---

## tests/test_event_handling.py

**Module Under Test**: `trellis.platforms.common.handler`, `trellis.platforms.common.serialization`, `trellis.html.events`, `trellis.core.rendering.session`
**Classification**: Mixed (Unit + Integration)
**Test Count**: 27
**Target Location**:
- `tests/py/unit/platforms/common/test_handler.py` (helper functions)
- `tests/py/integration/platforms/test_event_handling.py` (callback invocation)

### Dependencies
- Real: `RenderSession`, `render()`, `@component`, `Stateful`, event classes, handler helpers, serialization
- Mocked: None

### Fixtures Used
- None (uses local helper `get_callback_from_id`)

### Tests

#### `TestCallbackInvocation.test_callback_invoked_by_id`

| Field | Value |
|-------|-------|
| **Purpose** | Verify callback can be looked up by ID and invoked |
| **Invariants** | Callback ID from serialization maps to correct function |
| **Assertion Coverage** | Yes - invokes callback and checks side effect |

#### `TestCallbackInvocation.test_callback_with_args`

| Field | Value |
|-------|-------|
| **Purpose** | Verify callback can receive arguments from event |
| **Invariants** | Arguments passed to callback are preserved |
| **Assertion Coverage** | Yes - captures args and compares |

#### `TestCallbackInvocation.test_unknown_callback_returns_none`

| Field | Value |
|-------|-------|
| **Purpose** | Verify get_callback returns None for unknown IDs |
| **Invariants** | Missing callbacks don't throw, return None |
| **Assertion Coverage** | Yes - checks result is None |

#### `TestStateUpdateOnEvent.test_callback_updates_state`

| Field | Value |
|-------|-------|
| **Purpose** | Verify callback can modify Stateful and trigger re-render |
| **Invariants** | State change in callback marks components dirty; re-render shows new value |
| **Assertion Coverage** | Yes - checks serialized label text before/after |

#### `TestStateUpdateOnEvent.test_multiple_state_updates`

| Field | Value |
|-------|-------|
| **Purpose** | Verify multiple callbacks can update state sequentially |
| **Invariants** | Each callback invocation updates state independently |
| **Assertion Coverage** | Yes - increments twice, decrements once, checks final value |

#### `TestDisabledStateOnBoundary.test_button_disabled_at_min`

| Field | Value |
|-------|-------|
| **Purpose** | Verify decrement button disabled when at minimum value |
| **Invariants** | Disabled prop reflects boundary condition |
| **Assertion Coverage** | Yes - checks disabled is True at count=1 |

#### `TestDisabledStateOnBoundary.test_button_disabled_at_max`

| Field | Value |
|-------|-------|
| **Purpose** | Verify increment button disabled when at maximum value |
| **Invariants** | Disabled prop reflects boundary condition |
| **Assertion Coverage** | Yes - checks disabled is True at count=10 |

#### `TestDisabledStateOnBoundary.test_button_enabled_in_range`

| Field | Value |
|-------|-------|
| **Purpose** | Verify buttons enabled when value is within range |
| **Invariants** | Both buttons enabled when not at boundaries |
| **Assertion Coverage** | Yes - checks both disabled are False |

#### `TestDisabledStateOnBoundary.test_disabled_state_updates_on_boundary`

| Field | Value |
|-------|-------|
| **Purpose** | Verify button disabled state updates when hitting boundary |
| **Invariants** | Disabled prop updates reactively on state change |
| **Assertion Coverage** | Yes - button enabled at 2, disabled after decrement to 1 |

#### `TestArgsKwargsExtraction.test_empty_args`

| Field | Value |
|-------|-------|
| **Purpose** | Verify empty args returns empty lists |
| **Invariants** | Empty input produces empty args and empty kwargs |
| **Assertion Coverage** | Yes - checks both empty |

#### `TestArgsKwargsExtraction.test_positional_only`

| Field | Value |
|-------|-------|
| **Purpose** | Verify regular args pass through without modification |
| **Invariants** | Non-dict args preserved as-is |
| **Assertion Coverage** | Yes - checks args equal input |

#### `TestArgsKwargsExtraction.test_kwargs_marker_extracts_kwargs`

| Field | Value |
|-------|-------|
| **Purpose** | Verify dict with __kwargs__: True is unpacked as kwargs |
| **Invariants** | __kwargs__ marker triggers dict unpacking |
| **Assertion Coverage** | Yes - checks args and kwargs separately |

#### `TestArgsKwargsExtraction.test_kwargs_only`

| Field | Value |
|-------|-------|
| **Purpose** | Verify kwargs-only invocation works |
| **Invariants** | Can have just kwargs, no positional args |
| **Assertion Coverage** | Yes - args empty, kwargs populated |

#### `TestArgsKwargsExtraction.test_dict_without_marker_not_kwargs`

| Field | Value |
|-------|-------|
| **Purpose** | Verify regular dict without __kwargs__ is not treated as kwargs |
| **Invariants** | Missing marker means dict is a regular argument |
| **Assertion Coverage** | Yes - dict in args, kwargs empty |

#### `TestArgsKwargsExtraction.test_kwargs_marker_false_not_kwargs`

| Field | Value |
|-------|-------|
| **Purpose** | Verify dict with __kwargs__: False is not treated as kwargs |
| **Invariants** | Marker must be truthy to trigger unpacking |
| **Assertion Coverage** | Yes - dict in args with marker preserved |

#### `TestEventConversion.test_mouse_event_converted`

| Field | Value |
|-------|-------|
| **Purpose** | Verify mouse event dict becomes MouseEvent dataclass |
| **Invariants** | Dict with click/mouse fields → MouseEvent |
| **Assertion Coverage** | Yes - checks isinstance and all fields |

#### `TestEventConversion.test_keyboard_event_converted`

| Field | Value |
|-------|-------|
| **Purpose** | Verify keyboard event dict becomes KeyboardEvent dataclass |
| **Invariants** | Dict with key/keydown fields → KeyboardEvent |
| **Assertion Coverage** | Yes - checks isinstance and key fields |

#### `TestEventConversion.test_change_event_converted`

| Field | Value |
|-------|-------|
| **Purpose** | Verify change event dict becomes ChangeEvent dataclass |
| **Invariants** | Dict with change type → ChangeEvent |
| **Assertion Coverage** | Yes - checks isinstance and value/checked fields |

#### `TestEventConversion.test_unknown_event_type_fallback`

| Field | Value |
|-------|-------|
| **Purpose** | Verify unknown event type falls back to BaseEvent |
| **Invariants** | Unknown types don't crash, use base class |
| **Assertion Coverage** | Yes - checks isinstance BaseEvent |

#### `TestEventConversion.test_non_event_dict_unchanged`

| Field | Value |
|-------|-------|
| **Purpose** | Verify dict without 'type' passes through unchanged |
| **Invariants** | No type field means not an event, pass through |
| **Assertion Coverage** | Yes - result equals input |

#### `TestEventConversion.test_non_dict_unchanged`

| Field | Value |
|-------|-------|
| **Purpose** | Verify non-dict values pass through unchanged |
| **Invariants** | Only dicts are candidates for event conversion |
| **Assertion Coverage** | Yes - tests string, int, None, list |

#### `TestEventConversion.test_extra_fields_filtered`

| Field | Value |
|-------|-------|
| **Purpose** | Verify extra fields not in dataclass are filtered out |
| **Invariants** | Unknown fields don't cause errors |
| **Assertion Coverage** | Yes - creates MouseEvent despite extra fields |

#### `TestProcessCallbackArgs.test_event_conversion_and_kwargs`

| Field | Value |
|-------|-------|
| **Purpose** | Verify events are converted and kwargs extracted in one call |
| **Invariants** | _process_callback_args combines both transformations |
| **Assertion Coverage** | Yes - checks converted event and extracted kwargs |

#### `TestProcessCallbackArgs.test_multiple_events_converted`

| Field | Value |
|-------|-------|
| **Purpose** | Verify multiple event args are all converted |
| **Invariants** | Each event dict in args list gets converted |
| **Assertion Coverage** | Yes - checks both are correct types |

#### `TestProcessCallbackArgs.test_mixed_args`

| Field | Value |
|-------|-------|
| **Purpose** | Verify mix of events, regular args, and kwargs works |
| **Invariants** | All transformations apply to appropriate items |
| **Assertion Coverage** | Yes - checks each arg type preserved |

#### `TestAsyncCallbackDetection.test_sync_callback_detected`

| Field | Value |
|-------|-------|
| **Purpose** | Verify sync callbacks are correctly identified |
| **Invariants** | iscoroutinefunction returns False for sync |
| **Assertion Coverage** | Yes - uses inspect.iscoroutinefunction |

#### `TestAsyncCallbackDetection.test_async_callback_detected`

| Field | Value |
|-------|-------|
| **Purpose** | Verify async callbacks are correctly identified |
| **Invariants** | iscoroutinefunction returns True for async |
| **Assertion Coverage** | Yes - uses inspect.iscoroutinefunction |

#### `TestAsyncCallbackDetection.test_async_callback_with_args`

| Field | Value |
|-------|-------|
| **Purpose** | Verify async callback with args is correctly identified |
| **Invariants** | Signature doesn't affect coroutine detection |
| **Assertion Coverage** | Yes - async with typed args still detected |

#### `TestAsyncCallbackExecution.test_async_callback_invocation`

| Field | Value |
|-------|-------|
| **Purpose** | Verify async callback can be invoked and returns awaitable |
| **Invariants** | Callback from session is awaitable; asyncio.run executes it |
| **Assertion Coverage** | Yes - runs async callback and checks result |

#### `TestCallbackErrorHandling.test_sync_callback_exception_propagates`

| Field | Value |
|-------|-------|
| **Purpose** | Verify sync callback exceptions propagate normally |
| **Invariants** | Exceptions not swallowed by callback machinery |
| **Assertion Coverage** | Yes - pytest try/except checks exception |

#### `TestCallbackErrorHandling.test_multiple_callbacks_independent`

| Field | Value |
|-------|-------|
| **Purpose** | Verify multiple callbacks don't affect each other |
| **Invariants** | Each callback is independent; order preserved |
| **Assertion Coverage** | Yes - interleaved calls produce expected results |

### Quality Issues

- **Mixed classification**: Helper function tests (unit) mixed with callback+state tests (integration)
- **Should split**: Move TestArgsKwargsExtraction, TestEventConversion, TestProcessCallbackArgs to unit tests
- **Good coverage**: Tests sync/async, error handling, event types, arg extraction
- **Clear invariants**: Each test verifies specific behavior

---

## tests/test_fine_grained_classes.py

**Module Under Test**: `trellis.core.rendering.elements`, `trellis.core.rendering.element_state`, `trellis.core.rendering.dirty_tracker`, `trellis.core.rendering.frames`, `trellis.core.rendering.patches`, `trellis.core.rendering.lifecycle`, `trellis.core.rendering.active`, `trellis.core.rendering.session`
**Classification**: Unit
**Test Count**: 54
**Target Location**: Split by class into `tests/py/unit/core/rendering/`:
- `test_element_store.py`
- `test_element_state_store.py`
- `test_dirty_tracker.py`
- `test_frames.py`
- `test_patch_collector.py`
- `test_lifecycle_tracker.py`
- `test_active_render.py`
- `test_session.py`

### Dependencies
- Real: Direct class instantiation
- Mocked: None (uses local MockComponent and make_node helpers)

### Fixtures Used
- None (uses local helpers)

### Tests

#### `TestElementStore.test_store_and_get`

| Field | Value |
|-------|-------|
| **Purpose** | Verify store() saves node and get() retrieves it |
| **Invariants** | Stored nodes retrievable by ID |
| **Assertion Coverage** | Yes - stored node is same object |

#### `TestElementStore.test_get_nonexistent_returns_none`

| Field | Value |
|-------|-------|
| **Purpose** | Verify get() returns None for missing ID |
| **Invariants** | Missing IDs don't throw, return None |
| **Assertion Coverage** | Yes - result is None |

#### `TestElementStore.test_remove`

| Field | Value |
|-------|-------|
| **Purpose** | Verify remove() deletes node |
| **Invariants** | Removed nodes no longer retrievable |
| **Assertion Coverage** | Yes - get returns None after remove |

#### `TestElementStore.test_remove_nonexistent_no_error`

| Field | Value |
|-------|-------|
| **Purpose** | Verify remove() doesn't throw for missing ID |
| **Invariants** | Removing missing ID is no-op |
| **Assertion Coverage** | Yes - no exception |

#### `TestElementStore.test_contains`

| Field | Value |
|-------|-------|
| **Purpose** | Verify __contains__ works |
| **Invariants** | `in` operator checks presence |
| **Assertion Coverage** | Yes - stored ID in, missing ID not in |

#### `TestElementStore.test_len`

| Field | Value |
|-------|-------|
| **Purpose** | Verify __len__ returns count |
| **Invariants** | Length reflects stored node count |
| **Assertion Coverage** | Yes - checks 0, 1, 2 |

#### `TestElementStore.test_clear`

| Field | Value |
|-------|-------|
| **Purpose** | Verify clear() removes all nodes |
| **Invariants** | Clear empties store |
| **Assertion Coverage** | Yes - len is 0 after clear |

#### `TestElementStore.test_clone`

| Field | Value |
|-------|-------|
| **Purpose** | Verify clone() creates independent copy |
| **Invariants** | Cloned store shares nodes but not structure |
| **Assertion Coverage** | Yes - modifying original doesn't affect clone |

#### `TestElementStore.test_get_children`

| Field | Value |
|-------|-------|
| **Purpose** | Verify get_children returns child nodes |
| **Invariants** | Children retrieved by parent's child_ids |
| **Assertion Coverage** | Yes - returns both children in order |

#### `TestElementStore.test_get_children_missing_child`

| Field | Value |
|-------|-------|
| **Purpose** | Verify get_children skips missing children |
| **Invariants** | Missing children silently skipped |
| **Assertion Coverage** | Yes - only 1 child returned |

#### `TestElementStore.test_iter`

| Field | Value |
|-------|-------|
| **Purpose** | Verify __iter__ yields IDs |
| **Invariants** | Iteration produces stored IDs |
| **Assertion Coverage** | Yes - set comparison |

#### `TestElementStore.test_items`

| Field | Value |
|-------|-------|
| **Purpose** | Verify items() yields (id, node) pairs |
| **Invariants** | Dict-like items() method works |
| **Assertion Coverage** | Yes - dict from items has correct mappings |

#### `TestElementStateStore.test_get_nonexistent_returns_none`

| Field | Value |
|-------|-------|
| **Purpose** | Verify get() returns None for missing ID |
| **Invariants** | Missing states return None |
| **Assertion Coverage** | Yes - result is None |

#### `TestElementStateStore.test_set_and_get`

| Field | Value |
|-------|-------|
| **Purpose** | Verify set() stores and get() retrieves |
| **Invariants** | States storable and retrievable |
| **Assertion Coverage** | Yes - stored state is same object |

#### `TestElementStateStore.test_get_or_create_new`

| Field | Value |
|-------|-------|
| **Purpose** | Verify get_or_create creates new state if missing |
| **Invariants** | Missing state auto-created |
| **Assertion Coverage** | Yes - returns ElementState, stored |

#### `TestElementStateStore.test_get_or_create_existing`

| Field | Value |
|-------|-------|
| **Purpose** | Verify get_or_create returns existing state |
| **Invariants** | Existing state not replaced |
| **Assertion Coverage** | Yes - returns same object |

#### `TestElementStateStore.test_remove`

| Field | Value |
|-------|-------|
| **Purpose** | Verify remove() deletes state |
| **Invariants** | Removed states no longer retrievable |
| **Assertion Coverage** | Yes - get returns None after remove |

#### `TestElementStateStore.test_remove_nonexistent_no_error`

| Field | Value |
|-------|-------|
| **Purpose** | Verify remove() doesn't throw for missing ID |
| **Invariants** | Removing missing ID is no-op |
| **Assertion Coverage** | Yes - no exception |

#### `TestElementStateStore.test_contains`

| Field | Value |
|-------|-------|
| **Purpose** | Verify __contains__ works |
| **Invariants** | `in` operator checks presence |
| **Assertion Coverage** | Yes - stored ID in |

#### `TestElementStateStore.test_len`

| Field | Value |
|-------|-------|
| **Purpose** | Verify __len__ returns count |
| **Invariants** | Length reflects stored state count |
| **Assertion Coverage** | Yes - checks 0, 1 |

#### `TestElementStateStore.test_iter`

| Field | Value |
|-------|-------|
| **Purpose** | Verify __iter__ yields IDs |
| **Invariants** | Iteration produces stored IDs |
| **Assertion Coverage** | Yes - set comparison |

#### `TestDirtyTracker.test_mark_and_contains`

| Field | Value |
|-------|-------|
| **Purpose** | Verify mark() adds ID and __contains__ works |
| **Invariants** | Marked IDs are "in" tracker |
| **Assertion Coverage** | Yes - marked ID in, other not |

#### `TestDirtyTracker.test_clear`

| Field | Value |
|-------|-------|
| **Purpose** | Verify clear() removes specific ID |
| **Invariants** | Cleared ID no longer in tracker |
| **Assertion Coverage** | Yes - not in after clear |

#### `TestDirtyTracker.test_clear_nonexistent_no_error`

| Field | Value |
|-------|-------|
| **Purpose** | Verify clear() doesn't throw for missing ID |
| **Invariants** | Clearing missing ID is no-op |
| **Assertion Coverage** | Yes - no exception |

#### `TestDirtyTracker.test_discard`

| Field | Value |
|-------|-------|
| **Purpose** | Verify discard() removes ID |
| **Invariants** | Discard removes ID from set |
| **Assertion Coverage** | Yes - not in after discard |

#### `TestDirtyTracker.test_has_dirty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify has_dirty() checks for any dirty IDs |
| **Invariants** | Returns True iff any IDs marked |
| **Assertion Coverage** | Yes - checks empty, after mark, after clear |

#### `TestDirtyTracker.test_pop_all`

| Field | Value |
|-------|-------|
| **Purpose** | Verify pop_all() returns and clears all IDs |
| **Invariants** | Returns all marked IDs; clears tracker |
| **Assertion Coverage** | Yes - set comparison, then empty |

#### `TestDirtyTracker.test_len`

| Field | Value |
|-------|-------|
| **Purpose** | Verify __len__ returns count |
| **Invariants** | Length reflects unique marked IDs |
| **Assertion Coverage** | Yes - duplicate doesn't increase count |

#### `TestFrame.test_default_values`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Frame defaults |
| **Invariants** | child_ids=[], parent_id="", position=0 |
| **Assertion Coverage** | Yes - checks all defaults |

#### `TestFrame.test_with_parent_id`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Frame with parent_id |
| **Invariants** | parent_id stored correctly |
| **Assertion Coverage** | Yes - checks value |

#### `TestFrameStack.test_push_and_pop`

| Field | Value |
|-------|-------|
| **Purpose** | Verify push/pop basic behavior |
| **Invariants** | Push adds frame, pop returns child_ids and removes |
| **Assertion Coverage** | Yes - checks len after each op |

#### `TestFrameStack.test_current`

| Field | Value |
|-------|-------|
| **Purpose** | Verify current() returns active frame |
| **Invariants** | Returns None when empty, frame when pushed |
| **Assertion Coverage** | Yes - checks None, frame, None |

#### `TestFrameStack.test_add_child`

| Field | Value |
|-------|-------|
| **Purpose** | Verify add_child accumulates IDs |
| **Invariants** | child_ids collected in order |
| **Assertion Coverage** | Yes - pop returns both IDs in order |

#### `TestFrameStack.test_add_child_no_frame`

| Field | Value |
|-------|-------|
| **Purpose** | Verify add_child does nothing when no frame |
| **Invariants** | No error when no active frame |
| **Assertion Coverage** | Yes - no exception |

#### `TestFrameStack.test_has_active`

| Field | Value |
|-------|-------|
| **Purpose** | Verify has_active() checks for frame |
| **Invariants** | True iff stack non-empty |
| **Assertion Coverage** | Yes - checks before/during/after |

#### `TestFrameStack.test_nested_frames`

| Field | Value |
|-------|-------|
| **Purpose** | Verify nested push/pop works |
| **Invariants** | Inner frame's children separate from outer |
| **Assertion Coverage** | Yes - pop returns correct children at each level |

#### `TestFrameStack.test_next_child_id_positional`

| Field | Value |
|-------|-------|
| **Purpose** | Verify positional child ID generation |
| **Invariants** | IDs use position counter, include component id |
| **Assertion Coverage** | Yes - checks format of both IDs |

#### `TestFrameStack.test_next_child_id_keyed`

| Field | Value |
|-------|-------|
| **Purpose** | Verify keyed child ID generation |
| **Invariants** | Key embedded in ID with : prefix |
| **Assertion Coverage** | Yes - checks format |

#### `TestFrameStack.test_next_child_id_escapes_special_chars`

| Field | Value |
|-------|-------|
| **Purpose** | Verify special chars in keys are escaped |
| **Invariants** | :, /, @ are URL-encoded |
| **Assertion Coverage** | Yes - checks escaped format |

#### `TestFrameStack.test_next_child_id_no_frame_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify next_child_id raises when no frame |
| **Invariants** | RuntimeError with "no active frame" |
| **Assertion Coverage** | Yes - pytest.raises |

#### `TestFrameStack.test_root_id`

| Field | Value |
|-------|-------|
| **Purpose** | Verify root_id generation |
| **Invariants** | Root ID format is /@{component_id} |
| **Assertion Coverage** | Yes - checks format |

#### `TestPatchCollector.test_emit_and_get_all`

| Field | Value |
|-------|-------|
| **Purpose** | Verify emit() stores and get_all() retrieves patches |
| **Invariants** | Patches stored in order |
| **Assertion Coverage** | Yes - checks all 3 patches in order |

#### `TestPatchCollector.test_pop_all`

| Field | Value |
|-------|-------|
| **Purpose** | Verify pop_all() returns and clears |
| **Invariants** | Returns patches, empties collector |
| **Assertion Coverage** | Yes - returns 2, then len is 0 |

#### `TestPatchCollector.test_clear`

| Field | Value |
|-------|-------|
| **Purpose** | Verify clear() empties collector |
| **Invariants** | Clear removes all patches |
| **Assertion Coverage** | Yes - len is 0 |

#### `TestPatchCollector.test_len`

| Field | Value |
|-------|-------|
| **Purpose** | Verify __len__ returns count |
| **Invariants** | Length reflects patch count |
| **Assertion Coverage** | Yes - checks 0, 1 |

#### `TestPatchCollector.test_iter`

| Field | Value |
|-------|-------|
| **Purpose** | Verify __iter__ yields patches |
| **Invariants** | Iteration produces patches in order |
| **Assertion Coverage** | Yes - list equals expected |

#### `TestLifecycleTracker.test_track_mount`

| Field | Value |
|-------|-------|
| **Purpose** | Verify track_mount collects mount IDs |
| **Invariants** | Mounts collected in order |
| **Assertion Coverage** | Yes - pop_mounts returns both |

#### `TestLifecycleTracker.test_track_unmount`

| Field | Value |
|-------|-------|
| **Purpose** | Verify track_unmount collects unmount IDs |
| **Invariants** | Unmounts collected in order |
| **Assertion Coverage** | Yes - pop_unmounts returns both |

#### `TestLifecycleTracker.test_pop_mounts_clears`

| Field | Value |
|-------|-------|
| **Purpose** | Verify pop_mounts clears the list |
| **Invariants** | Pop clears; second pop is empty |
| **Assertion Coverage** | Yes - second call returns [] |

#### `TestLifecycleTracker.test_pop_unmounts_clears`

| Field | Value |
|-------|-------|
| **Purpose** | Verify pop_unmounts clears the list |
| **Invariants** | Pop clears; second pop is empty |
| **Assertion Coverage** | Yes - second call returns [] |

#### `TestLifecycleTracker.test_has_pending`

| Field | Value |
|-------|-------|
| **Purpose** | Verify has_pending checks for any events |
| **Invariants** | True if any mounts or unmounts pending |
| **Assertion Coverage** | Yes - checks empty, mount, pop, unmount |

#### `TestLifecycleTracker.test_clear`

| Field | Value |
|-------|-------|
| **Purpose** | Verify clear removes all pending |
| **Invariants** | Clear empties both lists |
| **Assertion Coverage** | Yes - has_pending False, both pops empty |

#### `TestActiveRender.test_default_values`

| Field | Value |
|-------|-------|
| **Purpose** | Verify ActiveRender default initialization |
| **Invariants** | All fields initialized with correct types/None |
| **Assertion Coverage** | Yes - checks all fields |

#### `TestActiveRender.test_current_node_id`

| Field | Value |
|-------|-------|
| **Purpose** | Verify current_node_id is settable |
| **Invariants** | Field is mutable |
| **Assertion Coverage** | Yes - set and read back |

#### `TestActiveRender.test_last_property_access`

| Field | Value |
|-------|-------|
| **Purpose** | Verify last_property_access stores tuple |
| **Invariants** | Can store (owner, name, value) tuple |
| **Assertion Coverage** | Yes - set and read back |

#### `TestActiveRender.test_frames_integration`

| Field | Value |
|-------|-------|
| **Purpose** | Verify frames work within ActiveRender |
| **Invariants** | Embedded FrameStack functions correctly |
| **Assertion Coverage** | Yes - push/add/pop works |

#### `TestActiveRender.test_patches_integration`

| Field | Value |
|-------|-------|
| **Purpose** | Verify patches work within ActiveRender |
| **Invariants** | Embedded PatchCollector functions correctly |
| **Assertion Coverage** | Yes - emit/len works |

#### `TestActiveRender.test_lifecycle_integration`

| Field | Value |
|-------|-------|
| **Purpose** | Verify lifecycle works within ActiveRender |
| **Invariants** | Embedded LifecycleTracker functions correctly |
| **Assertion Coverage** | Yes - track/pop works |

#### `TestRenderSession.test_creation`

| Field | Value |
|-------|-------|
| **Purpose** | Verify RenderSession initialization |
| **Invariants** | All stores created, root_node_id None, active None |
| **Assertion Coverage** | Yes - checks all fields |

#### `TestRenderSession.test_is_rendering`

| Field | Value |
|-------|-------|
| **Purpose** | Verify is_rendering() checks for active |
| **Invariants** | True iff active is not None |
| **Assertion Coverage** | Yes - False, True, False |

#### `TestRenderSession.test_is_executing`

| Field | Value |
|-------|-------|
| **Purpose** | Verify is_executing() checks for current_node_id |
| **Invariants** | True iff active and current_node_id set |
| **Assertion Coverage** | Yes - False, False (no node), True |

#### `TestRenderSession.test_current_node_id`

| Field | Value |
|-------|-------|
| **Purpose** | Verify current_node_id property |
| **Invariants** | Returns None or active's current_node_id |
| **Assertion Coverage** | Yes - None, then value |

#### `TestRenderSession.test_get_callback_from_node_props`

| Field | Value |
|-------|-------|
| **Purpose** | Verify get_callback looks up from node props |
| **Invariants** | Callback retrievable by node_id and prop_name |
| **Assertion Coverage** | Yes - found callback works, missing returns None |

#### `TestRenderSession.test_stores_integration`

| Field | Value |
|-------|-------|
| **Purpose** | Verify all stores work within RenderSession |
| **Invariants** | elements, states, dirty all functional |
| **Assertion Coverage** | Yes - basic ops on each |

#### `TestRenderSession.test_lock_is_reentrant`

| Field | Value |
|-------|-------|
| **Purpose** | Verify lock is RLock (reentrant) |
| **Invariants** | Nested `with session.lock` doesn't deadlock |
| **Assertion Coverage** | Yes - no exception |

### Quality Issues

- **Excellent unit test structure**: Each class tested in isolation
- **Good coverage**: All public methods tested
- **Should split**: File is large (700+ lines); split by class into separate files
- **Mock helper**: Uses local `make_node` helper - could move to conftest.py
- **Pure unit tests**: No integration dependencies, fast and deterministic

---

## tests/test_html.py

**Module Under Test**: `trellis.html.*`, `trellis.platforms.common.serialization`
**Classification**: Integration
**Test Count**: 28
**Target Location**: `tests/py/integration/html/test_html_elements.py`

### Dependencies
- Real: `RenderSession`, `render()`, `serialize_node()`, `@component`, HTML element decorators
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestHtmlElements.test_div_renders_as_container`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Div element can contain children via `with` block |
| **Invariants** | Container elements collect children; tree structure reflects parent-child relationships |
| **Assertion Coverage** | Yes - verifies Div has child Span with correct component name |

#### `TestHtmlElements.test_nested_divs`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Divs can be nested inside each other |
| **Invariants** | Nested containers produce correct multi-level tree structure |
| **Assertion Coverage** | Yes - verifies outer→inner→span hierarchy |

#### `TestHtmlElements.test_text_element_stores_text`

| Field | Value |
|-------|-------|
| **Purpose** | Verify text content is stored in `_text` prop for H1, P, Span |
| **Invariants** | Text elements store text content in `_text` property |
| **Assertion Coverage** | Yes - checks `_text` prop for three different elements |

#### `TestHtmlElements.test_element_with_style`

| Field | Value |
|-------|-------|
| **Purpose** | Verify elements accept style dict prop |
| **Invariants** | Style dict passed through as-is to properties |
| **Assertion Coverage** | Yes - verifies style dict equality |

#### `TestHtmlElements.test_element_with_class_name`

| Field | Value |
|-------|-------|
| **Purpose** | Verify elements accept className prop |
| **Invariants** | className prop passed through unchanged |
| **Assertion Coverage** | Yes - checks className property value |

#### `TestHtmlElements.test_text_renders_plain_text`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Text element renders plain text without wrapper |
| **Invariants** | Text element has component name "Text" and stores converted string in `_text` |
| **Assertion Coverage** | Yes - checks component name and _text value |

#### `TestHtmlElements.test_text_converts_values_to_string`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Text converts any value type to string |
| **Invariants** | int, float, bool, None all convert to string representations |
| **Assertion Coverage** | Yes - verifies 4 different types |

#### `TestHtmlSerialization.test_serialize_div_as_tag_name`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Div serializes with type='div' for native DOM rendering |
| **Invariants** | HTML elements serialize with lowercase tag name as type |
| **Assertion Coverage** | Yes - checks type="div" and name="Div" |

#### `TestHtmlSerialization.test_serialize_various_tags`

| Field | Value |
|-------|-------|
| **Purpose** | Verify different HTML elements serialize with correct tag names |
| **Invariants** | Each HTML element type maps to its lowercase tag name |
| **Assertion Coverage** | Yes - checks span, h1, p, a |

#### `TestHtmlSerialization.test_serialize_text_content`

| Field | Value |
|-------|-------|
| **Purpose** | Verify text content is serialized in _text prop |
| **Invariants** | Text content appears in serialized props as _text |
| **Assertion Coverage** | Yes - checks serialized props contain _text |

#### `TestHtmlSerialization.test_serialize_nested_structure`

| Field | Value |
|-------|-------|
| **Purpose** | Verify nested HTML elements serialize correctly |
| **Invariants** | Nested structure preserved in serialized children array |
| **Assertion Coverage** | Yes - verifies full nested tree structure |

#### `TestHtmlSerialization.test_serialize_onclick_as_callback`

| Field | Value |
|-------|-------|
| **Purpose** | Verify onClick handler serializes as callback reference |
| **Invariants** | Event handlers serialize with __callback__ format; callback is invocable |
| **Assertion Coverage** | Yes - verifies __callback__ format and invokes callback |

#### `TestHtmlSerialization.test_serialize_link_props`

| Field | Value |
|-------|-------|
| **Purpose** | Verify anchor element serializes with href and target |
| **Invariants** | Link-specific props (href, target) preserved in serialization |
| **Assertion Coverage** | Yes - checks all three props (_text, href, target) |

#### `TestHtmlSerialization.test_serialize_text_node`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Text element serializes with special __text__ type |
| **Invariants** | Text nodes have type="__text__" and kind="text" for client handling |
| **Assertion Coverage** | Yes - checks type, kind, name, and _text prop |

#### `TestHybridElements.test_td_with_text_auto_collects`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Td with text is auto-collected without with block |
| **Invariants** | Hybrid elements with text argument auto-collect as children |
| **Assertion Coverage** | Yes - verifies two Td children with correct _text |

#### `TestHybridElements.test_td_as_container`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Td without text can be used as container |
| **Invariants** | Hybrid elements without text act as containers |
| **Assertion Coverage** | Yes - checks children of Td |

#### `TestHybridElements.test_li_with_text_auto_collects`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Li with text is auto-collected |
| **Invariants** | Li elements with text auto-collect |
| **Assertion Coverage** | Yes - checks child count |

#### `TestHybridElements.test_li_as_container`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Li without text can be used as container |
| **Invariants** | Li elements without text act as containers |
| **Assertion Coverage** | Yes - checks child inside Li |

#### `TestHybridElements.test_a_with_text_auto_collects`

| Field | Value |
|-------|-------|
| **Purpose** | Verify A with text is auto-collected |
| **Invariants** | Anchor with text auto-collects with preserved props |
| **Assertion Coverage** | Yes - checks _text and href |

#### `TestHybridElements.test_a_as_container`

| Field | Value |
|-------|-------|
| **Purpose** | Verify A without text can be used as container |
| **Invariants** | Anchor without text acts as container |
| **Assertion Coverage** | Yes - checks child inside A |

#### `TestHybridElements.test_hybrid_no_double_collection`

| Field | Value |
|-------|-------|
| **Purpose** | Verify using with on text hybrid doesn't double-collect |
| **Invariants** | _auto_collected flag prevents duplicate collection |
| **Assertion Coverage** | Yes - verifies only one Td child exists |

#### `TestHtmlContainerBehavior.test_section_is_container`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Section element supports children via with block |
| **Invariants** | Section is a container element |
| **Assertion Coverage** | Yes - checks child count |

#### `TestHtmlContainerBehavior.test_article_is_container`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Article element supports children |
| **Invariants** | Article is a container element |
| **Assertion Coverage** | Yes - checks child count |

#### `TestHtmlContainerBehavior.test_ul_with_li_children`

| Field | Value |
|-------|-------|
| **Purpose** | Verify list elements work together |
| **Invariants** | Ul contains Li children with correct structure |
| **Assertion Coverage** | Yes - verifies count and each child's name and _text |

### Quality Issues

- **Integration tests**: All tests use RenderSession + render() + serialization together
- **Good coverage**: Tests rendering, serialization, hybrid behavior, container behavior
- **Clear structure**: Well-organized by behavior category
- **Could split**: Serialization tests could move to unit tests if mocking the render context

---

## tests/test_message_handler.py

**Module Under Test**: `trellis.platforms.common.handler`, `trellis.platforms.browser.handler`
**Classification**: Integration
**Test Count**: 21
**Target Location**: `tests/py/integration/platforms/test_message_handler.py`

### Dependencies
- Real: `MessageHandler`, `BrowserMessageHandler`, `RenderSession`, `render()`, widgets, message types
- Mocked: None (uses real rendering infrastructure)

### Fixtures Used
- None (uses local `get_initial_tree` helper)

### Tests

#### `TestMessageHandler.test_initial_render_returns_patch_message`

| Field | Value |
|-------|-------|
| **Purpose** | Verify initial_render() returns a PatchMessage with AddPatch |
| **Invariants** | First render produces PatchMessage containing full tree as AddPatch |
| **Assertion Coverage** | Yes - checks message type, patch count, patch type, tree structure |

#### `TestMessageHandler.test_handle_message_with_event`

| Field | Value |
|-------|-------|
| **Purpose** | Verify handle_message() invokes callback for EventMessage |
| **Invariants** | EventMessage triggers corresponding callback; returns None with batched rendering |
| **Assertion Coverage** | Yes - verifies callback invoked and response is None |

#### `TestMessageHandler.test_handle_message_with_unknown_callback`

| Field | Value |
|-------|-------|
| **Purpose** | Verify handle_message() returns ErrorMessage for unknown callback |
| **Invariants** | Missing callbacks produce ErrorMessage with context="callback" |
| **Assertion Coverage** | Yes - checks ErrorMessage type, context, error message |

#### `TestMessageHandler.test_handle_message_with_state_update`

| Field | Value |
|-------|-------|
| **Purpose** | Verify callback can modify Stateful and trigger re-render |
| **Invariants** | State change marks nodes dirty; subsequent render produces patches |
| **Assertion Coverage** | Yes - verifies dirty flag and update patches |

#### `TestMessageHandler.test_handle_message_with_event_args`

| Field | Value |
|-------|-------|
| **Purpose** | Verify handle_message() converts event args to dataclasses |
| **Invariants** | Dict with type field converted to appropriate event dataclass |
| **Assertion Coverage** | Yes - checks event fields (type, clientX, clientY) |

#### `TestMessageHandler.test_cleanup_clears_callbacks`

| Field | Value |
|-------|-------|
| **Purpose** | Verify cleanup() doesn't raise |
| **Invariants** | cleanup() is safe to call |
| **Assertion Coverage** | Partial - only verifies no exception |

#### `TestBrowserMessageHandler.test_message_to_dict_converts_patch_message`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _message_to_dict converts PatchMessage to dict |
| **Invariants** | Message serializes to dict with type field |
| **Assertion Coverage** | Yes - checks exact dict structure |

#### `TestBrowserMessageHandler.test_message_to_dict_converts_error_message`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _message_to_dict converts ErrorMessage to dict |
| **Invariants** | ErrorMessage preserves error and context fields |
| **Assertion Coverage** | Yes - checks exact dict structure |

#### `TestBrowserMessageHandler.test_dict_to_message_unknown_type_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _dict_to_message raises for unknown type |
| **Invariants** | Unknown message types raise ValueError |
| **Assertion Coverage** | Yes - pytest.raises with match |

#### `TestBrowserMessageHandler.test_dict_to_message_missing_callback_id_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _dict_to_message raises when event missing callback_id |
| **Invariants** | Event messages require callback_id |
| **Assertion Coverage** | Yes - pytest.raises with match |

#### `TestBrowserMessageHandler.test_dict_to_message_converts_hello`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _dict_to_message converts hello dict to HelloMessage |
| **Invariants** | Hello message deserialization preserves client_id |
| **Assertion Coverage** | Yes - checks isinstance and client_id |

#### `TestBrowserMessageHandler.test_dict_to_message_converts_event`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _dict_to_message converts event dict to EventMessage |
| **Invariants** | Event message deserialization preserves callback_id and args |
| **Assertion Coverage** | Yes - checks isinstance, callback_id, args |

#### `TestBrowserMessageHandler.test_post_event_adds_to_queue`

| Field | Value |
|-------|-------|
| **Purpose** | Verify post_event() adds EventMessage to inbox |
| **Invariants** | post_event creates EventMessage in queue |
| **Assertion Coverage** | Yes - verifies queue contents |

#### `TestBrowserMessageHandler.test_receive_message_gets_from_queue`

| Field | Value |
|-------|-------|
| **Purpose** | Verify receive_message() awaits message from inbox |
| **Invariants** | receive_message returns posted messages |
| **Assertion Coverage** | Yes - checks message callback_id |

#### `TestBrowserMessageHandler.test_send_message_calls_send_callback`

| Field | Value |
|-------|-------|
| **Purpose** | Verify send_message() calls registered send callback |
| **Invariants** | send_message invokes callback with serialized dict |
| **Assertion Coverage** | Yes - verifies callback called with correct dict |

#### `TestBrowserMessageHandler.test_send_message_without_callback_no_error`

| Field | Value |
|-------|-------|
| **Purpose** | Verify send_message() without callback doesn't raise |
| **Invariants** | Missing send callback is safely ignored |
| **Assertion Coverage** | Yes - no exception |

#### `TestBrowserMessageHandler.test_full_event_flow`

| Field | Value |
|-------|-------|
| **Purpose** | Verify full flow: post_event → receive → handle → callback |
| **Invariants** | End-to-end event processing works |
| **Assertion Coverage** | Yes - verifies callback invoked |

#### `TestAsyncCallbackHandling.test_async_callback_fires_and_forgets`

| Field | Value |
|-------|-------|
| **Purpose** | Verify async callbacks are scheduled without blocking |
| **Invariants** | Async callbacks run as background tasks |
| **Assertion Coverage** | Yes - verifies started before complete, then completed |

#### `TestAsyncCallbackHandling.test_background_tasks_tracked`

| Field | Value |
|-------|-------|
| **Purpose** | Verify background tasks are tracked to prevent GC |
| **Invariants** | Tasks in _background_tasks during execution, removed after |
| **Assertion Coverage** | Yes - checks task set size |

#### `TestRenderLoop.test_render_loop_sends_patches_when_dirty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify render loop sends PatchMessage when dirty nodes exist |
| **Invariants** | Dirty nodes trigger patch messages via render loop |
| **Assertion Coverage** | Yes - verifies PatchMessage sent after state change |

#### `TestRenderLoop.test_render_loop_sends_error_on_render_failure`

| Field | Value |
|-------|-------|
| **Purpose** | Verify render loop sends ErrorMessage on render exception |
| **Invariants** | Render errors produce ErrorMessage with context="render" |
| **Assertion Coverage** | Yes - checks ErrorMessage with correct context |

#### `TestRenderLoop.test_render_loop_cancels_cleanly`

| Field | Value |
|-------|-------|
| **Purpose** | Verify render loop cancels without error on disconnect |
| **Invariants** | Cancellation raises CancelledError; render task is cancelled |
| **Assertion Coverage** | Yes - verifies CancelledError and task.cancelled() |

#### `TestPatchComputation.test_compute_patches_deep_nesting`

| Field | Value |
|-------|-------|
| **Purpose** | Verify only changed nodes generate patches, not unchanged parents |
| **Invariants** | Patches are targeted to changed nodes only |
| **Assertion Coverage** | Yes - verifies update patch with new text value |

#### `TestPatchComputation.test_compute_patches_reordered_children`

| Field | Value |
|-------|-------|
| **Purpose** | Verify reordering children generates correct update patches |
| **Invariants** | Child reorder produces update patches |
| **Assertion Coverage** | Yes - verifies update patches exist |

#### `TestPatchComputation.test_unchanged_nodes_no_patches`

| Field | Value |
|-------|-------|
| **Purpose** | Verify unchanged nodes should not generate any patches |
| **Invariants** | Static content doesn't appear in patches |
| **Assertion Coverage** | Yes - verifies static label not in patches |

#### `TestPatchComputation.test_container_child_replacement_emits_add_remove_patches`

| Field | Value |
|-------|-------|
| **Purpose** | Verify replacing container children emits RemovePatch and AddPatch |
| **Invariants** | Tab switching produces remove for old content, add for new |
| **Assertion Coverage** | Yes - verifies both patch types and new content name |

### Quality Issues

- **Good end-to-end coverage**: Tests full message handling flow
- **Async testing**: Good coverage of async callbacks and render loop
- **Complex test setup**: TestRenderLoop tests create custom handler subclasses
- **Integration heavy**: Most tests require full rendering infrastructure
- **Could split**: BrowserMessageHandler tests could be separate file

---

## tests/test_messages.py

**Module Under Test**: `trellis.platforms.common.messages`
**Classification**: Unit
**Test Count**: 7
**Target Location**: `tests/py/unit/platforms/common/test_messages.py`

### Dependencies
- Real: msgspec (encoder/decoder)
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestEventMessage.test_event_message_creation`

| Field | Value |
|-------|-------|
| **Purpose** | Verify EventMessage can be created with callback_id and args |
| **Invariants** | EventMessage stores callback_id and args correctly |
| **Assertion Coverage** | Yes - checks both fields |

#### `TestEventMessage.test_event_message_default_args`

| Field | Value |
|-------|-------|
| **Purpose** | Verify EventMessage args defaults to empty list |
| **Invariants** | Omitting args produces empty list, not None |
| **Assertion Coverage** | Yes - checks default is [] |

#### `TestEventMessage.test_event_message_msgpack_roundtrip`

| Field | Value |
|-------|-------|
| **Purpose** | Verify EventMessage survives msgpack encode/decode |
| **Invariants** | Serialization preserves all fields |
| **Assertion Coverage** | Yes - checks type, callback_id, args after roundtrip |

#### `TestEventMessage.test_event_message_has_type_tag`

| Field | Value |
|-------|-------|
| **Purpose** | Verify EventMessage includes type tag for dispatch |
| **Invariants** | Serialized message has type="event" for discrimination |
| **Assertion Coverage** | Yes - decodes as raw dict and checks type field |

#### `TestMessageUnion.test_decode_hello_message`

| Field | Value |
|-------|-------|
| **Purpose** | Verify HelloMessage decodes correctly from union |
| **Invariants** | Union decoder correctly identifies HelloMessage |
| **Assertion Coverage** | Yes - isinstance check and client_id |

#### `TestMessageUnion.test_decode_hello_response_message`

| Field | Value |
|-------|-------|
| **Purpose** | Verify HelloResponseMessage decodes correctly from union |
| **Invariants** | Union decoder correctly identifies HelloResponseMessage |
| **Assertion Coverage** | Yes - isinstance and both fields |

#### `TestMessageUnion.test_decode_patch_message`

| Field | Value |
|-------|-------|
| **Purpose** | Verify PatchMessage decodes correctly from union |
| **Invariants** | Union decoder correctly identifies PatchMessage |
| **Assertion Coverage** | Yes - isinstance and patches field |

#### `TestMessageUnion.test_decode_event_message`

| Field | Value |
|-------|-------|
| **Purpose** | Verify EventMessage decodes correctly from union |
| **Invariants** | Union decoder correctly identifies EventMessage |
| **Assertion Coverage** | Yes - isinstance, callback_id, args |

#### `TestMessageUnion.test_all_message_types_distinguishable`

| Field | Value |
|-------|-------|
| **Purpose** | Verify all message types can be distinguished after decoding |
| **Invariants** | Each message type has unique tag; roundtrip preserves type |
| **Assertion Coverage** | Yes - checks type identity for all 4 message types |

### Quality Issues

- **Excellent unit tests**: Tests message types in isolation with msgspec
- **Wire format testing**: Verifies serialization format for protocol compatibility
- **Good invariant coverage**: Tests both creation and serialization
- **Pure unit tests**: No integration dependencies

---

## tests/test_mutable.py

**Module Under Test**: `trellis.core.state.mutable`
**Classification**: Mixed (Unit + Integration)
**Test Count**: 33
**Target Location**: Split into:
- `tests/py/unit/core/state/test_mutable.py` (Mutable class, mutable/callback functions)
- `tests/py/integration/core/state/test_mutable_serialization.py` (serialization, widgets, re-render)

### Dependencies
- Real: `Mutable`, `mutable()`, `callback()`, `RenderSession`, `render()`, widgets, serialization
- Mocked: None

### Fixtures Used
- `helpers.render_to_tree` (local helper)
- `get_callback_from_id` (local helper)

### Tests

#### `TestMutableClass.test_value_getter`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Mutable.value returns the current property value |
| **Invariants** | value property reads from underlying Stateful |
| **Assertion Coverage** | Yes - direct equality check |

#### `TestMutableClass.test_value_setter`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Mutable.value setter updates the property |
| **Invariants** | Setting value updates both Mutable read and Stateful |
| **Assertion Coverage** | Yes - checks both state and mutable.value |

#### `TestMutableClass.test_equality_same_reference`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Mutables with same owner and attr are equal |
| **Invariants** | Same binding → equal Mutables |
| **Assertion Coverage** | Yes - equality check |

#### `TestMutableClass.test_equality_different_attr`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Mutables with different attrs are not equal |
| **Invariants** | Different attr → unequal Mutables |
| **Assertion Coverage** | Yes - inequality check |

#### `TestMutableClass.test_equality_different_owner`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Mutables with different owners are not equal |
| **Invariants** | Different owner → unequal Mutables |
| **Assertion Coverage** | Yes - inequality check |

#### `TestMutableClass.test_equality_with_non_mutable`

| Field | Value |
|-------|-------|
| **Purpose** | Verify comparing Mutable to non-Mutable returns NotImplemented |
| **Invariants** | Type mismatch handled gracefully |
| **Assertion Coverage** | Yes - checks != with int and str |

#### `TestMutableClass.test_repr`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Mutable has useful repr |
| **Invariants** | repr shows attr name and value |
| **Assertion Coverage** | Yes - exact string match |

#### `TestMutableClass.test_mutable_is_not_hashable`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Mutable cannot be hashed |
| **Invariants** | Mutable is unhashable due to snapshot-based equality |
| **Assertion Coverage** | Yes - pytest.raises TypeError |

#### `TestMutableSnapshot.test_snapshot_captured_at_creation`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Mutable captures value snapshot at creation time |
| **Invariants** | snapshot property equals value at creation |
| **Assertion Coverage** | Yes - checks snapshot value |

#### `TestMutableSnapshot.test_snapshot_unchanged_after_state_modification`

| Field | Value |
|-------|-------|
| **Purpose** | Verify snapshot doesn't change when state is modified directly |
| **Invariants** | Snapshot is immutable; value is live |
| **Assertion Coverage** | Yes - checks snapshot vs live value after change |

#### `TestMutableSnapshot.test_snapshot_unchanged_after_mutable_set`

| Field | Value |
|-------|-------|
| **Purpose** | Verify snapshot doesn't change when value is set via Mutable |
| **Invariants** | Setting via Mutable doesn't update snapshot |
| **Assertion Coverage** | Yes - checks snapshot unchanged after m.value = |

#### `TestMutableSnapshot.test_equality_compares_snapshots`

| Field | Value |
|-------|-------|
| **Purpose** | Verify two Mutables are equal only if their snapshots match |
| **Invariants** | Same binding but different snapshot → not equal |
| **Assertion Coverage** | Yes - creates mutables at different times, checks inequality |

#### `TestMutableSnapshot.test_equality_same_snapshot_same_binding`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Mutables with same binding and same snapshot are equal |
| **Invariants** | Same binding + same snapshot → equal |
| **Assertion Coverage** | Yes - creates two at same time, checks equality |

#### `TestMutableSnapshot.test_value_read_is_live_not_snapshot`

| Field | Value |
|-------|-------|
| **Purpose** | Verify reading value returns live state, not snapshot |
| **Invariants** | value property always returns current state |
| **Assertion Coverage** | Yes - modifies state, checks value vs snapshot |

#### `TestMutableFunction.test_mutable_captures_property_access`

| Field | Value |
|-------|-------|
| **Purpose** | Verify mutable() captures the reference from a Stateful property access |
| **Invariants** | mutable() creates Mutable from last property access |
| **Assertion Coverage** | Yes - checks captured value |

#### `TestMutableFunction.test_mutable_outside_render_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify mutable() raises TypeError outside render context |
| **Invariants** | mutable() requires active render session |
| **Assertion Coverage** | Yes - pytest.raises with match |

#### `TestMutableFunction.test_mutable_with_non_property_value_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify mutable() raises TypeError if value doesn't match last access |
| **Invariants** | Value must be identity-equal to last accessed value |
| **Assertion Coverage** | Yes - pytest.raises with match |

#### `TestMutableFunction.test_mutable_with_plain_variable_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify mutable() raises TypeError with plain variable |
| **Invariants** | Must follow a Stateful property access |
| **Assertion Coverage** | Yes - pytest.raises with match |

#### `TestMutableFunction.test_mutable_clears_after_capture`

| Field | Value |
|-------|-------|
| **Purpose** | Verify mutable() clears the recorded access so it can't be reused |
| **Invariants** | Each property access can only be captured once |
| **Assertion Coverage** | Yes - second mutable() call raises |

#### `TestMutableFunction.test_mutable_works_with_new_access`

| Field | Value |
|-------|-------|
| **Purpose** | Verify mutable() works if you access the property again |
| **Invariants** | New access creates new capturable reference |
| **Assertion Coverage** | Yes - two sequential mutable() calls work |

#### `TestMutableSerialization.test_mutable_serializes_with_callback`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Mutable props serialize to __mutable__ format with callback |
| **Invariants** | Mutable serializes to {__mutable__: cb_id, value: current_value} |
| **Assertion Coverage** | Yes - checks __mutable__ and value keys |

#### `TestMutableSerialization.test_mutable_callback_updates_state`

| Field | Value |
|-------|-------|
| **Purpose** | Verify the mutable callback updates the underlying state |
| **Invariants** | Invoking callback changes Stateful property |
| **Assertion Coverage** | Yes - invokes callback, checks state changed |

#### `TestMutableWidgets.test_number_input_with_mutable`

| Field | Value |
|-------|-------|
| **Purpose** | Verify NumberInput accepts mutable value and updates state |
| **Invariants** | NumberInput works with Mutable binding |
| **Assertion Coverage** | Yes - checks serialization and callback update |

#### `TestMutableWidgets.test_checkbox_with_mutable`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Checkbox accepts mutable checked and updates state |
| **Invariants** | Checkbox works with Mutable binding |
| **Assertion Coverage** | Yes - checks serialization and callback update |

#### `TestMutableWidgets.test_select_with_mutable`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Select accepts mutable value and updates state |
| **Invariants** | Select works with Mutable binding |
| **Assertion Coverage** | Yes - checks serialization and callback update |

#### `TestMutableWidgets.test_slider_with_mutable`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Slider accepts mutable value and updates state |
| **Invariants** | Slider works with Mutable binding |
| **Assertion Coverage** | Yes - checks serialization and callback update |

#### `TestMutableWidgets.test_tabs_with_mutable`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Tabs accepts mutable selected and updates state |
| **Invariants** | Tabs works with Mutable binding |
| **Assertion Coverage** | Yes - checks serialization and callback update |

#### `TestMutableWidgets.test_collapsible_with_mutable`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Collapsible accepts mutable expanded and updates state |
| **Invariants** | Collapsible works with Mutable binding |
| **Assertion Coverage** | Yes - checks serialization and callback update |

#### `TestCallbackFunction.test_callback_captures_property_access`

| Field | Value |
|-------|-------|
| **Purpose** | Verify callback() captures the reference and stores on_change |
| **Invariants** | callback() creates Mutable with custom on_change handler |
| **Assertion Coverage** | Yes - checks value and on_change property |

#### `TestCallbackFunction.test_callback_outside_render_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify callback() raises TypeError outside render context |
| **Invariants** | callback() requires active render session |
| **Assertion Coverage** | Yes - pytest.raises with match |

#### `TestCallbackFunction.test_callback_with_non_property_value_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify callback() raises TypeError if value doesn't match last access |
| **Invariants** | Value must be identity-equal to last accessed value |
| **Assertion Coverage** | Yes - pytest.raises with match |

#### `TestCallbackFunction.test_callback_serializes_with_custom_handler`

| Field | Value |
|-------|-------|
| **Purpose** | Verify callback() serializes to __mutable__ format with custom handler |
| **Invariants** | Custom handler is invoked instead of auto-generated setter |
| **Assertion Coverage** | Yes - invokes callback, checks custom handler called |

#### `TestCallbackFunction.test_callback_with_state_method`

| Field | Value |
|-------|-------|
| **Purpose** | Verify callback() works with state methods for custom processing |
| **Invariants** | State methods can do custom transformation |
| **Assertion Coverage** | Yes - verifies custom processing applied |

#### `TestMutableRerender.test_checkbox_rerender_sends_updated_value`

| Field | Value |
|-------|-------|
| **Purpose** | After mutable callback changes state, re-render should send update patch |
| **Invariants** | Mutable value changes produce update patches |
| **Assertion Coverage** | Yes - verifies RenderUpdatePatch with new value |

#### `TestMutableRerender.test_text_input_rerender_sends_updated_value`

| Field | Value |
|-------|-------|
| **Purpose** | After mutable callback changes state, TextInput re-render should send update |
| **Invariants** | TextInput mutable changes produce update patches |
| **Assertion Coverage** | Yes - verifies RenderUpdatePatch with new value |

#### `TestMutableRerender.test_slider_rerender_sends_updated_value`

| Field | Value |
|-------|-------|
| **Purpose** | After mutable callback changes state, Slider re-render should send update |
| **Invariants** | Slider mutable changes produce update patches |
| **Assertion Coverage** | Yes - verifies RenderUpdatePatch with new value |

### Quality Issues

- **Mixed unit/integration**: Mutable class tests are unit; serialization/widget tests are integration
- **Should split**: Unit tests (TestMutableClass, TestMutableSnapshot, TestMutableFunction, TestCallbackFunction) vs Integration tests (TestMutableSerialization, TestMutableWidgets, TestMutableRerender)
- **Good regression tests**: TestMutableRerender explicitly tests bug fix scenario
- **Clear documentation**: Each test class has clear docstrings explaining purpose
- **Critical feature**: These tests verify the core two-way data binding mechanism

---

## tests/test_ports.py

**Module Under Test**: `trellis.platforms.common.ports`
**Classification**: Unit
**Test Count**: 5
**Target Location**: `tests/py/unit/platforms/common/test_ports.py`

### Dependencies
- Real: `socket` (standard library)
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestFindAvailablePort.test_returns_port_in_range`

| Field | Value |
|-------|-------|
| **Purpose** | Verify find_available_port returns a port within the specified range |
| **Invariants** | Returned port is >= start and < end |
| **Assertion Coverage** | Yes - asserts port is in range [9000, 9010) |

#### `TestFindAvailablePort.test_returns_first_available`

| Field | Value |
|-------|-------|
| **Purpose** | Verify when first port is busy, the next available port is returned |
| **Invariants** | Function skips bound ports and returns next free one |
| **Assertion Coverage** | Yes - binds 9100, verifies 9101 returned |

#### `TestFindAvailablePort.test_raises_when_all_ports_busy`

| Field | Value |
|-------|-------|
| **Purpose** | Verify RuntimeError is raised when all ports in range are busy |
| **Invariants** | When no port available, raises RuntimeError with descriptive message |
| **Assertion Coverage** | Yes - pytest.raises with match on error message |

#### `TestFindAvailablePort.test_respects_host_parameter`

| Field | Value |
|-------|-------|
| **Purpose** | Verify the host parameter is used when checking port availability |
| **Invariants** | Port availability is checked against specified host |
| **Assertion Coverage** | Yes - explicit host parameter used, port in range |

#### `TestFindAvailablePort.test_uses_default_range`

| Field | Value |
|-------|-------|
| **Purpose** | Verify default port range is used when not specified |
| **Invariants** | Defaults to DEFAULT_PORT_START to DEFAULT_PORT_END |
| **Assertion Coverage** | Yes - verifies port is in default range |

### Quality Issues

- **Excellent unit tests**: Tests single function in isolation
- **Good edge case coverage**: Tests happy path, busy ports, all busy, and defaults
- **Clean test isolation**: Each test manages its own sockets and cleans up in finally blocks
- **Port range safety**: Uses distinct port ranges to avoid test interference

---

## tests/test_react_component.py

**Module Under Test**: `trellis.core.components.react`, `trellis.core.components.composition`, `trellis.platforms.common.serialization`
**Classification**: Mixed (Unit + Integration)
**Test Count**: 17
**Target Location**: Split into:
- `tests/py/unit/core/components/test_react_component.py` (TestElementNameProperty, TestReactComponentBaseSubclass, TestReactComponentBaseDecorator)
- `tests/py/integration/platforms/test_react_component_serialization.py` (TestReactComponentBaseSerialization)

### Dependencies
- Real: `RenderSession`, `render()`, `serialize_node()`, `@component`, `@react_component_base`, widgets
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestElementNameProperty.test_react_component_subclass_returns_specific_type`

| Field | Value |
|-------|-------|
| **Purpose** | Verify ReactComponentBase subclasses return their _element_name |
| **Invariants** | element_name property returns the class's _element_name attribute |
| **Assertion Coverage** | Yes - creates subclass with _element_name, verifies property |

#### `TestElementNameProperty.test_composition_component_returns_composition_component`

| Field | Value |
|-------|-------|
| **Purpose** | Verify CompositionComponents return "CompositionComponent" as element_name |
| **Invariants** | All @component functions have same generic element_name |
| **Assertion Coverage** | Yes - checks element_name equals "CompositionComponent" |

#### `TestElementNameProperty.test_different_composition_components_same_element_name`

| Field | Value |
|-------|-------|
| **Purpose** | Verify all CompositionComponents share the same element_name |
| **Invariants** | CompositionComponent is a generic wrapper; identity is in Python name |
| **Assertion Coverage** | Yes - creates two @components, verifies both have same element_name |

#### `TestElementNameProperty.test_widget_element_names`

| Field | Value |
|-------|-------|
| **Purpose** | Verify built-in widgets have correct element_name values |
| **Invariants** | Label="Label", Button="Button", Column="Column", Row="Row" |
| **Assertion Coverage** | Yes - renders app with widgets, checks each element_name |

#### `TestElementNameProperty.test_react_component_without_element_name_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify ReactComponentBase without _element_name raises NotImplementedError |
| **Invariants** | Missing _element_name is a programming error that should fail fast |
| **Assertion Coverage** | Yes - pytest.raises with match |

#### `TestReactComponentBaseSubclass.test_subclass_sets_element_name`

| Field | Value |
|-------|-------|
| **Purpose** | Verify subclass _element_name is accessible via class and instance |
| **Invariants** | _element_name is class-level attribute accessible from instances |
| **Assertion Coverage** | Yes - checks both class and instance access |

#### `TestReactComponentBaseSubclass.test_subclass_has_children_false_by_default`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _has_children defaults to False |
| **Invariants** | Components are leaves by default, containers must explicitly set _has_children |
| **Assertion Coverage** | Yes - verifies default is False |

#### `TestReactComponentBaseSubclass.test_subclass_has_children_true`

| Field | Value |
|-------|-------|
| **Purpose** | Verify subclasses can set _has_children True for containers |
| **Invariants** | Container components set _has_children = True |
| **Assertion Coverage** | Yes - creates container class, verifies True |

#### `TestReactComponentBaseSubclass.test_has_children_param_property`

| Field | Value |
|-------|-------|
| **Purpose** | Verify _has_children_param property reads from class variable |
| **Invariants** | Instance property mirrors class variable |
| **Assertion Coverage** | Yes - checks both True and False cases |

#### `TestReactComponentBaseDecorator.test_decorator_creates_callable`

| Field | Value |
|-------|-------|
| **Purpose** | Verify @react_component_base creates callable returning Element |
| **Invariants** | Decorated function is callable, produces Element nodes |
| **Assertion Coverage** | Yes - calls decorated function, checks element_name and props |

#### `TestReactComponentBaseDecorator.test_decorator_preserves_function_metadata`

| Field | Value |
|-------|-------|
| **Purpose** | Verify decorator preserves __name__ and __doc__ |
| **Invariants** | Function identity preserved for introspection |
| **Assertion Coverage** | Yes - checks both __name__ and __doc__ |

#### `TestReactComponentBaseDecorator.test_decorator_has_children_false_by_default`

| Field | Value |
|-------|-------|
| **Purpose** | Verify decorator creates leaf components by default |
| **Invariants** | has_children defaults to False |
| **Assertion Coverage** | Yes - accesses _component._has_children_param |

#### `TestReactComponentBaseDecorator.test_decorator_has_children_true`

| Field | Value |
|-------|-------|
| **Purpose** | Verify decorator can create container components |
| **Invariants** | has_children=True parameter creates container |
| **Assertion Coverage** | Yes - verifies _has_children_param is True |

#### `TestReactComponentBaseDecorator.test_decorator_exposes_component`

| Field | Value |
|-------|-------|
| **Purpose** | Verify decorated function exposes _component for introspection |
| **Invariants** | _component attribute provides access to underlying ReactComponentBase |
| **Assertion Coverage** | Yes - checks hasattr, isinstance, and element_name |

#### `TestReactComponentBaseSerialization.test_react_component_type_equals_name`

| Field | Value |
|-------|-------|
| **Purpose** | Verify ReactComponents serialize with type=name (the React component name) |
| **Invariants** | For React components, type and name both equal the component name |
| **Assertion Coverage** | Yes - serializes Label, checks type="Label", name="Label" |

#### `TestReactComponentBaseSerialization.test_composition_component_type_differs_from_name`

| Field | Value |
|-------|-------|
| **Purpose** | Verify CompositionComponents serialize with generic type but specific name |
| **Invariants** | type="CompositionComponent", name=Python function name |
| **Assertion Coverage** | Yes - checks type vs name are different |

#### `TestReactComponentBaseSerialization.test_mixed_tree_serialization`

| Field | Value |
|-------|-------|
| **Purpose** | Verify tree with both component types serializes correctly |
| **Invariants** | Mixed tree preserves correct type/name for each node type |
| **Assertion Coverage** | Yes - checks full nested tree with both types |

### Quality Issues

- **Mixed classification**: Element name tests could be pure unit tests; serialization tests are integration
- **Should split**: Decorator and subclass tests don't need render context (could mock)
- **Good coverage**: Tests both class-based and decorator-based patterns
- **Clear invariants**: Distinction between type and name is well-documented

---

## tests/test_reconciler.py

**Module Under Test**: `trellis.core.rendering.reconcile`
**Classification**: Unit
**Test Count**: 27
**Target Location**: `tests/py/unit/core/rendering/test_reconcile.py`

### Dependencies
- Real: None (pure function testing)
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestReconcileChildrenBasic.test_empty_to_empty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify reconciling two empty lists produces empty result |
| **Invariants** | Empty inputs → empty added/removed/matched, empty child_order |
| **Assertion Coverage** | Yes - checks all fields of ReconcileResult |

#### `TestReconcileChildrenBasic.test_empty_to_many`

| Field | Value |
|-------|-------|
| **Purpose** | Verify all new IDs are marked as added |
| **Invariants** | New list with no old → all added, none removed/matched |
| **Assertion Coverage** | Yes - checks added list equals new, others empty |

#### `TestReconcileChildrenBasic.test_many_to_empty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify all old IDs are marked as removed |
| **Invariants** | Old list cleared → all removed, none added/matched |
| **Assertion Coverage** | Yes - checks removed list equals old, others empty |

#### `TestReconcileChildrenBasic.test_all_match`

| Field | Value |
|-------|-------|
| **Purpose** | Verify identical lists produce all matched |
| **Invariants** | Same IDs in same order → all matched, none added/removed |
| **Assertion Coverage** | Yes - checks matched equals input, others empty |

#### `TestReconcileChildrenBasic.test_partial_overlap`

| Field | Value |
|-------|-------|
| **Purpose** | Verify partial overlap produces correct add/remove/match sets |
| **Invariants** | Old {a,b,c} → new {b,c,d}: removed={a}, added={d}, matched={b,c} |
| **Assertion Coverage** | Yes - checks all three sets |

#### `TestReconcileChildrenHeadTail.test_head_match_append`

| Field | Value |
|-------|-------|
| **Purpose** | Verify head matching optimization with append at end |
| **Invariants** | Appending to end: head scan matches all old, rest added |
| **Assertion Coverage** | Yes - checks added={c,d}, matched={a,b} |

#### `TestReconcileChildrenHeadTail.test_tail_match_prepend`

| Field | Value |
|-------|-------|
| **Purpose** | Verify tail matching optimization with prepend at start |
| **Invariants** | Prepending at start: tail scan matches old, rest added |
| **Assertion Coverage** | Yes - checks added={a,b}, matched={c,d} |

#### `TestReconcileChildrenHeadTail.test_middle_removal`

| Field | Value |
|-------|-------|
| **Purpose** | Verify removal from middle (exercises head + tail scan) |
| **Invariants** | Removing from middle: head/tail match, middle removed |
| **Assertion Coverage** | Yes - checks removed={c}, matched={a,b,d,e} |

#### `TestReconcileChildrenHeadTail.test_middle_insertion`

| Field | Value |
|-------|-------|
| **Purpose** | Verify insertion in middle |
| **Invariants** | Inserting in middle: head/tail match, middle added |
| **Assertion Coverage** | Yes - checks added={b,c}, matched={a,d} |

#### `TestReconcileChildrenHeadTail.test_head_tail_no_middle`

| Field | Value |
|-------|-------|
| **Purpose** | Verify head and tail match with nothing in middle |
| **Invariants** | Head/tail scan consumes all; middle section empty |
| **Assertion Coverage** | Yes - removed={b}, matched={a,c} |

#### `TestReconcileChildrenEdgeCases.test_reverse_list`

| Field | Value |
|-------|-------|
| **Purpose** | Verify reversing a list matches all, just reordered |
| **Invariants** | Same set of IDs reversed → all matched, none added/removed |
| **Assertion Coverage** | Yes - checks sets match, child_order is reversed |

#### `TestReconcileChildrenEdgeCases.test_shuffle_list`

| Field | Value |
|-------|-------|
| **Purpose** | Verify shuffling a list matches all, just reordered |
| **Invariants** | Same set of IDs shuffled → all matched, none added/removed |
| **Assertion Coverage** | Yes - uses seeded random, checks sets match |

#### `TestReconcileChildrenEdgeCases.test_remove_from_start`

| Field | Value |
|-------|-------|
| **Purpose** | Verify removing items from start |
| **Invariants** | First half removed → removed set, rest matched |
| **Assertion Coverage** | Yes - checks set sizes and contents |

#### `TestReconcileChildrenEdgeCases.test_remove_from_middle`

| Field | Value |
|-------|-------|
| **Purpose** | Verify removing items from middle |
| **Invariants** | Middle section removed → removed set, ends matched |
| **Assertion Coverage** | Yes - 30 items removed from 50 |

#### `TestReconcileChildrenEdgeCases.test_remove_from_end`

| Field | Value |
|-------|-------|
| **Purpose** | Verify removing items from end |
| **Invariants** | Last half removed → removed set, first half matched |
| **Assertion Coverage** | Yes - checks set sizes and contents |

#### `TestReconcileChildrenEdgeCases.test_insert_at_start`

| Field | Value |
|-------|-------|
| **Purpose** | Verify inserting items at start |
| **Invariants** | Items prepended → added set, original matched |
| **Assertion Coverage** | Yes - 25 items added at start |

#### `TestReconcileChildrenEdgeCases.test_insert_at_end`

| Field | Value |
|-------|-------|
| **Purpose** | Verify inserting items at end |
| **Invariants** | Items appended → added set, original matched |
| **Assertion Coverage** | Yes - 25 items added at end |

#### `TestReconcileChildrenEdgeCases.test_complete_replacement`

| Field | Value |
|-------|-------|
| **Purpose** | Verify all old removed, all new added when no overlap |
| **Invariants** | Disjoint sets → all removed, all added, none matched |
| **Assertion Coverage** | Yes - {a,b,c} → {x,y,z} |

#### `TestReconcileChildrenEdgeCases.test_single_item_added`

| Field | Value |
|-------|-------|
| **Purpose** | Verify adding single item from empty |
| **Invariants** | Single add works correctly |
| **Assertion Coverage** | Yes - added=["a"] |

#### `TestReconcileChildrenEdgeCases.test_single_item_removed`

| Field | Value |
|-------|-------|
| **Purpose** | Verify removing single item to empty |
| **Invariants** | Single remove works correctly |
| **Assertion Coverage** | Yes - removed=["a"] |

#### `TestReconcileChildrenEdgeCases.test_single_item_unchanged`

| Field | Value |
|-------|-------|
| **Purpose** | Verify single item unchanged |
| **Invariants** | Single match works correctly |
| **Assertion Coverage** | Yes - matched=["a"] |

#### `TestReconcileChildrenLargeScale.test_large_list_append`

| Field | Value |
|-------|-------|
| **Purpose** | Verify append to large list (head scan optimization) |
| **Invariants** | 100 items appended to 1000, should be O(n) via head scan |
| **Assertion Coverage** | Yes - checks counts |

#### `TestReconcileChildrenLargeScale.test_large_list_prepend`

| Field | Value |
|-------|-------|
| **Purpose** | Verify prepend to large list (tail scan optimization) |
| **Invariants** | 100 items prepended to 1000, should be O(n) via tail scan |
| **Assertion Coverage** | Yes - checks counts |

#### `TestReconcileChildrenLargeScale.test_large_list_reverse`

| Field | Value |
|-------|-------|
| **Purpose** | Verify reversing large list |
| **Invariants** | 500 items reversed → all matched, none added/removed |
| **Assertion Coverage** | Yes - checks counts |

#### `TestReconcileChildrenLargeScale.test_large_list_shuffle`

| Field | Value |
|-------|-------|
| **Purpose** | Verify shuffling large list |
| **Invariants** | 500 items shuffled → all matched, none added/removed |
| **Assertion Coverage** | Yes - uses seeded random |

#### `TestReconcileChildrenDuplicates.test_duplicate_ids_in_new`

| Field | Value |
|-------|-------|
| **Purpose** | Verify behavior with duplicate IDs in new list (edge case) |
| **Invariants** | First match wins; duplicates handled gracefully |
| **Assertion Coverage** | Yes - "a" is matched, not added twice |

#### `TestReconcileChildrenDuplicates.test_duplicate_ids_in_old`

| Field | Value |
|-------|-------|
| **Purpose** | Verify behavior with duplicate IDs in old list (edge case) |
| **Invariants** | Set-based matching deduplicates; no spurious removes |
| **Assertion Coverage** | Yes - "a" matched, no removes |

### Quality Issues

- **Excellent pure unit tests**: Tests pure function with no side effects
- **Comprehensive coverage**: Basic, head/tail optimization, edge cases, large scale, duplicates
- **Algorithm documentation**: Test names document the multi-phase algorithm
- **Performance tests**: Large scale tests verify O(n) performance expectations
- **Deterministic**: Uses seeded random for reproducible shuffle tests

---

## tests/test_rendering.py

**Module Under Test**: `trellis.core.rendering.session`, `trellis.core.rendering.element`, `trellis.core.rendering.render`, `trellis.core.rendering.frames`
**Classification**: Mixed (Unit + Integration)
**Test Count**: 37
**Target Location**: Split into:
- `tests/py/unit/core/rendering/test_element.py` (TestElement)
- `tests/py/unit/core/rendering/test_session.py` (TestActiveSession, TestRenderSession basic)
- `tests/py/unit/core/rendering/test_escape_key.py` (TestEscapeKey)
- `tests/py/integration/core/rendering/test_rendering.py` (concurrent tests, reconciliation tests, position ID tests)

### Dependencies
- Real: `RenderSession`, `render()`, `@component`, `Stateful`, widgets, threading, concurrent.futures
- Mocked: None (uses local helpers)

### Fixtures Used
- `make_component` (local helper)
- `make_descriptor` (local helper)
- `_get_dummy_session_ref` (local helper)

### Tests

#### `TestElement.test_element_node_creation`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Element can be created with default values |
| **Invariants** | Default props={}, child_ids=[], key=None, id="" |
| **Assertion Coverage** | Yes - checks all default fields |

#### `TestElement.test_element_node_with_key`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Element stores key parameter |
| **Invariants** | Key is stored for reconciliation |
| **Assertion Coverage** | Yes - checks key value |

#### `TestElement.test_element_node_with_properties`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Element stores props and exposes via properties |
| **Invariants** | Props accessible via node.properties |
| **Assertion Coverage** | Yes - checks props dict |

#### `TestElement.test_element_node_is_mutable`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Element is mutable and hashable |
| **Invariants** | Element is mutable dataclass with render_count-based hash |
| **Assertion Coverage** | Yes - hash() doesn't raise, can modify id |

#### `TestActiveSession.test_default_is_none`

| Field | Value |
|-------|-------|
| **Purpose** | Verify get_active_session() returns None by default |
| **Invariants** | No active session when not rendering |
| **Assertion Coverage** | Yes - checks is None |

#### `TestActiveSession.test_set_and_get`

| Field | Value |
|-------|-------|
| **Purpose** | Verify set_active_session and get_active_session work |
| **Invariants** | Can set and retrieve active session |
| **Assertion Coverage** | Yes - set, get is same object, clear, get is None |

#### `TestRenderSession.test_creation`

| Field | Value |
|-------|-------|
| **Purpose** | Verify RenderSession initialization |
| **Invariants** | Root component stored, root_element None before render, dirty empty |
| **Assertion Coverage** | Yes - checks all initial state |

#### `TestRenderSession.test_mark_dirty_id`

| Field | Value |
|-------|-------|
| **Purpose** | Verify dirty.mark() and __contains__ work |
| **Invariants** | Marked IDs are "in" dirty tracker |
| **Assertion Coverage** | Yes - marks ID, checks containment |

#### `TestConcurrentRenderSessionIsolation.test_concurrent_threads_have_isolated_sessions`

| Field | Value |
|-------|-------|
| **Purpose** | Verify each thread has its own active render session |
| **Invariants** | contextvars provide thread-local storage |
| **Assertion Coverage** | Yes - two threads, each sees its own session |

#### `TestConcurrentRenderSessionIsolation.test_concurrent_renders_dont_interfere`

| Field | Value |
|-------|-------|
| **Purpose** | Verify concurrent renders in different threads don't corrupt each other |
| **Invariants** | Thread isolation means no cross-contamination |
| **Assertion Coverage** | Yes - each thread's render results isolated |

#### `TestComponentOutsideRenderSession.test_component_outside_render_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify creating component outside render context raises RuntimeError |
| **Invariants** | Components require active render session |
| **Assertion Coverage** | Yes - pytest.raises with match |

#### `TestComponentOutsideRenderSession.test_container_with_block_outside_render_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify using 'with' on container outside render raises RuntimeError |
| **Invariants** | Container with blocks require render context |
| **Assertion Coverage** | Yes - pytest.raises with match |

#### `TestDescriptorStackCleanupOnException.test_exception_in_component_cleans_up_stack`

| Field | Value |
|-------|-------|
| **Purpose** | Verify exception during component execution cleans up stack |
| **Invariants** | active is None after exception (no leaked state) |
| **Assertion Coverage** | Yes - raises error, checks ctx.active is None |

#### `TestDescriptorStackCleanupOnException.test_exception_in_nested_with_block_cleans_up`

| Field | Value |
|-------|-------|
| **Purpose** | Verify exception in nested with block cleans up |
| **Invariants** | Nested failures don't corrupt stack |
| **Assertion Coverage** | Yes - raises error, checks ctx.active is None |

#### `TestThreadSafeStateUpdates.test_state_updates_during_concurrent_renders`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state updates in one render don't affect concurrent render |
| **Invariants** | Each thread's state is isolated |
| **Assertion Coverage** | Yes - 4 threads with different values, all isolated |

#### `TestThreadSafeStateUpdates.test_callback_lookup_from_node_props`

| Field | Value |
|-------|-------|
| **Purpose** | Verify callbacks can be looked up from node props |
| **Invariants** | get_callback finds callable in props by name |
| **Assertion Coverage** | Yes - found callback works, missing returns None |

#### `TestThreadSafeStateUpdates.test_state_update_blocks_during_render`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state updates block while render holds lock |
| **Invariants** | dirty.mark() acquires lock, blocks during render |
| **Assertion Coverage** | Yes - event ordering verifies blocking behavior |

#### `TestElementStateParentId.test_element_state_parent_id_tracking`

| Field | Value |
|-------|-------|
| **Purpose** | Verify ElementState.parent_id tracks parent node |
| **Invariants** | Root has no parent, children track their parent |
| **Assertion Coverage** | Yes - checks root and child parent_id |

#### `TestElementStateParentId.test_parent_id_preserved_on_rerender`

| Field | Value |
|-------|-------|
| **Purpose** | Verify parent_id preserved when component re-renders |
| **Invariants** | Re-render doesn't change parent relationships |
| **Assertion Coverage** | Yes - triggers re-render, checks parent_id unchanged |

#### `TestPropsComparison.test_props_with_none_values`

| Field | Value |
|-------|-------|
| **Purpose** | Verify props with None values handled correctly |
| **Invariants** | None→None: no re-render; None→value: re-render |
| **Assertion Coverage** | Yes - tracks render counts through transitions |

#### `TestPropsComparison.test_props_with_callable`

| Field | Value |
|-------|-------|
| **Purpose** | Verify props with callable values use identity comparison |
| **Invariants** | Same function: no re-render; different function: re-render |
| **Assertion Coverage** | Yes - tracks render counts with function swap |

#### `TestPropsComparison.test_empty_props`

| Field | Value |
|-------|-------|
| **Purpose** | Verify components with no props work correctly |
| **Invariants** | Empty props: no re-render when parent re-renders |
| **Assertion Coverage** | Yes - child count stays at 1 |

#### `TestPropsComparison.test_props_with_tuple`

| Field | Value |
|-------|-------|
| **Purpose** | Verify props with tuple values compare correctly |
| **Invariants** | Same tuple: no re-render; different tuple: re-render |
| **Assertion Coverage** | Yes - tracks render counts |

#### `TestBuiltinWidgetsReconciliation.test_remove_widget_from_middle_of_list`

| Field | Value |
|-------|-------|
| **Purpose** | Verify removing widget from middle exercises type-based matching |
| **Invariants** | Widget removal works without TypeError |
| **Assertion Coverage** | Yes - checks child count before/after |

#### `TestBuiltinWidgetsReconciliation.test_html_elements_in_dynamic_list`

| Field | Value |
|-------|-------|
| **Purpose** | Verify HTML elements are hashable for reconciliation |
| **Invariants** | @html_element components work in dynamic lists |
| **Assertion Coverage** | Yes - removes from middle, checks count |

#### `TestBuiltinWidgetsReconciliation.test_widgets_in_dynamic_list`

| Field | Value |
|-------|-------|
| **Purpose** | Verify widgets are hashable for reconciliation |
| **Invariants** | @react_component_base components work in dynamic lists |
| **Assertion Coverage** | Yes - removes items, checks count |

#### `TestBuiltinWidgetsReconciliation.test_mixed_widgets_and_components_in_list`

| Field | Value |
|-------|-------|
| **Purpose** | Verify mix of @component and @react_component_base works |
| **Invariants** | Mixed component types reconcile correctly |
| **Assertion Coverage** | Yes - reorder and remove, checks count |

#### `TestEscapeKey.test_no_special_chars`

| Field | Value |
|-------|-------|
| **Purpose** | Verify keys without special chars pass through unchanged |
| **Invariants** | No encoding needed for safe characters |
| **Assertion Coverage** | Yes - checks multiple safe patterns |

#### `TestEscapeKey.test_escape_colon`

| Field | Value |
|-------|-------|
| **Purpose** | Verify colon is URL-encoded |
| **Invariants** | : → %3A |
| **Assertion Coverage** | Yes - single and multiple colons |

#### `TestEscapeKey.test_escape_at`

| Field | Value |
|-------|-------|
| **Purpose** | Verify @ is URL-encoded |
| **Invariants** | @ → %40 |
| **Assertion Coverage** | Yes - single @ in different positions |

#### `TestEscapeKey.test_escape_slash`

| Field | Value |
|-------|-------|
| **Purpose** | Verify / is URL-encoded |
| **Invariants** | / → %2F |
| **Assertion Coverage** | Yes - single and multiple slashes |

#### `TestEscapeKey.test_escape_percent`

| Field | Value |
|-------|-------|
| **Purpose** | Verify % is URL-encoded first to avoid double-encoding |
| **Invariants** | % → %25 (must be first to prevent %3A → %253A) |
| **Assertion Coverage** | Yes - % alone and in different positions |

#### `TestEscapeKey.test_multiple_special_chars`

| Field | Value |
|-------|-------|
| **Purpose** | Verify all special characters encoded in single key |
| **Invariants** | All special chars replaced correctly |
| **Assertion Coverage** | Yes - mixed special chars |

#### `TestPositionIdGeneration.test_root_id_format`

| Field | Value |
|-------|-------|
| **Purpose** | Verify root node ID format includes component identity |
| **Invariants** | Format: /@{id(component)} |
| **Assertion Coverage** | Yes - checks format pattern |

#### `TestPositionIdGeneration.test_child_id_includes_position`

| Field | Value |
|-------|-------|
| **Purpose** | Verify child IDs include position index |
| **Invariants** | Children have /0@, /1@, /2@ in their IDs |
| **Assertion Coverage** | Yes - checks each position |

#### `TestPositionIdGeneration.test_keyed_child_id_format`

| Field | Value |
|-------|-------|
| **Purpose** | Verify keyed children use :key@ format |
| **Invariants** | Key embedded with : prefix |
| **Assertion Coverage** | Yes - checks ":submit@" in ID |

#### `TestPositionIdGeneration.test_different_component_types_different_ids`

| Field | Value |
|-------|-------|
| **Purpose** | Verify same position, different component = different ID |
| **Invariants** | Component identity is part of ID |
| **Assertion Coverage** | Yes - TypeA and TypeB at same position have different IDs |

### Quality Issues

- **Large mixed file**: Contains unit tests (Element, EscapeKey), integration tests (rendering, concurrency)
- **Should split**: Unit tests don't need full render context; integration tests need the whole pipeline
- **Good concurrency coverage**: Tests thread isolation, locking, and context vars
- **Regression tests**: TestBuiltinWidgetsReconciliation documents TypeError fix
- **Critical tests**: Tests core rendering infrastructure including thread safety


---

## tests/test_routes.py

**Module Under Test**: `trellis.platforms.server.routes`
**Classification**: Unit
**Test Count**: 3
**Target Location**: `tests/py/unit/platforms/server/test_routes.py`

### Dependencies
- Real: None (pure function testing)
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestGetIndexHtml.test_valid_html_structure`

| Field | Value |
|-------|-------|
| **Purpose** | Verify `get_index_html()` generates valid HTML page structure for the React app |
| **Invariants** | Generated HTML must include DOCTYPE, html tags, root div for React mounting, and bundle asset references |
| **Assertion Coverage** | Yes - asserts presence of `<!DOCTYPE html>`, `<html>`, `</html>`, `<div id="root"></div>`, `bundle.js`, `bundle.css` |

#### `TestGetIndexHtml.test_uses_static_path`

| Field | Value |
|-------|-------|
| **Purpose** | Verify custom `static_path` parameter is used for bundle URLs |
| **Invariants** | When static_path="/assets", bundle URLs must be prefixed with "/assets/" |
| **Assertion Coverage** | Yes - asserts `/assets/bundle.js` and `/assets/bundle.css` appear in output |

#### `TestGetIndexHtml.test_default_static_path`

| Field | Value |
|-------|-------|
| **Purpose** | Verify default static path is `/static` when not specified |
| **Invariants** | Without explicit static_path, bundle URLs must use "/static/" prefix |
| **Assertion Coverage** | Yes - asserts `/static/bundle.js` and `/static/bundle.css` appear in output |

### Quality Issues
- None - well-isolated unit tests with clear invariants

---

## tests/test_serialization.py

**Module Under Test**: `trellis.platforms.common.serialization`
**Classification**: Integration
**Test Count**: 9
**Target Location**: `tests/py/integration/platforms/test_serialization.py`

### Dependencies
- Real: `trellis.core.components.composition.component`, `trellis.core.rendering.render`, `trellis.core.rendering.session.RenderSession`, `trellis.widgets.basic.Button`, `trellis.html`
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestSerializeNode.test_serialize_simple_node`

| Field | Value |
|-------|-------|
| **Purpose** | Verify basic Element serializes to correct JSON structure |
| **Invariants** | Serialized node must have type="CompositionComponent", correct name, position-based key starting with "/@", empty props and children |
| **Assertion Coverage** | Yes - asserts all required fields |

#### `TestSerializeNode.test_composition_component_props_not_serialized`

| Field | Value |
|-------|-------|
| **Purpose** | Verify CompositionComponent props are NOT sent to client (layout-only) |
| **Invariants** | CompositionComponent nodes must have empty props in serialization regardless of what props were passed |
| **Assertion Coverage** | Yes - asserts `props == {}` for CompositionComponent with text/count props |

#### `TestSerializeNode.test_serialize_node_with_key`

| Field | Value |
|-------|-------|
| **Purpose** | Verify user-provided keys are included in position-based IDs |
| **Invariants** | User key must appear in serialized key with `:key@` prefix format |
| **Assertion Coverage** | Yes - asserts `:my-key@` appears in result key |

#### `TestSerializeNode.test_serialize_nested_children`

| Field | Value |
|-------|-------|
| **Purpose** | Verify nested component trees serialize children inline recursively |
| **Invariants** | Parent/child relationships must be preserved in serialized children array |
| **Assertion Coverage** | Yes - asserts App→Parent→[Child,Child] structure with correct types/names |

#### `TestSerializeNode.test_serialize_callback_creates_reference`

| Field | Value |
|-------|-------|
| **Purpose** | Verify callbacks become ID references that can be invoked |
| **Invariants** | Callbacks serialize to `{"__callback__": "id"}` and can be looked up/invoked via parse_callback_id + get_callback |
| **Assertion Coverage** | Yes - asserts callback reference format, successful lookup, and invocation |

#### `TestSerializeNode.test_serialize_various_prop_types`

| Field | Value |
|-------|-------|
| **Purpose** | Verify various primitive types serialize correctly |
| **Invariants** | str, int, float, bool, None, list, dict values must serialize to equivalent JSON-compatible values |
| **Assertion Coverage** | Yes - asserts each type preserves its value |

#### `TestSerializeNode.test_serialize_nested_callbacks`

| Field | Value |
|-------|-------|
| **Purpose** | Verify callbacks inside lists/dicts are properly serialized |
| **Invariants** | Callbacks nested in collections must get `__callback__` references and remain invocable |
| **Assertion Coverage** | Yes - asserts both callbacks get references and can be invoked |

#### `TestSerializeNode.test_multiple_callbacks_get_unique_ids`

| Field | Value |
|-------|-------|
| **Purpose** | Verify each callback on a node gets a unique ID |
| **Invariants** | Different callback props must have different callback IDs |
| **Assertion Coverage** | Yes - asserts onClick and onMouseEnter callbacks have different IDs |

### Quality Issues
- **Integration not unit**: Tests use real RenderSession, render(), and full component system. Cannot test serialization in isolation.
- **Should be classified as integration**: These tests verify the serialization module works with the rendering system, not just serialization logic alone.

---

## tests/test_serve_platform.py

**Module Under Test**: `trellis.platforms.browser.serve_platform`
**Classification**: Unit
**Test Count**: 16
**Target Location**: `tests/py/unit/platforms/browser/test_serve_platform.py`

### Dependencies
- Real: None (uses tmp_path for filesystem isolation)
- Mocked: `sys.modules` (for entry point detection tests)

### Fixtures Used
- `tmp_path` (pytest built-in)

### Tests

#### `TestFindPackageRoot.test_not_in_package_returns_none`

| Field | Value |
|-------|-------|
| **Purpose** | Verify `_find_package_root` returns None for standalone files |
| **Invariants** | Files without `__init__.py` in their directory chain are not packages |
| **Assertion Coverage** | Yes - asserts None returned |

#### `TestFindPackageRoot.test_single_level_package`

| Field | Value |
|-------|-------|
| **Purpose** | Verify package root detection for single-level packages |
| **Invariants** | Directory with `__init__.py` containing a .py file is a package |
| **Assertion Coverage** | Yes - asserts correct package directory returned |

#### `TestFindPackageRoot.test_nested_packages_returns_topmost`

| Field | Value |
|-------|-------|
| **Purpose** | Verify nested packages return the topmost package directory |
| **Invariants** | For outer/inner/module.py, should return outer (not inner) |
| **Assertion Coverage** | Yes - asserts outer directory returned |

#### `TestFindPackageRoot.test_source_in_init_file`

| Field | Value |
|-------|-------|
| **Purpose** | Verify package detection works when source is `__init__.py` itself |
| **Invariants** | `__init__.py` should identify its directory as the package |
| **Assertion Coverage** | Yes - asserts package directory returned |

#### `TestCollectPackageFiles.test_collects_all_py_files`

| Field | Value |
|-------|-------|
| **Purpose** | Verify `_collect_package_files` gathers all .py files with contents |
| **Invariants** | All .py files in package should be collected with relative paths as keys and file contents as values |
| **Assertion Coverage** | Yes - asserts count=3, correct keys, correct content |

#### `TestCollectPackageFiles.test_includes_nested_subdirectories`

| Field | Value |
|-------|-------|
| **Purpose** | Verify nested subdirectory .py files are collected |
| **Invariants** | Files in sub-packages must be included with full relative paths |
| **Assertion Coverage** | Yes - asserts count=4, nested path present, correct content |

#### `TestCollectPackageFiles.test_ignores_non_py_files`

| Field | Value |
|-------|-------|
| **Purpose** | Verify only .py files are collected, not .md/.json/etc. |
| **Invariants** | Non-Python files must be excluded from collection |
| **Assertion Coverage** | Yes - asserts only `__init__.py` collected (count=1) |

#### `TestDetectEntryPoint.test_returns_main_file_path`

| Field | Value |
|-------|-------|
| **Purpose** | Verify `_detect_entry_point` returns file path for script execution |
| **Invariants** | For `python script.py`, returns (script_path, None) |
| **Assertion Coverage** | Yes - asserts path and None module name |

#### `TestDetectEntryPoint.test_returns_module_name_when_run_as_module`

| Field | Value |
|-------|-------|
| **Purpose** | Verify module name is returned for `python -m` execution |
| **Invariants** | For `python -m pkg.module`, returns (path, "pkg.module") |
| **Assertion Coverage** | Yes - asserts both path and module name |

#### `TestDetectEntryPoint.test_raises_when_main_not_found`

| Field | Value |
|-------|-------|
| **Purpose** | Verify RuntimeError when `__main__` not in sys.modules |
| **Invariants** | Missing `__main__` is an error condition |
| **Assertion Coverage** | Yes - asserts RuntimeError with correct message |

#### `TestDetectEntryPoint.test_raises_when_file_not_set`

| Field | Value |
|-------|-------|
| **Purpose** | Verify RuntimeError when `__main__.__file__` is None |
| **Invariants** | Missing `__file__` is an error condition |
| **Assertion Coverage** | Yes - asserts RuntimeError with correct message |

#### `TestGenerateHtml.test_module_source_contains_files_json`

| Field | Value |
|-------|-------|
| **Purpose** | Verify module source config is embedded in generated HTML |
| **Invariants** | HTML must contain JSON-serialized module files and module name |
| **Assertion Coverage** | Yes - asserts type, file paths, and module name present |

#### `TestGenerateHtml.test_code_source_contains_code`

| Field | Value |
|-------|-------|
| **Purpose** | Verify code source config is embedded in generated HTML |
| **Invariants** | HTML must contain JSON-serialized code |
| **Assertion Coverage** | Yes - asserts type and code content present |

#### `TestGenerateHtml.test_valid_html_structure`

| Field | Value |
|-------|-------|
| **Purpose** | Verify generated HTML has valid structure |
| **Invariants** | HTML must have DOCTYPE, html tags, root div, bundle refs, and config variable |
| **Assertion Coverage** | Yes - asserts all structural elements present |

#### `TestGenerateHtml.test_escapes_special_characters`

| Field | Value |
|-------|-------|
| **Purpose** | Verify special characters in code don't break HTML |
| **Invariants** | Embedded JSON must be properly escaped for safe inclusion in HTML |
| **Assertion Coverage** | Partial - verifies HTML is well-formed but doesn't check all escape cases |

#### `TestGenerateHtml.test_escapes_script_tags_in_code`

| Field | Value |
|-------|-------|
| **Purpose** | Verify `</script>` in code is escaped to prevent injection |
| **Invariants** | Closing script tags must be escaped (e.g., `<\/`) to prevent breaking out of script context |
| **Assertion Coverage** | Yes - asserts escape pattern present and literal `</script>` not in script section |

### Quality Issues
- None - excellent unit test isolation with proper filesystem mocking via tmp_path

---

## tests/test_state.py

**Module Under Test**: `trellis.core.state.stateful`
**Classification**: Integration
**Test Count**: 21
**Target Location**: `tests/py/integration/core/state/test_state.py`

### Dependencies
- Real: `trellis.core.components.composition.component`, `trellis.core.rendering.render`, `trellis.core.rendering.session.RenderSession`
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestStateful.test_stateful_set_and_get`

| Field | Value |
|-------|-------|
| **Purpose** | Verify basic state get/set works |
| **Invariants** | Assigned value must be retrievable via attribute access |
| **Assertion Coverage** | Yes - asserts value equals assigned |

#### `TestStateful.test_stateful_tracks_dependencies`

| Field | Value |
|-------|-------|
| **Purpose** | Verify reading state during render registers dependency |
| **Invariants** | Element that reads state.prop must appear in that prop's watchers |
| **Assertion Coverage** | Yes - asserts watchers length == 1 |

#### `TestStateful.test_stateful_marks_dirty_on_change`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state change marks dependent elements dirty |
| **Invariants** | When state.prop changes, all elements in prop's watchers must be marked dirty |
| **Assertion Coverage** | Yes - asserts root element ID in dirty set |

#### `TestStateful.test_stateful_render_dirty_updates`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state changes trigger re-renders |
| **Invariants** | render() after state change must re-execute affected component |
| **Assertion Coverage** | Yes - asserts render count increments |

#### `TestStateful.test_fine_grained_tracking`

| Field | Value |
|-------|-------|
| **Purpose** | Verify only components reading changed property re-render |
| **Invariants** | Changing state.name should re-render NameComponent but NOT CountComponent |
| **Assertion Coverage** | Yes - asserts name_renders==2, count_renders==1 |

#### `TestStateful.test_state_change_without_render_context`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state can be changed outside render |
| **Invariants** | State mutations outside render context must succeed without error |
| **Assertion Coverage** | Yes - asserts final value correct |

#### `TestLocalStatePersistence.test_local_state_persists_across_rerenders`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state instance is cached and reused across re-renders |
| **Invariants** | Same state object (by id()) must be returned on re-renders |
| **Assertion Coverage** | Yes - asserts all 3 captured IDs are equal |

#### `TestLocalStatePersistence.test_local_state_values_preserved`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state values persist across re-renders |
| **Invariants** | Modifications made outside render must be visible on next render |
| **Assertion Coverage** | Yes - asserts observed_counts == [0, 1, 2] |

#### `TestLocalStatePersistence.test_multiple_state_instances_same_type`

| Field | Value |
|-------|-------|
| **Purpose** | Verify multiple instances of same state type use call order for caching |
| **Invariants** | First call returns first instance, second call returns second instance, consistently |
| **Assertion Coverage** | Yes - asserts distinct instances and correct reuse on re-render |

#### `TestLocalStatePersistence.test_subclass_state_works`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state subclasses work correctly |
| **Invariants** | BaseState and ExtendedState must be cached separately by their actual types |
| **Assertion Coverage** | Yes - asserts separate cache keys and value preservation |

#### `TestLocalStatePersistence.test_state_outside_render_not_cached`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state created outside render is not cached |
| **Invariants** | Multiple instantiations outside render must create distinct instances |
| **Assertion Coverage** | Yes - asserts state1 is not state2 |

#### `TestStateDependencyTracking.test_watchers_weakset_populated`

| Field | Value |
|-------|-------|
| **Purpose** | Verify watchers WeakSet contains dependent Element |
| **Invariants** | Element reading state property must be added to that property's watchers |
| **Assertion Coverage** | Yes - asserts watcher count and ID match |

#### `TestStateDependencyTracking.test_session_ref_set_on_element_node`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Element has `_session_ref` pointing to RenderSession |
| **Invariants** | Element must hold weak reference to owning session for dirty marking |
| **Assertion Coverage** | Yes - asserts `_session_ref()` returns ctx |

#### `TestStateDependencyTracking.test_child_and_parent_track_same_state`

| Field | Value |
|-------|-------|
| **Purpose** | Verify parent and child both appear in watchers when both read state |
| **Invariants** | All readers must be tracked independently |
| **Assertion Coverage** | Yes - asserts both IDs in watchers, count==2 |

#### `TestStateDependencyTracking.test_state_change_marks_all_dependents_dirty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state change marks all watchers dirty |
| **Invariants** | All Elements in watchers must be marked dirty on property change |
| **Assertion Coverage** | Yes - asserts both parent and child IDs in dirty set |

#### `TestStateDependencyTracking.test_dependency_persists_across_rerenders`

| Field | Value |
|-------|-------|
| **Purpose** | Verify dependencies survive re-renders |
| **Invariants** | After re-render, element must still be tracked (same ID) |
| **Assertion Coverage** | Yes - asserts node_id in watchers before and after re-render |

#### `TestStateDependencyTracking.test_multiple_properties_tracked_independently`

| Field | Value |
|-------|-------|
| **Purpose** | Verify each property tracks its own watchers |
| **Invariants** | Component reading state.name should only be in name's watchers, not count's |
| **Assertion Coverage** | Yes - asserts name reader in name watchers only, count reader in count watchers only |

#### `TestStateDependencyTracking.test_dependency_cleanup_on_unmount`

| Field | Value |
|-------|-------|
| **Purpose** | Verify dependencies are cleaned up when component unmounts |
| **Invariants** | After unmount + GC, component must be removed from watchers (WeakSet auto-cleans) |
| **Assertion Coverage** | Yes - asserts consumer_id not in watchers after unmount + gc.collect() |

#### `TestStateDependencyTracking.test_dependency_cleanup_on_rerender_without_read`

| Field | Value |
|-------|-------|
| **Purpose** | Verify dependency removed when component stops reading state |
| **Invariants** | If component no longer reads state on re-render, it should not be in watchers |
| **Assertion Coverage** | Yes - asserts node_id not in watchers after re-render without read + gc.collect() |

### Quality Issues
- **Mixed unit/integration**: `test_stateful_set_and_get` and `test_state_outside_render_not_cached` are unit tests (no rendering); rest are integration
- **Could split**: Pure Stateful logic tests vs rendering integration tests could be separate files
- **Internal details tested**: Tests access `_state_props`, `_session_ref`, `watchers` - internal implementation details. Consider testing via public API only.
- **Test internals heavily**: Testing WeakSet behavior, cache keys by type, etc. - may be too implementation-coupled

---

## tests/test_state_edge_cases.py

**Module Under Test**: `trellis.core.state.stateful`, `trellis.core.rendering.render`, `trellis.core.rendering.session`, `trellis.core.components.composition`
**Classification**: Integration
**Test Count**: 17
**Target Location**: `tests/py/integration/core/test_state_edge_cases.py`

### Dependencies
- Real: `RenderSession`, `render()`, `@component` decorator
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestDeepDependencyTracking.test_state_read_in_deep_component`

| Field | Value |
|-------|-------|
| **Purpose** | Verify that state read 50 levels deep only triggers re-render of that component |
| **Invariants** | When state changes, only components that read the state during their last render should re-render; ancestor components that don't read the state remain unchanged |
| **Assertion Coverage** | Yes - verifies root renders once, deepest level renders twice after state change, all intermediate levels render only once |

#### `TestDeepDependencyTracking.test_multiple_components_same_property`

| Field | Value |
|-------|-------|
| **Purpose** | Verify multiple components reading the same state property all receive updates |
| **Invariants** | All components reading a shared state property must be marked dirty and re-render when that property changes |
| **Assertion Coverage** | Yes - verifies all 5 Reader components re-render after state change |

#### `TestDeepDependencyTracking.test_component_reads_but_doesnt_use_value`

| Field | Value |
|-------|-------|
| **Purpose** | Verify that reading state creates dependency even if value is ignored |
| **Invariants** | Dependency tracking is based on property access, not value usage; any read creates a dependency |
| **Assertion Coverage** | Yes - verifies component re-renders even though it discards the value |

#### `TestStateLifecycle.test_on_mount_called_once`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Stateful.on_mount is called exactly once per element |
| **Invariants** | on_mount must be called on first render only, not on re-renders |
| **Assertion Coverage** | Yes - verifies mount_count stays at 1 after 5 re-renders |

#### `TestStateLifecycle.test_on_unmount_called_when_removed`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Stateful.on_unmount is called when element is removed from tree |
| **Invariants** | on_unmount must be called when component is conditionally removed |
| **Assertion Coverage** | Yes - verifies unmount_log contains state name after removal |

#### `TestStateLifecycle.test_state_persists_across_rerenders`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state instance identity persists across re-renders |
| **Invariants** | Same state instance (same id()) must be returned on each render for hook-like behavior |
| **Assertion Coverage** | Yes - verifies all 3 renders return same id() |

#### `TestHookOrdering.test_multiple_state_instances_order`

| Field | Value |
|-------|-------|
| **Purpose** | Verify multiple state instances in same component use call order |
| **Invariants** | State instances are keyed by (class, call_index); indices must be 0, 1, 2 for sequential calls |
| **Assertion Coverage** | Yes - verifies local_state keys have indices [0, 1, 2] |

#### `TestHookOrdering.test_state_order_preserved_on_rerender`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state instances maintain identity across re-renders |
| **Invariants** | Same instances (same id()) must be returned in same order across re-renders |
| **Assertion Coverage** | Yes - verifies state_ids lists are identical across 3 renders |

#### `TestHookOrdering.test_state_in_loop`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state created in a loop gets different instances per iteration |
| **Invariants** | Each loop iteration gets its own cached state instance with distinct call_index |
| **Assertion Coverage** | Yes - verifies 3 state instances with indices [0, 1, 2], preserved on re-render |

#### `TestDependencyAcrossComponents.test_parent_and_child_read_same_state`

| Field | Value |
|-------|-------|
| **Purpose** | Verify parent and child reading same state both get updates |
| **Invariants** | State dependency tracking works across component hierarchy; both parent and child must re-render |
| **Assertion Coverage** | Yes - verifies both parent and child render counts increase from 1 to 2 |

#### `TestDependencyAcrossComponents.test_sibling_components_independent_state`

| Field | Value |
|-------|-------|
| **Purpose** | Verify siblings with different state dependencies update independently |
| **Invariants** | Changing state_a should only re-render SiblingA; changing state_b should only re-render SiblingB |
| **Assertion Coverage** | Yes - verifies selective re-rendering: after state_a change only "a" increases, after state_b change only "b" increases |

#### `TestStateCleanup.test_state_cleared_on_unmount`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state is cleared from element when unmounted |
| **Invariants** | After unmount, element ID must be removed from session.states |
| **Assertion Coverage** | Yes - verifies child_id not in ctx.states after unmount |

#### `TestStateCleanup.test_dirty_elements_cleaned_on_unmount`

| Field | Value |
|-------|-------|
| **Purpose** | Verify element is removed from dirty set when unmounted |
| **Invariants** | Unmounted elements must be removed from dirty set even if they were pending re-render |
| **Assertion Coverage** | Yes - verifies child_id not in ctx.dirty after unmount |

#### `TestMultipleStateTypes.test_different_state_types_independent`

| Field | Value |
|-------|-------|
| **Purpose** | Verify different state types in same component are independent |
| **Invariants** | Changing counter.count should re-render; changing name.name should also re-render; they track independently |
| **Assertion Coverage** | Yes - verifies render count increases from 1→2→3 after each state change |

#### `TestMultipleStateTypes.test_state_inheritance`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state subclasses work correctly |
| **Invariants** | ExtendedState should be cached separately from BaseState; both should be retrievable with correct values |
| **Assertion Coverage** | Yes - verifies 2 state instances, correct types and values for both |

### Quality Issues
- **Well-structured**: Tests are organized by concern (lifecycle, ordering, cleanup, etc.)
- **Good isolation**: Each test verifies a specific behavior
- **Internal access**: Tests access `ctx.states`, `root_state.local_state`, `ctx.dirty` - internal state structures
- **Clear invariants**: Each test has a clear expected behavior being verified
- **No mocking**: All tests use real rendering - appropriate for integration tests

---

## tests/test_style_props.py

**Module Under Test**: `trellis.core.components.style_props`, `trellis.core.components.react._merge_style_props`, `trellis.widgets`
**Classification**: Unit (dataclass tests), Integration (widget tests)
**Test Count**: 30
**Target Location**: `tests/py/unit/core/components/test_style_props.py` (unit), `tests/py/integration/widgets/test_style_props_integration.py` (widget integration)

### Dependencies
- Real: `Margin`, `Padding`, `Width`, `Height` dataclasses, `_merge_style_props`, widgets, `RenderSession`, `render()`
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestMargin.test_margin_single_side`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Margin with single side generates correct CSS |
| **Invariants** | Margin(top=8) must produce {"marginTop": "8px"} |
| **Assertion Coverage** | Yes - exact dict comparison |

#### `TestMargin.test_margin_multiple_sides`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Margin with multiple sides generates correct CSS |
| **Invariants** | Multiple sides must each appear in output |
| **Assertion Coverage** | Yes - verifies marginTop and marginBottom |

#### `TestMargin.test_margin_x_shorthand`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Margin x shorthand sets left and right |
| **Invariants** | Margin(x=8) must set both marginLeft and marginRight |
| **Assertion Coverage** | Yes - exact dict comparison |

#### `TestMargin.test_margin_y_shorthand`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Margin y shorthand sets top and bottom |
| **Invariants** | Margin(y=16) must set both marginTop and marginBottom |
| **Assertion Coverage** | Yes - exact dict comparison |

#### `TestMargin.test_margin_specific_overrides_shorthand`

| Field | Value |
|-------|-------|
| **Purpose** | Verify specific sides override shorthands |
| **Invariants** | Margin(x=8, left=12) must have left=12, right=8 |
| **Assertion Coverage** | Yes - verifies specific override |

#### `TestPadding.test_padding_single_side`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Padding with single side generates correct CSS |
| **Invariants** | Padding(top=8) must produce {"paddingTop": "8px"} |
| **Assertion Coverage** | Yes - exact dict comparison |

#### `TestPadding.test_padding_xy_shorthands`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Padding with x and y shorthands |
| **Invariants** | Both x and y shorthands must expand correctly |
| **Assertion Coverage** | Yes - verifies all 4 padding sides |

#### `TestWidth.test_width_value_int`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Width with int value converts to px |
| **Invariants** | Width(value=100) must produce {"width": "100px"} |
| **Assertion Coverage** | Yes - exact dict comparison |

#### `TestWidth.test_width_value_string`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Width with string value passes through |
| **Invariants** | Width(value="100%") must produce {"width": "100%"} |
| **Assertion Coverage** | Yes - exact dict comparison |

#### `TestWidth.test_width_with_constraints`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Width with min and max constraints |
| **Invariants** | All three properties (width, minWidth, maxWidth) must be present |
| **Assertion Coverage** | Yes - verifies all 3 properties |

#### `TestWidth.test_width_min_max_only`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Width with only constraints, no value |
| **Invariants** | When value is None, only minWidth/maxWidth should appear |
| **Assertion Coverage** | Yes - verifies only min/max present |

#### `TestHeight.test_height_value`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Height with value |
| **Invariants** | Height(value=300) must produce {"height": "300px"} |
| **Assertion Coverage** | Yes - exact dict comparison |

#### `TestHeight.test_height_max_string`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Height with string max (e.g., viewport units) |
| **Invariants** | Height(max="60vh") must produce {"maxHeight": "60vh"} |
| **Assertion Coverage** | Yes - exact dict comparison |

#### `TestMergeStyleProps.test_margin_dataclass_converted`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Margin dataclass is converted to style dict |
| **Invariants** | "margin" key removed, style dict contains converted values |
| **Assertion Coverage** | Yes - verifies key removal and style content |

#### `TestMergeStyleProps.test_margin_int_passed_through`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Margin int value is passed through for widget-specific handling |
| **Invariants** | Int margin stays as "margin" prop, not converted to style |
| **Assertion Coverage** | Yes - verifies margin=8 remains as prop |

#### `TestMergeStyleProps.test_padding_dataclass_converted`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Padding dataclass is converted to style dict |
| **Invariants** | "padding" key removed, style dict contains converted values |
| **Assertion Coverage** | Yes - verifies key removal and style content |

#### `TestMergeStyleProps.test_padding_int_passed_through`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Padding int value is passed through for widget-specific handling |
| **Invariants** | Int padding stays as "padding" prop, not converted to style |
| **Assertion Coverage** | Yes - verifies padding=16 remains as prop |

#### `TestMergeStyleProps.test_width_int_converted`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Width int is converted to style (generic) |
| **Invariants** | Int width becomes {"width": "Npx"} in style |
| **Assertion Coverage** | Yes - verifies conversion |

#### `TestMergeStyleProps.test_width_string_converted`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Width string is converted to style |
| **Invariants** | String width becomes style property |
| **Assertion Coverage** | Yes - verifies conversion |

#### `TestMergeStyleProps.test_width_dataclass_converted`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Width dataclass is converted to style |
| **Invariants** | Width dataclass properties expand to style dict |
| **Assertion Coverage** | Yes - verifies width and maxWidth |

#### `TestMergeStyleProps.test_height_dataclass_converted`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Height dataclass is converted to style |
| **Invariants** | Height dataclass becomes style property |
| **Assertion Coverage** | Yes - verifies conversion |

#### `TestMergeStyleProps.test_height_int_passed_through`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Height int value is passed through for widget-specific handling (e.g., ProgressBar) |
| **Invariants** | Int height stays as "height" prop, not converted |
| **Assertion Coverage** | Yes - verifies height=12 remains as prop |

#### `TestMergeStyleProps.test_flex_converted`

| Field | Value |
|-------|-------|
| **Purpose** | Verify flex is converted to style |
| **Invariants** | flex property becomes style {"flex": N} |
| **Assertion Coverage** | Yes - verifies conversion |

#### `TestMergeStyleProps.test_existing_style_preserved`

| Field | Value |
|-------|-------|
| **Purpose** | Verify existing style dict is preserved and extended |
| **Invariants** | Original style properties must remain, new style props merged in |
| **Assertion Coverage** | Yes - verifies original "color" preserved plus new properties |

#### `TestMergeStyleProps.test_multiple_props_combined`

| Field | Value |
|-------|-------|
| **Purpose** | Verify multiple style props are combined |
| **Invariants** | All style props (margin, padding, width, flex) must merge into single style dict |
| **Assertion Coverage** | Yes - verifies all 5 style properties present |

#### `TestWidgetIntegration.test_label_with_margin`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Label accepts Margin dataclass |
| **Invariants** | Label with Margin dataclass must have converted style in rendered properties |
| **Assertion Coverage** | Yes - verifies style on rendered element |

#### `TestWidgetIntegration.test_label_with_width`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Label accepts width prop |
| **Invariants** | Width prop must be converted to style on rendered element |
| **Assertion Coverage** | Yes - verifies style on rendered element |

#### `TestWidgetIntegration.test_label_with_flex`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Label accepts flex prop |
| **Invariants** | Flex prop must be converted to style on rendered element |
| **Assertion Coverage** | Yes - verifies style on rendered element |

#### `TestWidgetIntegration.test_column_with_padding_dataclass`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Column accepts Padding dataclass |
| **Invariants** | Padding dataclass must be converted to style on rendered element |
| **Assertion Coverage** | Yes - verifies all 4 padding sides in style |

#### `TestWidgetIntegration.test_column_with_padding_int`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Column accepts padding int (passed to React) |
| **Invariants** | Int padding must remain as "padding" prop, not style |
| **Assertion Coverage** | Yes - verifies padding=24 as prop |

#### `TestWidgetIntegration.test_card_with_width`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Card accepts width prop |
| **Invariants** | Width must be converted to style on rendered element |
| **Assertion Coverage** | Yes - verifies style on rendered element |

#### `TestWidgetIntegration.test_button_with_width_string`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Button accepts width string |
| **Invariants** | String width must be converted to style |
| **Assertion Coverage** | Yes - verifies width="100%" in style |

#### `TestWidgetIntegration.test_style_props_merge_with_existing_style`

| Field | Value |
|-------|-------|
| **Purpose** | Verify style props merge with existing style dict |
| **Invariants** | Custom style dict properties must be preserved alongside converted style props |
| **Assertion Coverage** | Yes - verifies all 4 properties (color, fontWeight, marginBottom, width) |

### Quality Issues
- **Well-structured**: Clear separation between dataclass unit tests, merge function tests, and widget integration tests
- **Good isolation**: Unit tests are truly isolated; integration tests use real rendering
- **Should split**: TestMergeStyleProps tests `_merge_style_props` (internal function); TestWidgetIntegration tests via public API
- **Comprehensive**: Good coverage of edge cases (int vs string, shorthands, overrides)

---

## tests/test_tracked.py

**Module Under Test**: `trellis.core.state.tracked` (TrackedList, TrackedDict, TrackedSet)
**Classification**: Unit (basics, mutations, edge cases), Integration (reactivity, render-time tests)
**Test Count**: 89
**Target Location**: `tests/py/unit/core/state/test_tracked.py` (basics), `tests/py/integration/core/test_tracked_reactivity.py` (reactivity)

### Dependencies
- Real: `TrackedList`, `TrackedDict`, `TrackedSet`, `ITER_KEY`, `Stateful`, `@component`, `RenderSession`, `render()`, `gc`
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestTrackedListBasics.test_isinstance_list`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TrackedList passes isinstance check for list |
| **Invariants** | TrackedList must be a true subtype of list |
| **Assertion Coverage** | Yes - isinstance check |

#### `TestTrackedListBasics.test_list_operations`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TrackedList supports all standard list operations |
| **Invariants** | Indexing, slicing, len, contains, iteration must all work |
| **Assertion Coverage** | Yes - tests each operation |

#### `TestTrackedListBasics.test_list_mutations`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TrackedList supports mutation operations |
| **Invariants** | append, insert, remove, pop, extend, clear must all work |
| **Assertion Coverage** | Yes - tests each mutation |

#### `TestTrackedListBasics.test_copy_returns_plain_list`

| Field | Value |
|-------|-------|
| **Purpose** | Verify copy() returns a plain list, not TrackedList |
| **Invariants** | Copy must break tracking |
| **Assertion Coverage** | Yes - type check on result |

#### `TestTrackedListBasics.test_add_returns_plain_list`

| Field | Value |
|-------|-------|
| **Purpose** | Verify + operator returns plain list |
| **Invariants** | Concatenation must return plain list |
| **Assertion Coverage** | Yes - type check on result |

#### `TestTrackedListBasics.test_slice_returns_plain_list`

| Field | Value |
|-------|-------|
| **Purpose** | Verify slicing returns a plain list |
| **Invariants** | Slice must return plain list |
| **Assertion Coverage** | Yes - type check on result |

#### `TestTrackedListBasics.test_repr`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TrackedList has useful repr |
| **Invariants** | repr must include "TrackedList" and contents |
| **Assertion Coverage** | Yes - exact repr check |

#### `TestTrackedDictBasics.test_isinstance_dict`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TrackedDict passes isinstance check for dict |
| **Invariants** | TrackedDict must be a true subtype of dict |
| **Assertion Coverage** | Yes - isinstance check |

#### `TestTrackedDictBasics.test_dict_operations`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TrackedDict supports all standard dict operations |
| **Invariants** | Indexing, get, keys, values, items, contains, len must all work |
| **Assertion Coverage** | Yes - tests each operation |

#### `TestTrackedDictBasics.test_dict_mutations`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TrackedDict supports mutation operations |
| **Invariants** | setitem, delitem, update, pop, clear must all work |
| **Assertion Coverage** | Yes - tests each mutation |

#### `TestTrackedDictBasics.test_copy_returns_plain_dict`

| Field | Value |
|-------|-------|
| **Purpose** | Verify copy() returns a plain dict |
| **Invariants** | Copy must break tracking |
| **Assertion Coverage** | Yes - type check on result |

#### `TestTrackedDictBasics.test_repr`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TrackedDict has useful repr |
| **Invariants** | repr must include "TrackedDict" |
| **Assertion Coverage** | Yes - exact repr check |

#### `TestTrackedSetBasics.test_isinstance_set`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TrackedSet passes isinstance check for set |
| **Invariants** | TrackedSet must be a true subtype of set |
| **Assertion Coverage** | Yes - isinstance check |

#### `TestTrackedSetBasics.test_set_operations`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TrackedSet supports all standard set operations |
| **Invariants** | Contains, len, iteration must all work |
| **Assertion Coverage** | Yes - tests each operation |

#### `TestTrackedSetBasics.test_set_mutations`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TrackedSet supports mutation operations |
| **Invariants** | add, remove, discard, pop, clear must all work |
| **Assertion Coverage** | Yes - tests each mutation |

#### `TestTrackedSetBasics.test_copy_returns_plain_set`

| Field | Value |
|-------|-------|
| **Purpose** | Verify copy() returns a plain set |
| **Invariants** | Copy must break tracking |
| **Assertion Coverage** | Yes - type check on result |

#### `TestTrackedSetBasics.test_set_operators_return_plain_set`

| Field | Value |
|-------|-------|
| **Purpose** | Verify set operators (&, |, -, ^) return plain sets |
| **Invariants** | Binary set operations must return plain sets |
| **Assertion Coverage** | Yes - type check on each operator |

#### `TestTrackedSetBasics.test_repr`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TrackedSet has useful repr |
| **Invariants** | repr must include "TrackedSet" |
| **Assertion Coverage** | Yes - string check |

#### `TestAutoConversion.test_list_auto_converts_on_stateful`

| Field | Value |
|-------|-------|
| **Purpose** | Verify plain list is auto-converted to TrackedList on Stateful |
| **Invariants** | After assignment, field must be TrackedList |
| **Assertion Coverage** | Yes - isinstance check |

#### `TestAutoConversion.test_dict_auto_converts_on_stateful`

| Field | Value |
|-------|-------|
| **Purpose** | Verify plain dict is auto-converted to TrackedDict on Stateful |
| **Invariants** | After assignment, field must be TrackedDict |
| **Assertion Coverage** | Yes - isinstance check |

#### `TestAutoConversion.test_set_auto_converts_on_stateful`

| Field | Value |
|-------|-------|
| **Purpose** | Verify plain set is auto-converted to TrackedSet on Stateful |
| **Invariants** | After assignment, field must be TrackedSet |
| **Assertion Coverage** | Yes - isinstance check |

#### `TestAutoConversion.test_assignment_auto_converts`

| Field | Value |
|-------|-------|
| **Purpose** | Verify assigning plain collection to Stateful property auto-converts |
| **Invariants** | Assignment must trigger conversion |
| **Assertion Coverage** | Yes - isinstance and content check |

#### `TestAutoConversion.test_nested_list_auto_converts_on_access`

| Field | Value |
|-------|-------|
| **Purpose** | Verify nested plain lists are auto-converted when accessed |
| **Invariants** | Inner lists must become TrackedList on access |
| **Assertion Coverage** | Yes - isinstance checks on outer and inner |

#### `TestAutoConversion.test_nested_dict_auto_converts_on_access`

| Field | Value |
|-------|-------|
| **Purpose** | Verify nested plain dicts are auto-converted when accessed |
| **Invariants** | Inner dicts must become TrackedDict on access |
| **Assertion Coverage** | Yes - isinstance checks on outer and inner |

#### `TestDependencyTracking.test_list_getitem_tracks_by_item_identity`

| Field | Value |
|-------|-------|
| **Purpose** | Verify accessing list[i] registers dependency on id(item) |
| **Invariants** | After access, id(item) must be in _deps with current element |
| **Assertion Coverage** | Yes - checks _deps directly |

#### `TestDependencyTracking.test_list_iteration_tracks_iter_key`

| Field | Value |
|-------|-------|
| **Purpose** | Verify iterating over list registers dependency on ITER_KEY |
| **Invariants** | After iteration, ITER_KEY must be in _deps |
| **Assertion Coverage** | Yes - checks _deps[ITER_KEY] |

#### `TestDependencyTracking.test_dict_getitem_tracks_by_key`

| Field | Value |
|-------|-------|
| **Purpose** | Verify accessing dict[key] registers dependency on that key |
| **Invariants** | After access, key must be in _deps |
| **Assertion Coverage** | Yes - checks _deps[key] |

#### `TestDependencyTracking.test_set_contains_tracks_by_value`

| Field | Value |
|-------|-------|
| **Purpose** | Verify `item in set` registers dependency on the value itself |
| **Invariants** | After contains check, value must be in _deps |
| **Assertion Coverage** | Yes - checks _deps[value] |

#### `TestDependencyTracking.test_list_sort_marks_iter_dirty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify sorting a list marks ITER_KEY dirty |
| **Invariants** | After sort, iterating components must re-render |
| **Assertion Coverage** | Yes - render count increases |

#### `TestDependencyTracking.test_dict_new_key_marks_iter_dirty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify adding a new key marks ITER_KEY dirty for iterators |
| **Invariants** | Iterator component must re-render; key-specific component must not |
| **Assertion Coverage** | Yes - selective render count check |

#### `TestFineGrainedReactivity.test_list_item_change_only_rerenders_affected`

| Field | Value |
|-------|-------|
| **Purpose** | Verify modifying one list item only re-renders components that read it |
| **Invariants** | Only Item0 component should re-render when items[0] changes |
| **Assertion Coverage** | Yes - Item0 renders twice, Item1 renders once |

#### `TestFineGrainedReactivity.test_dict_key_change_only_rerenders_affected`

| Field | Value |
|-------|-------|
| **Purpose** | Verify modifying one dict key only re-renders components that read it |
| **Invariants** | Only XViewer should re-render when data["x"] changes |
| **Assertion Coverage** | Yes - selective render count check |

#### `TestFineGrainedReactivity.test_list_append_rerenders_iterators`

| Field | Value |
|-------|-------|
| **Purpose** | Verify appending to list re-renders components that iterate |
| **Invariants** | ListViewer (iterates) re-renders; Item0Viewer (index access) does not |
| **Assertion Coverage** | Yes - selective render count check |

#### `TestRenderTimeMutationGuard.test_list_mutation_during_render_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify mutating TrackedList during render raises RuntimeError |
| **Invariants** | Cannot mutate tracked collection during render |
| **Assertion Coverage** | Yes - pytest.raises with message match |

#### `TestRenderTimeMutationGuard.test_dict_mutation_during_render_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify mutating TrackedDict during render raises RuntimeError |
| **Invariants** | Cannot mutate tracked collection during render |
| **Assertion Coverage** | Yes - pytest.raises with message match |

#### `TestRenderTimeMutationGuard.test_set_mutation_during_render_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify mutating TrackedSet during render raises RuntimeError |
| **Invariants** | Cannot mutate tracked collection during render |
| **Assertion Coverage** | Yes - pytest.raises with message match |

#### `TestDependencyCleanup.test_list_dependency_cleaned_on_unmount`

| Field | Value |
|-------|-------|
| **Purpose** | Verify list dependencies are cleaned up when component unmounts |
| **Invariants** | After unmount + GC, WeakSet must have removed dead references |
| **Assertion Coverage** | Yes - checks dep_node_ids after gc.collect() |

#### `TestDependencyCleanup.test_dict_dependency_cleaned_on_rerender_without_read`

| Field | Value |
|-------|-------|
| **Purpose** | Verify dict dependencies are cleaned when component stops reading |
| **Invariants** | If component no longer reads key on re-render, it must be removed from deps |
| **Assertion Coverage** | Yes - checks dep_node_ids after gc.collect() |

#### `TestEdgeCases.test_empty_list_operations`

| Field | Value |
|-------|-------|
| **Purpose** | Verify operations on empty TrackedList work correctly |
| **Invariants** | Empty list must support len, list(), append, clear |
| **Assertion Coverage** | Yes - tests each operation |

#### `TestTrackedWithStatefulItems.test_stateful_item_tracks_own_properties`

| Field | Value |
|-------|-------|
| **Purpose** | Verify Stateful items in a list track their own properties |
| **Invariants** | Modifying todo1.completed should only re-render Todo1Viewer |
| **Assertion Coverage** | Yes - selective render count check |

#### `TestTrackedWithStatefulItems.test_replacing_stateful_item_in_list`

| Field | Value |
|-------|-------|
| **Purpose** | Verify replacing a Stateful item in list marks the slot dirty |
| **Invariants** | Replacing item at index should trigger re-render |
| **Assertion Coverage** | Yes - render count increases |

#### `TestNewTrackingMethods.test_list_index_tracks_iter_key`

| Field | Value |
|-------|-------|
| **Purpose** | Verify list.index() registers ITER_KEY dependency |
| **Invariants** | After append, index-dependent component should re-render |
| **Assertion Coverage** | Yes - render count increases |

#### `TestNewTrackingMethods.test_list_count_tracks_iter_key`

| Field | Value |
|-------|-------|
| **Purpose** | Verify list.count() registers ITER_KEY dependency |
| **Invariants** | After append, count-dependent component should re-render |
| **Assertion Coverage** | Yes - render count increases |

#### `TestNewTrackingMethods.test_dict_contains_tracks_by_key`

| Field | Value |
|-------|-------|
| **Purpose** | Verify `key in dict` registers dependency on that key |
| **Invariants** | Adding "y" triggers re-render; adding "z" does not |
| **Assertion Coverage** | Yes - selective render count check |

#### `TestNewTrackingMethods.test_set_issubset_tracks_iter_key`

| Field | Value |
|-------|-------|
| **Purpose** | Verify set.issubset() registers ITER_KEY dependency |
| **Invariants** | After add, issubset-dependent component should re-render |
| **Assertion Coverage** | Yes - render count increases |

#### `TestNewTrackingMethods.test_set_issuperset_tracks_iter_key`

| Field | Value |
|-------|-------|
| **Purpose** | Verify set.issuperset() registers ITER_KEY dependency |
| **Invariants** | After remove, issuperset-dependent component should re-render |
| **Assertion Coverage** | Yes - render count increases |

#### `TestNewTrackingMethods.test_set_isdisjoint_tracks_iter_key`

| Field | Value |
|-------|-------|
| **Purpose** | Verify set.isdisjoint() registers ITER_KEY dependency |
| **Invariants** | After add, isdisjoint-dependent component should re-render |
| **Assertion Coverage** | Yes - render count increases |

#### `TestSliceOperations.test_list_slice_assignment`

| Field | Value |
|-------|-------|
| **Purpose** | Verify slice assignment marks old items and ITER_KEY dirty |
| **Invariants** | Iter component re-renders; Item0 viewer does not (slice is in middle) |
| **Assertion Coverage** | Yes - selective render count check |

#### `TestSliceOperations.test_list_slice_deletion`

| Field | Value |
|-------|-------|
| **Purpose** | Verify slice deletion marks old items and ITER_KEY dirty |
| **Invariants** | After del items[1:3], iter component re-renders and list is correct |
| **Assertion Coverage** | Yes - render count and list content |

#### `TestReverseAndSort.test_list_reverse_marks_iter_dirty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify reverse() marks ITER_KEY dirty |
| **Invariants** | After reverse, iter component re-renders and order is reversed |
| **Assertion Coverage** | Yes - render count and list content |

#### `TestPopWithIndex.test_list_pop_with_index`

| Field | Value |
|-------|-------|
| **Purpose** | Verify pop(i) marks the correct item dirty |
| **Invariants** | Popping index 1 marks item "b" dirty; both viewers re-render |
| **Assertion Coverage** | Yes - render counts and popped value |

#### `TestInPlaceOperators.test_list_iadd`

| Field | Value |
|-------|-------|
| **Purpose** | Verify list += triggers ITER_KEY |
| **Invariants** | After +=, iter component re-renders |
| **Assertion Coverage** | Yes - render count and list content |

#### `TestInPlaceOperators.test_list_imul`

| Field | Value |
|-------|-------|
| **Purpose** | Verify list *= triggers ITER_KEY |
| **Invariants** | After *=2, iter component re-renders and list is doubled |
| **Assertion Coverage** | Yes - render count and list content |

#### `TestInPlaceOperators.test_set_ior`

| Field | Value |
|-------|-------|
| **Purpose** | Verify set |= triggers ITER_KEY |
| **Invariants** | After |=, iter component re-renders |
| **Assertion Coverage** | Yes - render count increases |

#### `TestInPlaceOperators.test_set_iand`

| Field | Value |
|-------|-------|
| **Purpose** | Verify set &= triggers ITER_KEY |
| **Invariants** | After &=, iter component re-renders and set is intersection |
| **Assertion Coverage** | Yes - render count and set content |

#### `TestNegativeIndices.test_list_negative_index_getitem`

| Field | Value |
|-------|-------|
| **Purpose** | Verify negative index access works correctly |
| **Invariants** | items[-1] must track last item; modifying it triggers re-render |
| **Assertion Coverage** | Yes - render count increases |

#### `TestNegativeIndices.test_list_negative_index_setitem`

| Field | Value |
|-------|-------|
| **Purpose** | Verify negative index assignment works correctly |
| **Invariants** | lst[-1] = "z" must modify last element |
| **Assertion Coverage** | Yes - list content check |

#### `TestErrorCases.test_list_remove_missing_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify removing non-existent item raises ValueError |
| **Invariants** | Must raise ValueError |
| **Assertion Coverage** | Yes - pytest.raises |

#### `TestErrorCases.test_list_pop_empty_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify popping from empty list raises IndexError |
| **Invariants** | Must raise IndexError |
| **Assertion Coverage** | Yes - pytest.raises |

#### `TestErrorCases.test_list_index_missing_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify index() on missing item raises ValueError |
| **Invariants** | Must raise ValueError |
| **Assertion Coverage** | Yes - pytest.raises |

#### `TestErrorCases.test_dict_getitem_missing_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify getting missing key raises KeyError |
| **Invariants** | Must raise KeyError |
| **Assertion Coverage** | Yes - pytest.raises |

#### `TestErrorCases.test_set_remove_missing_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify removing non-existent item raises KeyError |
| **Invariants** | Must raise KeyError |
| **Assertion Coverage** | Yes - pytest.raises |

#### `TestPopitem.test_dict_popitem_marks_iter_dirty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify popitem() marks key and ITER_KEY dirty |
| **Invariants** | After popitem, iter component re-renders |
| **Assertion Coverage** | Yes - render count increases |

#### `TestSetUpdate.test_set_update_marks_multiple_items_dirty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify update() marks all new items and ITER_KEY dirty |
| **Invariants** | After update with 3 items, iter component re-renders |
| **Assertion Coverage** | Yes - render count and set content |

#### `TestMultiComponentScenarios.test_two_components_read_same_item`

| Field | Value |
|-------|-------|
| **Purpose** | Verify two components reading same item both re-render on change |
| **Invariants** | Both Component1 and Component2 must re-render |
| **Assertion Coverage** | Yes - both render counts increase |

#### `TestRebinding.test_tracked_list_cannot_rebind_to_different_owner`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TrackedList cannot be assigned to a different Stateful |
| **Invariants** | Must raise ValueError when attempting rebind |
| **Assertion Coverage** | Yes - pytest.raises with message match |

#### `TestRebinding.test_tracked_list_can_copy_to_new_owner`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TrackedList can be copied to a new owner |
| **Invariants** | list() copy creates new TrackedList; different instances, same content |
| **Assertion Coverage** | Yes - identity check and content check |

#### `TestDeeplyNested.test_deeply_nested_list_dict_list`

| Field | Value |
|-------|-------|
| **Purpose** | Verify deeply nested state.a[0]["x"][1] works correctly |
| **Invariants** | All nesting levels must be TrackedX; modification triggers re-render |
| **Assertion Coverage** | Yes - type checks on each level, render count |

#### `TestMutationsOutsideRender.test_mutations_outside_render_work`

| Field | Value |
|-------|-------|
| **Purpose** | Verify mutations outside of render context work fine |
| **Invariants** | All mutation operations must succeed without error |
| **Assertion Coverage** | Yes - implicit (no exception) |

#### `TestMutationsOutsideRender.test_standalone_tracked_then_assign`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TrackedList created standalone can be assigned to Stateful |
| **Invariants** | After assignment, _owner and _attr must be set |
| **Assertion Coverage** | Yes - checks _owner and _attr |

#### `TestSetValueTracking.test_set_contains_with_different_string_objects`

| Field | Value |
|-------|-------|
| **Purpose** | Verify set tracking works with different string objects of same value |
| **Invariants** | Adding "python" triggers re-render even if checking with different string object |
| **Assertion Coverage** | Yes - render count increases |

#### `TestDictSetdefault.test_setdefault_new_key_marks_dirty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify setdefault() with new key marks key and ITER_KEY dirty |
| **Invariants** | Both iter and key-specific components must re-render |
| **Assertion Coverage** | Yes - both render counts increase |

#### `TestDictSetdefault.test_setdefault_existing_key_no_change`

| Field | Value |
|-------|-------|
| **Purpose** | Verify setdefault() with existing key doesn't mark anything dirty |
| **Invariants** | Iter component must not re-render |
| **Assertion Coverage** | Yes - render count unchanged, correct return value |

#### `TestDictUpdateVariants.test_update_with_kwargs`

| Field | Value |
|-------|-------|
| **Purpose** | Verify update() with keyword arguments works correctly |
| **Invariants** | After update(b=2, c=3), iter component re-renders |
| **Assertion Coverage** | Yes - render count and dict content |

#### `TestDictUpdateVariants.test_update_with_iterable`

| Field | Value |
|-------|-------|
| **Purpose** | Verify update() with iterable of tuples works correctly |
| **Invariants** | After update with tuples, iter component re-renders |
| **Assertion Coverage** | Yes - render count and dict content |

#### `TestDictUpdateVariants.test_update_existing_key_no_iter_dirty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify update() of existing key doesn't mark ITER_KEY dirty |
| **Invariants** | Iter component doesn't re-render; key-specific component does |
| **Assertion Coverage** | Yes - selective render count check |

#### `TestSetBulkOperations.test_intersection_update_marks_removed_dirty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify intersection_update() marks removed items dirty |
| **Invariants** | Iter component re-renders; "c" checker re-renders (c was removed) |
| **Assertion Coverage** | Yes - both render counts increase, set content correct |

#### `TestSetBulkOperations.test_difference_update_marks_removed_dirty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify difference_update() marks removed items dirty |
| **Invariants** | "b" checker re-renders (b was removed) |
| **Assertion Coverage** | Yes - render count and set content |

#### `TestSetBulkOperations.test_symmetric_difference_update`

| Field | Value |
|-------|-------|
| **Purpose** | Verify symmetric_difference_update() marks changed items dirty |
| **Invariants** | "b" checker (removed) and "c" checker (added) both re-render |
| **Assertion Coverage** | Yes - both render counts and set content |

#### `TestSetBulkOperations.test_update_multiple_iterables`

| Field | Value |
|-------|-------|
| **Purpose** | Verify update() with multiple iterables works correctly |
| **Invariants** | All items from all iterables must be added |
| **Assertion Coverage** | Yes - set content check |

#### `TestEdgeCasesExtended.test_list_imul_zero_clears`

| Field | Value |
|-------|-------|
| **Purpose** | Verify list *= 0 clears the list |
| **Invariants** | After *= 0, list is empty and iter re-renders |
| **Assertion Coverage** | Yes - render count and list content |

#### `TestEdgeCasesExtended.test_dict_pop_with_default`

| Field | Value |
|-------|-------|
| **Purpose** | Verify pop() with default returns default when key missing |
| **Invariants** | Pop existing returns value; pop missing returns default |
| **Assertion Coverage** | Yes - return values check |

#### `TestEdgeCasesExtended.test_dict_pop_missing_no_dirty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify pop() on missing key with default doesn't mark dirty |
| **Invariants** | Iter component must not re-render |
| **Assertion Coverage** | Yes - render count unchanged |

#### `TestEdgeCasesExtended.test_set_discard_nonexistent_no_dirty`

| Field | Value |
|-------|-------|
| **Purpose** | Verify discard() on non-existent item doesn't trigger reactivity |
| **Invariants** | Iter component must not re-render |
| **Assertion Coverage** | Yes - render count unchanged, set unchanged |

#### `TestEdgeCasesExtended.test_list_index_with_bounds`

| Field | Value |
|-------|-------|
| **Purpose** | Verify index() with start/stop bounds works correctly |
| **Invariants** | index() with bounds must respect those bounds |
| **Assertion Coverage** | Yes - correct indices returned |

#### `TestEdgeCasesExtended.test_list_sort_with_key`

| Field | Value |
|-------|-------|
| **Purpose** | Verify sort() with key parameter works correctly |
| **Invariants** | After sort(key=len), iter re-renders and list is sorted by length |
| **Assertion Coverage** | Yes - render count and list content |

#### `TestEdgeCasesExtended.test_list_sort_with_reverse`

| Field | Value |
|-------|-------|
| **Purpose** | Verify sort() with reverse=True works correctly |
| **Invariants** | After sort(reverse=True), list is in descending order |
| **Assertion Coverage** | Yes - list content check |

#### `TestEdgeCasesExtended.test_list_of_sets_auto_converts`

| Field | Value |
|-------|-------|
| **Purpose** | Verify list containing sets auto-converts sets on assignment |
| **Invariants** | Outer list and inner sets must both be Tracked types |
| **Assertion Coverage** | Yes - type checks on outer and inner |

### Quality Issues
- **Comprehensive coverage**: Excellent coverage of tracked collection behaviors
- **Mixed unit/integration**: Basic tests are unit; reactivity tests are integration
- **Internal access**: Many tests access _deps, _owner, _attr - implementation details
- **Should split**: Unit tests (basics, mutations, errors) vs integration tests (reactivity, render-time)
- **Well-organized**: Tests grouped by concern (basics, auto-conversion, dependency tracking, fine-grained reactivity, etc.)
- **Good edge case coverage**: Negative indices, empty collections, missing keys, bulk operations

---

## tests/test_trellis.py

**Module Under Test**: `trellis.app.entry` (Trellis, _TrellisArgs, _detect_platform, _parse_cli_args)
**Classification**: Unit
**Test Count**: 23
**Target Location**: `tests/py/unit/app/test_entry.py`

### Dependencies
- Real: `Trellis`, `_TrellisArgs`, `_detect_platform`, `_parse_cli_args`, `PlatformType`, `PlatformArgumentError`
- Mocked: `sys.argv` (via unittest.mock.patch), `sys.modules` (for Pyodide detection)

### Fixtures Used
- `requires_pytauri` - pytest.mark.skipif for tests requiring pytauri

### Tests

#### `TestTrellisArgs.test_set_default_stores_value`

| Field | Value |
|-------|-------|
| **Purpose** | Verify set_default() stores value if key not present |
| **Invariants** | set_default() must store value when key is missing |
| **Assertion Coverage** | Yes - get() returns stored value |

#### `TestTrellisArgs.test_set_default_does_not_override`

| Field | Value |
|-------|-------|
| **Purpose** | Verify set_default() does not override existing value |
| **Invariants** | Explicit set() takes precedence over set_default() |
| **Assertion Coverage** | Yes - get() returns original value |

#### `TestTrellisArgs.test_set_marks_explicit`

| Field | Value |
|-------|-------|
| **Purpose** | Verify set() marks value as explicit |
| **Invariants** | is_explicit() must return True for set() values |
| **Assertion Coverage** | Yes - is_explicit() check |

#### `TestTrellisArgs.test_set_default_not_explicit`

| Field | Value |
|-------|-------|
| **Purpose** | Verify set_default() does not mark value as explicit |
| **Invariants** | is_explicit() must return False for set_default() values |
| **Assertion Coverage** | Yes - is_explicit() check |

#### `TestTrellisArgs.test_to_dict_returns_all_values`

| Field | Value |
|-------|-------|
| **Purpose** | Verify to_dict() returns all stored values |
| **Invariants** | Both default and explicit values must be in dict |
| **Assertion Coverage** | Yes - exact dict comparison |

#### `TestTrellisArgs.test_explicit_args_for_platform_server`

| Field | Value |
|-------|-------|
| **Purpose** | Verify explicit_args_for_platform() returns server args |
| **Invariants** | Only host and port should be in server platform args |
| **Assertion Coverage** | Yes - set comparison |

#### `TestTrellisArgs.test_explicit_args_for_platform_desktop`

| Field | Value |
|-------|-------|
| **Purpose** | Verify explicit_args_for_platform() returns desktop args |
| **Invariants** | Only window_title and window_width should be in desktop platform args |
| **Assertion Coverage** | Yes - set comparison |

#### `TestDetectPlatform.test_default_is_server`

| Field | Value |
|-------|-------|
| **Purpose** | Verify default platform is SERVER when not in Pyodide |
| **Invariants** | _detect_platform() must return PlatformType.SERVER by default |
| **Assertion Coverage** | Yes - enum comparison |

#### `TestDetectPlatform.test_pyodide_detected_as_browser`

| Field | Value |
|-------|-------|
| **Purpose** | Verify platform is BROWSER when pyodide module present |
| **Invariants** | _detect_platform() must return PlatformType.BROWSER in Pyodide |
| **Assertion Coverage** | Yes - enum comparison with mocked sys.modules |

#### `TestParseCLIArgs.test_no_args_returns_none_platform`

| Field | Value |
|-------|-------|
| **Purpose** | Verify no CLI args returns None platform |
| **Invariants** | Without CLI args, platform should be None (auto-detect) |
| **Assertion Coverage** | Yes - None check and empty dict |

#### `TestParseCLIArgs.test_platform_server`

| Field | Value |
|-------|-------|
| **Purpose** | Verify --platform=server sets SERVER |
| **Invariants** | CLI arg must set correct platform type |
| **Assertion Coverage** | Yes - enum comparison |

#### `TestParseCLIArgs.test_platform_desktop`

| Field | Value |
|-------|-------|
| **Purpose** | Verify --platform=desktop sets DESKTOP |
| **Invariants** | CLI arg must set correct platform type |
| **Assertion Coverage** | Yes - enum comparison |

#### `TestParseCLIArgs.test_platform_browser`

| Field | Value |
|-------|-------|
| **Purpose** | Verify --platform=browser sets BROWSER |
| **Invariants** | CLI arg must set correct platform type |
| **Assertion Coverage** | Yes - enum comparison |

#### `TestParseCLIArgs.test_desktop_shortcut`

| Field | Value |
|-------|-------|
| **Purpose** | Verify --desktop is shortcut for --platform=desktop |
| **Invariants** | Shortcut must set DESKTOP platform |
| **Assertion Coverage** | Yes - enum comparison |

#### `TestParseCLIArgs.test_desktop_and_platform_conflict`

| Field | Value |
|-------|-------|
| **Purpose** | Verify --desktop and --platform together raises error |
| **Invariants** | Conflicting args must raise PlatformArgumentError |
| **Assertion Coverage** | Yes - pytest.raises with message checks |

#### `TestParseCLIArgs.test_host_arg`

| Field | Value |
|-------|-------|
| **Purpose** | Verify --host is parsed |
| **Invariants** | Host arg must be in returned dict |
| **Assertion Coverage** | Yes - dict content check |

#### `TestParseCLIArgs.test_port_arg`

| Field | Value |
|-------|-------|
| **Purpose** | Verify --port is parsed as int |
| **Invariants** | Port arg must be int in returned dict |
| **Assertion Coverage** | Yes - dict content check with int value |

#### `TestParseCLIArgs.test_unknown_args_ignored`

| Field | Value |
|-------|-------|
| **Purpose** | Verify unknown args are ignored (for app-specific args) |
| **Invariants** | Unknown args must not cause errors or appear in result |
| **Assertion Coverage** | Yes - platform None and empty args dict |

#### `TestTrellisInit.test_default_platform_is_server`

| Field | Value |
|-------|-------|
| **Purpose** | Verify default platform is SERVER |
| **Invariants** | Trellis() without args must use SERVER platform |
| **Assertion Coverage** | Yes - enum comparison |

#### `TestTrellisInit.test_platform_from_constructor_string`

| Field | Value |
|-------|-------|
| **Purpose** | Verify platform can be set as string in constructor |
| **Invariants** | String platform arg must be converted to enum |
| **Assertion Coverage** | Yes - enum comparison (requires pytauri) |

#### `TestTrellisInit.test_platform_from_constructor_enum`

| Field | Value |
|-------|-------|
| **Purpose** | Verify platform can be set as enum in constructor |
| **Invariants** | Enum platform arg must be used directly |
| **Assertion Coverage** | Yes - enum comparison |

#### `TestTrellisInit.test_constructor_overrides_cli`

| Field | Value |
|-------|-------|
| **Purpose** | Verify constructor platform takes precedence over CLI |
| **Invariants** | Constructor arg must override CLI arg |
| **Assertion Coverage** | Yes - enum comparison (requires pytauri) |

#### `TestTrellisInit.test_cli_overrides_detection`

| Field | Value |
|-------|-------|
| **Purpose** | Verify CLI platform takes precedence over auto-detection |
| **Invariants** | CLI arg must override detected platform |
| **Assertion Coverage** | Yes - enum comparison (requires pytauri) |

#### `TestTrellisInit.test_ignore_cli_flag`

| Field | Value |
|-------|-------|
| **Purpose** | Verify ignore_cli=True ignores CLI arguments |
| **Invariants** | With ignore_cli=True, CLI args must be ignored |
| **Assertion Coverage** | Yes - uses default SERVER despite CLI |

#### `TestTrellisInit.test_server_args_with_server_platform`

| Field | Value |
|-------|-------|
| **Purpose** | Verify server args are accepted with server platform |
| **Invariants** | host and port must be accepted for server |
| **Assertion Coverage** | Yes - no exception, correct platform |

#### `TestTrellisInit.test_server_args_with_desktop_platform_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify server args with desktop platform raises error |
| **Invariants** | host arg must be rejected for desktop platform |
| **Assertion Coverage** | Yes - pytest.raises with message checks (requires pytauri) |

#### `TestTrellisInit.test_desktop_args_with_server_platform_raises`

| Field | Value |
|-------|-------|
| **Purpose** | Verify desktop args with server platform raises error |
| **Invariants** | window_title must be rejected for server platform |
| **Assertion Coverage** | Yes - pytest.raises with message checks |

#### `TestTrellisInit.test_cli_args_override_defaults`

| Field | Value |
|-------|-------|
| **Purpose** | Verify CLI args override defaults but not constructor args |
| **Invariants** | CLI port must be used when no constructor port |
| **Assertion Coverage** | Yes - _args.get() check |

#### `TestTrellisInit.test_constructor_args_override_cli`

| Field | Value |
|-------|-------|
| **Purpose** | Verify constructor args take precedence over CLI args |
| **Invariants** | Constructor port must override CLI port |
| **Assertion Coverage** | Yes - _args.get() check |

### Quality Issues
- **Good unit testing**: Tests are well-isolated with mocked sys.argv
- **Conditional tests**: Uses skipif for pytauri-dependent tests
- **Priority testing**: Good coverage of args priority (constructor > CLI > defaults)
- **Internal access**: Tests access `app._args` - internal implementation detail
- **Missing serve() tests**: No tests for the actual serve() method (would require platform mocking)

---

## tests/test_utils.py

**Module Under Test**: `trellis.utils.async_main`, `trellis.utils.log_setup`, `trellis.utils.logger`
**Classification**: Unit
**Test Count**: 8
**Target Location**: `tests/py/unit/utils/test_utils.py`

### Dependencies
- Real: `logging` (standard library), `subprocess` (standard library), `asyncio` (standard library)
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestAsyncMain.test_runs_when_main`

| Field | Value |
|-------|-------|
| **Purpose** | Verify @async_main decorator runs the function when module is `__main__` |
| **Invariants** | When decorated function's module is `__main__`, the function must be executed via asyncio.run() |
| **Assertion Coverage** | Yes - subprocess runs code, checks return code and stdout for "executed" |

#### `TestAsyncMain.test_does_not_run_when_imported`

| Field | Value |
|-------|-------|
| **Purpose** | Verify @async_main does not run when module is imported (not `__main__`) |
| **Invariants** | When imported, decorator must return function without executing it |
| **Assertion Coverage** | Yes - uses nonlocal flag to verify function body never executed |

#### `TestAsyncMain.test_returns_callable`

| Field | Value |
|-------|-------|
| **Purpose** | Verify @async_main returns the original function for later use |
| **Invariants** | Decorated function must be callable and remain a coroutine function |
| **Assertion Coverage** | Yes - checks callable() and asyncio.iscoroutinefunction() |

#### `TestSetupLogging.test_setup_logging_configures_root_logger`

| Field | Value |
|-------|-------|
| **Purpose** | Verify setup_logging configures the root logger with handlers |
| **Invariants** | After setup_logging(), root logger must have handlers and correct level |
| **Assertion Coverage** | Yes - checks len(handlers) > 0 and level == DEBUG |

#### `TestSetupLogging.test_setup_logging_defaults_to_info`

| Field | Value |
|-------|-------|
| **Purpose** | Verify setup_logging defaults to INFO level when no level specified |
| **Invariants** | Default logging level must be INFO |
| **Assertion Coverage** | Yes - checks root.level == logging.INFO |

#### `TestLogger.test_logger_returns_logger_for_caller`

| Field | Value |
|-------|-------|
| **Purpose** | Verify logger import returns a logger named for the importing module |
| **Invariants** | Logger name must equal the importing module's `__name__` |
| **Assertion Coverage** | Yes - checks isinstance(Logger) and name == __name__ |

#### `TestLogger.test_logger_different_per_module`

| Field | Value |
|-------|-------|
| **Purpose** | Verify different modules get different logger names |
| **Invariants** | Each module importing logger gets its own named logger |
| **Assertion Coverage** | Yes - subprocess checks logger.name contains "__main__" |

#### `TestLogger.test_logger_raises_for_unknown_attr`

| Field | Value |
|-------|-------|
| **Purpose** | Verify accessing unknown attributes raises AttributeError |
| **Invariants** | Module __getattr__ must raise AttributeError for non-"logger" attributes |
| **Assertion Coverage** | Yes - pytest.raises with match on attribute name |

### Quality Issues

- **Good isolation**: Tests properly save and restore logger state
- **Subprocess testing**: Uses subprocess for `__main__` context tests - necessary but slower
- **Clear structure**: Each test class focuses on one utility component
- **No mocking needed**: Tests actual behavior without complex dependencies
- **Target structure**: Could be split into three files: `test_async_main.py`, `test_log_setup.py`, `test_logger.py`

---

## tests/test_widgets.py

**Module Under Test**: `trellis.widgets.*`, `trellis.core.rendering`, `trellis.platforms.common.serialization`
**Classification**: Integration
**Test Count**: 97
**Target Location**: `tests/py/integration/widgets/test_widgets.py`

### Dependencies
- Real: `trellis.core.components.composition.component`, `trellis.core.rendering.render`, `trellis.core.rendering.session.RenderSession`, `trellis.platforms.common.serialization.serialize_node`
- Mocked: None

### Fixtures Used
- None (each test creates its own RenderSession)

### Tests

#### `TestLayoutWidgets` (4 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify Column and Row layout widgets render children correctly with props |
| **Invariants** | Layout widgets must contain child elements and pass through props like gap, padding |
| **Assertion Coverage** | Yes - checks component names, child_ids counts, property values |

Tests: `test_column_renders_children`, `test_row_renders_children`, `test_column_with_props`, `test_nested_layout`

#### `TestBasicWidgets` (12 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify Label, Button, and Slider store props and handle callbacks |
| **Invariants** | Widgets must store explicit props; callbacks must be callable and invokable |
| **Assertion Coverage** | Yes - checks property storage, callback invocation, disabled state |

Tests: `test_label_with_text`, `test_label_with_styling`, `test_button_with_text`, `test_button_with_callback`, `test_button_disabled`, `test_slider_with_value`, `test_slider_with_callback`, `test_slider_default_values`, `test_slider_disabled`, `test_slider_custom_range`

#### `TestWidgetSerialization` (3 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify widgets serialize correctly for wire protocol |
| **Invariants** | Serialized output must have correct type, props, and __callback__ format for callbacks |
| **Assertion Coverage** | Yes - checks serialized structure, type names, callback markers |

Tests: `test_serialize_label`, `test_serialize_button_with_callback`, `test_serialize_nested_layout`

#### `TestInputWidgets` (12 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify TextInput, NumberInput, Checkbox, Select store props and callbacks |
| **Invariants** | Input widgets must store value, handle on_change, support disabled state |
| **Assertion Coverage** | Yes - checks properties, callback invocation with values |

Tests: `test_text_input_with_value`, `test_text_input_with_callback`, `test_text_input_disabled`, `test_number_input_with_value`, `test_number_input_with_callback`, `test_number_input_disabled`, `test_checkbox_with_checked`, `test_checkbox_with_callback`, `test_checkbox_disabled`, `test_select_with_options`, `test_select_with_callback`, `test_select_disabled`

#### `TestCardAndDivider` (7 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify Card and Divider widgets render with props and children |
| **Invariants** | Card must accept children and padding; Divider must accept orientation, margin, color |
| **Assertion Coverage** | Yes - checks child rendering, property storage |

Tests: `test_card_renders_children`, `test_card_with_padding`, `test_card_nested_in_layout`, `test_divider_renders`, `test_divider_with_props`, `test_divider_vertical_orientation`, `test_divider_in_layout`

#### `TestHeadingWidget` (5 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify Heading widget stores text, level, color, and style |
| **Invariants** | Heading must store explicit props; defaults handled by React client |
| **Assertion Coverage** | Yes - checks property storage and absence of defaults |

Tests: `test_heading_with_text`, `test_heading_with_level`, `test_heading_with_color`, `test_heading_with_style`, `test_heading_default_level`

#### `TestProgressBarWidget` (6 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify ProgressBar widget stores value, range, loading, and style props |
| **Invariants** | ProgressBar must store explicit props for value, min, max, loading, disabled, color, height, style |
| **Assertion Coverage** | Yes - checks property storage for all prop types |

Tests: `test_progress_bar_with_value`, `test_progress_bar_loading`, `test_progress_bar_disabled`, `test_progress_bar_with_color`, `test_progress_bar_with_height`, `test_progress_bar_with_style`

#### `TestStatusIndicatorWidget` (3 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify StatusIndicator stores status, label, and show_icon props |
| **Invariants** | StatusIndicator must store status type and optional label/icon visibility |
| **Assertion Coverage** | Yes - checks property storage |

Tests: `test_status_indicator_with_status`, `test_status_indicator_with_label`, `test_status_indicator_hide_icon`

#### `TestBadgeWidget` (3 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify Badge widget stores text, variant, and size |
| **Invariants** | Badge must store text and style variants |
| **Assertion Coverage** | Yes - checks property storage |

Tests: `test_badge_with_text`, `test_badge_with_variant`, `test_badge_with_size`

#### `TestTooltipWidget` (3 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify Tooltip renders children and stores content, position, delay |
| **Invariants** | Tooltip must wrap children and store tooltip configuration |
| **Assertion Coverage** | Yes - checks children and property storage |

Tests: `test_tooltip_with_content`, `test_tooltip_with_position`, `test_tooltip_with_delay`

#### `TestTableWidget` (7 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify Table stores columns, data, styles, and custom cell rendering with slot keys |
| **Invariants** | Table must support columns/data, styling options, custom render functions with correct slot IDs |
| **Assertion Coverage** | Yes - checks data structure, CellSlot creation, row key resolution |

Tests: `test_table_with_columns_and_data`, `test_table_with_styling_options`, `test_table_with_custom_cell_render`, `test_table_row_key_from_column`, `test_table_row_key_from_key_field`, `test_table_row_key_from_index`

#### `TestStatWidget` (3 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify Stat widget stores label, value, delta, and size |
| **Invariants** | Stat must store metric display properties |
| **Assertion Coverage** | Yes - checks property storage |

Tests: `test_stat_with_label_and_value`, `test_stat_with_delta`, `test_stat_with_size`

#### `TestTagWidget` (3 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify Tag widget stores text, variant, removable, and on_remove callback |
| **Invariants** | Tag must store text/variant and support removal callback |
| **Assertion Coverage** | Yes - checks properties and callback invocation |

Tests: `test_tag_with_text`, `test_tag_with_variant`, `test_tag_removable_with_callback`

#### `TestChartWidgets` (6 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify chart widgets store data and configuration props |
| **Invariants** | Charts must store data arrays and configuration like height, colors, curve types |
| **Assertion Coverage** | Yes - checks data and config properties |

Tests: `test_time_series_chart_with_data`, `test_line_chart_with_data`, `test_bar_chart_with_data`, `test_area_chart_with_data`, `test_pie_chart_with_data`, `test_sparkline_with_data`

#### `TestIconWidget` (3 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify Icon widget stores name, size, color, and stroke_width |
| **Invariants** | Icon must store icon name and style properties |
| **Assertion Coverage** | Yes - checks property storage |

Tests: `test_icon_with_name`, `test_icon_with_size_and_color`, `test_icon_with_stroke_width`

#### `TestNavigationWidgets` (8 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify Tabs, Tab, Tree, Breadcrumb store props, render children, handle callbacks |
| **Invariants** | Navigation widgets must store selection state, render children, and invoke callbacks |
| **Assertion Coverage** | Yes - checks children, properties, and callback invocation |

Tests: `test_tabs_with_children`, `test_tabs_with_callback`, `test_tab_with_props`, `test_tree_with_data`, `test_tree_with_callbacks`, `test_breadcrumb_with_items`, `test_breadcrumb_with_callback`

#### `TestFeedbackWidgets` (4 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify Callout and Collapsible render children, store props, handle callbacks |
| **Invariants** | Feedback widgets must wrap children and support dismiss/toggle callbacks |
| **Assertion Coverage** | Yes - checks children, properties, and callback invocation |

Tests: `test_callout_with_title_and_intent`, `test_callout_dismissible_with_callback`, `test_collapsible_with_title`, `test_collapsible_with_callback`

#### `TestActionWidgets` (5 tests)

| Field | Value |
|-------|-------|
| **Purpose** | Verify Menu, MenuItem, MenuDivider, Toolbar render children and store props |
| **Invariants** | Action widgets must render children and support props like icon, disabled, shortcut |
| **Assertion Coverage** | Yes - checks children, properties, and callback invocation |

Tests: `test_menu_with_items`, `test_menu_item_with_props`, `test_menu_item_with_callback`, `test_menu_divider_renders`, `test_toolbar_with_children`

### Quality Issues

- **Integration not unit**: All tests use real RenderSession and render() - these are integration tests
- **Repetitive pattern**: Every test follows same pattern: define App component, render, check properties
- **No isolation**: Widgets aren't tested in isolation from rendering system
- **Good coverage**: Comprehensive coverage of all widget types and props
- **Missing edge cases**: No tests for invalid props, missing required props, or error conditions
- **Should consider**: Splitting into widget-specific files (test_layout.py, test_inputs.py, test_charts.py, etc.)
- **Serialization tests**: Should move to a separate serialization test file

---

## tests/integration/test_bundler.py

**Module Under Test**: `trellis.bundler`, `trellis.platforms.server.platform.ServerPlatform`, `trellis.platforms.desktop.platform.DesktopPlatform`
**Classification**: Integration
**Test Count**: 4
**Target Location**: `tests/py/integration/bundler/test_bundler.py`

### Dependencies
- Real: `httpx` (network), `subprocess`, `tarfile`, filesystem
- Mocked: None

### Fixtures Used
- None

### Tests

#### `TestEnsureEsbuild.test_downloads_esbuild_binary`

| Field | Value |
|-------|-------|
| **Purpose** | Verify ensure_esbuild downloads esbuild binary from npm registry and makes it executable |
| **Invariants** | Binary must exist at expected path, match platform, and be executable (st_mode & 0o111) |
| **Assertion Coverage** | Yes - checks exists(), path equality, and executable bit |

#### `TestEnsurePackages.test_downloads_core_packages`

| Field | Value |
|-------|-------|
| **Purpose** | Verify ensure_packages downloads all CORE_PACKAGES from npm registry |
| **Invariants** | Each package must have a directory with package.json in PACKAGES_DIR |
| **Assertion Coverage** | Yes - checks directory exists and package.json exists for each package |

#### `TestServerPlatformBundle.test_builds_bundle`

| Field | Value |
|-------|-------|
| **Purpose** | Verify ServerPlatform.bundle() builds client bundle successfully |
| **Invariants** | bundle.js must exist and have non-zero size after force rebuild |
| **Assertion Coverage** | Yes - checks exists() and st_size > 0 |

#### `TestDesktopPlatformBundle.test_builds_bundle_and_copies_html`

| Field | Value |
|-------|-------|
| **Purpose** | Verify DesktopPlatform.bundle() builds bundle and copies index.html |
| **Invariants** | bundle.js and index.html must exist; HTML must contain root div and script reference |
| **Assertion Coverage** | Yes - checks exists(), st_size, and HTML content patterns |

### Quality Issues

- **Slow tests**: Requires network access to download from npm registry
- **Side effects**: Modifies ~/.cache/trellis directory
- **Platform-dependent**: DesktopPlatform test requires pytauri, properly skipped if missing
- **Good integration tests**: Properly tests the full bundling pipeline
- **Force rebuild**: Tests use force=True to ensure actual build happens
- **Consider**: Adding markers for slow/network tests (@pytest.mark.slow, @pytest.mark.network)
- **Consider**: Mocking network calls for faster, more reliable tests

---

## tests/js/ClientMessageHandler.test.ts

**Module Under Test**: `@common/ClientMessageHandler`
**Classification**: Unit
**Test Count**: 13
**Target Location**: `tests/js/unit/ClientMessageHandler.test.ts`

### Dependencies
- Real: None
- Mocked: `@common/core/store` (store.applyPatches)

### Fixtures Used
- beforeEach: Creates fresh handler with mock callbacks

### Tests

#### `initial state > starts disconnected`

| Field | Value |
|-------|-------|
| **Purpose** | Verify handler starts in disconnected state |
| **Invariants** | New handler must have connectionState="disconnected" |
| **Assertion Coverage** | Yes - asserts getConnectionState() === "disconnected" |

#### `initial state > has no session ID initially`

| Field | Value |
|-------|-------|
| **Purpose** | Verify handler has no session before HELLO_RESPONSE |
| **Invariants** | Session ID must be null until server sends HELLO_RESPONSE |
| **Assertion Coverage** | Yes - asserts getSessionId() === null |

#### `initial state > has no server version initially`

| Field | Value |
|-------|-------|
| **Purpose** | Verify handler has no server version before HELLO_RESPONSE |
| **Invariants** | Server version must be null until server sends HELLO_RESPONSE |
| **Assertion Coverage** | Yes - asserts getServerVersion() === null |

#### `setConnectionState > updates connection state`

| Field | Value |
|-------|-------|
| **Purpose** | Verify setConnectionState updates internal state |
| **Invariants** | Connection state must reflect what was set |
| **Assertion Coverage** | Yes - sets "connecting", asserts getConnectionState() === "connecting" |

#### `setConnectionState > calls onConnectionStateChange callback`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state change triggers callback |
| **Invariants** | onConnectionStateChange must be called with new state |
| **Assertion Coverage** | Yes - asserts callback called with "connecting" |

#### `handleMessage - HELLO_RESPONSE > sets session ID`

| Field | Value |
|-------|-------|
| **Purpose** | Verify HELLO_RESPONSE stores session ID |
| **Invariants** | Session ID from server must be stored and retrievable |
| **Assertion Coverage** | Yes - asserts getSessionId() === "test-session-123" |

#### `handleMessage - HELLO_RESPONSE > sets server version`

| Field | Value |
|-------|-------|
| **Purpose** | Verify HELLO_RESPONSE stores server version |
| **Invariants** | Server version from message must be stored |
| **Assertion Coverage** | Yes - asserts getServerVersion() === "1.2.3" |

#### `handleMessage - HELLO_RESPONSE > sets connection state to connected`

| Field | Value |
|-------|-------|
| **Purpose** | Verify HELLO_RESPONSE transitions to connected state |
| **Invariants** | Receiving HELLO_RESPONSE means connection is established |
| **Assertion Coverage** | Yes - asserts getConnectionState() === "connected" |

#### `handleMessage - HELLO_RESPONSE > calls onConnected callback`

| Field | Value |
|-------|-------|
| **Purpose** | Verify onConnected callback is invoked |
| **Invariants** | Client code must be notified when connection succeeds |
| **Assertion Coverage** | Yes - asserts onConnected called with the message |

#### `handleMessage - HELLO_RESPONSE > calls onConnectionStateChange callback`

| Field | Value |
|-------|-------|
| **Purpose** | Verify state change callback fires on connect |
| **Invariants** | State change must trigger callback even during message handling |
| **Assertion Coverage** | Yes - asserts onConnectionStateChange called with "connected" |

#### `handleMessage - PATCH > calls store.applyPatches with patches`

| Field | Value |
|-------|-------|
| **Purpose** | Verify PATCH messages are forwarded to store |
| **Invariants** | All patches from server must be applied to store |
| **Assertion Coverage** | Yes - asserts store.applyPatches called with exact patches |

#### `handleMessage - ERROR > logs error to console`

| Field | Value |
|-------|-------|
| **Purpose** | Verify errors are logged for debugging |
| **Invariants** | Server errors must be visible in console |
| **Assertion Coverage** | Yes - asserts console.error called with error message |

#### `handleMessage - ERROR > calls onError callback with error and context`

| Field | Value |
|-------|-------|
| **Purpose** | Verify onError callback receives error details |
| **Invariants** | Client code must be able to react to server errors |
| **Assertion Coverage** | Yes - asserts onError called with error string and context |

#### `works without callbacks > handles messages without errors when no callbacks provided`

| Field | Value |
|-------|-------|
| **Purpose** | Verify handler works when callbacks are optional |
| **Invariants** | Handler must not throw when callbacks not provided |
| **Assertion Coverage** | Yes - asserts no exception thrown |

### Quality Issues

- **Good isolation**: Store properly mocked, testing only handler logic
- **Good structure**: Tests organized by functionality (initial state, setConnectionState, handleMessage by type)
- **Good callback testing**: Verifies both state updates and callback invocations
- **Well-named tests**: Names clearly describe expected behavior
- **No issues identified**: Clean unit tests following best practices

---

## tests/js/core/store.test.ts

**Module Under Test**: `@common/core/store` (TrellisStore class)
**Classification**: Unit
**Test Count**: 22
**Target Location**: `tests/js/unit/core/store.test.ts`

### Dependencies
- Real: None
- Mocked: None (tests the store directly)

### Fixtures Used
- beforeEach: Creates fresh TrellisStore instance
- Helper functions: makeElement(), initTree()

### Tests

#### `applyPatches - add (initial tree) > sets root ID from tree`

| Field | Value |
|-------|-------|
| **Purpose** | Verify initial AddPatch with null parent sets root ID |
| **Invariants** | First tree addition must establish root ID |
| **Assertion Coverage** | Yes - asserts getRootId() === "root" |

#### `applyPatches - add (initial tree) > populates node data for single node`

| Field | Value |
|-------|-------|
| **Purpose** | Verify node data is correctly stored from serialized element |
| **Invariants** | Node type, props, and childIds must match input |
| **Assertion Coverage** | Yes - asserts type, props, and childIds match expected values |

#### `applyPatches - add (initial tree) > populates node data recursively`

| Field | Value |
|-------|-------|
| **Purpose** | Verify nested tree structure is fully populated |
| **Invariants** | All descendants must be accessible by ID |
| **Assertion Coverage** | Yes - checks root, e1, e2, e3 all exist with correct data |

#### `applyPatches - add (initial tree) > clears previous data on new tree`

| Field | Value |
|-------|-------|
| **Purpose** | Verify new root replaces entire previous tree |
| **Invariants** | Old nodes must be removed when new root is set |
| **Assertion Coverage** | Yes - asserts old node undefined, new node defined |

#### `applyPatches - update > updates props on existing node`

| Field | Value |
|-------|-------|
| **Purpose** | Verify UpdatePatch modifies specified props |
| **Invariants** | Updated props must change; unspecified props must remain |
| **Assertion Coverage** | Yes - asserts text changed, color unchanged |

#### `applyPatches - update > removes props when set to null`

| Field | Value |
|-------|-------|
| **Purpose** | Verify null in UpdatePatch deletes the prop |
| **Invariants** | null values in patch.props must delete the property |
| **Assertion Coverage** | Yes - asserts color undefined, text unchanged |

#### `applyPatches - update > updates childIds when provided`

| Field | Value |
|-------|-------|
| **Purpose** | Verify UpdatePatch can reorder children |
| **Invariants** | Children array from patch must replace existing childIds |
| **Assertion Coverage** | Yes - asserts childIds order matches patch |

#### `applyPatches - update > creates new object reference on update (immutability)`

| Field | Value |
|-------|-------|
| **Purpose** | Verify update creates new object for React change detection |
| **Invariants** | Node reference must change after update for Object.is checks |
| **Assertion Coverage** | Yes - asserts nodeAfter !== nodeBefore, new props correct |

#### `applyPatches - update > creates new props object on update`

| Field | Value |
|-------|-------|
| **Purpose** | Verify props object reference changes on update |
| **Invariants** | Props object must be new reference for React memoization |
| **Assertion Coverage** | Yes - asserts nodeAfter.props !== propsBefore |

#### `applyPatches - update > warns but continues on unknown node`

| Field | Value |
|-------|-------|
| **Purpose** | Verify graceful handling of update for non-existent node |
| **Invariants** | Unknown node updates must warn, not crash |
| **Assertion Coverage** | Yes - asserts console.warn called with "unknown node" |

#### `applyPatches - add > adds new node to store`

| Field | Value |
|-------|-------|
| **Purpose** | Verify AddPatch creates new node |
| **Invariants** | New node must be accessible after add |
| **Assertion Coverage** | Yes - asserts getNode("e1") defined with correct props |

#### `applyPatches - add > updates parent childIds`

| Field | Value |
|-------|-------|
| **Purpose** | Verify AddPatch updates parent's children array |
| **Invariants** | Parent's childIds must match patch.children |
| **Assertion Coverage** | Yes - asserts root.childIds equals patch.children |

#### `applyPatches - add > creates new parent reference on add (immutability)`

| Field | Value |
|-------|-------|
| **Purpose** | Verify add creates new parent object for React |
| **Invariants** | Parent reference must change when children added |
| **Assertion Coverage** | Yes - asserts parentAfter !== parentBefore |

#### `applyPatches - add > adds nested subtree recursively`

| Field | Value |
|-------|-------|
| **Purpose** | Verify AddPatch with nested children adds all descendants |
| **Invariants** | Container and all nested children must be accessible |
| **Assertion Coverage** | Yes - checks container childIds and nested children props |

#### `applyPatches - remove > removes node from store`

| Field | Value |
|-------|-------|
| **Purpose** | Verify RemovePatch deletes the node |
| **Invariants** | Removed node must be undefined after patch |
| **Assertion Coverage** | Yes - asserts getNode("e2") undefined after remove |

#### `applyPatches - remove > removes descendants recursively`

| Field | Value |
|-------|-------|
| **Purpose** | Verify remove deletes entire subtree |
| **Invariants** | Removed node and all descendants must be undefined |
| **Assertion Coverage** | Yes - asserts e1, e2, e3 all undefined after removing e1 |

#### `subscriptions > notifies node listener on update`

| Field | Value |
|-------|-------|
| **Purpose** | Verify subscribed listeners are called on update |
| **Invariants** | Node listeners must be notified when node changes |
| **Assertion Coverage** | Yes - asserts listener called once |

#### `subscriptions > does not notify unrelated node listeners`

| Field | Value |
|-------|-------|
| **Purpose** | Verify listeners only fire for their subscribed node |
| **Invariants** | Listeners must be node-specific, not broadcast |
| **Assertion Coverage** | Yes - asserts e1 listener called, root listener not called |

#### `subscriptions > unsubscribes correctly`

| Field | Value |
|-------|-------|
| **Purpose** | Verify unsubscribe stops notifications |
| **Invariants** | Unsubscribed listeners must not be called |
| **Assertion Coverage** | Yes - asserts listener not called after unsubscribe |

#### `subscriptions > notifies global listeners on initial tree via AddPatch`

| Field | Value |
|-------|-------|
| **Purpose** | Verify global subscribers notified on tree set |
| **Invariants** | Global listeners must fire on any store change |
| **Assertion Coverage** | Yes - asserts global listener called on initial add |

#### `subscriptions > notifies global listeners on patches`

| Field | Value |
|-------|-------|
| **Purpose** | Verify global listeners fire on patch application |
| **Invariants** | Any patch must trigger global notification |
| **Assertion Coverage** | Yes - asserts listener called on update patch |

#### `subscriptions > cleans up node listeners on remove`

| Field | Value |
|-------|-------|
| **Purpose** | Verify removed nodes don't retain stale listeners |
| **Invariants** | Listeners for removed nodes must be cleaned up |
| **Assertion Coverage** | Yes - asserts listener not called after node removed |

### Quality Issues

- **Excellent isolation**: Pure unit tests with no external dependencies
- **Good immutability testing**: Explicitly tests reference changes for React compatibility
- **Comprehensive coverage**: Tests all patch types (add, update, remove) and subscriptions
- **Good regression test**: Includes comment about React's useSyncExternalStore requirements
- **Well-organized**: Tests grouped by functionality
- **No issues identified**: Clean, well-structured unit tests

---

## tests/js/core/types.test.ts

**Module Under Test**: `@common/core/types` (isCallbackRef, ElementKind)
**Classification**: Unit
**Test Count**: 5
**Target Location**: `tests/js/unit/core/types.test.ts`

### Dependencies
- Real: None
- Mocked: None

### Fixtures Used
- None

### Tests

#### `isCallbackRef > returns true for valid callback refs`

| Field | Value |
|-------|-------|
| **Purpose** | Verify type guard correctly identifies CallbackRef objects |
| **Invariants** | Objects with string __callback__ property must return true |
| **Assertion Coverage** | Yes - tests { __callback__: "cb_123" } and { __callback__: "" } |

#### `isCallbackRef > returns false for non-objects`

| Field | Value |
|-------|-------|
| **Purpose** | Verify type guard rejects primitives |
| **Invariants** | null, undefined, string, number, boolean must return false |
| **Assertion Coverage** | Yes - tests null, undefined, "string", 123, true |

#### `isCallbackRef > returns false for objects without __callback__`

| Field | Value |
|-------|-------|
| **Purpose** | Verify type guard requires __callback__ property |
| **Invariants** | Objects missing __callback__ must return false |
| **Assertion Coverage** | Yes - tests {}, { callback: ... }, { other: ... } |

#### `isCallbackRef > returns false when __callback__ is not a string`

| Field | Value |
|-------|-------|
| **Purpose** | Verify type guard validates __callback__ type |
| **Invariants** | __callback__ must be string, not number/null/object |
| **Assertion Coverage** | Yes - tests __callback__ as 123, null, {} |

#### `ElementKind > has expected values matching Python ElementKind`

| Field | Value |
|-------|-------|
| **Purpose** | Verify JS enum values match Python enum for protocol compatibility |
| **Invariants** | Enum values must be "react_component", "jsx_element", "text" |
| **Assertion Coverage** | Yes - asserts all three enum values match expected strings |

### Quality Issues

- **Good isolation**: Pure type guard tests, no side effects
- **Good boundary testing**: Tests edge cases for type guard (null, undefined, wrong types)
- **Cross-language validation**: ElementKind test ensures Python-JS protocol compatibility
- **Simple and focused**: Each test verifies one specific behavior
- **No issues identified**: Clean, minimal unit tests

---

## tests/js/core/renderTree.test.tsx

**Module Under Test**: `@common/core/renderTree` (processProps, renderNode)
**Classification**: Unit (with React Testing Library for rendering)
**Test Count**: 14
**Target Location**: `tests/js/unit/core/renderTree.test.tsx`

### Dependencies
- Real: React, @testing-library/react
- Mocked: getWidget (widget registry function)

### Fixtures Used
- beforeEach: Clears mocks
- test-utils: Custom render wrapper from ../test-utils

### Tests

#### `processProps > passes through regular props unchanged`

| Field | Value |
|-------|-------|
| **Purpose** | Verify non-callback props are preserved |
| **Invariants** | Regular props (text, number, boolean, array) must pass through |
| **Assertion Coverage** | Yes - asserts result equals input props, onEvent not called |

#### `processProps > converts callback refs to functions`

| Field | Value |
|-------|-------|
| **Purpose** | Verify CallbackRef objects become functions |
| **Invariants** | { __callback__: id } must become executable function |
| **Assertion Coverage** | Yes - asserts typeof result.on_click === "function" |

#### `processProps > calls onEvent when callback function is invoked`

| Field | Value |
|-------|-------|
| **Purpose** | Verify callback functions trigger onEvent |
| **Invariants** | Invoking callback must call onEvent with callback ID |
| **Assertion Coverage** | Yes - asserts onEvent called with ("cb_456", []) |

#### `processProps > passes arguments through to onEvent`

| Field | Value |
|-------|-------|
| **Purpose** | Verify callback arguments are forwarded |
| **Invariants** | Arguments passed to callback must reach onEvent |
| **Assertion Coverage** | Yes - asserts onEvent called with ("cb_789", ["new value"]) |

#### `processProps > handles multiple callback refs in same props`

| Field | Value |
|-------|-------|
| **Purpose** | Verify multiple callbacks can coexist |
| **Invariants** | Each callback must independently invoke onEvent |
| **Assertion Coverage** | Yes - verifies both callbacks work, each calls onEvent correctly |

#### `renderNode > renders text nodes`

| Field | Value |
|-------|-------|
| **Purpose** | Verify TEXT kind elements render text content |
| **Invariants** | _text prop must become visible text in DOM |
| **Assertion Coverage** | Yes - asserts "Hello World" in document |

#### `renderNode > renders JSX elements (HTML tags)`

| Field | Value |
|-------|-------|
| **Purpose** | Verify JSX_ELEMENT kind creates HTML elements |
| **Invariants** | type: "div" with className must create styled div |
| **Assertion Coverage** | Yes - asserts .test-class element in document |

#### `renderNode > renders JSX elements with _text content`

| Field | Value |
|-------|-------|
| **Purpose** | Verify HTML elements with _text prop show text |
| **Invariants** | _text on JSX_ELEMENT must become element content |
| **Assertion Coverage** | Yes - asserts "Paragraph text" in document |

#### `renderNode > renders nested children`

| Field | Value |
|-------|-------|
| **Purpose** | Verify recursive child rendering |
| **Invariants** | Children array must be rendered inside parent |
| **Assertion Coverage** | Yes - asserts both "Child 1" and "Child 2" in document |

#### `renderNode > renders custom widgets from registry`

| Field | Value |
|-------|-------|
| **Purpose** | Verify REACT_COMPONENT kind uses widget registry |
| **Invariants** | getWidget must be called, returned component must render |
| **Assertion Coverage** | Yes - asserts getWidget called with type, widget content visible |

#### `renderNode > renders warning for unknown components`

| Field | Value |
|-------|-------|
| **Purpose** | Verify graceful handling of missing widgets |
| **Invariants** | Unknown components must show helpful error message |
| **Assertion Coverage** | Yes - asserts "Unknown component: UnknownWidget" visible |

#### `renderNode > passes children to custom widgets`

| Field | Value |
|-------|-------|
| **Purpose** | Verify widget children are passed correctly |
| **Invariants** | children prop must contain rendered child elements |
| **Assertion Coverage** | Yes - asserts container has "Child content" |

#### `renderNode > processes callback refs in widget props`

| Field | Value |
|-------|-------|
| **Purpose** | Verify callbacks work in custom widget props |
| **Invariants** | CallbackRefs in widget props must become working functions |
| **Assertion Coverage** | Yes - clicks button, asserts onEvent called with callback ID |

### Quality Issues

- **Good isolation for processProps**: Pure function tests without rendering
- **Good React integration**: Uses Testing Library for renderNode tests
- **Comprehensive coverage**: Tests all ElementKind types (TEXT, JSX_ELEMENT, REACT_COMPONENT)
- **Good error handling test**: Verifies unknown component shows helpful message
- **Callback flow tested**: Full path from prop to function to onEvent verified
- **Minor issue**: renderTree.test.tsx should import React (currently works due to JSX transform but explicit import is clearer)
- **No major issues**: Well-structured tests covering core rendering logic
