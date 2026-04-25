/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Outfit', 'sans-serif'],
        serif: ['Lora', 'serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        sidebar: {
          DEFAULT: '#0f0f10',
          surface: '#1a1a1b',
          border: 'rgba(255,255,255,0.08)',
          text: '#e5e3de',
          muted: '#9b9794',
          accent: '#f97316',
        },
        content: {
          DEFAULT: '#f7f6f3',
          surface: '#ffffff',
          border: '#e4e2dc',
          text: '#1c1b18',
          muted: '#6b6860',
          accent: '#f97316',
        },
        accent: {
          DEFAULT: '#f97316',
          muted: '#c2410c',
          soft: 'rgba(249,115,22,0.12)',
          hover: '#ea6c0a',
        },
        agent: {
          a: '#f97316',
          b: '#e11d48',
          c: '#d97706',
          d: '#2563eb',
        },
        status: {
          success: '#16a34a',
          warning: '#d97706',
          error: '#dc2626',
          idle: '#9b9794',
        },
      },
      borderRadius: {
        card: '10px',
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.10)',
        focus: '0 0 0 2px #f97316',
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-up': 'slideUp 0.3s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
        shimmer: 'shimmer 1.5s infinite',
      },
      keyframes: {
        slideUp: {
          '0%': { transform: 'translateY(12px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      transitionDuration: {
        150: '150ms',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
