import { describe, expect, it } from "vitest";

import { extract_react_event_bindings } from "../src/sources/react_ts.js";

describe("react event bindings", () => {
  it("derives payload and handler families from react handler aliases", async () => {
    const bindings = await extract_react_event_bindings();

    expect(bindings.get("onClick")).toEqual({
      prop_name: "onClick",
      dom_event_name: "click",
      react_handler_alias: "MouseEventHandler",
      react_event_interface: "MouseEvent",
      payload_name: "MouseEvent",
      typed_handler_name: "MouseEventHandler",
      handler_name: "MouseHandler",
    });

    expect(bindings.get("onChange")).toEqual({
      prop_name: "onChange",
      dom_event_name: "change",
      react_handler_alias: "ChangeEventHandler",
      react_event_interface: "ChangeEvent",
      payload_name: "ChangeEvent",
      typed_handler_name: "ChangeEventHandler",
      handler_name: "ChangeHandler",
    });

    expect(bindings.get("onScroll")).toEqual({
      prop_name: "onScroll",
      dom_event_name: "scroll",
      react_handler_alias: "UIEventHandler",
      react_event_interface: "UIEvent",
      payload_name: "ScrollEvent",
      typed_handler_name: "ScrollEventHandler",
      handler_name: "ScrollHandler",
    });

    expect(bindings.get("onSubmit")).toEqual({
      prop_name: "onSubmit",
      dom_event_name: "submit",
      react_handler_alias: "SubmitEventHandler",
      react_event_interface: "SubmitEvent",
      payload_name: "FormEvent",
      typed_handler_name: "FormEventHandler",
      handler_name: "FormHandler",
    });
  });
});
