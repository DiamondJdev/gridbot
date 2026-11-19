/** Map metres to canvas pixels with north at the top. */

export type MapBounds = {
  resolution: number;
  width: number;
  height: number;
  originX: number;
  originY: number;
};

export type View = {
  pxPerM: number;
  /** Top-left corner of the map on the canvas, in pixels. */
  left: number;
  top: number;
  toPx(x: number, y: number): { x: number; y: number };
};

/** Fit the whole map inside the canvas, keeping its aspect and centring it. */
export function fitView(
  world: MapBounds,
  canvasWidth: number,
  canvasHeight: number,
): View {
  const widthM = world.width * world.resolution;
  const heightM = world.height * world.resolution;
  const pxPerM = Math.min(canvasWidth / widthM, canvasHeight / heightM);
  const left = (canvasWidth - widthM * pxPerM) / 2;
  const top = (canvasHeight - heightM * pxPerM) / 2;
  const northM = world.originY + heightM;
  return {
    pxPerM,
    left,
    top,
    toPx: (x, y) => ({
      x: left + (x - world.originX) * pxPerM,
      y: top + (northM - y) * pxPerM,
    }),
  };
}
