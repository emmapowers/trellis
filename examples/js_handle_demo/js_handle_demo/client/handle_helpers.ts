export function createCounter(label: string) {
  return {
    label,
    value: 0,
    increment() {
      this.value += 1;
      return this.value;
    },
  };
}
