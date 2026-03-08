/** Helpers for values crossing the JS proxy boundary. */

const PROXY_CALLBACK_SENTINEL = "__proxy_callback__";

export type ProxyCallbackInvoker = (
  callbackId: string,
  args: unknown[]
) => Promise<unknown>;

function isProxyCallbackSentinel(
  value: unknown
): value is { __proxy_callback__: string } {
  return (
    value !== null &&
    typeof value === "object" &&
    PROXY_CALLBACK_SENTINEL in (value as Record<string, unknown>) &&
    Object.keys(value as Record<string, unknown>).length === 1 &&
    typeof (value as Record<string, unknown>)[PROXY_CALLBACK_SENTINEL] === "string"
  );
}

export function materializeProxyValue(
  value: unknown,
  invokeCallback: ProxyCallbackInvoker
): unknown {
  if (isProxyCallbackSentinel(value)) {
    const callbackId = value.__proxy_callback__;
    return (...args: unknown[]) => invokeCallback(callbackId, args);
  }

  if (Array.isArray(value)) {
    return value.map((item) => materializeProxyValue(item, invokeCallback));
  }

  if (value !== null && typeof value === "object") {
    const result: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value as Record<string, unknown>)) {
      result[key] = materializeProxyValue(item, invokeCallback);
    }
    return result;
  }

  return value;
}
