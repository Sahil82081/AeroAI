/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // --- Stitch Design System Color Tokens ---
        "inverse-primary": "#006875",
        "on-secondary": "#05297a",
        "secondary-fixed": "#dce1ff",
        "on-surface-variant": "#bac9cc",
        "primary-fixed-dim": "#00daf3",
        "on-primary-container": "#00626e",
        "surface-bright": "#353944",
        "on-secondary-fixed": "#00164e",
        "on-background": "#dfe2f0",
        "inverse-surface": "#dfe2f0",
        "surface-container-high": "#262a34",
        "tertiary-container": "#99d9ff",
        "primary": "#c3f5ff",
        "tertiary-fixed": "#c4e7ff",
        "on-tertiary-fixed": "#001e2c",
        "secondary": "#b6c4ff",
        "on-surface": "#dfe2f0",
        "surface-container-highest": "#31353f",
        "inverse-on-surface": "#2c303b",
        "primary-fixed": "#9cf0ff",
        "on-primary": "#00363d",
        "outline-variant": "#3b494c",
        "primary-container": "#00e5ff",
        "on-tertiary": "#00354a",
        "secondary-fixed-dim": "#b6c4ff",
        "on-tertiary-container": "#006083",
        "error-container": "#93000a",
        "surface-variant": "#31353f",
        "surface-tint": "#00daf3",
        "on-tertiary-fixed-variant": "#004c69",
        "on-error": "#690005",
        "tertiary-fixed-dim": "#7bd0ff",
        "on-secondary-container": "#9db2ff",
        "on-primary-fixed-variant": "#004f58",
        "on-secondary-fixed-variant": "#264191",
        "tertiary": "#dbf0ff",
        "background": "#0f131d",
        "surface-container": "#1b2029",
        "outline": "#849396",
        "surface-container-low": "#171c25",
        "surface-container-lowest": "#0a0e17",
        "surface-dim": "#0f131d",
        "on-primary-fixed": "#001f24",
        "error": "#ffb4ab",
        "on-error-container": "#ffdad6",
        "surface": "#0f131d",
        "secondary-container": "#264191",

        // --- Backwards-compatible mapped tokens ---
        space: {
          950: '#0a0e17', // surface-container-lowest
          900: '#0f131d', // surface / background
          850: '#171c25', // surface-container-low
          800: '#1b2029', // surface-container
          750: '#262a34', // surface-container-high
          700: '#31353f', // surface-container-highest
          600: '#849396', // outline
        },
        brand: {
          50: '#f0f9ff',
          100: '#dbf0ff',
          200: '#c3f5ff',
          300: '#9cf0ff',
          400: '#00daf3',
          500: '#00e5ff',
          600: '#006875',
          700: '#004f58',
          800: '#00363d',
          900: '#001f24',
          950: '#00161a',
        },
        electric: {
          cyan: '#00e5ff',
          sky: '#00daf3',
          violet: '#b6c4ff',
          indigo: '#264191',
          emerald: '#00e5ff',
          amber: '#f59e0b',
          rose: '#ffb4ab',
        }
      },
      borderRadius: {
        DEFAULT: "0.125rem",
        md: "0.375rem",
        lg: "0.5rem",
        xl: "0.75rem",
        "2xl": "0.875rem",
        "3xl": "1rem",
        full: "9999px"
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        display: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
        mono: ['Inter', 'Consolas', 'Menlo', 'monospace'],
        "body-sm": ["Inter", "sans-serif"],
        "label-caps": ["Inter", "sans-serif"],
        "headline-lg-mobile": ["Plus Jakarta Sans", "sans-serif"],
        "telemetry-data": ["Inter", "sans-serif"],
        "display-lg": ["Plus Jakarta Sans", "sans-serif"],
        "body-lg": ["Inter", "sans-serif"],
        "body-md": ["Inter", "sans-serif"],
        "title-sm": ["Inter", "sans-serif"],
        "headline-md": ["Plus Jakarta Sans", "sans-serif"],
        "headline-lg": ["Plus Jakarta Sans", "sans-serif"],
        "display-lg-mobile": ["Plus Jakarta Sans", "sans-serif"]
      },
      boxShadow: {
        'glow-sm': '0 0 10px -2px rgba(0, 229, 255, 0.15)',
        'glow-md': '0 0 18px -4px rgba(0, 229, 255, 0.20)',
        'glow-lg': '0 0 24px -6px rgba(0, 229, 255, 0.25)',
        'glow-cyan': '0 0 12px rgba(0, 229, 255, 0.20)',
        'glow-secondary': '0 0 16px rgba(182, 196, 255, 0.15)',
        'glass-card': '0 4px 20px 0 rgba(0, 0, 0, 0.35), inset 0 1px 0 0 rgba(255, 255, 255, 0.04)',
        'glass-card-hover': '0 8px 24px -4px rgba(0, 0, 0, 0.5), inset 0 1px 0 0 rgba(0, 229, 255, 0.12)',
        'glass-inner': 'inset 0 1px 1px 0 rgba(255, 255, 255, 0.05)',
      },
      animation: {
        'pulse-slow': 'pulse 3.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 5s ease-in-out infinite',
        'aurora': 'aurora 15s ease infinite',
        'shimmer': 'shimmer 2.2s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        aurora: {
          '0%, 100%': { transform: 'translate(0, 0) scale(1)' },
          '33%': { transform: 'translate(30px, -25px) scale(1.08)' },
          '66%': { transform: 'translate(-25px, 20px) scale(0.95)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        }
      }
    },
  },
  plugins: [],
};
