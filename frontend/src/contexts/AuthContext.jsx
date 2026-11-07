import { createContext, useCallback, useEffect, useState } from 'react';
import { authService } from '../services/authService';
import { getToken } from '../api/client';

export const AuthContext = createContext(null);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!getToken());
  const refresh = useCallback(async () => { try { setUser(await authService.me()); } catch { authService.logout(); setUser(null); } }, []);
  useEffect(() => { if (getToken()) refresh().finally(() => setLoading(false)); }, [refresh]);
  useEffect(() => { const h = () => { authService.logout(); setUser(null); }; window.addEventListener('auth:expired', h); return () => window.removeEventListener('auth:expired', h); }, []);
  const login = async (email, password) => { const u = await authService.login(email, password); setUser(u); return u; };
  const register = async (data) => { const u = await authService.register(data); setUser(u); return u; };
  const logout = () => { authService.logout(); setUser(null); };
  return <AuthContext.Provider value={{ user, loading, login, register, logout, refresh }}>{children}</AuthContext.Provider>;
}
