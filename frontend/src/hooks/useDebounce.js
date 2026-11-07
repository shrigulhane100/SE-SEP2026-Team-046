import { useEffect, useState } from 'react';
export const useDebounce = (value, ms = 300) => { const [v, set] = useState(value); useEffect(() => { const t = setTimeout(() => set(value), ms); return () => clearTimeout(t); }, [value, ms]); return v; };
