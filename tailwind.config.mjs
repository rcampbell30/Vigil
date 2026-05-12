/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        'observatory': {
          'bg': '#050812',
          'panel': '#0a101d',
          'panel-2': '#0e1728',
          'panel-3': '#111c30',
          'line': '#1f314a',
          'line-soft': 'rgba(125, 164, 214, 0.14)',
          'text': '#c8d5e7',
          'muted': '#7c8fa8',
          'dim': '#52647d',
          'white': '#edf5ff',
        },
        'status': {
          'teal': '#3af7b5',
          'cyan': '#70d7ff',
          'amber': '#ffb454',
          'red': '#f75a3a',
        }
      },
      fontFamily: {
        'serif': ['Libre Baskerville', 'serif'],
        'mono': ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
