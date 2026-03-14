'use client';
import { useState, useEffect, useRef, useCallback } from 'react';
import TinderCard from 'react-tinder-card';
import { sampleCards } from '@/data/sampleCards';
import { useBasketStore } from '@/stores/useBasketStore';
import CardItem from './CardItem';
import EmptyState from './EmptyState';

export default function CardDeck({ activeTopic }: { activeTopic: string }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const addItem = useBasketStore((s) => s.addItem);
  const logInteraction = useBasketStore((s) => s.logInteraction);

  const filteredCards =
    activeTopic === 'All'
      ? sampleCards
      : sampleCards.filter((c) => c.keywords.some((k) => k.toLowerCase().includes(activeTopic.toLowerCase())));

  useEffect(() => {
    setCurrentIndex(0);
  }, [activeTopic]);

  const handleSwipe = useCallback(
    (dir: string, cardId: string) => {
      if (dir === 'right') {
        addItem(cardId);
        logInteraction(cardId, 'save');
      } else {
        logInteraction(cardId, 'skip');
      }
    },
    [addItem, logInteraction]
  );

  const handleCardLeftScreen = useCallback(() => {
    setCurrentIndex((prev) => prev + 1);
  }, []);

  const currentCard = filteredCards[currentIndex];

  if (!currentCard) {
    return (
      <div style={{ flex: 1, display: 'flex', padding: '10px 10px 16px' }}>
        <EmptyState />
      </div>
    );
  }

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        alignItems: 'stretch',
        padding: '10px 10px 16px',
        position: 'relative',
        minHeight: 0,
      }}
    >
      {/* Peek card — back */}
      <div
        style={{
          position: 'absolute',
          top: 14,
          left: 14,
          right: 14,
          bottom: 20,
          background: '#1c1c1e',
          borderRadius: 18,
          transform: 'scale(0.96)',
          opacity: 0.35,
        }}
      />
      {/* Peek card — middle */}
      <div
        style={{
          position: 'absolute',
          top: 12,
          left: 12,
          right: 12,
          bottom: 18,
          background: '#1c1c1e',
          borderRadius: 18,
          transform: 'scale(0.98)',
          opacity: 0.55,
        }}
      />

      {/* Active swipeable card */}
      <TinderCard
        key={currentCard.id}
        onSwipe={(dir) => handleSwipe(dir, currentCard.id)}
        onCardLeftScreen={handleCardLeftScreen}
        preventSwipe={['up', 'down']}
        className="absolute inset-0 z-10"
      >
        <div style={{ width: '100%', height: '100%', padding: '10px 10px 16px' }}>
          <CardItem card={currentCard} />
        </div>
      </TinderCard>
    </div>
  );
}
