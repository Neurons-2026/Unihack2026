'use client';
import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useBasketStore } from '@/stores/useBasketStore';
import { unlockAudio, playSaveSound, playSkipSound } from '@/lib/sounds';
import { getCards, postInteraction, addToBasket } from '@/lib/api';
import { getSessionId } from '@/lib/session';
import { Card } from '@/lib/types';
import { CardData } from '@/types/card';
import CardItem from './CardItem';
import EmptyState from './EmptyState';
import SwipeBackground from './SwipeBackground';
import SwipeIndicator from './SwipeIndicator';
import GravityCard from './GravityCard';

const KNOWN_SOURCES: CardData['source'][] = ['github', 'huggingface', 'openai_blog', 'anthropic_blog'];

function mapCard(c: Card): CardData {
  const source: CardData['source'] = KNOWN_SOURCES.includes(c.source as CardData['source'])
    ? (c.source as CardData['source'])
    : 'github';
  return {
    id: c.id,
    source,
    title: c.card_title,
    description: c.card_summary,
    keywords: c.keywords,
    sourceUrl: c.source_url ?? '',
    publishedDate: c.published_at ?? '',
    imageUrl: c.image_url ?? `https://picsum.photos/seed/${c.id}/800/600`,
    metadata: c.metadata ?? {},
  };
}

type RevealState = { dir: 'left' | 'right'; fading: boolean } | null;

export default function CardDeck({ activeTopic }: { activeTopic: string }) {
  const [allCards, setAllCards] = useState<CardData[]>([]);
  const [loading, setLoading] = useState(true);
  const [dismissedCardIds, setDismissedCardIds] = useState<string[]>([]);
  const [swipeDir, setSwipeDir] = useState<'left' | 'right' | null>(null);
  const [swipeIntensity, setSwipeIntensity] = useState(0);
  const [reveal, setReveal] = useState<RevealState>(null);
  const [iconHold, setIconHold] = useState<{ action: 'save' | 'skip'; fading: boolean } | null>(null);
  const revealTimer = useRef<ReturnType<typeof setTimeout>>();
  const iconTimers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const addItem = useBasketStore((s) => s.addItem);
  const logInteraction = useBasketStore((s) => s.logInteraction);
  const pendingDir = useRef<'left' | 'right' | null>(null);

  useEffect(() => {
    const sessionId = getSessionId();
    getCards(sessionId)
      .then((cards) => setAllCards(cards.map(mapCard)))
      .catch(() => setAllCards([]))
      .finally(() => setLoading(false));
  }, []);

  const filteredCards = useMemo(
    () =>
      activeTopic === 'All'
        ? allCards
        : allCards.filter((c) =>
            c.keywords.some((k) => k.toLowerCase().includes(activeTopic.toLowerCase())),
          ),
    [activeTopic, allCards],
  );

  const dismissedLookup = useMemo(() => new Set(dismissedCardIds), [dismissedCardIds]);

  const visibleCards = useMemo(
    () => filteredCards.filter((card) => !dismissedLookup.has(card.id)),
    [filteredCards, dismissedLookup],
  );

  useEffect(() => {
    setDismissedCardIds([]);
    setSwipeDir(null);
    setSwipeIntensity(0);
    setReveal(null);
  }, [activeTopic]);

  const audioUnlocked = useRef(false);
  const handleFirstTouch = useCallback(() => {
    if (!audioUnlocked.current) {
      unlockAudio();
      audioUnlocked.current = true;
    }
  }, []);

  const handleDrag = useCallback((offsetX: number) => {
    const absX = Math.abs(offsetX);
    if (absX > 10) {
      const t = Math.min(absX / 600, 1);
      const intensity = t * (2 - t);
      setReveal(null);
      setIconHold(null);
      iconTimers.current.forEach(clearTimeout);
      iconTimers.current = [];
      setSwipeDir(offsetX > 0 ? 'right' : 'left');
      setSwipeIntensity(intensity);
    } else {
      setSwipeDir(null);
      setSwipeIntensity(0);
    }
  }, []);

  const currentCard = visibleCards[0];

  const handleSwipe = useCallback(
    (dir: 'left' | 'right') => {
      pendingDir.current = dir;
      setSwipeDir(dir);
      setSwipeIntensity(1);
      if (dir === 'right') playSaveSound();
      else playSkipSound();
    },
    [],
  );

  const handleCardLeftScreen = useCallback(() => {
    if (!currentCard) return;
    const dir = pendingDir.current;
    const resolvedDir: 'left' | 'right' = dir ?? 'left';
    const action: 'save' | 'skip' = resolvedDir === 'right' ? 'save' : 'skip';
    const sessionId = getSessionId();

    if (resolvedDir === 'right') {
      addItem(currentCard);
      addToBasket(sessionId, currentCard.id).catch(() => {});
      postInteraction({ session_id: sessionId, card_id: currentCard.id, action: 'swipe_right' }).catch(() => {});
    } else {
      postInteraction({ session_id: sessionId, card_id: currentCard.id, action: 'swipe_left' }).catch(() => {});
    }

    logInteraction(currentCard.id, action);

    setReveal({ dir: resolvedDir, fading: false });
    setSwipeDir(null);
    setSwipeIntensity(0);

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        setReveal({ dir: resolvedDir, fading: true });
      });
    });

    clearTimeout(revealTimer.current);
    revealTimer.current = setTimeout(() => setReveal(null), 800);

    setIconHold({ action, fading: false });
    iconTimers.current.forEach(clearTimeout);
    iconTimers.current = [];
    iconTimers.current.push(setTimeout(() => setIconHold({ action, fading: true }), 900));
    iconTimers.current.push(setTimeout(() => setIconHold(null), 1600));

    pendingDir.current = null;
    setDismissedCardIds((prev) =>
      prev.includes(currentCard.id) ? prev : [...prev, currentCard.id],
    );
  }, [currentCard, addItem, logInteraction]);

  const nextCard = visibleCards[1];

  const cardFrameStyle = {
    width: '100%',
    height: '100%',
    padding: '10px 10px 16px',
    boxSizing: 'border-box' as const,
  };

  if (loading) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: 14 }}>Loading cards…</div>
      </div>
    );
  }

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
      {/* Next card sits at the bottom of the stack */}
      {nextCard && (
        <div
          className="absolute inset-0 z-[1] w-full h-full"
          style={{
            pointerEvents: 'none',
            transform: reveal
              ? reveal.fading ? 'scale(1)' : 'scale(0.975)'
              : 'scale(1)',
            transition: reveal?.fading
              ? 'transform 0.7s cubic-bezier(0.4,0,0.2,1)'
              : 'none',
            transformOrigin: '50% 50%',
          }}
        >
          <div style={cardFrameStyle}>
            <CardItem card={nextCard} />
          </div>
        </div>
      )}

      {/* Color wash — z-5, between next card and active card */}
      <SwipeBackground direction={swipeDir} intensity={swipeIntensity} reveal={reveal} />

      {/* Active card — z-10, on top */}
      <GravityCard
        key={currentCard.id}
        onSwipe={handleSwipe}
        onCardLeftScreen={handleCardLeftScreen}
        onDrag={handleDrag}
        className="absolute inset-0 z-10 w-full h-full"
      >
        <div style={cardFrameStyle}>
          <div style={{ position: 'relative', height: '100%' }}>
            <CardItem card={currentCard} />
            <SwipeIndicator direction={swipeDir} intensity={swipeIntensity} />
          </div>
        </div>
      </GravityCard>

      <ActionIcon swipeDir={swipeDir} swipeIntensity={swipeIntensity} hold={iconHold} />
    </div>
  );
}

