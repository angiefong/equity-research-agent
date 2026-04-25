import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PriceChart } from "@/components/viz/PriceChart";

describe("PriceChart", () => {
  const data = Array.from({ length: 12 }, (_, i) => ({ date: `2026-${i + 1}`, price: 100 + i * 5 }));

  it("renders an SVG with one polyline", () => {
    render(<PriceChart data={data} high52w={200} low52w={80} current={155} />);
    const svg = screen.getByRole("img", { name: /price chart/i });
    expect(svg).toBeInTheDocument();
    expect(svg.querySelectorAll("polyline").length).toBe(1);
  });

  it("renders 52-week high and low labels", () => {
    render(<PriceChart data={data} high52w={200} low52w={80} current={155} />);
    expect(screen.getByText(/52W HIGH 200/i)).toBeInTheDocument();
    expect(screen.getByText(/52W LOW 80/i)).toBeInTheDocument();
  });
});
