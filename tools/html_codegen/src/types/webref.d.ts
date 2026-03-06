declare module "@webref/elements" {
  export function listAll(): Promise<Record<string, unknown>>;
}

declare module "@webref/events" {
  export function listAll(): Promise<Array<{ type?: string }>>;
}

declare module "@webref/idl" {
  export function listAll(): Promise<Record<string, unknown>>;
  export function parseAll(): Promise<Record<string, unknown[]>>;
}
