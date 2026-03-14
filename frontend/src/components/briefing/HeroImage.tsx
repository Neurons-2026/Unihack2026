'use client';

export default function HeroImage({ imageUrl }: { imageUrl: string }) {
  return (
    <div
      style={{
        borderRadius: 14,
        overflow: 'hidden',
        marginBottom: 24,
        position: 'relative',
        height: 180,
      }}
    >
      <img
        src={imageUrl}
        alt=""
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(to top, rgba(0,0,0,0.4) 0%, transparent 60%)',
        }}
      />
    </div>
  );
}
