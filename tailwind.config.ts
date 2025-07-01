import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/templates/**/*.html',
    './app/static/js/**/*.js',
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('tailwindcss-animate'),
  ],
}
export default config 