/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#090A0F',
        surface: {
          DEFAULT: '#12141C',
          muted: '#181B26',
          border: '#232736',
          hover: '#1F2433',
        },
        primary: {
          DEFAULT: '#3B82F6',
          hover: '#2563EB',
          accent: '#60A5FA',
        },
        cyber: {
          cyan: '#06B6D4',
          amber: '#F59E0B',
          emerald: '#10B981',
          rose: '#F43F5E'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}

