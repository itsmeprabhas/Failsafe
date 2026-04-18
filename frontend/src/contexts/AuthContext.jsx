import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const response = await authAPI.getMe();
        setUser(response.data);
      } catch (error) {
        // If token is invalid, just clear it and stay logged out
        localStorage.removeItem('token');
        setUser(null);
      }
    }
    setLoading(false);
  };

  const login = async (username, password) => {
    const response = await authAPI.login(username, password);
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);
    
    // Fetch user details immediately after login
    try {
      const userResponse = await authAPI.getMe();
      setUser(userResponse.data);
    } catch (error) {
      console.error("Logged in but couldn't fetch user details");
    }
    
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
    isFaculty: user?.role === 'faculty',
    isHOD: user?.role === 'hod',
    isAdmin: user?.role === 'admin',
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
