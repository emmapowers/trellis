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
const proxyTargets: Record<string, ProxyTarget> = {};

export function registerProxyTarget(name: string, target: ProxyTarget): void {
  proxyTargets[name] = target;
}

export function getProxyTarget(name: string): ProxyTarget | undefined {
  return proxyTargets[name];
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

  const target = getProxyTarget(proxyId);
  return {
    found: target !== undefined,
    isGlobal: false,
    receiver: typeof target === "function" ? undefined : target,
    target,
  };
}
