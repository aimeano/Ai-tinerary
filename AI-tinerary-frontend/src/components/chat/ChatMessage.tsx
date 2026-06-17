/**
 * @file ChatMessage.tsx
 * @description Bubble component for individual chat messages. User messages use
 *              the primary blue; assistant messages are explicitly white with
 *              navy text and a visible border to increase contrast.
 */

import React from 'react'
import type { ChatMessage as ChatMessageType } from '../../types/chat'

/**
 * Props for ChatMessage component.
 */
interface ChatMessageProps {
  /** Single chat message to display. */
  message: ChatMessageType
}

/**
 * ChatMessage
 * Renders a single chat bubble. User bubbles are right-aligned and use the
 * primary blue. Assistant bubbles are left-aligned and use a white background
 * with navy text and a visible ring/border for clarity.
 *
 * @param props - Component props containing the message to render.
 */
export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm shadow-sm ${
          isUser
            ? 'rounded-br-sm bg-[#0159FA] text-white shadow-[0_6px_18px_rgba(1,89,250,0.12)]'
            : 'rounded-bl-sm bg-white text-[#0F172A] ring-1 ring-[#BFDBFE]'
        }`}
      >
        <p className="whitespace-pre-line">{message.content}</p>
      </div>
    </div>
  )
}