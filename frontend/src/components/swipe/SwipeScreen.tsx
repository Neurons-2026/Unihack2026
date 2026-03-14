'use client';
import { useState } from 'react';
import Header from './Header';
import TopicFilters from './TopicFilters';
import CardDeck from './CardDeck';

export default function SwipeScreen() {
  const [activeTopic, setActiveTopic] = useState('All');

  return (
    <div
      style={{
        maxWidth: 390,
        margin: '0 auto',
        height: '100dvh',
        background: '#111111',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{ paddingTop: 48, paddingLeft: 20, paddingRight: 20, flexShrink: 0 }}>
        <Header />
        <TopicFilters activeTopic={activeTopic} onTopicChange={setActiveTopic} />
      </div>
      <CardDeck activeTopic={activeTopic} />
    </div>
  );
}
