/** Registry and resolver helpers for JS proxy targets. */

export type ProxyTarget = Record<string, unknown> | ((...args: unknown[]) => unknown);

export interface ResolvedProxyTarget {
  target: unknown;
  path?: string;
  isGlobal: boolean;
  receiver: unknown;
  found: boolean;
}

const GLOBAL_PROXY_PREFIX = "__global__:";
const HANDLE_PROXY_PREFIX = "__handle__:";
const proxyTargets: Record<string, ProxyTarget> = {};
const handleTargets = new Map<string, object | Function>();
const targetHandleIds = new WeakMap<object, string>();

export function registerProxyTarget(name: string, target: ProxyTarget): void {
  proxyTargets[name] = target;
}

export function getProxyTarget(name: string): ProxyTarget | undefined {
  return proxyTargets[name];
}

export function registerHandleTarget(target: object | Function): string {
  const existing = targetHandleIds.get(target as object);
  if (existing && handleTargets.has(existing)) {
    return existing;
  }

  const handleId = `${HANDLE_PROXY_PREFIX}${crypto.randomUUID()}`;
  handleTargets.set(handleId, target);
  targetHandleIds.set(target as object, handleId);
  return handleId;
}

export function getHandleTarget(handleId: string): object | Function | undefined {
  return handleTargets.get(handleId);
}

export function releaseHandleTarget(handleId: string): void {
  handleTargets.delete(handleId);
}

function resolveGlobalPath(path: string): ResolvedProxyTarget {
  const segments = path.split(".");
  let current: unknown = globalThis;
  let receiver: unknown = globalThis;
  let index = 0;

  if (segments[0] === "globalThis") {
    index = 1;
  }

  for (; index < segments.length; index += 1) {
    if (
      current === null ||
      current === undefined ||
      (typeof current !== "object" && typeof current !== "function")
    ) {
      return {
        found: false,
        isGlobal: true,
        path,
        receiver,
        target: undefined,
      };
    }

    const record = current as Record<string, unknown>;
    if (!(segments[index] in record)) {
      return {
        found: false,
        isGlobal: true,
        path,
        receiver: current,
        target: undefined,
      };
    }

    receiver = current;
    current = record[segments[index]];
  }

  return {
    found: true,
    isGlobal: true,
    path,
    receiver,
    target: current,
  };
}

export function resolveProxyTarget(proxyId: string): ResolvedProxyTarget {
  if (proxyId.startsWith(GLOBAL_PROXY_PREFIX)) {
    return resolveGlobalPath(proxyId.slice(GLOBAL_PROXY_PREFIX.length));
  }

  if (proxyId.startsWith(HANDLE_PROXY_PREFIX)) {
    const target = getHandleTarget(proxyId);
    return {
      found: target !== undefined,
      isGlobal: false,
      receiver: typeof target === "function" ? target : target,
      target,
    };
  }

  const target = getProxyTarget(proxyId);
  return {
    found: target !== undefined,
    isGlobal: false,
    receiver: typeof target === "function" ? undefined : target,
    target,
  };
}
