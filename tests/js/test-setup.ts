import "@testing-library/jest-dom/vitest";

// Mock PointerEvent for jsdom
class PointerEventMock extends MouseEvent {
  pointerId: number;
  pointerType: string;
  isPrimary: boolean;
  pressure: number;

  constructor(type: string, params: PointerEventInit = {}) {
    super(type, params);
    this.pointerId = params.pointerId ?? 0;
    this.pointerType = params.pointerType ?? "";
    this.isPrimary = params.isPrimary ?? false;
    this.pressure = params.pressure ?? 0;
  }
}
Object.defineProperty(window, "PointerEvent", {
  writable: true,
  value: PointerEventMock,
});

// Mock matchMedia for jsdom (required by uplot and other libs)
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => true,
  }),
});

// Mock ResizeObserver for jsdom
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
Object.defineProperty(window, "ResizeObserver", {
  writable: true,
  value: ResizeObserverMock,
});
