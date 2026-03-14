let audioCtx: AudioContext | null = null;

function getCtx(): AudioContext {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
  }
  return audioCtx;
}

// Call this on the first user touch/click to unlock audio on iOS/Android
export function unlockAudio(): void {
  try {
    const ctx = getCtx();
    if (ctx.state === 'suspended') ctx.resume();
    loadSaveSound();
  } catch (e) {}
}

let saveSoundBuffer: AudioBuffer | null = null;
let saveSoundLoading = false;

function loadSaveSound(): void {
  if (saveSoundBuffer || saveSoundLoading) return;
  saveSoundLoading = true;
  fetch('/sounds/save.wav')
    .then((res) => res.arrayBuffer())
    .then((buf) => getCtx().decodeAudioData(buf))
    .then((decoded) => { saveSoundBuffer = decoded; })
    .catch(() => { saveSoundLoading = false; });
}

export function playSaveSound(): void {
  try {
    const ctx = getCtx();
    loadSaveSound();
    if (!saveSoundBuffer) return;
    const source = ctx.createBufferSource();
    source.buffer = saveSoundBuffer;
    source.connect(ctx.destination);
    source.start();
  } catch (e) {}
}

/**
 * Skip sound: soft dampened note
 * Two low tones (G3 + C4) through a 350Hz lowpass filter.
 * Very short (~50ms audible), immediately dampened.
 * Sounds like a muted piano key or a soft book closing.
 */
export function playSkipSound(): void {
  try {
    const a = getCtx();
    const now = a.currentTime;

    const tones = [
      { freq: 196, delay: 0 },     // G3
      { freq: 261.63, delay: 0.05 }, // C4
    ];

    tones.forEach((t) => {
      const osc = a.createOscillator();
      const gain = a.createGain();
      const filter = a.createBiquadFilter();

      osc.type = 'sine';
      osc.frequency.value = t.freq;

      filter.type = 'lowpass';
      filter.frequency.value = 350;
      filter.Q.value = 2;

      gain.gain.setValueAtTime(0, now + t.delay);
      gain.gain.linearRampToValueAtTime(0.25, now + t.delay + 0.015);
      gain.gain.setTargetAtTime(0.0001, now + t.delay + 0.05, 0.15);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(a.destination);
      osc.start(now + t.delay);
      osc.stop(now + t.delay + 0.6);
    });
  } catch (e) {}
}
