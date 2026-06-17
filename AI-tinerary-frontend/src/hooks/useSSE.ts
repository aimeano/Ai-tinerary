/**
 * @file useSSE.ts
 * @description Small hook for consuming Server-Sent Events (SSE) streams.
 */

import { useEffect, useRef, useState } from 'react'

/**
 * Options for configuring the SSE stream.
 */
interface UseSSEOptions {
  /** Endpoint URL that serves SSE events. */
  url: string
  /** Called when a new event chunk is received. */
  onMessage: (data: string) => void
}

/**
 * Hook that manages a single EventSource connection for SSE.
 *
 * Backend contract:
 *  - Use `Content-Type: text/event-stream`
 *  - Send events in `data: {...}\n\n` format (JSON-encoded payload).
 */
export function useSSE({ url, onMessage }: UseSSEOptions) {
  const [isConnected, setIsConnected] = useState(false)
  const sourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    const source = new EventSource(url)
    sourceRef.current = source

    source.onopen = () => setIsConnected(true)
    source.onerror = () => {
      setIsConnected(false)
      source.close()
    }
    source.onmessage = (event) => {
      onMessage(event.data)
    }

    return () => {
      source.close()
      sourceRef.current = null
    }
  }, [url, onMessage])

  return { isConnected }
}
