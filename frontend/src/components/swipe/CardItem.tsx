'use client';
import { CardData } from '@/types/card';
import { sourceThemes } from '@/lib/sourceThemes';
import SourceOverlay from './SourceOverlay';
import MetadataBadges from './MetadataBadges';


export default function CardItem({ card }: { card: CardData }) {
  const theme = sourceThemes[card.source];

  return (
    <div
      style={{
        borderRadius: 18,
        overflow: 'hidden',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: '#1c1c1e',
        transformOrigin: '50% 135%',
      }}
    >
      {/* IMAGE ZONE — expands to fill available space */}
      <div
        style={{
          position: 'relative',
          flex: 1,
          minHeight: 0,
          overflow: 'hidden',
        }}
      >
        {/* Layer 1: Article image */}
        {card.imageUrl ? (
          <img
            src={card.imageUrl}
            alt=""
            draggable={false}
            fetchPriority="high"
            decoding="async"
            style={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
        ) : (
          <div style={{ position: 'absolute', inset: 0, background: theme.fallbackBg }} />
        )}

        {/* Layer 2: Gradient overlay — fades image into text zone */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(to bottom, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.05) 40%, rgba(28,28,30,0.7) 75%, #1c1c1e 100%)',
          }}
        />

        {/* Layer 3: Source info at top */}
        <SourceOverlay source={card.source} date={card.publishedDate} />

        {/* Layer 4: Metadata at bottom */}
        <div style={{ position: 'absolute', bottom: 16, left: 18, right: 18 }}>
          <MetadataBadges metadata={card.metadata} source={card.source} />
        </div>
      </div>

      {/* TEXT ZONE — fixed height, never expands or shrinks */}
      <div
        style={{
          padding: '20px 18px 22px',
          flexShrink: 0,
          background: '#1c1c1e',
        }}
      >
        {/* Title */}
        <div
          style={{
            fontSize: 22,
            fontWeight: 500,
            color: '#fff',
            lineHeight: 1.22,
            letterSpacing: -0.5,
            marginBottom: 10,
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical' as const,
            overflow: 'hidden',
          }}
        >
          {card.title}
        </div>

        {/* Description — ONE LINE. No "why it matters" box. */}
        <div
          style={{
            fontSize: 14,
            color: 'rgba(255,255,255,0.42)',
            lineHeight: 1.5,
            marginBottom: 16,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical' as const,
            overflow: 'hidden',
          }}
        >
          {card.description}
        </div>

        {/* DO NOT add anything else here. No "why it matters" box. No extra text. */}
      </div>
    </div>
  );
}
