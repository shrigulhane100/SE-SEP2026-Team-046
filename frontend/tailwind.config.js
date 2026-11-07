export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: '#6558B8', indigo2: '#292447', lav: '#A99BEF', pale: '#EAE5FA', peach: '#E7A17C', ivory: '#F7F5F2',
        student: '#8274D8', mentor: '#397F78', admin: '#435A79',
        accent: 'rgb(var(--accent) / <alpha-value>)',
      },
      fontFamily: { head: ['Manrope', 'sans-serif'], sans: ['Inter', 'sans-serif'], mono: ['"DM Mono"', 'monospace'] },
      borderRadius: { card: '16px', section: '24px' },
      boxShadow: { soft: '0 1px 2px rgba(41,36,71,.04), 0 8px 24px -12px rgba(41,36,71,.12)' },
    },
  },
  plugins: [],
};
