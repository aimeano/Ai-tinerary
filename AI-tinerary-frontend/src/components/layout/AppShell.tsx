/**
 * @file AppShell.tsx
 * @description Application shell providing top navigation, mock user display and logout.
 *
 * TODO: Replace mock auth UI with real account menu after backend integration.
 */

import type { ReactNode } from "react";
import { Link, useLocation } from "react-router";
import { Plus } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import logo from "../../assets/logo.jpeg";

interface AppShellProps {
  /** Children content representing the active page. */
  children: ReactNode;
}

/**
 * Global layout with header, brand, and refined blue background.
 */
export function AppShell({ children }: AppShellProps) {
  const location = useLocation();
  const isHome = location.pathname === "/";
  const auth = useAuth();

  /**
   * handleLogout
   * @description Clears mock auth state and navigates user back to login by removing stored user.
   */
  function handleLogout() {
    auth.logout();
    // Let the router redirect via route guards (no explicit navigate here).
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#F8FAFC] to-[#EFF6FF] text-[#0F172A]">
      <header className="border-b border-[#BFDBFE] bg-white/75 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-3">
            <img
              src={logo}
              alt="AI-tinerary Logo"
              className="h-9 w-9 rounded-lg"
            />
            <span className="text-lg font-semibold tracking-tight text-[#0F172A]">
              AI-tinerary
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              to="/new"
              className="inline-flex items-center gap-2 rounded-full bg-[#0159FA] px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-[#1458DD] transition"
            >
              <Plus className="h-4 w-4" />
              <span>New Trip</span>
            </Link>

            {/* Small mock user area: show name/email and logout */}
            {auth.isAuthenticated ? (
              <div className="flex items-center gap-3 rounded-full bg-white/80 px-3 py-1 text-sm text-[#0F172A] shadow-sm ring-1 ring-[#BFDBFE]">
                <span className="text-sm text-[#475569]">Hi,</span>
                <span className="font-semibold">
                  {auth.user?.name ?? auth.user?.email}
                </span>
                <button
                  onClick={handleLogout}
                  className="ml-2 rounded-full bg-[#FEF2F2] px-2 py-1 text-xs text-[#B91C1C] hover:bg-[#FECACA]"
                  title="Log out"
                >
                  Log out
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="text-sm text-[#0159FA] hover:underline"
              >
                Sign in
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 pb-10 pt-6">
        {isHome ? (
          children
        ) : (
          <div className="rounded-3xl bg-white p-6 shadow-[0_24px_48px_rgba(2,6,23,0.06)] ring-1 ring-[#BFDBFE]">
            {children}
          </div>
        )}
      </main>
    </div>
  );
}
