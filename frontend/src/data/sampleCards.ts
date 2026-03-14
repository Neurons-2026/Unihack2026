import { CardData } from '@/types/card';

export const sampleCards: CardData[] = [
  // GitHub #1
  {
    id: 'github-1',
    source: 'github',
    title: 'LLaMA Safety Alignment Framework',
    description: 'Open-source toolkit for evaluating model safety across diverse scenarios.',
    keywords: ['Safety', 'Models', 'Open Source', 'Research'],
    sourceUrl: 'https://github.com/meta-llama/llama',
    publishedDate: 'Mar 12',
    imageUrl: 'https://picsum.photos/seed/llama-safety/800/600',
    metadata: {
      stars: 24500,
      forks: 3200,
      language: 'PyTorch',
    },
  },

  // GitHub #2
  {
    id: 'github-2',
    source: 'github',
    title: 'Prompt Injection Detection Suite',
    description: 'Real-time detection library for adversarial prompt attacks.',
    keywords: ['Safety', 'Security', 'Tools', 'Research'],
    sourceUrl: 'https://github.com/prompt-security-suite',
    publishedDate: 'Mar 11',
    imageUrl: 'https://picsum.photos/seed/prompt-injection/800/600',
    metadata: {
      stars: 8900,
      forks: 1200,
      language: 'Python',
    },
  },

  // GitHub #3
  {
    id: 'github-3',
    source: 'github',
    title: 'Multi-Modal Agent Orchestration',
    description: 'Framework coordinating vision, language, and action agents.',
    keywords: ['Agents', 'Models', 'Open Source', 'Tools'],
    sourceUrl: 'https://github.com/multi-modal-agents',
    publishedDate: 'Mar 10',
    imageUrl: 'https://picsum.photos/seed/multi-agent/800/600',
    metadata: {
      stars: 5600,
      forks: 920,
      language: 'TypeScript',
    },
  },

  // HuggingFace #1
  {
    id: 'huggingface-1',
    source: 'huggingface',
    title: 'Vision Transformer Safety Analysis',
    description: 'Comprehensive adversarial robustness evaluation for vision models.',
    keywords: ['Safety', 'Research', 'Models', 'Alignment'],
    sourceUrl: 'https://huggingface.co/papers/2024-vision-safety',
    publishedDate: 'Mar 9',
    imageUrl: 'https://picsum.photos/seed/vision-safety/800/600',
    metadata: {
      likes: 2340,
      downloads: 156000,
      taskType: 'Image Classification',
    },
  },

  // HuggingFace #2
  {
    id: 'huggingface-2',
    source: 'huggingface',
    title: 'Efficient Fine-Tuning for Edge',
    description: 'Lightweight adaptation techniques for mobile and edge devices.',
    keywords: ['Training', 'Models', 'Tools', 'Open Source'],
    sourceUrl: 'https://huggingface.co/papers/2024-edge-tuning',
    publishedDate: 'Mar 8',
    imageUrl: 'https://picsum.photos/seed/edge-training/800/600',
    metadata: {
      likes: 1890,
      downloads: 98500,
      taskType: 'Model Optimization',
    },
  },

  // OpenAI Blog #1
  {
    id: 'openai-1',
    source: 'openai_blog',
    title: 'Reasoning Models in Production',
    description: 'Scaling chain-of-thought reasoning for enterprise applications.',
    keywords: ['Models', 'Research', 'Alignment', 'Safety'],
    sourceUrl: 'https://openai.com/blog/reasoning-models',
    publishedDate: 'Mar 7',
    imageUrl: 'https://picsum.photos/seed/reasoning/800/600',
    metadata: {
      category: 'Research',
      readTimeMin: 8,
    },
  },

  // OpenAI Blog #2
  {
    id: 'openai-2',
    source: 'openai_blog',
    title: 'Constitutional AI: Building Safe Systems',
    description: 'New methods for aligning AI with human values at scale.',
    keywords: ['Safety', 'Alignment', 'Models', 'Research'],
    sourceUrl: 'https://openai.com/blog/constitutional-ai',
    publishedDate: 'Mar 6',
    imageUrl: 'https://picsum.photos/seed/constitutional/800/600',
    metadata: {
      category: 'Safety',
      readTimeMin: 10,
    },
  },

  // Anthropic Blog #1
  {
    id: 'anthropic-1',
    source: 'anthropic_blog',
    title: 'Scaling Interpretability Beyond LLMs',
    description: 'Techniques for understanding large neural network behavior.',
    keywords: ['Research', 'Alignment', 'Safety', 'Models'],
    sourceUrl: 'https://www.anthropic.com/research/interpretability',
    publishedDate: 'Mar 5',
    imageUrl: 'https://picsum.photos/seed/interpretability/800/600',
    metadata: {
      category: 'Interpretability',
      readTimeMin: 12,
    },
  },
];
