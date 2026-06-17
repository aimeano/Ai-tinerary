/**
 * src/pages/Login.tsx
 * @file Login.tsx
 * @description Connect to FastAPI backend for real authentication
 */

import React, { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const navigate = useNavigate();
  const auth = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await auth.login(email, password);

      await new Promise((resolve) => setTimeout(resolve, 0));

      setIsSubmitting(false);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to log in");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-md">
      <div className="rounded-3xl bg-white p-6 shadow-[0_12px_40px_rgba(2,6,23,0.06)] ring-1 ring-[#BFDBFE]">
        <header className="mb-4">
          <h1 className="text-xl font-semibold text-[#0F172A]">
            Ready to travel?
          </h1>
          <p className="mt-1 text-sm text-[#475569]">
            Sign in to access your itineraries.
          </p>
        </header>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-[#475569]">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-xl border border-blue-200 bg-white px-3 py-2 text-sm text-blue-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-[#475569]">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-xl border border-blue-200 bg-white px-3 py-2 text-sm text-blue-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
          </div>

          {error && <div className="text-sm text-red-600">{error}</div>}

          <div className="flex items-center justify-between">
            <div className="text-sm text-[#475569]">
              <Link to="/signup" className="text-blue-700 hover:underline">
                Need an account?
              </Link>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 rounded-full bg-[#0159FA] px-5 py-2.5 text-sm font-medium text-white shadow-md hover:bg-[#1458DD] disabled:opacity-60"
            >
              {isSubmitting ? "Signing in…" : "Sign in"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
