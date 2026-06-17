/**
 * @file chat.ts
 * @description Shared types for chat messages between user and AI assistant.
 */

/**
 * Chat role, either user or assistant.
 */
export type ChatRole = 'user' | 'assistant'

/**
 * Single chat message in the conversation.
 */
export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  createdAt: string
}

/**
 * Payload to send when user asks the assistant a question.
 */
export interface ChatRequestPayload {
  tripId: string
  message: string
  history: ChatMessage[]
}
