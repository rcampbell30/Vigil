import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  site: 'https://rcampbell30.github.io',
  base: '/Vigil',
  integrations: [tailwind()],
  output: 'static',
});
