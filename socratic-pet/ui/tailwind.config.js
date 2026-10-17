/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './dashboard.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        glass: 'rgba(14,16,28,0.55)',
        accent: '#7c9cff',
        accent2: '#b388ff',
        warn: '#ff6b81',
        ok: '#4ade80',
      },
      boxShadow: { glow: '0 0 24px rgba(124,156,255,0.35)' },
    },
  },
  plugins: [],
};
