export async function invokeCallback(
  callback: (value: number) => number | Promise<number>,
  value: number
): Promise<number> {
  return await callback(value + 1);
}
