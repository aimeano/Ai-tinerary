/**
 * src/pages/Signup.tsx
 * @file Signup.tsx
 * @description Connect to FastAPI backend for real user registration
 */

import React, { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router";

export default function SignupPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }

    setIsSubmitting(true);

    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

      const response = await fetch(`${API_BASE}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, name }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Signup failed");
      }

      const data = await response.json();

      // Store token and user info
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_id", data.user_id);
      localStorage.setItem("email", data.email);
      localStorage.setItem("name", data.name);

      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create account");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-md">
      <div className="rounded-3xl bg-white p-6 shadow-[0_12px_40px_rgba(2,6,23,0.06)] ring-1 ring-[#BFDBFE]">
        <header className="mb-4">
          <h1 className="text-xl font-semibold text-[#0F172A]">
            Create your account
          </h1>
          <p className="mt-1 text-sm text-[#475569]">
            Sign up today to create the best travel memory.
          </p>
        </header>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-[#475569]">
              Full name
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 w-full rounded-xl border border-blue-200 bg-white px-3 py-2 text-sm text-blue-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
          </div>

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

          <div className="grid grid-cols-2 gap-3">
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
            <div>
              <label className="block text-xs font-medium text-[#475569]">
                Confirm
              </label>
              <input
                type="password"
                required
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className="mt-1 w-full rounded-xl border border-blue-200 bg-white px-3 py-2 text-sm text-blue-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              />
            </div>
          </div>

          {error && <div className="text-sm text-red-600">{error}</div>}

          <div className="flex items-center justify-between">
            <div className="text-sm text-[#475569]">
              <Link to="/login" className="text-blue-700 hover:underline">
                Already have an account?
              </Link>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 rounded-full bg-[#0159FA] px-5 py-2.5 text-sm font-medium text-white shadow-md hover:bg-[#1458DD] disabled:opacity-60"
            >
              {isSubmitting ? "Creating…" : "Create account"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
