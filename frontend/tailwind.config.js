/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        'aviation-navy': '#1F3A5F',      // Primary
        'signal-blue': '#2E6E9E',        // Secondary / accent
        'bg-offwhite': '#F7F8FA',        // Background
        'surface-white': '#FFFFFF',      // Surface / card
        'text-charcoal': '#222222',      // Text — primary
        'text-slate': '#6B7280',         // Text — muted
        'severity-low': '#3E9C5E',
        'severity-medium': '#D9A404',
        'severity-high': '#E0662A',
        'severity-critical': '#C4331E',
        'success': '#3E9C5E',
        'error': '#C4331E',
        'border-light': '#D9DEE3',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      spacing: {
        // base unit 8px, spec calls out 8/16/24/32 explicitly
        '8': '8px', '16': '16px', '24': '24px', '32': '32px',
      },
      maxWidth: {
        'content': '1040px',
      },
      borderRadius: {
        'card': '12px',
        'button': '8px',
        'input': '8px',
      },
    },
  },
  plugins: [],
}
