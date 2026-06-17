/**
 * @file ChatInput.tsx
 * @description Input bar for sending a new chat message to the assistant.
 */

import { FormEvent, useState } from 'react'
import { Send } from 'lucide-react'

interface ChatInputProps {
  /** Handler called with the user's message when the form is submitted. */
  onSend: (message: string) => void
  /** Whether a message is currently being processed. */
  disabled?: boolean
}

/**
 * Text input and send button allowing users to ask follow-up questions.
 */
export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState('')

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!value.trim() || disabled) return
    onSend(value.trim())
    setValue('')
  }

  return (  
    <form onSubmit={handleSubmit} className="flex items-center gap-2 rounded-full border border-[#93C5FD] bg-white px-3 py-2">  
      <input  
        className="flex-1 bg-transparent text-[13px] text-[#0F172A] placeholder:text-[#475569] focus:outline-none"  
        placeholder="How can we help with your itinerary?"  
        value={value}  
        onChange={(e) => setValue(e.target.value)}  
        disabled={disabled}  
      />  
      <button  
        type="submit"  
        disabled={disabled || !value.trim()}  
        className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-[#0159FA] text-white shadow-lg shadow-[rgba(1,89,250,0.25)] disabled:cursor-not-allowed disabled:bg-[#BFDBFE] hover:bg-[#1458DD]"  
      >  
        <Send className="h-4 w-4" />  
      </button>  
    </form>  
  )  
}