function ActionIcon({
  swipeDir,
  swipeIntensity,
  hold,
}: {
  swipeDir: 'left' | 'right' | null;
  swipeIntensity: number;
  hold: { action: 'save' | 'skip'; fading: boolean } | null;
}) {
  const dragActive = swipeDir !== null && swipeIntensity > 0.35;
  const holdActive = hold !== null && !hold.fading;
  const fading = hold?.fading ?? false;
  const visible = dragActive || holdActive;

  const action: 'save' | 'skip' | null = dragActive
    ? (swipeDir === 'right' ? 'save' : 'skip')
    : hold?.action ?? null;

  if (!visible && !fading) return null;

  const isSave = action === 'save';

  return (
    <div
      style={{
        position: 'absolute',
        inset: '10px 10px 16px',
        zIndex: 8,
        pointerEvents: 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        opacity: fading ? 0 : visible ? 1 : 0,
        transform: fading ? 'scale(1.15)' : 'scale(1)',
        transition: fading
          ? 'opacity 0.6s ease-out, transform 0.6s ease-out'
          : 'none',
      }}
    >
      <div
        style={{
          width: 56,
          height: 56,
          borderRadius: '50%',
          background: isSave ? 'rgba(74,222,128,0.88)' : 'rgba(248,113,113,0.88)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: isSave
            ? '0 0 40px rgba(74,222,128,0.3)'
            : '0 0 40px rgba(248,113,113,0.3)',
        }}
      >
        {isSave ? (
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        )}
      </div>
    </div>
  );
}
