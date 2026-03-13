"use client";

import { useEffect, useState } from "react";
import { addToBasket, postInteraction } from "../lib/api";
import { useAppStore } from "../lib/store";
import { Card } from "../lib/types";
import { BasketBar } from "./BasketBar";
import { CardDeck } from "./CardDeck";

const BASKET_LIMIT = 5;

interface FeedClientProps {
  initialCards: Card[];
}

export function FeedClient({ initialCards }: FeedClientProps) {
  const { sessionId, basket, cards, setCards, addBasket } = useAppStore();
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    setCards(initialCards);
  }, [initialCards, setCards]);

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
      <CardDeck cards={cards} onSwipe={handleSwipe} />
      {status && <p className="text-xs text-slate-600">{status}</p>}
    </div>
  );
}
