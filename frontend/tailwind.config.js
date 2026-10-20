/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        display: ['"Space Grotesk"', 'Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Consolas', 'Menlo', 'monospace'],
      },
      colors: {
        space: {
          950: '#030712', // Deepest background
          900: '#070b16', // Deep panel background
          850: '#0b1120', // Surface glass card base
          800: '#0f172a', // Card highlight
          750: '#141f36', // Elevated surface
          700: '#1e293b', // Border surface
          600: '#334155',
        },
        brand: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
          950: '#082f49',
        },
        electric: {
          cyan: '#00d2ff',
          sky: '#38bdf8',
          violet: '#a855f7',
          indigo: '#6366f1',
          emerald: '#10b981',
          amber: '#f59e0b',
          rose: '#f43f5e',
        }
      },
      boxShadow: {
        'glow-sm': '0 0 16px -2px rgba(14, 165, 233, 0.25)',
        'glow-md': '0 0 28px -4px rgba(14, 165, 233, 0.35)',
        'glow-lg': '0 0 44px -6px rgba(14, 165, 233, 0.45)',
        'glow-violet': '0 0 30px -5px rgba(139, 92, 246, 0.35)',
        'glow-emerald': '0 0 30px -5px rgba(16, 185, 129, 0.35)',
        'glow-rose': '0 0 30px -5px rgba(244, 63, 94, 0.35)',
        'glass-card': '0 8px 32px 0 rgba(0, 0, 0, 0.45), inset 0 1px 0 0 rgba(255, 255, 255, 0.08)',
        'glass-card-hover': '0 16px 40px -4px rgba(0, 0, 0, 0.6), inset 0 1px 0 0 rgba(255, 255, 255, 0.15)',
        'glass-inner': 'inset 0 1px 1px 0 rgba(255, 255, 255, 0.1)',
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
}
