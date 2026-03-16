"""Source-to-source unit tests for the state_var AST transform."""

from __future__ import annotations

import textwrap

from trellis.core.transforms.state_var import transform_source as transform_component_source


def _t(source: str) -> str:
    """Transform dedented source, return dedented result."""
    result, changed = transform_component_source(textwrap.dedent(source))
    assert changed
    return result


def _unchanged(source: str) -> None:
    """Assert that the source is returned unchanged."""
    dedented = textwrap.dedent(source)
    result, changed = transform_component_source(dedented)
    assert not changed
    assert result == dedented


class TestDetection:
    def test_positional_state_var(self) -> None:
        result = _t("""\
            def App():
                count = state_var(0)
                f(count)
        """)
        assert "f(count.value)" in result

    def test_factory_state_var(self) -> None:
        result = _t("""\
            def App():
                items = state_var(factory=list)
                f(items)
        """)
        assert "f(items.value)" in result

    def test_annotated_state_var(self) -> None:
        result = _t("""\
            def App():
                count: int = state_var(0)
                f(count)
        """)
        assert "f(count.value)" in result

    def test_multiple_state_vars(self) -> None:
        result = _t("""\
            def App():
                a = state_var(0)
                b = state_var("x")
                f(a, b)
        """)
        assert "f(a.value, b.value)" in result

    def test_non_state_var_untouched(self) -> None:
        result = _t("""\
            def App():
                count = state_var(0)
                other = 42
                f(count, other)
        """)
        assert "f(count.value, other)" in result


class TestRewriting:
    def test_read(self) -> None:
        result = _t("""\
            def App():
                x = state_var(0)
                f(x)
        """)
        assert "f(x.value)" in result

    def test_write(self) -> None:
        result = _t("""\
            def App():
                x = state_var(0)
                x = 3
        """)
        assert "x.value = 3" in result

    def test_augmented_assign(self) -> None:
        result = _t("""\
            def App():
                x = state_var(0)
                x += 1
        """)
        assert "x.value += 1" in result

    def test_fstring(self) -> None:
        result = _t("""\
            def App():
                name = state_var("Ada")
                s = f"Hello, {name}"
        """)
        assert 'f"Hello, {name.value}"' in result

    def test_attribute_chain(self) -> None:
        result = _t("""\
            def App():
                name = state_var("Ada")
                name.lower()
        """)
        assert "name.value.lower()" in result

    def test_mutable_call(self) -> None:
        result = _t("""\
            def App():
                text = state_var("")
                mutable(text)
        """)
        assert "mutable(text.value)" in result


class TestBindingTarget:
    def test_initial_binding_preserved(self) -> None:
        result = _t("""\
            def App():
                count = state_var(0)
                count = 3
        """)
        assert "count = state_var(0)" in result
        assert "count.value = 3" in result

    def test_annotated_binding_preserved(self) -> None:
        result = _t("""\
            def App():
                count: int = state_var(0)
                count = 3
        """)
        assert "count: int = state_var(0)" in result
        assert "count.value = 3" in result


class TestClosures:
    def test_nested_def(self) -> None:
        result = _t("""\
            def App():
                count = state_var(0)
                def increment():
                    count = count + 1
        """)
        assert "count.value = count.value + 1" in result

    def test_nonlocal_preserved(self) -> None:
        result = _t("""\
            def App():
                count = state_var(0)
                def increment():
                    nonlocal count
                    count = count + 1
        """)
        assert "nonlocal count\n" in result
        assert "count.value = count.value + 1" in result

    def test_lambda(self) -> None:
        result = _t("""\
            def App():
                count = state_var(0)
                f(lambda: count + 1)
        """)
        assert "lambda: count.value + 1" in result


class TestDecoratorStripping:
    def test_bare_decorator_stripped(self) -> None:
        result = _t("""\
            @component
            def App():
                x = state_var(0)
                f(x)
        """)
        assert "@component" not in result
        assert "def App():" in result

    def test_parameterized_decorator_stripped(self) -> None:
        result = _t("""\
            @component(is_container=True)
            def App(children):
                x = state_var(0)
                f(x)
        """)
        assert "@component" not in result
        assert "def App(children):" in result


class TestNoStateVars:
    def test_no_state_vars_returns_unchanged(self) -> None:
        _unchanged("""\
            def App():
                w.Label(text="hello")
        """)

    def test_no_function_returns_unchanged(self) -> None:
        _unchanged("""\
            x = 42
        """)


class TestWhitespace:
    def test_comments_preserved(self) -> None:
        result = _t("""\
            def App():
                # A counter
                count = state_var(0)
                f(count)  # use it
        """)
        assert "# A counter" in result
        assert "# use it" in result

    def test_blank_lines_preserved(self) -> None:
        result = _t("""\
            def App():
                count = state_var(0)

                f(count)
        """)
        lines = result.strip().split("\n")
        # Should have a blank line between the assignment and f(count.value)
        assert any(line.strip() == "" for line in lines)


class TestKeywordArguments:
    def test_keyword_arg_name_not_transformed(self) -> None:
        result = _t("""\
            def App():
                count = state_var(0)
                Counter(count=count)
        """)
        # The keyword name 'count' stays, but the value 'count' gets .value
        assert "Counter(count=count.value)" in result

    def test_keyword_arg_value_transformed(self) -> None:
        result = _t("""\
            def App():
                x = state_var(0)
                f(value=x)
        """)
        assert "f(value=x.value)" in result


class TestSelfReferential:
    def test_self_referential_state_var_init(self) -> None:
        """state_var(count) where count is also the binding name should not transform RHS."""
        result = _t("""\
            def App(count: int):
                count = state_var(count)
                f(count)
        """)
        assert "state_var(count)" in result  # RHS count is NOT transformed
        assert "f(count.value)" in result  # subsequent reads ARE transformed

    def test_self_referential_annotated(self) -> None:
        """Annotated form: count: T = state_var(count) should not transform RHS."""
        result = _t("""\
            def App(count: int):
                count: int = state_var(count)
                f(count)
        """)
        assert "state_var(count)" in result
        assert "f(count.value)" in result


class TestEdgeCases:
    def test_state_var_in_rhs_of_non_state_var_assignment(self) -> None:
        """state_var() on the RHS of a non-Name target should not break."""
        _unchanged("""\
            def App():
                d = {}
                d["key"] = state_var(0)
        """)

    def test_multi_target_assignment_not_transformed(self) -> None:
        """a = b = expr with state var name should not crash."""
        result = _t("""\
            def App():
                x = state_var(0)
                a = b = x
        """)
        # The multi-target `a = b = x` should have x transformed to x.value
        # but the targets a, b should not be transformed (they're not state vars)
        assert "x.value" in result
