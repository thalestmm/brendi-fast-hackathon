/**
 * Persistent chat button component.
 */

import { useState } from 'react';
import { ChatPanel } from './ChatPanel';

export function ChatButton() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="btn btn-primary"
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          borderRadius: '50%',
          width: '60px',
          height: '60px',
          fontSize: '24px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          zIndex: 1000,
        }}
        aria-label="Open chat"
      >
        💬
      </button>
      {isOpen && <ChatPanel onClose={() => setIsOpen(false)} />}
    </>
  );
}

