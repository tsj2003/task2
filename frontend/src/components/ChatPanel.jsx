import { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { sendChatMessage } from '../services/api';

export default function ChatPanel({ onReferencedEntities, suggestedQuery }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hi! I can help you analyze the **Order to Cash** process.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId] = useState(() => `conv-${Date.now()}`);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (suggestedQuery) {
      setInput(suggestedQuery);
      inputRef.current?.focus();
    }
  }, [suggestedQuery]);

  const handleSend = useCallback(async () => {
    const msg = input.trim();
    if (!msg || loading) return;

    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: msg }]);
    setLoading(true);

    try {
      const result = await sendChatMessage(msg, conversationId);
      const assistantMsg = {
        role: 'assistant',
        content: result.answer,
        sql_query: result.sql_query,
      };
      setMessages(prev => [...prev, assistantMsg]);

      if (result.referenced_entities?.length && onReferencedEntities) {
        onReferencedEntities(result.referenced_entities);
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: `❌ ${err.message || 'Error occurred.'}`, isError: true },
      ]);
    }
    setLoading(false);
  }, [input, loading, conversationId, onReferencedEntities]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <h3>Chat with Graph</h3>
        <div className="chat-subtitle">Order to Cash</div>
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message ${msg.role}`}>
            {msg.role === 'assistant' ? (
              <>
                <div className="message-avatar">
                  <div className="avatar-circle">D</div>
                  <div className="avatar-info">
                    <span className="avatar-name">Dodge AI</span>
                    <span className="avatar-role">Graph Agent</span>
                  </div>
                </div>
                <div className="message-content">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                  {msg.sql_query && (
                    <details className="sql-details">
                      <summary>View SQL Query</summary>
                      <pre><code>{msg.sql_query}</code></pre>
                    </details>
                  )}
                </div>
              </>
            ) : (
              <>
                <div className="message-avatar" style={{ justifyContent: 'flex-end', width: '100%' }}>
                  <div className="avatar-info" style={{ alignItems: 'flex-end' }}>
                    <span className="avatar-name">You</span>
                  </div>
                  <div className="avatar-circle user-avatar">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                  </div>
                </div>
                <div className="message-content">
                  {msg.content}
                </div>
              </>
            )}
          </div>
        ))}
        {loading && (
          <div className="chat-message assistant">
            <div className="message-avatar">
              <div className="avatar-circle">D</div>
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <div className="input-container">
          <div className="status-indicator">
            <span className="status-dot"></span>
            <span>Dodge AI is awaiting instructions</span>
          </div>
          <div className="input-row">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Analyze anything"
              rows={1}
              disabled={loading}
            />
            <button
              className="btn-send"
              onClick={handleSend}
              disabled={!input.trim() || loading}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
