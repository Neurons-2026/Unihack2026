'use client';
import { SourceType } from '@/lib/sourceThemes';

const LOGO_DATA_URLS = {
  github: `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='rgba(255,255,255,0.85)'%3E%3Cpath d='M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.89 1.529 2.341 1.546 2.914 1.182.092-.916.35-1.546.636-1.903-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.14 20.164 22 16.418 22 12c0-5.523-4.477-10-10-10z'/%3E%3C/svg%3E`,
  
  huggingface: `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cdefs%3E%3ClinearGradient id='hf-grad' x1='0%25' y1='0%25' x2='0%25' y2='100%25'%3E%3Cstop offset='0%25' style='stop-color:rgba(255,255,255,0.85);stop-opacity:1'/%3E%3Cstop offset='100%25' style='stop-color:rgba(255,255,255,0.7);stop-opacity:1'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect x='2' y='2' width='20' height='20' rx='4' fill='%23FFE55C' opacity='0.15'/%3E%3Cpath d='M8 7 Q6 10 7 14 Q8 16 10 17 L14 17 Q16 16 17 14 Q18 10 16 7 M9 10 C9 9 8.5 8.5 8 8.5 M15 10 C15 9 15.5 8.5 16 8.5 M10 13 Q12 14 14 13' stroke='url(%23hf-grad)' stroke-width='1.2' fill='none' stroke-linecap='round'/%3E%3C/svg%3E`,
  
  openai_blog: `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cdefs%3E%3ClinearGradient id='oai-grad' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' style='stop-color:rgba(255,255,255,0.85);stop-opacity:1'/%3E%3Cstop offset='100%25' style='stop-color:rgba(255,255,255,0.65);stop-opacity:1'/%3E%3C/linearGradient%3E%3C/defs%3E%3Cpath d='M12 2 C16.97 2 21 6.03 21 11 A9 9 0 0 1 3 11 A9 9 0 0 1 12 2 Z' fill='none' stroke='url(%23oai-grad)' stroke-width='1.5'/%3E%3Cpath d='M12 6 L12 16 M8 12 L16 12' stroke='url(%23oai-grad)' stroke-width='1.2' stroke-linecap='round'/%3E%3Ccircle cx='12' cy='11' r='2.5' fill='url(%23oai-grad)'/%3E%3C/svg%3E`,
  
  anthropic_blog: `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cdefs%3E%3ClinearGradient id='anthro-grad' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' style='stop-color:rgba(255,255,255,0.85);stop-opacity:1'/%3E%3Cstop offset='100%25' style='stop-color:rgba(255,255,255,0.65);stop-opacity:1'/%3E%3C/linearGradient%3E%3C/defs%3E%3Cpath d='M12 2 Q18 8 15 14 Q13 18 12 20 Q11 18 9 14 Q6 8 12 2' fill='none' stroke='url(%23anthro-grad)' stroke-width='1.5' stroke-linejoin='round'/%3E%3Cpath d='M8 12 Q12 14 16 12' fill='none' stroke='url(%23anthro-grad)' stroke-width='1.2' stroke-linecap='round'/%3E%3C/svg%3E`,
} as const;

export default function LogoIcon({ source, size = 20 }: { source: SourceType; size?: number }) {
  const logoUrl = LOGO_DATA_URLS[source];
  
  return (
    <img
      src={logoUrl}
      alt={`${source} logo`}
      width={size}
      height={size}
      style={{
        display: 'block',
        userSelect: 'none',
      }}
    />
  );
}
