import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-inter)', 'sans-serif'],
      },
      colors: {
        brand: {
          50: "#eff9f1",
          100: "#d7f0dc",
          500: "#1f7a4d",
          600: "#186339",
          700: "#134d2d",
        },
      },
    },
  },
  plugins: [],
};

export default config;
