export interface BriefingSignal {
  id: string;
  source: 'github' | 'huggingface' | 'openai_blog' | 'anthropic_blog';
  title: string;
  summary: string;
  sourceUrl: string;
  imageUrl: string;
}

export interface BriefingData {
  id: string;
  generatedAt: string;
  readingTimeMin: number;
  headlineTitle: string;
  topicTags: string[];
  heroImageUrl: string;
  overview: string;
  signals: BriefingSignal[];
  whyItMatters: string;
  inlineVisualUrl: string;
  inlineVisualCaption: string;
  trends: string[];
  takeaways: string[];
}
