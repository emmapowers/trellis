import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen } from "../../test-utils";
import { processProps, renderNode, toReactDomProps } from "@common/core/renderTree";
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

  it("calls preventDefault on on_click handlers", () => {
    const onEvent = vi.fn();
    const props = {
      on_click: { __callback__: "cb_click" },
    };

    const result = processProps(props, onEvent);

    const mockEvent = {
      preventDefault: vi.fn(),
      type: "click",
    };

    (result.on_click as (e: unknown) => void)(mockEvent);

    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(onEvent).toHaveBeenCalledWith("cb_click", [expect.anything()]);
  });

  it("calls preventDefault on on_submit handlers", () => {
    const onEvent = vi.fn();
    const props = {
      on_submit: { __callback__: "cb_submit" },
    };

    const result = processProps(props, onEvent);

    const mockEvent = {
      preventDefault: vi.fn(),
      type: "submit",
    };

    (result.on_submit as (e: unknown) => void)(mockEvent);

    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(onEvent).toHaveBeenCalledWith("cb_submit", [expect.anything()]);
  });

  it("does not call preventDefault on other handlers", () => {
    const onEvent = vi.fn();
    const props = {
      on_change: { __callback__: "cb_change" },
    };

    const result = processProps(props, onEvent);

    const mockEvent = {
      preventDefault: vi.fn(),
      type: "change",
    };

    (result.on_change as (e: unknown) => void)(mockEvent);

    expect(mockEvent.preventDefault).not.toHaveBeenCalled();
    expect(onEvent).toHaveBeenCalledWith("cb_change", [expect.anything()]);
  });

  it("serializes mouse event payloads to snake_case", () => {
    const onEvent = vi.fn();
    const props = {
      on_click: { __callback__: "cb_click" },
    };

    const result = processProps(props, onEvent);
    const nativeEvent = new MouseEvent("click", {
      clientX: 15,
      clientY: 25,
      button: 0,
      bubbles: true,
    });
    const mockEvent = {
      type: "click",
      nativeEvent,
      currentTarget: document.createElement("button"),
      preventDefault: vi.fn(),
      timeStamp: 1234,
      bubbles: true,
      cancelable: false,
      defaultPrevented: false,
      eventPhase: 0,
      isTrusted: false,
    };

    (result.on_click as (e: unknown) => void)(mockEvent);

    expect(onEvent).toHaveBeenCalledWith(
      "cb_click",
      [
        expect.objectContaining({
          type: "click",
          time_stamp: 1234,
          bubbles: true,
          cancelable: false,
          default_prevented: false,
          event_phase: 0,
          is_trusted: false,
          client_x: 15,
          client_y: 25,
          alt_key: false,
          ctrl_key: false,
        }),
      ]
    );
  });

  it("serializes input events with source-native fields", () => {
    const onEvent = vi.fn();
    const props = {
      on_input: { __callback__: "cb_input" },
    };

    const result = processProps(props, onEvent);
    const nativeEvent = new InputEvent("input", {
      data: "x",
      bubbles: true,
    });
    const input = document.createElement("input");
    const mockEvent = {
      type: "input",
      nativeEvent,
      target: input,
      currentTarget: input,
      preventDefault: vi.fn(),
      timeStamp: 4567,
    };

    (result.on_input as (e: unknown) => void)(mockEvent);

    expect(onEvent).toHaveBeenCalledWith(
      "cb_input",
      [
        expect.objectContaining({
          type: "input",
          time_stamp: 4567,
          data: "x",
          is_composing: false,
          input_type: "",
        }),
      ]
    );
  });

  describe("anchor click handling", () => {
    // These tests verify that modifier-key clicks on anchors don't call
    // preventDefault, allowing the browser to handle opening in new tabs.
    // The shouldLetBrowserHandleClick function checks currentTarget.

    const createMouseEvent = (
      target: EventTarget,
      options: {
        button?: number;
        metaKey?: boolean;
        ctrlKey?: boolean;
        shiftKey?: boolean;
        altKey?: boolean;
      } = {}
    ) => {
      const nativeEvent = new MouseEvent("click", {
        button: options.button ?? 0,
        metaKey: options.metaKey ?? false,
        ctrlKey: options.ctrlKey ?? false,
        shiftKey: options.shiftKey ?? false,
        altKey: options.altKey ?? false,
        bubbles: true,
      });

      // Create a mock SyntheticEvent-like object
      return {
        type: "click",
        nativeEvent,
        currentTarget: target,
        preventDefault: vi.fn(),
        timeStamp: Date.now(),
      };
    };

    it("lets browser handle middle-click on anchor with href", () => {
      const onEvent = vi.fn();
      const props = { on_click: { __callback__: "cb_click" } };
      const result = processProps(props, onEvent);

      const anchor = document.createElement("a");
      anchor.href = "https://example.com";
      const mockEvent = createMouseEvent(anchor, { button: 1 });

      (result.on_click as (e: unknown) => void)(mockEvent);

      // Should NOT call preventDefault - let browser open in new tab
      expect(mockEvent.preventDefault).not.toHaveBeenCalled();
      // Should NOT call onEvent - browser handles navigation
      expect(onEvent).not.toHaveBeenCalled();
    });

    it("lets browser handle Cmd/Meta+click on anchor with href", () => {
      const onEvent = vi.fn();
      const props = { on_click: { __callback__: "cb_click" } };
      const result = processProps(props, onEvent);

      const anchor = document.createElement("a");
      anchor.href = "https://example.com";
      const mockEvent = createMouseEvent(anchor, { metaKey: true });

      (result.on_click as (e: unknown) => void)(mockEvent);

      expect(mockEvent.preventDefault).not.toHaveBeenCalled();
      expect(onEvent).not.toHaveBeenCalled();
    });

    it("lets browser handle Ctrl+click on anchor with href", () => {
      const onEvent = vi.fn();
      const props = { on_click: { __callback__: "cb_click" } };
      const result = processProps(props, onEvent);

      const anchor = document.createElement("a");
      anchor.href = "https://example.com";
      const mockEvent = createMouseEvent(anchor, { ctrlKey: true });

      (result.on_click as (e: unknown) => void)(mockEvent);

      expect(mockEvent.preventDefault).not.toHaveBeenCalled();
      expect(onEvent).not.toHaveBeenCalled();
    });

    it("lets browser handle Shift+click on anchor with href", () => {
      const onEvent = vi.fn();
      const props = { on_click: { __callback__: "cb_click" } };
      const result = processProps(props, onEvent);

      const anchor = document.createElement("a");
      anchor.href = "https://example.com";
      const mockEvent = createMouseEvent(anchor, { shiftKey: true });

      (result.on_click as (e: unknown) => void)(mockEvent);

      expect(mockEvent.preventDefault).not.toHaveBeenCalled();
      expect(onEvent).not.toHaveBeenCalled();
    });

    it("calls preventDefault on regular click on anchor with href", () => {
      const onEvent = vi.fn();
      const props = { on_click: { __callback__: "cb_click" } };
      const result = processProps(props, onEvent);

      const anchor = document.createElement("a");
      anchor.href = "https://example.com";
      const mockEvent = createMouseEvent(anchor, {});

      (result.on_click as (e: unknown) => void)(mockEvent);

      // Regular click should preventDefault and call handler
      expect(mockEvent.preventDefault).toHaveBeenCalled();
      expect(onEvent).toHaveBeenCalledWith("cb_click", [expect.anything()]);
    });

    it("calls preventDefault on click on anchor without href", () => {
      const onEvent = vi.fn();
      const props = { on_click: { __callback__: "cb_click" } };
      const result = processProps(props, onEvent);

      const anchor = document.createElement("a");
      // No href set
      const mockEvent = createMouseEvent(anchor, { metaKey: true });

      (result.on_click as (e: unknown) => void)(mockEvent);

      // Even with modifier key, anchor without href should call handler
      expect(mockEvent.preventDefault).toHaveBeenCalled();
      expect(onEvent).toHaveBeenCalledWith("cb_click", [expect.anything()]);
    });

    it("calls preventDefault on click on non-anchor element", () => {
      const onEvent = vi.fn();
      const props = { on_click: { __callback__: "cb_click" } };
      const result = processProps(props, onEvent);

      const button = document.createElement("button");
      const mockEvent = createMouseEvent(button, { metaKey: true });

      (result.on_click as (e: unknown) => void)(mockEvent);

      // Non-anchor elements always call preventDefault
      expect(mockEvent.preventDefault).toHaveBeenCalled();
      expect(onEvent).toHaveBeenCalledWith("cb_click", [expect.anything()]);
    });
  });
});



