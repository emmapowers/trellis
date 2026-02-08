// Type declaration for worker bundle imports (built as text by esbuild)
declare module "*.worker-bundle" {
  const content: string;
  export default content;
}

// Type declarations for wheel bundle virtual modules (built by esbuild)
declare module "@trellis/wheel-bundle" {
  const data: Uint8Array;
  export default data;
}

declare module "@trellis/wheel-manifest" {
  const manifest: {
    entryModule: string;
    pyodidePackages: string[];
  };
  export default manifest;
}
