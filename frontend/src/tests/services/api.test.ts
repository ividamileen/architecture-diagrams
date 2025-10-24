import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { conversationsApi, messagesApi, diagramsApi } from '../../services/api'

// Mock axios
vi.mock('axios')

describe('API Services', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('conversationsApi', () => {
    it('creates a conversation', async () => {
      const mockConversation = {
        id: 1,
        platform: 'web',
        created_at: new Date().toISOString(),
      }

      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockResolvedValue({ data: mockConversation }),
      } as any)

      const result = await conversationsApi.create({ platform: 'web' })

      expect(result).toEqual(mockConversation)
    })

    it('gets a conversation', async () => {
      const mockConversation = {
        id: 1,
        platform: 'web',
        created_at: new Date().toISOString(),
      }

      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValue({ data: mockConversation }),
      } as any)

      const result = await conversationsApi.get(1)

      expect(result).toEqual(mockConversation)
    })
  })

  describe('messagesApi', () => {
    it('creates a message', async () => {
      const mockMessage = {
        id: 1,
        conversation_id: 1,
        content: 'Test message',
        user_id: 'user-1',
        is_technical: false,
        confidence_score: 0.2,
      }

      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockResolvedValue({ data: mockMessage }),
      } as any)

      const result = await messagesApi.create({
        content: 'Test message',
        user_id: 'user-1',
      })

      expect(result).toEqual(mockMessage)
    })
  })

  describe('diagramsApi', () => {
    it('generates a diagram', async () => {
      const mockDiagram = {
        id: 1,
        conversation_id: 1,
        plantuml_code: '@startuml\n@enduml',
        version: 1,
      }

      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockResolvedValue({ data: mockDiagram }),
      } as any)

      const result = await diagramsApi.generate({
        conversation_id: 1,
      })

      expect(result).toEqual(mockDiagram)
    })

    it('returns correct PNG URL', () => {
      const url = diagramsApi.getPng(123)
      expect(url).toBe('/api/v1/diagrams/123/png')
    })
  })
})
