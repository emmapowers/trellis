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

declare module "@webref/css" {
  export interface CssFeature {
    name: string;
    href: string;
    syntax?: string;
    styleDeclaration?: string[];
    longhands?: string[];
    descriptors?: Record<string, CssFeature>;
  }

  export interface CssIndex {
    atrules: Record<string, CssFeature>;
    functions: Record<string, CssFeature>;
    properties: Record<string, CssFeature>;
    selectors: Record<string, CssFeature>;
    types: Record<string, CssFeature>;
  }

  export function index(): Promise<CssIndex>;
}
