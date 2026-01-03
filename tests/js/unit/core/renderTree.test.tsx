import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen } from "../../test-utils";
import { processProps, renderNode } from "@common/core/renderTree";
import { ElementKind, SerializedElement } from "@common/core/types";

describe("processProps", () => {
  it("passes through regular props unchanged", () => {
    const onEvent = vi.fn();
    const props = {
      text: "Hello",
      count: 42,
      enabled: true,
      items: [1, 2, 3],
    };

    const result = processProps(props, onEvent);

    expect(result).toEqual(props);
    expect(onEvent).not.toHaveBeenCalled();
  });

  it("converts callback refs to functions", () => {
    const onEvent = vi.fn();
    const props = {
      text: "Hello",
      on_click: { __callback__: "cb_123" },
    };

    const result = processProps(props, onEvent);

    expect(result.text).toBe("Hello");
    expect(typeof result.on_click).toBe("function");
  });

  it("calls onEvent when callback function is invoked", () => {
    const onEvent = vi.fn();
    const props = {
      on_click: { __callback__: "cb_456" },
    };

    const result = processProps(props, onEvent);
    (result.on_click as () => void)();

    expect(onEvent).toHaveBeenCalledWith("cb_456", []);
  });

  it("passes arguments through to onEvent", () => {
    const onEvent = vi.fn();
    const props = {
      on_change: { __callback__: "cb_789" },
    };

    const result = processProps(props, onEvent);
    (result.on_change as (value: string) => void)("new value");

    expect(onEvent).toHaveBeenCalledWith("cb_789", ["new value"]);
  });

  it("handles multiple callback refs in same props", () => {
    const onEvent = vi.fn();
    const props = {
      on_click: { __callback__: "cb_1" },
      on_hover: { __callback__: "cb_2" },
      label: "Test",
    };

    const result = processProps(props, onEvent);

    expect(typeof result.on_click).toBe("function");
    expect(typeof result.on_hover).toBe("function");
    expect(result.label).toBe("Test");

    (result.on_click as () => void)();
    expect(onEvent).toHaveBeenCalledWith("cb_1", []);

    (result.on_hover as () => void)();
    expect(onEvent).toHaveBeenCalledWith("cb_2", []);
  });

  it("calls preventDefault on onClick handlers", () => {
    const onEvent = vi.fn();
    const props = {
      onClick: { __callback__: "cb_click" },
    };

    const result = processProps(props, onEvent);

    const mockEvent = {
      preventDefault: vi.fn(),
      type: "click",
    };

    (result.onClick as (e: unknown) => void)(mockEvent);

    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(onEvent).toHaveBeenCalledWith("cb_click", [expect.anything()]);
  });

  it("calls preventDefault on onSubmit handlers", () => {
    const onEvent = vi.fn();
    const props = {
      onSubmit: { __callback__: "cb_submit" },
    };

    const result = processProps(props, onEvent);

    const mockEvent = {
      preventDefault: vi.fn(),
      type: "submit",
    };

    (result.onSubmit as (e: unknown) => void)(mockEvent);

    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(onEvent).toHaveBeenCalledWith("cb_submit", [expect.anything()]);
  });

  it("does not call preventDefault on other handlers", () => {
    const onEvent = vi.fn();
    const props = {
      onChange: { __callback__: "cb_change" },
    };

    const result = processProps(props, onEvent);

    const mockEvent = {
      preventDefault: vi.fn(),
      type: "change",
    };

    (result.onChange as (e: unknown) => void)(mockEvent);

    expect(mockEvent.preventDefault).not.toHaveBeenCalled();
    expect(onEvent).toHaveBeenCalledWith("cb_change", [expect.anything()]);
  });
});

