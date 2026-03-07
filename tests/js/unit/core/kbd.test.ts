import { describe, it, expect } from "vitest";
import { resolveKeyTokens } from "@widgets/Kbd";

describe("resolveKeyTokens", () => {
  describe("on Mac", () => {
    const mac = true;

    it("resolves Mod to command symbol", () => {
      expect(resolveKeyTokens("Mod+S", mac)).toEqual(["⌘", "S"]);
    });

    it("resolves Meta to command symbol", () => {
      expect(resolveKeyTokens("Meta+ArrowLeft", mac)).toEqual(["⌘", "←"]);
    });

    it("resolves Control to control symbol", () => {
      expect(resolveKeyTokens("Control+C", mac)).toEqual(["⌃", "C"]);
    });

    it("resolves Alt to option symbol", () => {
      expect(resolveKeyTokens("Alt+Tab", mac)).toEqual(["⌥", "⇥"]);
    });

    it("resolves Shift to symbol", () => {
      expect(resolveKeyTokens("Shift+?", mac)).toEqual(["⇧", "?"]);
    });

    it("resolves arrow keys to symbols", () => {
      expect(resolveKeyTokens("ArrowUp", mac)).toEqual(["↑"]);
      expect(resolveKeyTokens("ArrowDown", mac)).toEqual(["↓"]);
      expect(resolveKeyTokens("ArrowLeft", mac)).toEqual(["←"]);
      expect(resolveKeyTokens("ArrowRight", mac)).toEqual(["→"]);
    });

    it("resolves special keys", () => {
      expect(resolveKeyTokens("Enter", mac)).toEqual(["↩"]);
      expect(resolveKeyTokens("Escape", mac)).toEqual(["Esc"]);
      expect(resolveKeyTokens("Backspace", mac)).toEqual(["⌫"]);
      expect(resolveKeyTokens("Delete", mac)).toEqual(["⌦"]);
      expect(resolveKeyTokens("Tab", mac)).toEqual(["⇥"]);
      expect(resolveKeyTokens("Space", mac)).toEqual(["Space"]);
    });

    it("resolves compound shortcuts", () => {
      expect(resolveKeyTokens("Mod+Shift+S", mac)).toEqual(["⌘", "⇧", "S"]);
    });

    it("passes through single letters unchanged", () => {
      expect(resolveKeyTokens("K", mac)).toEqual(["K"]);
    });

    it("passes through bracket keys", () => {
      expect(resolveKeyTokens("Mod+[", mac)).toEqual(["⌘", "["]);
    });
  });

  describe("on non-Mac", () => {
    const mac = false;

    it("resolves Mod to Ctrl", () => {
      expect(resolveKeyTokens("Mod+S", mac)).toEqual(["Ctrl", "S"]);
    });

    it("resolves Meta to Super", () => {
      expect(resolveKeyTokens("Meta+ArrowLeft", mac)).toEqual(["Super", "←"]);
    });

    it("resolves Control to Ctrl", () => {
      expect(resolveKeyTokens("Control+C", mac)).toEqual(["Ctrl", "C"]);
    });

    it("resolves Alt to Alt", () => {
      expect(resolveKeyTokens("Alt+Tab", mac)).toEqual(["Alt", "⇥"]);
    });

    it("resolves Shift to Shift", () => {
      expect(resolveKeyTokens("Shift+?", mac)).toEqual(["Shift", "?"]);
    });

    it("resolves arrow keys to symbols", () => {
      expect(resolveKeyTokens("ArrowLeft", mac)).toEqual(["←"]);
    });

    it("resolves compound shortcuts", () => {
      expect(resolveKeyTokens("Mod+Shift+S", mac)).toEqual(["Ctrl", "Shift", "S"]);
    });
  });
});
