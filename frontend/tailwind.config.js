/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg:       '#f8fafc',
        surface:  '#ffffff',
        surface2: '#f1f5f9',
        border:   '#e2e8f0',
        muted:    '#94a3b8',
        accent:   '#3b82f6',
        pink:     '#ec4899',
        purple:   '#a855f7',
      },
    },
  },
  plugins: [],
}
