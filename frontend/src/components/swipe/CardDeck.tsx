'use client';
import { useState, useEffect, useCallback } from 'react';
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

  const nextCard = filteredCards[currentIndex + 1];

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
      {/* Next card rendered underneath with the same layout as active card */}
      {nextCard && (
        <div className="absolute inset-0 z-0" style={{ pointerEvents: 'none' }}>
          <div style={{ width: '100%', height: '100%', padding: '10px 10px 16px' }}>
            <CardItem card={nextCard} />
          </div>
        </div>
      )}

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
