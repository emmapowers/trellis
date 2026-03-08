export const DemoApi = {
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

export function renameMe(): never {
  throw new Error("function failure");
}
