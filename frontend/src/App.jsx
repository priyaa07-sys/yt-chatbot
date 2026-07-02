import { useState } from 'react';
import './App.css';
import FileUpload from '../componenets/Urlupload'; // FileUpload component updated to handle URLs below
import ChatInterface from '../componenets/ChatInterface';

function App() {
  const [documentInfo, setDocumentInfo] = useState(null);

  const resetSession = () => {
    setDocumentInfo(null);
  };

  return (
    <div className="app-container">
      <header className="header animate-fade-in">
        <h1>Chat with YT Video</h1>
        <p>Paste any link of a YouTube video and chat with it in real-time using AI - ask questions, get summaries, pinpoint key points!

</p>
      </header>

      <main className="main-content">
        {!documentInfo ? (
          <FileUpload onUploadComplete={setDocumentInfo} />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', width: '100%', gap: '1rem' }}>
            <div style={{ alignSelf: 'flex-start' }}>
              <button onClick={resetSession} className="glass-panel" style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
                ← Analyze Different Video
              </button>
            </div>
            <ChatInterface documentInfo={documentInfo} />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;