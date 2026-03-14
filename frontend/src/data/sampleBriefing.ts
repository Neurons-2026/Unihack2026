import { BriefingData } from '@/types/briefing';

export const sampleBriefing: BriefingData = {
  id: 'briefing-2026-03-14',
  generatedAt: 'March 14, 2026',
  readingTimeMin: 10,
  headlineTitle: 'Open-source safety tooling reaches a tipping point',
  topicTags: ['Safety', 'Open Source', 'Models'],
  heroImageUrl: 'https://images.pexels.com/photos/34804018/pexels-photo-34804018.jpeg?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop',
  overview:
    "Today's AI landscape is dominated by a push toward standardised safety evaluation. A new open-source framework from GitHub is gaining traction as the first benchmark suite that could become an industry default — and two Fortune 500 companies are already piloting it. Meanwhile, a 7B parameter model on HuggingFace is outperforming GPT-4V on visual reasoning, signaling that the gap between open and proprietary models isn't just closing — it's collapsing.",
  signals: [
    {
      id: 's1',
      source: 'github',
      title: 'AI safety framework for model alignment',
      summary:
        'An open-source toolkit that benchmarks LLM safety across bias, toxicity, and instruction-following has reached 2.4k stars in its first week. It supports custom evaluation suites and integrates with all major model providers including OpenAI, Anthropic, and Google.',
      sourceUrl: 'https://github.com',
      imageUrl: 'https://images.pexels.com/photos/8438998/pexels-photo-8438998.jpeg?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop',
    },
    {
      id: 's2',
      source: 'huggingface',
      title: '7B model outperforms GPT-4V on visual reasoning',
      summary:
        'A fully open-weight multimodal model achieves state-of-the-art results on visual reasoning benchmarks while enabling local deployment and fine-tuning. Downloaded 50k times in its first three days.',
      sourceUrl: 'https://huggingface.co',
      imageUrl: 'https://images.pexels.com/photos/18069814/pexels-photo-18069814.png?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop',
    },
    {
      id: 's3',
      source: 'openai_blog',
      title: 'Structured outputs API for reliable JSON',
      summary:
        'New API feature guarantees valid JSON schema adherence in responses, reducing parsing failures in production applications by up to 95%.',
      sourceUrl: 'https://openai.com/blog',
      imageUrl: 'https://images.pexels.com/photos/2061168/pexels-photo-2061168.jpeg?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop',
    },
    {
      id: 's4',
      source: 'anthropic_blog',
      title: 'Constitutional AI training improvements',
      summary:
        'New iteration of constitutional training reduces refusal rates by 40% while maintaining safety properties through improved constitutional principles.',
      sourceUrl: 'https://anthropic.com/blog',
      imageUrl: 'https://images.pexels.com/photos/17485632/pexels-photo-17485632.png?auto=compress&cs=tinysrgb&w=800&h=400&fit=crop',
    },
  ],
  whyItMatters:
    'The convergence of open-source safety tooling and increasingly capable small models is shifting power dynamics. Companies no longer need to rely solely on proprietary APIs for production-grade AI — and regulators now have auditable benchmarks to point to. This is not a gradual shift. Three of the four signals today point in the same direction: open, auditable, deployable AI is becoming the default expectation.',
  inlineVisualUrl: 'https://images.pexels.com/photos/7580765/pexels-photo-7580765.jpeg?auto=compress&cs=tinysrgb&w=800&h=350&fit=crop',
  inlineVisualCaption: 'Open-source model performance vs proprietary (2024–2026)',
  trends: [
    'Safety benchmarking becoming a prerequisite for enterprise AI adoption',
    'Sub-10B parameter models closing the gap with proprietary frontier models',
    'EU AI Act compliance driving structured evaluation adoption in Q2',
  ],
  takeaways: [
    'Open-source safety tooling is maturing rapidly — first standardised benchmarks are here',
    'Small open models are production-viable, not just research toys',
    'The regulatory push for auditability is accelerating adoption of structured evaluation',
  ],
};
