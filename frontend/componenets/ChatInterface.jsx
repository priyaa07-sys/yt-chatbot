import React, { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';

export default function ChatInterface({ documentInfo }) {
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: `Hello! I've fully indexed the video. Ask me anything about what was said throughout this video `
        }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setIsLoading(true);

        try {
            const response = await fetch('http://localhost:8000/api/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: userMessage,
                    document_id: documentInfo.video_id
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to fetch a localized response.');
            }

            const data = await response.json();
            setMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);
        } catch (err) {
            console.error('Q&A Process Failure:', err);
            setMessages(prev => [
                ...prev,
                { role: 'error', content: 'Apologies, I hit a snag attempting to parse context matches for that request.' }
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="chat-container glass-panel animate-fade-in">
            <div className="chat-header">
                <span className="doc-badge">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M23 7a2 2 0 0 0-2.45-1.45L16 7V5a2 2 0 0 0-2-2H2a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2l4.55 1.45A2 2 0 0 0 23 17V7z"></path>
                    </svg>
                    {documentInfo.title || documentInfo.filename}
                </span>
            </div>

            <div className="messages-area">
                {messages.map((msg, index) => (
                    <div key={index} className={`message-wrapper ${msg.role}`}>
                        <div className={`message bubble ${msg.role}`}>
                            {msg.role === 'assistant' && (
                                <div className="avatar">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M12 2a2 2 0 0 1 2 2c-.11.88-.34 1.74-.68 2.54A7.47 7.47 0 0 1 18.5 11c0 4.14-3.36 7.5-7.5 7.5S3.5 15.14 3.5 11a7.47 7.47 0 0 1 5.18-4.46A8.5 8.5 0 0 0 8 4a2 2 0 0 1 4-2Z"></path>
                                    </svg>
                                </div>
                            )}
                            <div className="content">{msg.content}</div>
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="message-wrapper assistant">
                        <div className="message bubble assistant typing">
                            <span className="dot"></span>
                            <span className="dot"></span>
                            <span className="dot"></span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form className="input-area" onSubmit={handleSubmit}>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask any question about the video..."
                    disabled={isLoading}
                />
                <button type="submit" disabled={!input.trim() || isLoading} className="send-btn">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                </button>
            </form>
        </div>
    );
}