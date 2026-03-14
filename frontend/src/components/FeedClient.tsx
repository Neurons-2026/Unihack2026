"use client";

import { useEffect, useState } from "react";
import { addToBasket, getCards, postInteraction } from "../lib/api";
import { useAppStore } from "../lib/store";
import { Card } from "../lib/types";
import { BasketBar } from "./BasketBar";
import { CardDeck } from "./CardDeck";

const BASKET_LIMIT = 5;

interface FeedClientProps {
  initialCards: Card[];
}

const fallbackCards: Card[] = [
  {
    id: "fallback-1",
    card_title: "New model tops long-context benchmark",
    card_summary: "A lightweight transformer variant improves efficiency for 32k tokens.",
    keywords: ["transformer", "long context", "research"],
    source: "huggingface",
    source_url: "https://huggingface.co/papers",
    thumbnail_keyword: "transformer",
  },
  {
    id: "fallback-2",
    card_title: "GitHub trending: eval toolkit",
    card_summary: "Open-source harness to benchmark small LLMs quickly.",
    keywords: ["github", "eval", "tooling"],
    source: "github",
    source_url: "https://github.com/trending",
    thumbnail_keyword: "github",
  },
];

export function FeedClient({ initialCards }: FeedClientProps) {
  const { sessionId, basket, cards, setCards, addBasket } = useAppStore();
  const [status, setStatus] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadCards() {
      setIsLoading(true);
      try {
        const latest = await getCards(sessionId);
        if (!cancelled) {
          if (latest.length > 0) {
            setCards(latest);
            setStatus(null);
          } else {
            setCards(initialCards.length ? initialCards : fallbackCards);
            setStatus("No cards returned yet. Showing fallback feed.");
          }
        }
      } catch (err) {
        if (!cancelled) {
          setCards(initialCards.length ? initialCards : fallbackCards);
          setStatus("Failed to load latest cards. Showing fallback feed.");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadCards();

    return () => {
      cancelled = true;
    };
  }, [initialCards, sessionId, setCards]);

  async function handleSwipe(direction: "left" | "right", card: Card) {
    setStatus(null);
    try {
      await postInteraction({
        session_id: sessionId,
        card_id: card.id,
        action: direction === "right" ? "swipe_right" : "swipe_left",
      });
    } catch (err) {
      setStatus("Failed to log interaction (still proceeding)");
    }

    if (direction === "right") {
      if (basket.length >= BASKET_LIMIT) {
        setStatus("Basket limit reached");
        return;
      }
      try {
        const added = await addToBasket(sessionId, card.id);
        addBasket(added);
        setStatus("Added to basket");
      } catch (err) {
        setStatus("Failed to add to basket");
      }
    }
  }

  return (
    <div className="space-y-4">
      <BasketBar count={basket.length} limit={BASKET_LIMIT} />
      {isLoading && <p className="text-xs text-slate-600">Loading cards...</p>}
      <CardDeck cards={cards} onSwipe={handleSwipe} />
      {status && <p className="text-xs text-slate-600">{status}</p>}
    </div>
  );
}
