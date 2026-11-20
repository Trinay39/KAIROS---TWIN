/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: '#121317',
        surface: '#16181f',
        surface2: '#1a1b22',
        card: '#181921',
        accent: '#00bfa5',
        accent2: '#f0a500',
        violet: '#7c6cf5',
        danger: '#e0606e',
        muted: '#a0a3b0',
        border: 'rgba(255,255,255,0.08)',
      },
      fontFamily: {
        display: ['Inter', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      borderRadius: { xl: '16px', lg: '12px', sm: '8px' },
    },
  },
  plugins: [],
};
