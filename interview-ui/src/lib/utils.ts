import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60).toString().padStart(2, "0");
  const s = (seconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

export function playBase64Audio(
  b64: string,
  onStart?: () => void,
  onEnd?: () => void
): void {
  if (!b64) return;
  try {
    const raw = atob(b64);
    const buf = new ArrayBuffer(raw.length);
    const view = new Uint8Array(buf);
    for (let i = 0; i < raw.length; i++) view[i] = raw.charCodeAt(i);

    const ctx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
    ctx.decodeAudioData(buf, (audioBuf) => {
      const source = ctx.createBufferSource();
      source.buffer = audioBuf;
      source.connect(ctx.destination);
      onStart?.();
      source.onended = () => {
        onEnd?.();
        ctx.close();
      };
      source.start(0);
    });
  } catch (e) {
    console.error("Audio playback error:", e);
    onEnd?.();
  }
}
