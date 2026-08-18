import { describe, expect, it } from "vitest";

import { percent } from "./format";

describe("percent", () => {
  it("renders anomaly scores for analyst review", () => {
    expect(percent(0.873)).toBe("87%");
  });
});
