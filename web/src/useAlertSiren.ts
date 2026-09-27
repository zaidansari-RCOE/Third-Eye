import { useCallback, useEffect, useRef, useState } from "react";

type SirenInputs = {
  /** True while the selected/any vehicle is on a road segment flagged is_blind_curve by the backend map. */
  blindCurveApproach: boolean;
  /** Mirrors the real safety.simulated_brake_active field — never invented client-side. */
  brakeActive: boolean;
};

/**
 * Ambient alert engine. Silent by default. Browsers require a user gesture
 * before audio can play, so nothing sounds until `enable()` is called from a
 * click handler. While enabled: a pulsing "beep… beep" plays when a vehicle
 * is approaching a blind curve, and a continuous tone plays while an
 * emergency simulated-brake override is active (brake tone takes priority).
 */
export function useAlertSiren({ blindCurveApproach, brakeActive }: SirenInputs) {
  const [enabled, setEnabled] = useState(false);
  const ctxRef = useRef<AudioContext | null>(null);
  const oscRef = useRef<OscillatorNode | null>(null);
  const gainRef = useRef<GainNode | null>(null);
  const pulseTimerRef = useRef<number | null>(null);

  const stopTone = useCallback(() => {
    if (pulseTimerRef.current !== null) {
      window.clearInterval(pulseTimerRef.current);
      pulseTimerRef.current = null;
    }
    if (oscRef.current) {
      try {
        oscRef.current.stop();
      } catch {
        /* already stopped */
      }
      oscRef.current.disconnect();
      oscRef.current = null;
    }
    if (gainRef.current) {
      gainRef.current.disconnect();
      gainRef.current = null;
    }
  }, []);

  const enable = useCallback(() => {
    if (ctxRef.current) {
      setEnabled(true);
      return;
    }
    const AudioCtor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AudioCtor) return;
    ctxRef.current = new AudioCtor();
    setEnabled(true);
  }, []);

  const disable = useCallback(() => {
    stopTone();
    setEnabled(false);
  }, [stopTone]);

  const toggle = useCallback(() => {
    if (enabled) disable();
    else enable();
  }, [enabled, disable, enable]);

  useEffect(() => {
    return () => {
      stopTone();
      void ctxRef.current?.close();
    };
  }, [stopTone]);

  useEffect(() => {
    const ctx = ctxRef.current;
    if (!enabled || !ctx) {
      stopTone();
      return;
    }

    stopTone();

    if (brakeActive) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "square";
      osc.frequency.value = 880;
      gain.gain.value = 0.06;
      osc.connect(gain).connect(ctx.destination);
      osc.start();
      oscRef.current = osc;
      gainRef.current = gain;
      return () => stopTone();
    }

    if (blindCurveApproach) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = 660;
      gain.gain.value = 0;
      osc.connect(gain).connect(ctx.destination);
      osc.start();
      oscRef.current = osc;
      gainRef.current = gain;

      let on = false;
      pulseTimerRef.current = window.setInterval(() => {
        on = !on;
        gain.gain.setTargetAtTime(on ? 0.05 : 0, ctx.currentTime, 0.02);
      }, 420);
      return () => stopTone();
    }

    return () => stopTone();
  }, [enabled, brakeActive, blindCurveApproach, stopTone]);

  return { enabled, enable, disable, toggle };
}
