import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#000000",
        paper: "#FFFFFF",
        accent: "#FFE100",
        accentSoft: "#FFF9D6",
        inset: "#FAFAF7",
        bull: "#006633",
        bear: "#B40000",
        muted: "#666666",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      letterSpacing: {
        display: "-0.04em",
        big: "-0.05em",
      },
    },
  },
  plugins: [],
};
export default config;
