'use client';

export default function InlineVisual({
  imageUrl,
  caption,
}: {
  imageUrl: string;
  caption: string;
}) {
  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ borderRadius: 12, overflow: 'hidden', height: 160, position: 'relative' }}>
        <img
          src={imageUrl}
          alt={caption}
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>
      {caption && (
        <p
          style={{
            fontSize: 11,
            color: 'rgba(255,255,255,0.3)',
            marginTop: 8,
            textAlign: 'center',
          }}
        >
          {caption}
        </p>
      )}
    </div>
  );
}
