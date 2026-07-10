import React from 'react';
import { MessageSquare, RotateCcw, Send, Trash2, Volume2 } from 'lucide-react';

type ChatMessage = { text: string; time: string };

interface Props {
  chatHistory: ChatMessage[];
  messageDraft: string;
  onSend: () => void;
  onClear: () => void;
  onReplay: () => void;
}

export const MessagingModule: React.FC<Props> = ({ chatHistory, messageDraft, onSend, onClear, onReplay }) => {
  return (
    <div className="messaging-module">
      <div className="section-heading section-heading--compact">
        <div>
          <span className="section-kicker"><MessageSquare /> Messaging</span>
          <h2>Composer</h2>
        </div>
        <div className="composer-actions" aria-label="Composer actions">
          <button type="button" className="icon-button" onClick={onReplay} title="Speak draft or last message">
            <Volume2 />
          </button>
          <button type="button" className="icon-button" onClick={onClear} title="Clear draft">
            <Trash2 />
          </button>
        </div>
      </div>

      <div className="chat-history">
        {chatHistory.length === 0 ? (
          <div className="empty-chat">
            <MessageSquare />
            <p>Compose via gestures or manual controls.</p>
          </div>
        ) : (
          chatHistory.map((msg, i) => (
            <div
              key={i}
              className="chat-bubble"
            >
              <span>{msg.text}</span>
              <time>{msg.time}</time>
            </div>
          ))
        )}
      </div>

      <div className="composer">
        <input
          type="text"
          value={messageDraft}
          readOnly
          placeholder="Awaiting entry..."
          className="composer-input"
          aria-label="Current gesture-composed message"
        />
        <button
          type="button"
          className="send-button"
          onClick={onSend}
          disabled={messageDraft.trim().length === 0}
          title="Send message"
        >
          <Send />
        </button>
      </div>

      <div className="gesture-hint">
        <RotateCcw />
        <span>Thumbs up sends. Pinky clears. Ring-only backspaces. Palm, OK, V, Y, and ILY append quick phrases.</span>
      </div>
    </div>
  );
};
