import { expect, it } from "vitest";
import { versionLine } from "../src/index.js";

it("reports the package version", () => {
  expect(versionLine()).toBe("gridbot-ui 0.1.0");
});
