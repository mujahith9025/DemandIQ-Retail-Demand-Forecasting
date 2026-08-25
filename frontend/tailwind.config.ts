import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f5fa",
          100: "#dbe8f5",
          200: "#bad3eb",
          300: "#8bb6de",
          400: "#5794ce",
          500: "#3476be",
          600: "#255da1",
          700: "#1e3a5f", // Primary DemandIQ Brand Navy
          800: "#1b3e6b",
          900: "#022448", // Deep Navy Accent
          950: "#0b1524",
        },
        tealAccent: {
          50: "#f0fdfa",
          100: "#ccfbf1",
          200: "#99f6e4",
          300: "#5eead4",
          400: "#2dd4bf",
          500: "#14b8a6", // DemandIQ Teal
          600: "#0d9488",
          700: "#0f766e",
          800: "#115e59",
          900: "#134e4a",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "sans-serif"],
        mono: ["var(--font-jetbrains)", "JetBrains Mono", "monospace"],
      },
      boxShadow: {
        ambient: "0 4px 20px -2px rgba(30, 58, 95, 0.06)",
        card: "0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03)",
        elevation: "0 10px 30px -4px rgba(30, 58, 95, 0.1)",
      },
    },
  },
  plugins: [],
};

export default config;
