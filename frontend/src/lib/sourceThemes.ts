export const sourceThemes = {
  github: {
    dotColor: '#3fb950',
    label: 'GitHub Trending',
    iconPath: 'M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 00-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0020 4.77 5.07 5.07 0 0019.91 1S18.73.65 16 2.48a13.38 13.38 0 00-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 005 4.77a5.44 5.44 0 00-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 009 18.13V22',
    fallbackBg: 'linear-gradient(135deg, #0d1117 0%, #161b22 50%, #21262d 100%)',
  },
  huggingface: {
    dotColor: '#FFB938',
    label: 'HuggingFace Papers',
    iconPath: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z',
    fallbackBg: 'linear-gradient(135deg, #1a1a2e 0%, #2d1b4e 50%, #1a1a2e 100%)',
  },
  openai_blog: {
    dotColor: '#19c37d',
    label: 'OpenAI Blog',
    iconPath: 'M12 2a10 10 0 100 20 10 10 0 000-20zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z',
    fallbackBg: 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 50%, #1a1a1a 100%)',
  },
  anthropic_blog: {
    dotColor: '#C4956A',
    label: 'Anthropic Blog',
    iconPath: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
    fallbackBg: 'linear-gradient(135deg, #1c1917 0%, #292524 50%, #1c1917 100%)',
  },
} as const;

export type SourceType = keyof typeof sourceThemes;

export function formatCount(n: number): string {
  if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
  return n.toString();
}
