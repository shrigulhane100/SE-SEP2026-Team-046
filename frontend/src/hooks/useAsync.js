import { useCallback, useEffect, useRef, useState } from 'react';
export function useAsync(fn, deps = []) {
  const [s, set] = useState({ data: null, loading: true, error: null });
  const n = useRef(0);
  const run = useCallback(async (silent) => {
    const id = ++n.current;
    if (!silent) set((x) => ({ ...x, loading: true, error: null }));
    try { const data = await fn(); if (id === n.current) set({ data, loading: false, error: null }); }
    catch (e) { if (id === n.current) set({ data: null, loading: false, error: e.message || 'Something went wrong' }); }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(() => { run(); return () => { n.current++; }; }, [run]);
  return { ...s, reload: () => run(true), retry: () => run(false) };
}
