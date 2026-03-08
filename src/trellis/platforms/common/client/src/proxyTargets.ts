/** Registry for bundled JS proxy targets. */

export type ProxyTarget = Record<string, unknown> | ((...args: unknown[]) => unknown);

const proxyTargets: Record<string, ProxyTarget> = {};

export function registerProxyTarget(name: string, target: ProxyTarget): void {
  proxyTargets[name] = target;
}

export function getProxyTarget(name: string): ProxyTarget | undefined {
  return proxyTargets[name];
}
