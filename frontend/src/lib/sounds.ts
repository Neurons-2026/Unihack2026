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
  } catch (e) {}
}

/**
 * Save sound: harmonic bell tone
 * A C5-G5-C6 triad played as pure sines, each staggered 60ms apart.
 * Each note has a sharp 10ms attack and a long ~500-700ms exponential decay.
 * Sounds like a singing bowl or crystal glass being tapped.
 * Total duration: ~120ms of audible attack, then rings out for ~1.5s.
 */
export function playSaveSound(): void {
  try {
    const a = getCtx();
    const now = a.currentTime;

    const notes = [
      { freq: 523.25, delay: 0, vol: 0.08, decay: 0.5 },    // C5
      { freq: 783.99, delay: 0.06, vol: 0.05, decay: 0.6 },  // G5
      { freq: 1046.5, delay: 0.12, vol: 0.035, decay: 0.7 }, // C6
    ];

    notes.forEach((n) => {
      const osc = a.createOscillator();
      const gain = a.createGain();
      osc.type = 'sine';
      osc.frequency.value = n.freq;

      // Sharp attack, long exponential decay
      gain.gain.setValueAtTime(0, now + n.delay);
      gain.gain.linearRampToValueAtTime(n.vol, now + n.delay + 0.01);
      gain.gain.setTargetAtTime(0.0001, now + n.delay + 0.06, n.decay);

      osc.connect(gain);
      gain.connect(a.destination);
      osc.start(now + n.delay);
      osc.stop(now + n.delay + 2.5);
    });
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
      gain.gain.linearRampToValueAtTime(0.06, now + t.delay + 0.015);
      gain.gain.setTargetAtTime(0.0001, now + t.delay + 0.05, 0.15);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(a.destination);
      osc.start(now + t.delay);
      osc.stop(now + t.delay + 0.6);
    });
  } catch (e) {}
}
