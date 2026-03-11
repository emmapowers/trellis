import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { decode, encode } from "@msgpack/msgpack";
import { ServerTrellisClient } from "@trellis/trellis-server/client/src/TrellisClient";
import { MessageType } from "@common/types";

describe("ServerTrellisClient", () => {
  let originalWebSocket: typeof WebSocket;
  let originalMatchMedia: typeof window.matchMedia;
  let fakeSocket: {
    binaryType: string;
    readyState: number;
    onopen: (() => void) | null;
    onmessage: ((event: { data: ArrayBuffer }) => void) | null;
    onerror: (() => void) | null;
    onclose: (() => void) | null;
    send: ReturnType<typeof vi.fn>;
    close: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    originalWebSocket = globalThis.WebSocket;
    originalMatchMedia = window.matchMedia;

    fakeSocket = {
      binaryType: "",
      readyState: 1,
      onopen: null,
      onmessage: null,
      onerror: null,
      onclose: null,
      send: vi.fn(),
      close: vi.fn(),
    };

    class MockWebSocket {
      static OPEN = 1;
      binaryType = "";
      readyState = 1;
      onopen: (() => void) | null = null;
      onmessage: ((event: { data: ArrayBuffer }) => void) | null = null;
      onerror: (() => void) | null = null;
      onclose: (() => void) | null = null;

      constructor(_url: string) {
        fakeSocket = this as unknown as typeof fakeSocket;
        this.send = fakeSocket.send;
        this.close = fakeSocket.close;
      }

      send = vi.fn();
      close = vi.fn();
    }

    Object.defineProperty(globalThis, "WebSocket", {
      value: MockWebSocket,
      configurable: true,
      writable: true,
    });

    Object.defineProperty(window, "matchMedia", {
      value: vi.fn().mockReturnValue({ matches: false }),
      configurable: true,
      writable: true,
    });
  });

  afterEach(() => {
    Object.defineProperty(globalThis, "WebSocket", {
      value: originalWebSocket,
      configurable: true,
      writable: true,
    });
    Object.defineProperty(window, "matchMedia", {
      value: originalMatchMedia,
      configurable: true,
      writable: true,
    });
    vi.clearAllMocks();
  });

  it("sends hello on websocket open", () => {
    const client = new ServerTrellisClient();

    void client.connect();
    fakeSocket.onopen?.();

    expect(fakeSocket.send).toHaveBeenCalledTimes(1);

    const encoded = fakeSocket.send.mock.calls[0][0] as Uint8Array;
    const message = decode(encoded) as { type: string; path: string };
    expect(message.type).toBe(MessageType.HELLO);
    expect(message.path).toBe("/");

    client.disconnect();
  });

  it("logs rejected async message handling", async () => {
    const client = new ServerTrellisClient();
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    const handleMessage = vi
      .spyOn((client as { handler: { handleMessage: (msg: unknown) => Promise<void> } }).handler, "handleMessage")
      .mockRejectedValue(new Error("message boom"));
    const encoded = encode({ type: MessageType.RELOAD });

    void client.connect();
    fakeSocket.onmessage?.({
      data: encoded.buffer.slice(
        encoded.byteOffset,
        encoded.byteOffset + encoded.byteLength
      ),
    });
    await Promise.resolve();

    expect(handleMessage).toHaveBeenCalledTimes(1);
    expect(consoleError).toHaveBeenCalledWith(
      "Message handling failed:",
      expect.objectContaining({ message: "message boom" })
    );

    consoleError.mockRestore();
    client.disconnect();
  });
});
