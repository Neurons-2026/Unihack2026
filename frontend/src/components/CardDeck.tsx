"use client";

import { useCallback } from "react";
import { Card } from "../lib/types";
import { CardItem } from "./CardItem";

interface CardDeckProps {
  cards: Card[];
  onSwipe: (direction: "left" | "right", card: Card) => void;
}

export function CardDeck({ cards, onSwipe }: CardDeckProps) {
  const handleSwipe = useCallback(
    (direction: "left" | "right", card: Card) => {
      onSwipe(direction, card);
    },
    [onSwipe]
  );

  if (!cards.length) {
    return <p className="text-sm text-slate-600">No cards yet. Seed or ingest data to get started.</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      {cards.map((card) => (
        <CardItem key={card.id} card={card} onSwipe={handleSwipe} />
      ))}
    </div>
  );
}
