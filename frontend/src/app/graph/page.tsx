import dynamic from 'next/dynamic';

const KnowledgeGraph = dynamic(
  () => import('@/components/graph/KnowledgeGraph'),
  { ssr: false }
);

export default function GraphRoute() {
  return <KnowledgeGraph />;
}
