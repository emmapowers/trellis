export const demo_api = {
  greet(name: string): string {
    return `hello ${name}`;
  },

  fail(): never {
    throw new Error("demo failure");
  },
};
