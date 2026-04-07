'use client';
import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useBasketStore } from '@/stores/useBasketStore';
import { unlockAudio, playSaveSound, playSkipSound } from '@/lib/sounds';
import { getCards, postInteraction, addToBasket } from '@/lib/api';
import { getSessionId } from '@/lib/session';
import { shareContent } from '@/lib/share';
import { Card } from '@/lib/types';
import { CardData } from '@/types/card';
import CardItem from './CardItem';
import EmptyState from './EmptyState';
import SwipeBackground from './SwipeBackground';
import SwipeIndicator from './SwipeIndicator';
import GravityCard, { type SwipeDir } from './GravityCard';

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
    imageUrl: c.image_url
      ? (c.image_url.startsWith('/static/')
          ? `${process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '') ?? 'http://localhost:8000'}${c.image_url}`
          : c.image_url)
      : `https://picsum.photos/seed/${c.id}/800/600`,
    metadata: c.metadata ?? {},
  };
}

type RevealState = { dir: SwipeDir; fading: boolean } | null;

function isSaveDir(dir: SwipeDir) {
  return dir === 'right' || dir === 'up';
}

export default function CardDeck({ activeTopic }: { activeTopic: string }) {
  const router = useRouter();
  const [allCards, setAllCards] = useState<CardData[]>([]);
  const [loading, setLoading] = useState(true);
  const [dismissedCardIds, setDismissedCardIds] = useState<string[]>([]);
  const [swipeDir, setSwipeDir] = useState<SwipeDir | null>(null);
  const [swipeIntensity, setSwipeIntensity] = useState(0);
  const [reveal, setReveal] = useState<RevealState>(null);
  const [iconHold, setIconHold] = useState<{ action: 'save' | 'skip'; fading: boolean } | null>(null);
  const [tagToast, setTagToast] = useState<{ keywords: string[]; action: 'save' | 'skip'; fading: boolean } | null>(null);
  const [shareCopied, setShareCopied] = useState(false);
  const tagToastTimer = useRef<ReturnType<typeof setTimeout>[]>([]);
  const revealTimer = useRef<ReturnType<typeof setTimeout>>();
  const iconTimers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const addItem = useBasketStore((s) => s.addItem);
  const logInteraction = useBasketStore((s) => s.logInteraction);
  const basketItems = useBasketStore((s) => s.items);
  const keywordScores = useBasketStore((s) => s.keywordScores);

  useEffect(() => {
    if (basketItems.length >= 3) {
      router.push('/briefing');
    }
  }, [basketItems.length, router]);
  const pendingDir = useRef<SwipeDir | null>(null);
  const cardStartTime = useRef<number>(Date.now());

  useEffect(() => {
    const sessionId = getSessionId();
    getCards(sessionId)
      .then((cards) => setAllCards(cards.map(mapCard)))
      .catch(() => setAllCards([]))
      .finally(() => setLoading(false));
  }, []);

  const filteredCards = useMemo(() => {
    const base = activeTopic === 'All'
      ? allCards
      : allCards.filter((c) =>
          c.keywords.some((k) => k.toLowerCase().includes(activeTopic.toLowerCase())),
        );
    return [...base].sort((a, b) => {
      const score = (card: CardData) =>
        card.keywords.reduce((sum, kw) => sum + (keywordScores[kw.toLowerCase()] ?? 0), 0);
      return score(b) - score(a);
    });
  }, [activeTopic, allCards, keywordScores]);

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

  const handleDrag = useCallback((offsetX: number, offsetY: number) => {
    const absX = Math.abs(offsetX);
    const absY = Math.abs(offsetY);
    const dominant = Math.max(absX, absY);
    if (dominant > 10) {
      const t = Math.min(dominant / 600, 1);
      const intensity = t * (2 - t);
      setReveal(null);
      setIconHold(null);
      iconTimers.current.forEach(clearTimeout);
      iconTimers.current = [];
      const dir: SwipeDir = absY > absX
        ? (offsetY < 0 ? 'up' : 'down')
        : (offsetX > 0 ? 'right' : 'left');
      setSwipeDir(dir);
      setSwipeIntensity(intensity);
    } else {
      setSwipeDir(null);
      setSwipeIntensity(0);
    }
  }, []);

  const currentCard = visibleCards[0];

  async function handleCardShare() {
    if (!currentCard) return;
    const result = await shareContent({
      title: currentCard.title,
      text: `${currentCard.title}\n\n${currentCard.description}`,
    });
    if (result === 'copied') {
      setShareCopied(true);
      setTimeout(() => setShareCopied(false), 1800);
    }
  }

  const handleSwipe = useCallback(
    (dir: SwipeDir) => {
      pendingDir.current = dir;
      setSwipeDir(dir);
      setSwipeIntensity(1);
      if (isSaveDir(dir)) playSaveSound();
      else playSkipSound();
    },
    [],
  );

  const handleCardLeftScreen = useCallback(() => {
    if (!currentCard) return;
    const dir = pendingDir.current;
    const resolvedDir: SwipeDir = dir ?? 'left';
    const save = isSaveDir(resolvedDir);
    const action: 'save' | 'skip' = save ? 'save' : 'skip';
    const sessionId = getSessionId();
    const dwellMs = Date.now() - cardStartTime.current;
    cardStartTime.current = Date.now();

    if (save) {
      addItem(currentCard);
      addToBasket(sessionId, currentCard.id).catch(() => {});
      postInteraction({ session_id: sessionId, card_id: currentCard.id, action: 'swipe_right', dwell_time_ms: dwellMs }).catch(() => {});
    } else {
      postInteraction({ session_id: sessionId, card_id: currentCard.id, action: 'swipe_left', dwell_time_ms: dwellMs }).catch(() => {});
    }

    logInteraction(currentCard.id, action, currentCard.keywords, dwellMs);

    // Show tag priority toast
    if (currentCard.keywords.length > 0) {
      tagToastTimer.current.forEach(clearTimeout);
      tagToastTimer.current = [];
      setTagToast({ keywords: currentCard.keywords, action, fading: false });
      tagToastTimer.current.push(setTimeout(() => setTagToast((t) => t ? { ...t, fading: true } : null), 1200));
      tagToastTimer.current.push(setTimeout(() => setTagToast(null), 1800));
    }

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

  const { nextIfSave, nextIfSkip } = useMemo(() => {
    if (!currentCard) return { nextIfSave: null, nextIfSkip: null };
    const remaining = visibleCards.filter((c) => c.id !== currentCard.id);
    const simulate = (delta: number) => {
      const sim = { ...keywordScores };
      for (const kw of currentCard.keywords) {
        const key = kw.toLowerCase();
        sim[key] = (sim[key] ?? 0) + delta;
      }
      const sorted = [...remaining].sort((a, b) => {
        const sc = (card: CardData) =>
          card.keywords.reduce((s, kw) => s + (sim[kw.toLowerCase()] ?? 0), 0);
        return sc(b) - sc(a);
      });
      return sorted[0] ?? null;
    };
    return { nextIfSave: simulate(1), nextIfSkip: simulate(-1) };
  }, [currentCard, visibleCards, keywordScores]);

  const nextCard = (swipeDir && isSaveDir(swipeDir)) ? nextIfSave
    : (swipeDir && !isSaveDir(swipeDir)) ? nextIfSkip
    : (nextIfSave ?? visibleCards[1]);

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
          key={nextCard.id}
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

      {/* Share button — sibling of GravityCard so it's outside pointer capture scope */}
      <button
        onClick={handleCardShare}
        style={{
          position: 'absolute',
          top: 24,
          right: 24,
          zIndex: 15,
          background: shareCopied ? 'rgba(74,222,128,0.2)' : 'rgba(0,0,0,0.35)',
          border: 'none',
          borderRadius: '50%',
          width: 32,
          height: 32,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          backdropFilter: 'blur(6px)',
          WebkitBackdropFilter: 'blur(6px)',
          transition: 'background 0.2s',
        }}
        aria-label="Share"
      >
        {shareCopied ? (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(74,222,128,0.9)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        ) : (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.85)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8" />
            <polyline points="16 6 12 2 8 6" />
            <line x1="12" y1="2" x2="12" y2="15" />
          </svg>
        )}
      </button>

      {/* Tag priority toast */}
      {tagToast && (
        <div
          style={{
            position: 'absolute',
            bottom: 250,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 20,
            pointerEvents: 'none',
            display: 'flex',
            gap: 6,
            flexWrap: 'wrap',
            justifyContent: 'center',
            maxWidth: '90%',
            opacity: tagToast.fading ? 0 : 1,
            transition: 'opacity 0.5s ease-out',
          }}
        >
          {tagToast.keywords.map((kw) => {
            const isSave = tagToast.action === 'save';
            return (
              <span
                key={kw}
                style={{
                  fontSize: 11,
                  fontWeight: 500,
                  padding: '4px 10px',
                  borderRadius: 20,
                  background: isSave ? 'rgba(74,222,128,0.15)' : 'rgba(248,113,113,0.15)',
                  color: isSave ? 'rgba(74,222,128,0.9)' : 'rgba(248,113,113,0.9)',
                  border: `1px solid ${isSave ? 'rgba(74,222,128,0.25)' : 'rgba(248,113,113,0.25)'}`,
                  whiteSpace: 'nowrap',
                }}
              >
                {isSave ? '↑' : '↓'} {kw}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}

function ActionIcon({
  swipeDir,
  swipeIntensity,
  hold,
}: {
  swipeDir: SwipeDir | null;
  swipeIntensity: number;
  hold: { action: 'save' | 'skip'; fading: boolean } | null;
}) {
  const dragActive = swipeDir !== null && swipeIntensity > 0.35;
  const holdActive = hold !== null && !hold.fading;
  const fading = hold?.fading ?? false;
  const visible = dragActive || holdActive;

  const action: 'save' | 'skip' | null = dragActive
    ? (swipeDir && isSaveDir(swipeDir) ? 'save' : 'skip')
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
