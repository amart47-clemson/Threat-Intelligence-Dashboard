import { useState, useEffect } from 'react';

export function useCountUp(target, duration = 400) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (target == null || target === '—') {
      setCount(0);
      return;
    }
    const num = Number(target);
    if (Number.isNaN(num)) return;

    const start = performance.now();
    let frame;

    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      setCount(Math.round(num * progress));
      if (progress < 1) frame = requestAnimationFrame(tick);
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, duration]);

  return count;
}
