/**
 * @file App.tsx
 * @description Root application component with routes and auth guards.
 */

import React from 'react'
import { useEffect, useState } from 'react'
import { HashRouter, Route, Routes, Navigate } from 'react-router'
import HomePage from './pages/Home'
import NewTripPage from './pages/NewTrip'
import TripDetailPage from './pages/TripDetail'
import LoginPage from './pages/Login'
import SignupPage from './pages/Signup'
import { AppShell } from './components/layout/AppShell'
import { AuthProvider, useAuth } from './context/AuthContext'

/**
 * PrivateRoute - Protected route with auth check
 */
function PrivateRoute({ children }: { children: JSX.Element }) {
  const auth = useAuth()
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    setIsReady(true)
  }, [auth])

  if (!isReady) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      </div>
    )
  }

  if (!auth.isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return children
}

/**
 * PublicRoute - Auth pages (redirects authenticated users away)
 */
function PublicRoute({ children }: { children: JSX.Element }) {
  const auth = useAuth()

  if (auth.isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return children
}

/**
 * Root App component
 */
export default function App() {
  return (
    <AuthProvider>
      <HashRouter>
        <AppShell>
          <Routes>
            {/* Auth routes (public) */}
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <LoginPage />
                </PublicRoute>
              }
            />
            <Route
              path="/signup"
              element={
                <PublicRoute>
                  <SignupPage />
                </PublicRoute>
              }
            />

            {/* Protected app routes */}
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <HomePage />
                </PrivateRoute>
              }
            />
            <Route
              path="/new"
              element={
                <PrivateRoute>
                  <NewTripPage />
                </PrivateRoute>
              }
            />
            <Route
              path="/trip/:tripId"
              element={
                <PrivateRoute>
                  <TripDetailPage />
                </PrivateRoute>
              }
            />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppShell>
      </HashRouter>
    </AuthProvider>
  )
}
