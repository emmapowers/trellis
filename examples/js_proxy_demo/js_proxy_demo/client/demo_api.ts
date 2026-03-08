export const demo_api = {
  greet(name: string): string {
    return `hello ${name}`;
  },

  fail(): never {
    throw new Error("demo failure");
  },
};

export function formatNow(value: number): string {
  return `value: ${value}`;
}

export function explodeNow(): never {
  throw new Error("function failure");
}
