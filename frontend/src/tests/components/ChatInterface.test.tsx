import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatInterface } from '../../components/ChatInterface'
import type { Message } from '../../types'

// Mock messagesApi
vi.mock('../../services/api', () => ({
  messagesApi: {
    create: vi.fn(),
  },
}))

describe('ChatInterface', () => {
  const mockMessages: Message[] = [
    {
      id: 1,
      conversation_id: 1,
      content: 'Test message',
      user_id: 'user-1',
      user_name: 'Test User',
      timestamp: new Date().toISOString(),
      is_technical: false,
      confidence_score: 0.2,
      entities: null,
    },
  ]

  const mockOnMessageSent = vi.fn()
  const mockOnDiagramGenerationStarted = vi.fn()

  it('renders chat interface', () => {
    render(
      <ChatInterface
        conversationId={1}
        messages={mockMessages}
        onMessageSent={mockOnMessageSent}
        onDiagramGenerationStarted={mockOnDiagramGenerationStarted}
      />
    )

    expect(screen.getByText('Test message')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/type your message/i)).toBeInTheDocument()
  })

  it('displays user name and message content', () => {
    render(
      <ChatInterface
        conversationId={1}
        messages={mockMessages}
        onMessageSent={mockOnMessageSent}
        onDiagramGenerationStarted={mockOnDiagramGenerationStarted}
      />
    )

    expect(screen.getByText('Test User')).toBeInTheDocument()
    expect(screen.getByText('Test message')).toBeInTheDocument()
  })

  it('displays technical confidence indicator for technical messages', () => {
    const technicalMessages: Message[] = [
      {
        ...mockMessages[0],
        is_technical: true,
        confidence_score: 0.85,
      },
    ]

    render(
      <ChatInterface
        conversationId={1}
        messages={technicalMessages}
        onMessageSent={mockOnMessageSent}
        onDiagramGenerationStarted={mockOnDiagramGenerationStarted}
      />
    )

    expect(screen.getByText(/technical/i)).toBeInTheDocument()
    expect(screen.getByText(/85%/i)).toBeInTheDocument()
  })

  it('allows user to type message', async () => {
    render(
      <ChatInterface
        conversationId={1}
        messages={[]}
        onMessageSent={mockOnMessageSent}
        onDiagramGenerationStarted={mockOnDiagramGenerationStarted}
      />
    )

    const input = screen.getByPlaceholderText(/type your message/i) as HTMLTextAreaElement

    await userEvent.type(input, 'New message')

    expect(input.value).toBe('New message')
  })

  it('send button is disabled when input is empty', () => {
    render(
      <ChatInterface
        conversationId={1}
        messages={[]}
        onMessageSent={mockOnMessageSent}
        onDiagramGenerationStarted={mockOnDiagramGenerationStarted}
      />
    )

    const sendButton = screen.getByRole('button')
    expect(sendButton).toBeDisabled()
  })

  it('renders multiple messages', () => {
    const multipleMessages: Message[] = [
      { ...mockMessages[0], id: 1, content: 'Message 1' },
      { ...mockMessages[0], id: 2, content: 'Message 2' },
      { ...mockMessages[0], id: 3, content: 'Message 3' },
    ]

    render(
      <ChatInterface
        conversationId={1}
        messages={multipleMessages}
        onMessageSent={mockOnMessageSent}
        onDiagramGenerationStarted={mockOnDiagramGenerationStarted}
      />
    )

    expect(screen.getByText('Message 1')).toBeInTheDocument()
    expect(screen.getByText('Message 2')).toBeInTheDocument()
    expect(screen.getByText('Message 3')).toBeInTheDocument()
  })
})
