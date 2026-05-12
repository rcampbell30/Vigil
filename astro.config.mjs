import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

const isGitHubPages = process.env.GITHUB_PAGES === 'true';

export default defineConfig({
  site: isGitHubPages ? 'https://rcampbell30.github.io' : undefined,
  base: isGitHubPages ? '/Vigil' : '/',
  integrations: [tailwind()],
  output: 'static',
});
