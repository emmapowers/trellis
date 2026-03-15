import type { TypeExpr } from "../../ir/types.js";

function render_literal(value: string | number | boolean | null): string {
  if (typeof value === "string") {
    return `"${value}"`;
  }
  if (value === null) {
    return "None";
  }
  return String(value);
}

export function render_type_expr(type_expr: TypeExpr): string {
  switch (type_expr.kind) {
    case "literal":
      return `Literal[${render_literal(type_expr.value)}]`;
    case "primitive":
      if (type_expr.name === "str") return "str";
      if (type_expr.name === "int") return "int";
      if (type_expr.name === "float") return "float";
      if (type_expr.name === "bool") return "bool";
      return "None";
    case "union":
      if (type_expr.options.every((option) => option.kind === "literal")) {
        return `Literal[${type_expr.options
          .map((option) => render_literal(option.value))
          .join(", ")}]`;
      }
      return type_expr.options.map((option) => render_type_expr(option)).join(" | ");
    case "array":
      return `list[${render_type_expr(type_expr.item)}]`;
    case "reference":
      return type_expr.name;
    case "style_object":
      return "StyleInput";
    case "nullable":
      return `${render_type_expr(type_expr.item)} | None`;
    case "callable":
      return "Callable[..., Any]";
    case "object":
      return "dict[str, Any]";
    default:
      return "Any";
  }
}
