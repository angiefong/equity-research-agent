import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ThesisMatrix } from "@/components/viz/ThesisMatrix";

describe("ThesisMatrix", () => {
  const claims = [
    { side: "bull" as const, topic: "Services Margin", confidence: 0.92 },
    { side: "bull" as const, topic: "China Share", confidence: 0.74 },
    { side: "bear" as const, topic: "EU DMA", confidence: 0.83 },
    { side: "bear" as const, topic: "Vision Pro", confidence: 0.71 },
  ];

  it("renders one tile per claim", () => {
    render(<ThesisMatrix claims={claims} />);
    expect(screen.getByText("Services Margin")).toBeInTheDocument();
    expect(screen.getByText("EU DMA")).toBeInTheDocument();
  });

  it("applies strong saturation class for high-confidence bull tile", () => {
    const { container } = render(<ThesisMatrix claims={[claims[0]]} />);
    expect(container.querySelector(".bg-bull")).toBeInTheDocument();
  });
});
