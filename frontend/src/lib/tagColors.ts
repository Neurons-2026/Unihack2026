type TagStyle = { bg: string; text: string };

const map: Record<string, TagStyle> = {
  safety:        { bg: 'rgba(59,130,246,0.15)',  text: 'rgba(147,197,253,0.85)' },
  security:      { bg: 'rgba(59,130,246,0.15)',  text: 'rgba(147,197,253,0.85)' },
  'open source': { bg: 'rgba(34,197,94,0.15)',   text: 'rgba(134,239,172,0.85)' },
  oss:           { bg: 'rgba(34,197,94,0.15)',   text: 'rgba(134,239,172,0.85)' },
  alignment:     { bg: 'rgba(234,179,8,0.15)',   text: 'rgba(253,224,71,0.8)' },
  training:      { bg: 'rgba(234,179,8,0.15)',   text: 'rgba(253,224,71,0.8)' },
  models:        { bg: 'rgba(168,85,247,0.15)',  text: 'rgba(196,181,253,0.85)' },
  agents:        { bg: 'rgba(168,85,247,0.15)',  text: 'rgba(196,181,253,0.85)' },
  research:      { bg: 'rgba(236,72,153,0.15)',  text: 'rgba(249,168,212,0.85)' },
};

const fallback: TagStyle = { bg: 'rgba(255,255,255,0.08)', text: 'rgba(255,255,255,0.5)' };

export function getTagStyle(keyword: string): TagStyle {
  return map[keyword.toLowerCase()] ?? fallback;
}
