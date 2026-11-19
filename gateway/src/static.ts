import { readFile, stat } from "node:fs/promises";
import { extname, resolve, sep } from "node:path";

const CONTENT_TYPES: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2",
};

export type StaticFile = { body: Buffer; contentType: string };

/** Resolve a URL path inside the UI folder, or return null. */
export function resolveUiPath(uiDir: string, urlPath: string): string | null {
  let decoded: string;
  try {
    decoded = decodeURIComponent(urlPath);
  } catch {
    return null;
  }
  if (decoded.includes("\0")) return null;
  const root = resolve(uiDir);
  const target = resolve(root, `.${decoded === "/" ? "/index.html" : decoded}`);
  return target.startsWith(root + sep) ? target : null;
}

/** Read a UI file, or return null when it is missing or outside the folder. */
export async function readUiFile(
  uiDir: string,
  urlPath: string,
): Promise<StaticFile | null> {
  const path = resolveUiPath(uiDir, urlPath);
  if (path === null) return null;
  try {
    if (!(await stat(path)).isFile()) return null;
    const contentType =
      CONTENT_TYPES[extname(path)] ?? "application/octet-stream";
    return { body: await readFile(path), contentType };
  } catch {
    return null;
  }
}
