/**
 * @file ChatPanel.tsx
 * @description Side panel chat interface for the AI travel assistant.
 *
 * Centralized assistant interaction through sendToAssistant.
 */

import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "../../types/chat";
import { ChatMessage as ChatMessageBubble } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { sendAssistantRequest } from "../../lib/assistant";
import React from "react";

interface ChatPanelProps {
  /** Current trip identifier so backend can ground responses. */
  tripId: string;
}

/**
 * ChatPanel
 * Displays conversation and sends new messages to the assistant.
 */
export function ChatPanel({ tripId }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(() => [
    {
      id: "intro",
      role: "assistant",
      content:
        "Hi! I'm your AI travel assistant. I can help you tweak this itinerary, add attractions, or answer questions about your trip.",
      createdAt: new Date().toISOString(),
    },
  ]);
  const [isSending, setIsSending] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Keep a ref to messages to avoid stale closures when computing history.
  const messagesRef = useRef<ChatMessage[]>(messages);
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.scrollTop = containerRef.current.scrollHeight;
  }, [messages]);

  /**
   * sendToAssistant
   * Sends a structured payload to the assistant implementation and handles the
   * assistant response.
   */
  async function sendToAssistant(payload: any, userMsgOptional?: ChatMessage) {
    if (!tripId) return;
    if (isSending) return;
    setIsSending(true);

    try {
      const history = userMsgOptional
        ? [...messagesRef.current, userMsgOptional]
        : messagesRef.current;
      const finalPayload = { ...payload, history };

      const data = await sendAssistantRequest(finalPayload);

      const assistantText = data?.assistantMessage ?? "Response received.";
      const assistantMsg: ChatMessage = {
        id: `remote-${Date.now()}`,
        role: "assistant",
        content: assistantText,
        createdAt: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      if (data?.updatedDay) {
        window.dispatchEvent(
          new CustomEvent("itinerary-day-updated", {
            detail: { day: data.updatedDay },
          }),
        );
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: "Sorry, something went wrong. Please try again.",
          createdAt: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  const handleSend = async (content: string) => {
    if (isSending) return;

    const newMessage: ChatMessage = {
      id: `local-${Date.now()}`,
      role: "user",
      content,
      createdAt: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, newMessage]);

    const payload = {
      action: "GENERAL_CHAT",
      tripId,
      message: content,
    };

    await sendToAssistant(payload, newMessage);
  };

  const handleQuickAction = async (text: string) => {
    if (isSending) return;

    const newMessage: ChatMessage = {
      id: `local-${Date.now()}`,
      role: "user",
      content: text,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, newMessage]);

    const payload = {
      action: "GENERAL_CHAT",
      tripId,
      message: text,
    };

    await sendToAssistant(payload, newMessage);
  };

  useEffect(() => {
    /**
     * handleStructuredSend
     * Handles structured events coming from other UI components (e.g. an
     * itinerary day requesting an AI action). For the UNDO action we provide a
     * frontend-mocked assistant reply and avoid contacting the backend so the
     * undo feels instant and predictable.
     */
    function handleStructuredSend(e: Event) {
      const ev = e as CustomEvent;
      const payload = ev.detail;
      if (!payload) return;
      if (!tripId) return;
      if (isSending) return;

      const message = payload.message ?? `Assistant action: ${payload.action}`;

      const userMsg: ChatMessage = {
        id: `local-${Date.now()}`,
        role: "user",
        content: message,
        createdAt: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);

      // Special-case UNDO: show a direct assistant reply (mock) and skip remote call.
      if (payload.action === "UNDO_LAST_DAY_CHANGE") {
        const assistantMsg: ChatMessage = {
          id: `assistant-undo-${Date.now()}`,
          role: "assistant",
          content: `I've undone the most recent change for Day ${payload.dayNumber ?? ""} and restored the previous version.`,
          createdAt: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
        return;
      }

      // ✅ For ADJUST_DAY_FOR_RAIN, send to backend immediately
      if (payload.action === "ADJUST_DAY_FOR_RAIN") {
        // Show intermediate status message
        const statusMsg: ChatMessage = {
          id: `status-${Date.now()}`,
          role: "assistant",
          content: `Adjusting Day ${payload.dayNumber ?? ""} for rainy weather...`,
          createdAt: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, statusMsg]);

        const finalPayload = {
          tripId,
          message: payload.message,
          dayNumber: payload.dayNumber,
        };

        void sendToAssistant(finalPayload, userMsg);
        return;
      }

      // For other structured actions
      const finalPayload = { ...payload, tripId };
      void sendToAssistant(finalPayload, userMsg);
    }

    window.addEventListener(
      "ai-send-structured",
      handleStructuredSend as EventListener,
    );
    return () => {
      window.removeEventListener(
        "ai-send-structured",
        handleStructuredSend as EventListener,
      );
    };
  }, [tripId, isSending]);

  return (
    <aside className="flex h-[calc(100vh-2.5rem)] flex-col rounded-2xl bg-white p-3 ring-1 ring-[#93C5FD] shadow-[0_8px_30px_rgba(1,89,250,0.06)] lg:sticky lg:top-4">
      {/* 
        Removed 'space-y-2' and adjusted margin-bottom to 'mb-2' 
        so the blue chat panel sits higher up, covering the removed text's space.
      */}
      <header className="mb-2">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#1D4ED8]">
          AI Travel Assistant
        </p>
      </header>

      {/* 
        This blue chat messages panel now fills all available vertical space 
        all the way to the newly tightened header.
      */}
      <div
        ref={containerRef}
        className="flex-1 h-0 space-y-3 overflow-y-auto rounded-xl bg-[#EFF6FF] p-3 border border-[#BFDBFE]"
      >
        {messages.map((message) => (
          <ChatMessageBubble key={message.id} message={message} />
        ))}
      </div>

      {/* Quick action chips */}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          onClick={() => handleQuickAction("Make this day lighter")}
          className="rounded-full bg-[#DBEAFE] px-3 py-1 text-xs font-medium text-[#1D4ED8] hover:bg-[#93C5FD] ring-1 ring-[#93C5FD]"
        >
          Make this day lighter
        </button>
        <button
          onClick={() => handleQuickAction("Add food stops")}
          className="rounded-full bg-[#DBEAFE] px-3 py-1 text-xs font-medium text-[#1D4ED8] hover:bg-[#93C5FD] ring-1 ring-[#93C5FD]"
        >
          Add food stops
        </button>
        <button
          onClick={() => handleQuickAction("Adjust for rain")}
          className="rounded-full bg-[#DBEAFE] px-3 py-1 text-xs font-medium text-[#1D4ED8] hover:bg-[#93C5FD] ring-1 ring-[#93C5FD]"
        >
          Adjust for rain
        </button>
        <button
          onClick={() => handleQuickAction("Show route tips")}
          className="rounded-full bg-[#DBEAFE] px-3 py-1 text-xs font-medium text-[#1D4ED8] hover:bg-[#93C5FD] ring-1 ring-[#93C5FD]"
        >
          Show route tips
        </button>
        <button
          onClick={() => handleQuickAction("Find cheaper options")}
          className="rounded-full bg-[#DBEAFE] px-3 py-1 text-xs font-medium text-[#1D4ED8] hover:bg-[#93C5FD] ring-1 ring-[#93C5FD]"
        >
          Find cheaper options
        </button>
      </div>

      <div className="mt-3">
        <ChatInput onSend={handleSend} disabled={isSending} />
        <p className="mt-2 text-[12px] text-[#475569]">
          Ask to swap attractions, add food stops, adjust for weather, or sync
          with your flights.
        </p>
      </div>
    </aside>
  );
}