describe("compiled CSS runtime props", () => {
  beforeEach(() => {
    document.head.innerHTML = "";
  });

  it("maps DOM-style inline CSS to React style props", () => {
    const props = toReactDomProps({
      style: {
        "border-radius": "8px",
        "background-color": "red",
      },
    });

    expect(props.style).toEqual({
      borderRadius: "8px",
      backgroundColor: "red",
    });
  });

  it("preserves CSS custom properties verbatim in inline styles", () => {
    const props = toReactDomProps({
      style: {
        "--paper": "oklch(0.98 0.01 95)",
        "background-color": "var(--paper)",
      },
    });

    expect(props.style).toEqual({
      "--paper": "oklch(0.98 0.01 95)",
      backgroundColor: "var(--paper)",
    });
  });

  it("maps special DOM attribute names to the React runtime spellings", () => {
    const props = toReactDomProps({
      item_id: "story-1",
      popover_target: "note-popover",
      popover_target_action: "show",
    });

    expect(props.itemID).toBe("story-1");
    expect(props.popovertarget).toBe("note-popover");
    expect(props.popovertargetaction).toBe("show");
  });

  it("keeps escaped html attrs distinct from data-* mappings", () => {
    const props = toReactDomProps({
      data_: "/movie.swf",
      data: { "asset-id": 1 },
    });

    expect(props.data).toBe("/movie.swf");
    expect(props["data-asset-id"]).toBe(1);
  });

  it("injects compiled style rules once and strips internal props from html nodes", () => {
    const node: SerializedElement = {
      kind: ElementKind.JSX_ELEMENT,
      type: "div",
      name: "Div",
      key: "node-1",
      props: {
        class_name: "existing tcss_demo",
        _style_rules: ".tcss_demo:hover{color:red}",
        style: { color: "black" },
      },
      children: [],
    };

    renderNode(node, {
      onEvent: vi.fn(),
      getWidget: () => undefined,
    });

    const styleNode = document.head.querySelector('style[data-trellis-dynamic-styles="true"]');
    expect(styleNode?.textContent).toContain('.tcss_demo:hover{color:red}');

    const domProps = toReactDomProps({
      class_name: "existing tcss_demo",
      style: { color: "black" },
    });
    expect(domProps.className).toBe("existing tcss_demo");
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
      props: { class_name: "test-class" },
      children: [],
    };

    const element = renderNode(node, options);
    const { container } = render(element);

    expect(container.querySelector(".test-class")).toBeInTheDocument();
  });

  it("expands data mappings to data-* DOM props", () => {
    const domProps = toReactDomProps({
      class_name: "test-class",
      data: {
        "test-id": "abc",
        enabled: true,
      },
    });

    expect(domProps.className).toBe("test-class");
    expect(domProps["data-test-id"]).toBe("abc");
    expect(domProps["data-enabled"]).toBe(true);
    expect(domProps.data).toBeUndefined();
  });

  it("maps snake_case DOM attrs to browser prop names", () => {
    const node: SerializedElement = {
      kind: ElementKind.JSX_ELEMENT,
      type: "div",
      name: "",
      key: null,
      props: { class_name: "mapped", data_testid: "mapped-id", aria_label: "Mapped Label" },
      children: [],
    };

    const element = renderNode(node, options);
    render(element);

    const mapped = screen.getByTestId("mapped-id");
    expect(mapped).toHaveClass("mapped");
    expect(mapped).toHaveAttribute("aria-label", "Mapped Label");
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
      props: { data_testid: "parent" },
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

  it("maps snake_case callback props to DOM event handlers", () => {
    const node: SerializedElement = {
      kind: ElementKind.JSX_ELEMENT,
      type: "button",
      name: "",
      key: null,
      props: {
        _text: "Click mapped handler",
        on_click: { __callback__: "mapped_click" },
      },
      children: [],
    };

    const element = renderNode(node, options);
    render(element);

    screen.getByText("Click mapped handler").click();
    expect(mockOnEvent).toHaveBeenCalledWith("mapped_click", [expect.anything()]);
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
