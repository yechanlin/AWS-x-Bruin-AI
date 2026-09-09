// Tailwind config for the client. Note: only the unused Dashboard/components
// tree actually uses Tailwind classes; the active App.js wizard uses App.css.
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}