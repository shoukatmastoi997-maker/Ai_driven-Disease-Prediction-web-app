/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        primary: "#06b6d4",
        card: "rgba(255,255,255,0.42)"
      },
      boxShadow: {
        soft: "0 12px 38px rgba(2, 6, 23, 0.10)",
        glow: "0 0 0 1px rgba(255,255,255,0.42), 0 18px 55px rgba(2,6,23,0.16)",
        "glow-cyan": "0 0 0 1px rgba(6,182,212,0.30), 0 0 26px rgba(6,182,212,0.22)"
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "Segoe UI", "Roboto", "Helvetica", "Arial", "sans-serif"],
        display: ["Outfit", "Inter", "ui-sans-serif", "system-ui", "sans-serif"]
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" }
        },
        floaty: {
          "0%, 100%": { transform: "translate3d(0,0,0)" },
          "50%": { transform: "translate3d(0,-8px,0)" }
        }
      },
      animation: {
        shimmer: "shimmer 1.25s linear infinite",
        floaty: "floaty 6s ease-in-out infinite"
      },
      backgroundImage: {
        "med-gradient":
          "radial-gradient(900px circle at 12% 8%, rgba(6,182,212,0.22) 0%, rgba(6,182,212,0) 55%), radial-gradient(900px circle at 90% 10%, rgba(59,130,246,0.18) 0%, rgba(59,130,246,0) 55%), radial-gradient(900px circle at 55% 95%, rgba(14,165,233,0.16) 0%, rgba(14,165,233,0) 55%), linear-gradient(180deg, #f8fafc 0%, #ecfeff 40%, #e0f2fe 100%)"
      }
    }
  },
  plugins: []
};
