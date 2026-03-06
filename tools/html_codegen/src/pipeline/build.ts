import type { AttributeDef, ElementDef, IrDocument, SourceProvenance, TypeExpr } from "../ir/types.js";
import { extract_react_surface } from "../sources/react_ts.js";

function react_source(): SourceProvenance {
  return {
    winner: "react_ts",
    contributors: ["react_ts"],
    reason: "runtime_precedence",
    source_version: "@types/react@19.2.14",
  };
}

function primitive(name: "str" | "int" | "float" | "bool" | "none"): TypeExpr {
  return { kind: "primitive", name };
}

function nullable(item: TypeExpr): TypeExpr {
  return { kind: "nullable", item };
}

function reference(name: string): TypeExpr {
  return { kind: "reference", name };
}

function union(...options: TypeExpr[]): TypeExpr {
  return { kind: "union", options };
}

function standard_attribute(
  id: string,
  name_source: string,
  name_python: string,
  type_expr: TypeExpr,
): AttributeDef {
  return {
    id,
    name_source,
    name_python,
    applies_to: "element",
    type_expr,
    required: false,
    category: "standard",
    source: react_source(),
  };
}

function global_attribute(
  id: string,
  name_source: string,
  name_python: string,
  type_expr: TypeExpr,
): AttributeDef {
  return {
    id,
    name_source,
    name_python,
    applies_to: "global",
    type_expr,
    required: false,
    category: "standard",
    source: react_source(),
  };
}

function element(
  tag_name: string,
  python_name: string,
  is_container: boolean,
  attributes: string[],
): ElementDef {
  return {
    namespace: "html",
    tag_name,
    python_name,
    is_container,
    attributes,
    events: [],
    source: react_source(),
  };
}