describe("renderNode", () => {
  const mockGetWidget = vi.fn();
  const mockOnEvent = vi.fn();
  const options = { onEvent: mockOnEvent, getWidget: mockGetWidget };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders text nodes", () => {
    const node: SerializedElement = {
      kind: ElementKind.TEXT,
      type: "text",
      name: "",
      key: null,
      props: { _text: "Hello World" },
      children: [],
    };

    const element = renderNode(node, options);
    render(element);

    expect(screen.getByText("Hello World")).toBeInTheDocument();
  });

  it("renders JSX elements (HTML tags)", () => {
    const node: SerializedElement = {
      kind: ElementKind.JSX_ELEMENT,
      type: "div",
      name: "",
      key: null,
      props: { className: "test-class" },
      children: [],
    };

    const element = renderNode(node, options);
    const { container } = render(element);

    expect(container.querySelector(".test-class")).toBeInTheDocument();
  });

  it("renders JSX elements with _text content", () => {
    const node: SerializedElement = {
      kind: ElementKind.JSX_ELEMENT,
      type: "p",
      name: "",
      key: null,
      props: { _text: "Paragraph text" },
      children: [],
    };

    const element = renderNode(node, options);
    render(element);

    expect(screen.getByText("Paragraph text")).toBeInTheDocument();
  });

  it("renders nested children", () => {
    const node: SerializedElement = {
      kind: ElementKind.JSX_ELEMENT,
      type: "div",
      name: "",
      key: null,
      props: { "data-testid": "parent" },
      children: [
        {
          kind: ElementKind.JSX_ELEMENT,
          type: "span",
          name: "",
          key: null,
          props: { _text: "Child 1" },
          children: [],
        },
        {
          kind: ElementKind.JSX_ELEMENT,
          type: "span",
          name: "",
          key: null,
          props: { _text: "Child 2" },
          children: [],
        },
      ],
    };

    const element = renderNode(node, options);
    render(element);

    expect(screen.getByText("Child 1")).toBeInTheDocument();
    expect(screen.getByText("Child 2")).toBeInTheDocument();
  });

  it("renders custom widgets from registry", () => {
    const TestWidget = ({ text }: { text: string }) => (
      <div data-testid="custom-widget">{text}</div>
    );
    mockGetWidget.mockReturnValue(TestWidget);

    const node: SerializedElement = {
      kind: ElementKind.REACT_COMPONENT,
      type: "TestWidget",
      name: "my_widget",
      key: null,
      props: { text: "Widget content" },
      children: [],
    };

    const element = renderNode(node, options);
    render(element);

    expect(mockGetWidget).toHaveBeenCalledWith("TestWidget");
    expect(screen.getByTestId("custom-widget")).toHaveTextContent("Widget content");
  });

  it("renders warning for unknown components", () => {
    mockGetWidget.mockReturnValue(undefined);

    const node: SerializedElement = {
      kind: ElementKind.REACT_COMPONENT,
      type: "UnknownWidget",
      name: "",
      key: null,
      props: {},
      children: [],
    };

    const element = renderNode(node, options);
    render(element);

    expect(screen.getByText(/Unknown component: UnknownWidget/)).toBeInTheDocument();
  });

  it("passes children to custom widgets", () => {
    const ContainerWidget = ({ children }: { children: React.ReactNode }) => (
      <div data-testid="container">{children}</div>
    );
    mockGetWidget.mockReturnValue(ContainerWidget);

    const node: SerializedElement = {
      kind: ElementKind.REACT_COMPONENT,
      type: "ContainerWidget",
      name: "",
      key: null,
      props: {},
      children: [
        {
          kind: ElementKind.TEXT,
          type: "text",
          name: "",
          key: null,
          props: { _text: "Child content" },
          children: [],
        },
      ],
    };

    const element = renderNode(node, options);
    render(element);

    expect(screen.getByTestId("container")).toHaveTextContent("Child content");
  });

  it("processes callback refs in widget props", () => {
    const ButtonWidget = ({ on_click, text }: { on_click: () => void; text: string }) => (
      <button onClick={on_click}>{text}</button>
    );
    mockGetWidget.mockReturnValue(ButtonWidget);

    const node: SerializedElement = {
      kind: ElementKind.REACT_COMPONENT,
      type: "ButtonWidget",
      name: "",
      key: null,
      props: {
        text: "Click me",
        on_click: { __callback__: "btn_callback" },
      },
      children: [],
    };

    const element = renderNode(node, options);
    render(element);

    screen.getByText("Click me").click();

    expect(mockOnEvent).toHaveBeenCalledWith("btn_callback", [expect.anything()]);
  });
});
