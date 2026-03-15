export type DataValue = string | number | boolean | null;

const data_suffix_regex = /^[a-z0-9._:-]+$/;

export function encode_data_attributes(data: Record<string, DataValue>): Record<string, DataValue> {
  const encoded: Record<string, DataValue> = {};
  for (const [suffix, value] of Object.entries(data)) {
    if (!data_suffix_regex.test(suffix)) {
      throw new Error(`Invalid data key: ${suffix}`);
    }
    encoded[`data-${suffix}`] = value;
  }
  return encoded;
}
