/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        institutional: {
          navy: "#0B3553",
          action: "#087D9F",
          surface: "#EEF5FA",
          muted: "#64748B",
          error: "#B42318",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      boxShadow: {
        card: "0 18px 45px -12px rgba(11, 53, 83, 0.18)",
      },
    },
  },
  plugins: [],
};
