/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: "#3B82F6",
        accent: "#14B8A6",
        secondary: "#8B5CF6",
        "dark-bg": "#0F172A",
        "dark-surface": "#1E293B",
        "light-text": "#F1F5F9",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      typography: {
        invert: {
          css: {
            "--tw-prose-body": "#CBD5E1",
            "--tw-prose-headings": "#F1F5F9",
            "--tw-prose-links": "#3B82F6",
            "--tw-prose-bold": "#F1F5F9",
            "--tw-prose-counters": "#94A3B8",
            "--tw-prose-bullets": "#94A3B8",
            "--tw-prose-hr": "#334155",
            "--tw-prose-quotes": "#E2E8F0",
            "--tw-prose-quote-borders": "#3B82F6",
            "--tw-prose-code": "#F1F5F9",
            "--tw-prose-pre-code": "#E2E8F0",
            "--tw-prose-pre-bg": "#0F172A",
            "--tw-prose-th-borders": "#475569",
            "--tw-prose-td-borders": "#334155",
            "--tw-prose-strikethrough": "#64748B",
          },
        },
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
