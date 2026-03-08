/** Registry for bundled JS proxy targets. */

const proxyTargets: Record<string, Record<string, unknown>> = {};

export function registerProxyTarget(
  name: string,
  target: Record<string, unknown>
): void {
  proxyTargets[name] = target;
}

export function getProxyTarget(
  name: string
): Record<string, unknown> | undefined {
  return proxyTargets[name];
}
