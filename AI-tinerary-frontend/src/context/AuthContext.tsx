/**
 * @file AuthContext.tsx
 * @description Minimal frontend-only mock authentication context using localStorage.
 *              Provides currentUser, login, signup, logout and isAuthenticated.
 *
 * TODO: Replace mock auth with real backend/Supabase auth later.
 * TODO: Connect currentUser.id to real user_id after backend integration.
 */

// src/context/AuthContext.tsx
import React, { createContext, useContext, useState, ReactNode } from "react";

interface AuthContextType {
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  user: { email: string; name: string; user_id: string } | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<AuthContextType["user"]>(null);

  const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

  const login = async (email: string, password: string) => {
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Login failed");
      }

      const data = await response.json();

      // ✅ Store token in localStorage
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_id", data.user_id);

      // ✅ Update local state
      setUser({
        email: data.email,
        name: data.name,
        user_id: data.user_id,
      });
      setIsAuthenticated(true);
    } catch (error) {
      throw error;
    }
  };

  const signup = async (name: string, email: string, password: string) => {
    try {
      const response = await fetch(`${API_BASE}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Signup failed");
      }

      const data = await response.json();

      // ✅ Store token and user info
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_id", data.user_id);

      setUser({
        email: data.email,
        name: data.name,
        user_id: data.user_id,
      });
      setIsAuthenticated(true);
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_id");
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider
      value={{ login, signup, logout, isAuthenticated, user }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
