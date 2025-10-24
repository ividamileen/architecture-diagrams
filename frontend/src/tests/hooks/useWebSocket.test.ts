import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useWebSocket } from '../../hooks/useWebSocket'

// Mock WebSocket
class MockWebSocket {
  onopen: ((event: any) => void) | null = null
  onmessage: ((event: any) => void) | null = null
  onerror: ((event: any) => void) | null = null
  onclose: ((event: any) => void) | null = null
  readyState = 0

  constructor(public url: string) {
    setTimeout(() => {
      this.readyState = 1
      this.onopen?.({})
    }, 0)
  }

  send(data: string) {
    // Mock send
  }

  close() {
    this.readyState = 3
    this.onclose?.({})
  }
}

global.WebSocket = MockWebSocket as any

describe('useWebSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  it('connects to WebSocket when conversationId is provided', async () => {
    const { result } = renderHook(() => useWebSocket(1))

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })
  })

  it('does not connect when conversationId is null', () => {
    const { result } = renderHook(() => useWebSocket(null))

    expect(result.current.isConnected).toBe(false)
  })

  it('disconnects when unmounted', async () => {
    const { result, unmount } = renderHook(() => useWebSocket(1))

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })

    unmount()

    // WebSocket should be closed after unmount
    expect(result.current.isConnected).toBe(false)
  })
})