export async function build_ir_document(): Promise<IrDocument> {
  const react_surface = await extract_react_surface();
  const input_type_expr =
    react_surface.elements.get("input")?.attributes.get("type") ?? primitive("str");

  const attributes: AttributeDef[] = [
    global_attribute("html:global:class_name", "className", "class_name", nullable(primitive("str"))),
    global_attribute("html:global:style", "style", "style", nullable(reference("Style"))),
    global_attribute("html:global:id", "id", "id", nullable(primitive("str"))),

    standard_attribute("html:a:href", "href", "href", nullable(primitive("str"))),
    standard_attribute("html:a:target", "target", "target", nullable(primitive("str"))),
    standard_attribute("html:a:rel", "rel", "rel", nullable(primitive("str"))),
    standard_attribute(
      "html:a:download",
      "download",
      "download",
      nullable(union(primitive("str"), primitive("bool"))),
    ),
    standard_attribute(
      "html:a:on_click",
      "onClick",
      "on_click",
      nullable(reference("MouseHandler")),
    ),
    standard_attribute(
      "html:a:on_double_click",
      "onDoubleClick",
      "on_double_click",
      nullable(reference("MouseHandler")),
    ),
    standard_attribute(
      "html:a:on_context_menu",
      "onContextMenu",
      "on_context_menu",
      nullable(reference("MouseHandler")),
    ),
    standard_attribute(
      "html:a:on_key_down",
      "onKeyDown",
      "on_key_down",
      nullable(reference("KeyboardHandler")),
    ),
    standard_attribute(
      "html:a:on_key_up",
      "onKeyUp",
      "on_key_up",
      nullable(reference("KeyboardHandler")),
    ),

    standard_attribute("html:div:on_click", "onClick", "on_click", nullable(reference("MouseHandler"))),
    standard_attribute(
      "html:div:on_double_click",
      "onDoubleClick",
      "on_double_click",
      nullable(reference("MouseHandler")),
    ),
    standard_attribute(
      "html:div:on_context_menu",
      "onContextMenu",
      "on_context_menu",
      nullable(reference("MouseHandler")),
    ),
    standard_attribute(
      "html:div:on_mouse_enter",
      "onMouseEnter",
      "on_mouse_enter",
      nullable(reference("MouseHandler")),
    ),
    standard_attribute(
      "html:div:on_mouse_leave",
      "onMouseLeave",
      "on_mouse_leave",
      nullable(reference("MouseHandler")),
    ),
    standard_attribute(
      "html:div:on_key_down",
      "onKeyDown",
      "on_key_down",
      nullable(reference("KeyboardHandler")),
    ),
    standard_attribute(
      "html:div:on_key_up",
      "onKeyUp",
      "on_key_up",
      nullable(reference("KeyboardHandler")),
    ),
    standard_attribute(
      "html:div:on_scroll",
      "onScroll",
      "on_scroll",
      nullable(reference("ScrollHandler")),
    ),
    standard_attribute(
      "html:div:on_wheel",
      "onWheel",
      "on_wheel",
      nullable(reference("WheelHandler")),
    ),
    standard_attribute(
      "html:div:on_drag_start",
      "onDragStart",
      "on_drag_start",
      nullable(reference("DragHandler")),
    ),
    standard_attribute("html:div:on_drag", "onDrag", "on_drag", nullable(reference("DragHandler"))),
    standard_attribute(
      "html:div:on_drag_end",
      "onDragEnd",
      "on_drag_end",
      nullable(reference("DragHandler")),
    ),
    standard_attribute(
      "html:div:on_drag_enter",
      "onDragEnter",
      "on_drag_enter",
      nullable(reference("DragHandler")),
    ),
    standard_attribute(
      "html:div:on_drag_over",
      "onDragOver",
      "on_drag_over",
      nullable(reference("DragHandler")),
    ),
    standard_attribute(
      "html:div:on_drag_leave",
      "onDragLeave",
      "on_drag_leave",
      nullable(reference("DragHandler")),
    ),
    standard_attribute("html:div:on_drop", "onDrop", "on_drop", nullable(reference("DragHandler"))),

    standard_attribute("html:img:src", "src", "src", primitive("str")),
    standard_attribute("html:img:alt", "alt", "alt", nullable(primitive("str"))),
    standard_attribute(
      "html:img:width",
      "width",
      "width",
      nullable(union(primitive("int"), primitive("str"))),
    ),
    standard_attribute(
      "html:img:height",
      "height",
      "height",
      nullable(union(primitive("int"), primitive("str"))),
    ),
    standard_attribute("html:img:loading", "loading", "loading", nullable(primitive("str"))),
    standard_attribute(
      "html:img:on_click",
      "onClick",
      "on_click",
      nullable(reference("MouseHandler")),
    ),
    standard_attribute(
      "html:img:on_double_click",
      "onDoubleClick",
      "on_double_click",
      nullable(reference("MouseHandler")),
    ),
    standard_attribute(
      "html:img:on_context_menu",
      "onContextMenu",
      "on_context_menu",
      nullable(reference("MouseHandler")),
    ),

    standard_attribute("html:input:type", "type", "type", input_type_expr),
    standard_attribute("html:input:value", "value", "value", nullable(primitive("str"))),
    standard_attribute(
      "html:input:placeholder",
      "placeholder",
      "placeholder",
      nullable(primitive("str")),
    ),
    standard_attribute("html:input:disabled", "disabled", "disabled", primitive("bool")),
    standard_attribute("html:input:read_only", "readOnly", "read_only", primitive("bool")),
    standard_attribute("html:input:name", "name", "name", nullable(primitive("str"))),
    standard_attribute("html:input:checked", "checked", "checked", nullable(primitive("bool"))),
    standard_attribute("html:input:required", "required", "required", primitive("bool")),
    standard_attribute(
      "html:input:min",
      "min",
      "min",
      nullable(union(primitive("str"), primitive("int"), primitive("float"))),
    ),
    standard_attribute(
      "html:input:max",
      "max",
      "max",
      nullable(union(primitive("str"), primitive("int"), primitive("float"))),
    ),
    standard_attribute(
      "html:input:step",
      "step",
      "step",
      nullable(union(primitive("str"), primitive("int"), primitive("float"))),
    ),
    standard_attribute("html:input:pattern", "pattern", "pattern", nullable(primitive("str"))),
    standard_attribute("html:input:max_length", "maxLength", "max_length", nullable(primitive("int"))),
    standard_attribute(
      "html:input:auto_complete",
      "autoComplete",
      "auto_complete",
      nullable(primitive("str")),
    ),
    standard_attribute("html:input:auto_focus", "autoFocus", "auto_focus", primitive("bool")),
    standard_attribute("html:input:accept", "accept", "accept", nullable(primitive("str"))),
    standard_attribute("html:input:multiple", "multiple", "multiple", primitive("bool")),
    standard_attribute(
      "html:input:on_change",
      "onChange",
      "on_change",
      nullable(reference("ChangeHandler")),
    ),
    standard_attribute(
      "html:input:on_input",
      "onInput",
      "on_input",
      nullable(reference("InputHandler")),
    ),
    standard_attribute(
      "html:input:on_focus",
      "onFocus",
      "on_focus",
      nullable(reference("FocusHandler")),
    ),
    standard_attribute(
      "html:input:on_blur",
      "onBlur",
      "on_blur",
      nullable(reference("FocusHandler")),
    ),
    standard_attribute(
      "html:input:on_key_down",
      "onKeyDown",
      "on_key_down",
      nullable(reference("KeyboardHandler")),
    ),
    standard_attribute(
      "html:input:on_key_up",
      "onKeyUp",
      "on_key_up",
      nullable(reference("KeyboardHandler")),
    ),
  ];

  return {
    elements: [
      element("a", "A", true, [
        "html:a:href",
        "html:a:target",
        "html:a:rel",
        "html:a:download",
        "html:global:class_name",
        "html:global:style",
        "html:global:id",
        "html:a:on_click",
        "html:a:on_double_click",
        "html:a:on_context_menu",
        "html:a:on_key_down",
        "html:a:on_key_up",
      ]),
      element("div", "Div", true, [
        "html:global:class_name",
        "html:global:style",
        "html:global:id",
        "html:div:on_click",
        "html:div:on_double_click",
        "html:div:on_context_menu",
        "html:div:on_mouse_enter",
        "html:div:on_mouse_leave",
        "html:div:on_key_down",
        "html:div:on_key_up",
        "html:div:on_scroll",
        "html:div:on_wheel",
        "html:div:on_drag_start",
        "html:div:on_drag",
        "html:div:on_drag_end",
        "html:div:on_drag_enter",
        "html:div:on_drag_over",
        "html:div:on_drag_leave",
        "html:div:on_drop",
      ]),
      element("img", "Img", false, [
        "html:img:src",
        "html:img:alt",
        "html:img:width",
        "html:img:height",
        "html:img:loading",
        "html:global:class_name",
        "html:global:style",
        "html:global:id",
        "html:img:on_click",
        "html:img:on_double_click",
        "html:img:on_context_menu",
      ]),
      element("input", "Input", false, [
        "html:input:type",
        "html:input:value",
        "html:input:placeholder",
        "html:input:disabled",
        "html:input:read_only",
        "html:input:name",
        "html:input:checked",
        "html:input:required",
        "html:input:min",
        "html:input:max",
        "html:input:step",
        "html:input:pattern",
        "html:input:max_length",
        "html:input:auto_complete",
        "html:input:auto_focus",
        "html:input:accept",
        "html:input:multiple",
        "html:input:on_change",
        "html:input:on_input",
        "html:input:on_focus",
        "html:input:on_blur",
        "html:input:on_key_down",
        "html:input:on_key_up",
        "html:global:class_name",
        "html:global:style",
        "html:global:id",
      ]),
    ],
    attributes,
    events: [],
    attribute_patterns: [
      {
        name: "data",
        python_param_name: "data",
        dom_prefix: "data-",
        key_style: "dom_suffix",
        value_type_expr: union(
          primitive("str"),
          primitive("int"),
          primitive("float"),
          primitive("bool"),
          primitive("none"),
        ),
      },
    ],
  };
}
