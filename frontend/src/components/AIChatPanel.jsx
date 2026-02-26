import React, { useState, useEffect, useRef, useCallback } from 'react';
import { aiAPI } from '../services/api';
import { Bot, X, Send, ThumbsUp, ThumbsDown, Plus, Trash2, ChevronRight } from 'lucide-react';

/* ── Single message bubble ────────────────────────────── */
function ChatMessage({ msg, onFeedback }) {
  const isUser = msg.role === 'user';
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`ai-msg ${isUser ? 'ai-msg-user' : 'ai-msg-assistant'}`}>
      {!isUser && <div className="ai-msg-avatar"><Bot size={16} /></div>}
      <div className="ai-msg-body">
        <div className="ai-msg-content">{msg.content}</div>
        {msg.tool_calls && msg.tool_calls.length > 0 && (
          <div className="ai-tool-calls">
            <button className="ai-tool-toggle" onClick={() => setExpanded(!expanded)}>
              <ChevronRight size={12} style={{ transform: expanded ? 'rotate(90deg)' : 'none', transition: '0.15s' }} />
              {msg.tool_calls.length} tool{msg.tool_calls.length > 1 ? 's' : ''} used
            </button>
            {expanded && (
              <div className="ai-tool-list">
                {msg.tool_calls.map((tc, i) => (
                  <div key={i} className="ai-tool-badge">
                    <span className="ai-tool-name">{tc.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        {!isUser && onFeedback && (
          <div className="ai-msg-feedback">
            <button title="Helpful" onClick={() => onFeedback('thumbs_up')}><ThumbsUp size={12} /></button>
            <button title="Not helpful" onClick={() => onFeedback('thumbs_down')}><ThumbsDown size={12} /></button>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Main AI Chat Panel ───────────────────────────────── */
export default function AIChatPanel({ open, onClose }) {
  const [conversations, setConversations] = useState([]);
  const [activeConvo, setActiveConvo] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [interactionId, setInteractionId] = useState(null);
  const [view, setView] = useState('chat'); // 'list' | 'chat'
  const bottomRef = useRef(null);

  const loadConversations = useCallback(async () => {
    try {
      const res = await aiAPI.listConversations();
      setConversations(res.data.conversations || []);
    } catch { /* ignore */ }
  }, []);

  const loadMessages = useCallback(async (convoId) => {
    try {
      const res = await aiAPI.getConversation(convoId);
      setMessages(res.data.conversation?.messages || []);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    if (open) loadConversations();
  }, [open, loadConversations]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const startNew = async () => {
    try {
      const res = await aiAPI.createConversation();
      const convo = res.data.conversation;
      setActiveConvo(convo);
      setMessages([]);
      setView('chat');
      loadConversations();
    } catch { /* ignore */ }
  };

  const openConvo = async (convo) => {
    setActiveConvo(convo);
    setView('chat');
    await loadMessages(convo.id);
  };

  const deleteConvo = async (id, e) => {
    e.stopPropagation();
    try {
      await aiAPI.deleteConversation(id);
      if (activeConvo?.id === id) {
        setActiveConvo(null);
        setMessages([]);
        setView('list');
      }
      loadConversations();
    } catch { /* ignore */ }
  };

  const handleSend = async () => {
    if (!input.trim() || sending) return;
    const content = input.trim();
    setInput('');
    setSending(true);

    // If no active convo, create one
    let convoId = activeConvo?.id;
    if (!convoId) {
      try {
        const res = await aiAPI.createConversation(content.slice(0, 60));
        convoId = res.data.conversation.id;
        setActiveConvo(res.data.conversation);
        setView('chat');
      } catch {
        setSending(false);
        return;
      }
    }

    // Optimistic user message
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', content }]);

    try {
      const res = await aiAPI.sendMessage(convoId, content);
      const { assistant_message, interaction_id } = res.data;
      setMessages(prev => [...prev, assistant_message]);
      setInteractionId(interaction_id);
      loadConversations();
    } catch {
      setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', content: 'Sorry, something went wrong.' }]);
    } finally {
      setSending(false);
    }
  };

  const handleFeedback = async (feedback) => {
    if (!interactionId) return;
    try {
      await aiAPI.submitFeedback(interactionId, feedback);
    } catch { /* ignore */ }
  };

  if (!open) return null;

  return (
    <div className="ai-panel">
      <div className="ai-panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Bot size={18} />
          <span style={{ fontWeight: 600 }}>AI Assistant</span>
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          <button className="ai-panel-icon-btn" onClick={() => setView(view === 'list' ? 'chat' : 'list')} title="Conversations">
            ☰
          </button>
          <button className="ai-panel-icon-btn" onClick={startNew} title="New chat"><Plus size={14} /></button>
          <button className="ai-panel-icon-btn" onClick={onClose}><X size={14} /></button>
        </div>
      </div>

      {view === 'list' ? (
        <div className="ai-convo-list">
          {conversations.length === 0 ? (
            <div style={{ padding: 24, textAlign: 'center', color: 'var(--gray-400)' }}>
              No conversations yet
            </div>
          ) : conversations.map(c => (
            <div key={c.id} className={`ai-convo-item${activeConvo?.id === c.id ? ' active' : ''}`}
                 onClick={() => openConvo(c)}>
              <span className="ai-convo-title">{c.title}</span>
              <button className="ai-convo-del" onClick={(e) => deleteConvo(c.id, e)}>
                <Trash2 size={12} />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <>
          <div className="ai-messages">
            {messages.length === 0 && (
              <div style={{ padding: 32, textAlign: 'center', color: 'var(--gray-400)', fontSize: 13 }}>
                <Bot size={40} style={{ opacity: 0.3, marginBottom: 12 }} /><br />
                Ask me anything about your ERP data.<br />
                <span style={{ fontSize: 12 }}>Try "show me overdue invoices" or "list products"</span>
              </div>
            )}
            {messages.map((m, i) => (
              <ChatMessage key={m.id || i} msg={m}
                onFeedback={i === messages.length - 1 && m.role === 'assistant' ? handleFeedback : null} />
            ))}
            {sending && (
              <div className="ai-msg ai-msg-assistant">
                <div className="ai-msg-avatar"><Bot size={16} /></div>
                <div className="ai-msg-body"><div className="ai-typing">Thinking…</div></div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="ai-input-bar">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Ask a question…"
              disabled={sending}
            />
            <button onClick={handleSend} disabled={sending || !input.trim()}>
              <Send size={16} />
            </button>
          </div>
        </>
      )}
    </div>
  );
}
