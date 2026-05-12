import { describe, expect, test } from "vitest";
import { fmtCompact, fmtPct, fmtCurrency, fmtVolume, fmtOrDash } from "@/lib/format";

describe("fmtCompact", () => {
  test("formats trillions", () => {
    expect(fmtCompact(3.2e12)).toBe("3.2T");
  });
  test("formats billions", () => {
    expect(fmtCompact(2.5e9)).toBe("2.5B");
  });
  test("formats millions", () => {
    expect(fmtCompact(72_000_000)).toBe("72.0M");
  });
  test("formats thousands", () => {
    expect(fmtCompact(12_345)).toBe("12.3K");
  });
  test("passes through small numbers", () => {
    expect(fmtCompact(42)).toBe("42");
  });
});

describe("fmtPct", () => {
  test("formats fraction as percent", () => {
    expect(fmtPct(0.0049)).toBe("0.49%");
  });
  test("handles zero", () => {
    expect(fmtPct(0)).toBe("0.00%");
  });
});

describe("fmtCurrency", () => {
  test("formats with two decimals", () => {
    expect(fmtCurrency(214.82)).toBe("$214.82");
  });
  test("handles negatives", () => {
    expect(fmtCurrency(-3.5)).toBe("-$3.50");
  });
});

describe("fmtVolume", () => {
  test("formats large volume as compact", () => {
    expect(fmtVolume(72_000_000)).toBe("72.0M");
  });
});

describe("fmtOrDash", () => {
  test("returns dash for null", () => {
    expect(fmtOrDash(null, fmtCompact)).toBe("—");
  });
  test("returns dash for undefined", () => {
    expect(fmtOrDash(undefined, fmtCompact)).toBe("—");
  });
  test("formats real value", () => {
    expect(fmtOrDash(3.2e12, fmtCompact)).toBe("3.2T");
  });
});
