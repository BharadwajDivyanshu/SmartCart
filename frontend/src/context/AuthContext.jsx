import React, { createContext, useState, useContext } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);
export const useAuth = () => {
  const c = useContext(AuthContext);
  if (!c) throw new Error('useAuth must be used inside AuthProvider');
  return c;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const login = async (email, password) => {
    const u = await api.login(email, password);
    setUser(u);
    return u;
  };
  const signup = async (name, email, password) => {
    const u = await api.signup(name, email, password);
    setUser(u);
    return u;
  };
  const logout = () => setUser(null);
  return <AuthContext.Provider value={{ user, login, signup, logout }}>{children}</AuthContext.Provider>;
};