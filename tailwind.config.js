/** رنگ‌ها و فونت — عیناً از نمونهٔ ریاضی‌کوئست */
module.exports = {
  content: ["./*.html", "./lessons/**/*.html", "./assets/js/*.js"],
  theme: {
    extend: {
      screens: { xs: "380px" },
      colors: {
        ink: "#05080f", abyss: "#0a1020", panel: "#0d1526", panel2: "#111b32",
        line: "#22304e", fog: "#93a2c0", snow: "#eef2fb",
        mint: "#34d399", skyy: "#22d3ee", amberr: "#fbbf24", rosee: "#fb7185",
        violet: "#a78bfa", orangey: "#fb923c", pinky: "#f472b6", indigoo: "#818cf8",
        teal: "#2dd4bf", xp: "#facc15",
      },
      fontFamily: {
        sans: ['"Abar Low"', "Vazirmatn", "Tahoma", "Segoe UI", "sans-serif"],
        head: ['"Abar High"', "Vazirmatn", "Tahoma", "sans-serif"],
        ui: ['"Abar Mid"', "Vazirmatn", "Tahoma", "sans-serif"],
      },
    },
  },
  plugins: [],
};
