'use client';
import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
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
  const [dismissedCardIds, setDismissedCardIds] = useState<string[]>([]);
  const [swipeDir, setSwipeDir] = useState<'left' | 'right' | null>(null);
  const [swipeIntensity, setSwipeIntensity] = useState(0);
  const [toastAction, setToastAction] = useState<'save' | 'skip' | null>(null);
  const [toastTrigger, setToastTrigger] = useState(0);
  const pendingSwipeByCardId = useRef<Record<string, 'left' | 'right'>>({});
  const addItem = useBasketStore((s) => s.addItem);
  const logInteraction = useBasketStore((s) => s.logInteraction);

  const filteredCards = useMemo(
    () =>
      activeTopic === 'All'
        ? sampleCards
        : sampleCards.filter((c) => c.keywords.some((k) => k.toLowerCase().includes(activeTopic.toLowerCase()))),
    [activeTopic]
  );

  const dismissedLookup = useMemo(() => new Set(dismissedCardIds), [dismissedCardIds]);

  const visibleCards = useMemo(
    () => filteredCards.filter((card) => !dismissedLookup.has(card.id)),
    [filteredCards, dismissedLookup]
  );

  useEffect(() => {
    setDismissedCardIds([]);
    setSwipeDir(null);
    setSwipeIntensity(0);
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
      if (dir !== 'left' && dir !== 'right') return;
      pendingSwipeByCardId.current[cardId] = dir;

      const saved = dir === 'right';

      // Play sound
      if (saved) playSaveSound(); else playSkipSound();

      // Trigger ripple
      emitRipples(saved);
    },
    []
  );

  const handleCardLeftScreen = useCallback(
    (cardId: string) => {
      const dir = pendingSwipeByCardId.current[cardId];
      if (dir) {
        const saved = dir === 'right';
        setToastAction(saved ? 'save' : 'skip');
        setToastTrigger((prev) => prev + 1);
        setSwipeDir(null);
        setSwipeIntensity(0);

        if (saved) {
          addItem(cardId);
          logInteraction(cardId, 'save');
        } else {
          logInteraction(cardId, 'skip');
        }

        delete pendingSwipeByCardId.current[cardId];
      }

      setDismissedCardIds((prev) => (prev.includes(cardId) ? prev : [...prev, cardId]));
    },
    [addItem, logInteraction]
  );

  const currentCard = visibleCards[0];
  const nextCard = visibleCards[1];

  const cardFrameStyle = {
    width: '100%',
    height: '100%',
    padding: '10px 10px 16px',
    boxSizing: 'border-box' as const,
  };

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
        <div className="absolute inset-0 z-[2] w-full h-full" style={{ pointerEvents: 'none' }}>
          <div style={cardFrameStyle}>
            <CardItem card={nextCard} />
          </div>
        </div>
      )}

      {/* Active swipeable card */}
      <TinderCard
        key={currentCard.id}
        onSwipe={(dir) => handleSwipe(dir, currentCard.id)}
        onCardLeftScreen={() => handleCardLeftScreen(currentCard.id)}
        preventSwipe={['up', 'down']}
        className="absolute inset-0 z-10 w-full h-full"
      >
        <div style={cardFrameStyle}>
          <CardItem card={currentCard} />
        </div>
      </TinderCard>

      {/* Swipe feedback toast */}
      <SwipeToast action={toastAction} trigger={toastTrigger} />
    </div>
  );
}
