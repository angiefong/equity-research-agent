import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { WeightBar } from "@/components/viz/WeightBar";

describe("WeightBar", () => {
  it("renders bull and bear weight numbers", () => {
    render(<WeightBar bullWeight={0.78} bearWeight={0.64} bullClaims={4} bearClaims={2} />);
    expect(screen.getByText("0.78")).toBeInTheDocument();
    expect(screen.getByText("0.64")).toBeInTheDocument();
    expect(screen.getByText(/4 BULL CLAIMS/i)).toBeInTheDocument();
    expect(screen.getByText(/2 BEAR CLAIMS/i)).toBeInTheDocument();
  });

  it("computes bull-side share from weights", () => {
    const { container } = render(<WeightBar bullWeight={0.6} bearWeight={0.4} bullClaims={3} bearClaims={2} />);
    const bullDiv = container.querySelector("[data-side=bull]") as HTMLElement;
    expect(bullDiv.style.width).toBe("60%");
  });
});
