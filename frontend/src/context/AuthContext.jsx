import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('rag_auth_user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState(() => {
    return localStorage.getItem('rag_auth_token') || null;
  });

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user && token) {
      localStorage.setItem('rag_auth_user', JSON.stringify(user));
      localStorage.setItem('rag_auth_token', token);
    } else {
      localStorage.removeItem('rag_auth_user');
      localStorage.removeItem('rag_auth_token');
    }
  }, [user, token]);

  const login = async (email, password, remember = true) => {
    setLoading(true);
    // Simulate auth latency for smooth UX
    await new Promise((res) => setTimeout(res, 600));

    // Demo authentication handling
    const mockUser = {
      id: 'usr_' + Math.random().toString(36).substring(2, 9),
      name: email.split('@')[0].replace(/[^a-zA-Z]/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()) || 'Research User',
      email: email,
      role: 'Principal Researcher',
      organization: 'Evidence AI Lab',
      avatarUrl: `https://ui-avatars.com/api/?name=${encodeURIComponent(email)}&background=0e8eed&color=fff`,
    };
    const mockToken = 'jwt_demo_token_' + Date.now();

    setUser(mockUser);
    setToken(mockToken);
    setLoading(false);
    return { success: true, user: mockUser };
  };

  const signup = async (fullName, email, password) => {
    setLoading(true);
    await new Promise((res) => setTimeout(res, 800));

    const newUser = {
      id: 'usr_' + Math.random().toString(36).substring(2, 9),
      name: fullName,
      email: email,
      role: 'Researcher',
      organization: 'Academic Research',
      avatarUrl: `https://ui-avatars.com/api/?name=${encodeURIComponent(fullName)}&background=0270ca&color=fff`,
    };
    const mockToken = 'jwt_demo_token_' + Date.now();

    setUser(newUser);
    setToken(mockToken);
    setLoading(false);
    return { success: true, user: newUser };
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('rag_auth_user');
    localStorage.removeItem('rag_auth_token');
  };

  const value = {
    user,
    token,
    isAuthenticated: !!user && !!token,
    loading,
    login,
    signup,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
