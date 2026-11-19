import { describe, expect, it } from "vitest";
import { fitView } from "../src/view.js";

// A 2 m x 1 m map with its origin at (0, 0).
const WORLD = { resolution: 0.5, width: 4, height: 2, originX: 0, originY: 0 };

describe("fitView", () => {
  it("north appears at the top of the canvas", () => {
    const view = fitView(WORLD, 200, 100);
    expect(view.toPx(0, 1)).toEqual({ x: 0, y: 0 });
    expect(view.toPx(2, 0)).toEqual({ x: 200, y: 100 });
  });

  it("keeps the map's aspect and centres it", () => {
    const view = fitView(WORLD, 200, 200);
    expect(view.pxPerM).toBe(100);
    expect(view.toPx(0, 1)).toEqual({ x: 0, y: 50 });
  });
});
