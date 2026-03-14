export const sourceThemes = {
  github: {
    dotColor: '#3fb950',
    label: 'GitHub Trending',
    fallbackBg: 'linear-gradient(135deg, #0d1117 0%, #161b22 50%, #21262d 100%)',
  },
  huggingface: {
    dotColor: '#FFB938',
    label: 'HuggingFace Papers',
    fallbackBg: 'linear-gradient(135deg, #1a1a2e 0%, #2d1b4e 50%, #1a1a2e 100%)',
  },
  openai_blog: {
    dotColor: '#19c37d',
    label: 'OpenAI Blog',
    fallbackBg: 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 50%, #1a1a1a 100%)',
  },
  anthropic_blog: {
    dotColor: '#C4956A',
    label: 'Anthropic Blog',
    fallbackBg: 'linear-gradient(135deg, #1c1917 0%, #292524 50%, #1c1917 100%)',
  },
} as const;

export type SourceType = keyof typeof sourceThemes;

export function formatCount(n: number): string {
  if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
  return n.toString();
}
