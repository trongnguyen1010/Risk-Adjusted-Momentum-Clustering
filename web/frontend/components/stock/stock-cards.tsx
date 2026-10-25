"use client";
import type { StockCard } from "@/lib/types";
import { formatMetric, ratingTone, statusText } from "@/lib/indicator-format";
import { InfoTip } from "./info-tip";

export function StockCards({
  cards,
  sector,
}: {
  cards: StockCard[];
  sector: string;
}) {
  return (
    <div className="stock-cards" aria-label="Chỉ số chính">
      {cards.map((card) => (
        <div className="stock-card" key={card.metric} data-metric={card.metric}>
          <div className="stock-card-label">
            <span>{card.label}</span>
            <InfoTip label={card.label} text={card.description} />
          </div>
          <strong className={card.value == null ? "is-empty" : ""}>
            {formatMetric(card.value, card.unit, card.metric)}
          </strong>
          {card.value == null ? (
            <small>{statusText(card, card.year, sector)}</small>
          ) : card.rating ? (
            <span className={`badge ${ratingTone(card.rating)}`}>
              {card.rating}
            </span>
          ) : (
            <small>Năm {card.year}</small>
          )}
        </div>
      ))}
    </div>
  );
}
