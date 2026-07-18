import type { Config } from "tailwindcss";

/**
 * Patient Companion — Tailwind theme extension (shadcn/ui compatible).
 * Reads the CSS variables declared in src/index.css so light/dark
 * switch automatically via the `.dark` class.
 */
const config: Config = {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    container: { center: true, padding: "1rem", screens: { "2xl": "1400px" } },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        // Semantic status — green=done, amber=waiting, red=blocked, blue=in-progress
        success: { DEFAULT: "hsl(var(--success))", foreground: "hsl(var(--success-foreground))" },
        warning: { DEFAULT: "hsl(var(--warning))", foreground: "hsl(var(--warning-foreground))" },
        danger:  { DEFAULT: "hsl(var(--danger))",  foreground: "hsl(var(--danger-foreground))" },
        info:    { DEFAULT: "hsl(var(--info))",    foreground: "hsl(var(--info-foreground))" },
        // Sequential load heatmap (green → amber → red)
        heat: {
          1: "hsl(var(--heat-1))",
          2: "hsl(var(--heat-2))",
          3: "hsl(var(--heat-3))",
          4: "hsl(var(--heat-4))",
          5: "hsl(var(--heat-5))",
          6: "hsl(var(--heat-6))",
        },
        neutral: {
          50: "hsl(var(--neutral-50))",
          100: "hsl(var(--neutral-100))",
          200: "hsl(var(--neutral-200))",
          300: "hsl(var(--neutral-300))",
          400: "hsl(var(--neutral-400))",
          500: "hsl(var(--neutral-500))",
          900: "hsl(var(--neutral-900))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 4px)",
        sm: "calc(var(--radius) - 8px)",
        pill: "999px",
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      spacing: {
        // 4px base scale
        1: "4px", 2: "6px", 3: "8px", 4: "10px", 5: "12px",
        6: "14px", 7: "16px", 8: "18px", 9: "20px", 10: "22px",
        12: "24px", 14: "28px", 16: "32px",
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.06)",
        raised: "0 8px 24px rgba(14,116,144,0.25)",
        fab: "0 10px 24px rgba(14,116,144,0.35)",
        sheet: "0 -4px 24px rgba(0,0,0,0.12)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
