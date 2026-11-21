/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        obsidian: {
          950: '#090a0f',
          900: '#0f1117',
          850: '#151821',
          800: '#1a1e29',
          700: '#262b3a',
          600: '#353c50',
          500: '#525c74',
        },
        paper: {
          50: '#fbfbfa',
          100: '#f6f6f4',
          200: '#ebebe8',
          300: '#deded9',
          400: '#b8b8b0',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'SFMono-Regular', 'Consolas', 'monospace'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
