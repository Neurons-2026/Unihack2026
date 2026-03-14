'use client';
import { useState, useEffect, useCallback, useRef } from 'react';
import TinderCard from 'react-tinder-card';
import { sampleCards } from '@/data/sampleCards';
import { useBasketStore } from '@/stores/useBasketStore';
import { unlockAudio, playSaveSound, playSkipSound } from '@/lib/sounds';
import { emitRipples } from '@/lib/rippleCanvas';
import CardItem from './CardItem';
import EmptyState from './EmptyState';
import RippleCanvas from './RippleCanvas';
import SwipeBackground from './SwipeBackground';
import SwipeToast from './SwipeToast';

export default function CardDeck({ activeTopic }: { activeTopic: string }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [swipeDir, setSwipeDir] = useState<'left' | 'right' | null>(null);
  const [swipeIntensity, setSwipeIntensity] = useState(0);
  const [toastAction, setToastAction] = useState<'save' | 'skip' | null>(null);
  const [toastTrigger, setToastTrigger] = useState(0);
  const addItem = useBasketStore((s) => s.addItem);
  const logInteraction = useBasketStore((s) => s.logInteraction);

  const filteredCards =
    activeTopic === 'All'
      ? sampleCards
      : sampleCards.filter((c) => c.keywords.some((k) => k.toLowerCase().includes(activeTopic.toLowerCase())));

  useEffect(() => {
    setCurrentIndex(0);
  }, [activeTopic]);

  const audioUnlocked = useRef(false);
  const handleFirstTouch = useCallback(() => {
    if (!audioUnlocked.current) {
      unlockAudio();
      audioUnlocked.current = true;
    }
  }, []);

  const handleSwipe = useCallback(
    (dir: string, cardId: string) => {
      const saved = dir === 'right';

      // Play sound
      if (saved) playSaveSound(); else playSkipSound();

      // Trigger ripple
      emitRipples(saved);

      // Show toast
      setToastAction(saved ? 'save' : 'skip');
      setToastTrigger((prev) => prev + 1);

      // Reset swipe feedback
      setSwipeDir(null);
      setSwipeIntensity(0);

      // Existing basket/logging logic
      if (saved) {
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
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '10px 10px 16px' }}>
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
      onTouchStart={handleFirstTouch}
      onMouseDown={handleFirstTouch}
    >
      {/* Swipe background color feedback */}
      <SwipeBackground direction={swipeDir} intensity={swipeIntensity} />

      {/* Ripple animation canvas */}
      <RippleCanvas />

      {/* Next card rendered underneath with the same layout as active card */}
      {nextCard && (
        <div className="absolute inset-0 z-0" style={{ pointerEvents: 'none' }}>
          <div style={{ width: '100%', height: '100%', padding: '10px 10px 16px' }}>
            <CardItem card={nextCard} />
          </div>
        </div>
      )}

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
          zIndex: 1,
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
          zIndex: 1,
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

      {/* Swipe feedback toast */}
      <SwipeToast action={toastAction} trigger={toastTrigger} />
    </div>
  );
}
