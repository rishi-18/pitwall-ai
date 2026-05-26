import React, { useState, useRef, useEffect } from 'react'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface Message {
  role: 'user' | 'assistant'
  content: string
  loading?: boolean
}

const SUGGESTED = [
  "What happened to Verstappen in Australia?",
  "What tyre strategy did Verstappen use in Bahrain?",
  "Who had the highest top speed in Bahrain?",
  "Who won the Australian Grand Prix and why?",
]

export default function RaceAnalyst() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (question: string) => {
    if (!question.trim() || isStreaming) return

    const userMsg: Message = { role: 'user', content: question.trim() }
    setMessages(prev => [...prev, userMsg, { role: 'assistant', content: '', loading: true }])
    setInput('')
    setIsStreaming(true)

    try {
      const resp = await fetch(`${API}/v1/rag/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim() }),
      })

      const reader = resp.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n').filter(l => l.startsWith('data: '))
        for (const line of lines) {
          const data = line.replace('data: ', '')
          if (data === '[DONE]') continue
          buffer += data
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              role: 'assistant',
              content: buffer,
              loading: false,
            }
            return updated
          })
        }
      }
    } catch (e) {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          role: 'assistant',
          content: 'Error connecting to Race Analyst. Check API status.',
          loading: false,
        }
        return updated
      })
    } finally {
      setIsStreaming(false)
    }
  }

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: 'calc(100vh - 45px)',
      background: '#0a0a0a', color: 'white',
    }}>

      {/* Header */}
      <div style={{ padding: '1rem 2rem', borderBottom: '1px solid #1a1a1a' }}>
        <h2 style={{ margin: 0, fontFamily: 'monospace', color: '#e10600', fontSize: '1rem' }}>
          RACE ANALYST
        </h2>
        <p style={{ margin: '0.25rem 0 0', color: '#444', fontSize: '0.75rem' }}>
          Powered by ChromaDB · Groq Llama 3 · RAG Pipeline
        </p>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem 2rem' }}>

        {/* Empty state */}
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', marginTop: '3rem' }}>
            <div style={{ color: '#e10600', fontSize: '2rem', marginBottom: '1rem' }}>🏎️</div>
            <p style={{ color: '#444', fontSize: '0.875rem', marginBottom: '2rem' }}>
              Ask anything about the 2024 Bahrain, Jeddah, or Australian Grand Prix
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', justifyContent: 'center' }}>
              {SUGGESTED.map(q => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  style={{
                    background: '#111', border: '1px solid #222', color: '#999',
                    padding: '0.5rem 1rem', borderRadius: '20px', cursor: 'pointer',
                    fontSize: '0.8rem', transition: 'all 0.15s',
                  }}
                  onMouseEnter={e => {
                    (e.target as HTMLButtonElement).style.borderColor = '#e10600'
                    ;(e.target as HTMLButtonElement).style.color = '#fff'
                  }}
                  onMouseLeave={e => {
                    (e.target as HTMLButtonElement).style.borderColor = '#222'
                    ;(e.target as HTMLButtonElement).style.color = '#999'
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Chat messages */}
        {messages.map((msg, i) => (
          <div key={i} style={{
            display: 'flex',
            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            marginBottom: '1rem',
          }}>
            {msg.role === 'assistant' && (
              <div style={{
                width: '24px', height: '24px', borderRadius: '50%',
                background: '#e10600', display: 'flex', alignItems: 'center',
                justifyContent: 'center', fontSize: '0.7rem', marginRight: '0.5rem',
                flexShrink: 0, marginTop: '2px',
              }}>
                AI
              </div>
            )}
            <div style={{
              maxWidth: '70%',
              padding: '0.75rem 1rem',
              borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
              background: msg.role === 'user' ? '#e10600' : '#111',
              border: msg.role === 'assistant' ? '1px solid #1e1e1e' : 'none',
              fontSize: '0.875rem',
              lineHeight: '1.6',
              color: msg.role === 'user' ? '#fff' : '#ccc',
              whiteSpace: 'pre-wrap',
            }}>
              {msg.loading ? (
                <span style={{ color: '#555' }}>▊</span>
              ) : (
                msg.content || <span style={{ color: '#555' }}>▊</span>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{
        padding: '1rem 2rem', borderTop: '1px solid #1a1a1a',
        display: 'flex', gap: '0.75rem', alignItems: 'center',
      }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage(input)}
          placeholder="Ask about race strategy, driver performance, tyre choices..."
          disabled={isStreaming}
          style={{
            flex: 1, background: '#111', border: '1px solid #222',
            borderRadius: '8px', color: 'white', padding: '0.75rem 1rem',
            fontSize: '0.875rem', outline: 'none',
            opacity: isStreaming ? 0.6 : 1,
          }}
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={isStreaming || !input.trim()}
          style={{
            background: isStreaming || !input.trim() ? '#1a1a1a' : '#e10600',
            color: isStreaming || !input.trim() ? '#444' : 'white',
            border: 'none', borderRadius: '8px',
            padding: '0.75rem 1.5rem', cursor: isStreaming ? 'not-allowed' : 'pointer',
            fontSize: '0.875rem', fontFamily: 'monospace',
            transition: 'all 0.15s',
          }}
        >
          {isStreaming ? '...' : 'ASK'}
        </button>
      </div>
    </div>
  )
}