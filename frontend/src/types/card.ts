export interface CardData {
  id: string;
  source: 'github' | 'huggingface' | 'openai_blog' | 'anthropic_blog';
  title: string;
  description: string;
  keywords: string[];
  sourceUrl: string;
  publishedDate: string;
  imageUrl: string;
  metadata: {
    stars?: number;
    forks?: number;
    language?: string;
    likes?: number;
    downloads?: number;
    taskType?: string;
    category?: string;
    readTimeMin?: number;
  };
}
