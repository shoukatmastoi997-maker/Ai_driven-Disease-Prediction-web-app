/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#13233a",
        card: "#f8fbff"
      },
      boxShadow: {
        soft: "0 12px 30px rgba(16, 28, 48, 0.08)"
      },
      backgroundImage: {
        "hero-radial":
          "radial-gradient(circle at 10% 15%, rgba(255, 236, 179, 0.85) 0%, rgba(255,255,255,0) 42%), radial-gradient(circle at 90% 5%, rgba(185, 221, 255, 0.8) 0%, rgba(255,255,255,0) 35%)"
      }
    }
  },
  plugins: []
};
