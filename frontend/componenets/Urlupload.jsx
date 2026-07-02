import React, { useState } from 'react';
import './Urlupload.css';

export default function Urlupload({ onUploadComplete }) {
    const [videoUrl, setVideoUrl] = useState('');
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);

        if (!videoUrl.trim()) {
            setError('Please enter a valid YouTube URL.');
            return;
        }

        setIsUploading(true);
        try {
            const response = await fetch('http://localhost:8000/api/process-video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: videoUrl.trim() }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to process video transcript.');
            }

            const data = await response.json();
            onUploadComplete(data);
        } catch (err) {
            console.error('Processing Error:', err);
            setError(err.message || 'An error occurred while loading video content.');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="video-input-container glass-panel animate-fade-in">
            {/* Elegant YouTube Identity Header */}

            <h2>Analyze YouTube Video</h2>
            <p className="input-subtitle">Enter a YouTube link below to index its transcript context</p>

            <form onSubmit={handleSubmit} className="url-form">
                {isUploading ? (
                    /* High-fidelity custom loading bar state matching your CSS rules */
                    <div className="loading-status">
                        <p>collecting video transcripts...</p>
                        <div className="progress-bar">
                            <div className="progress-fill"></div>
                        </div>
                    </div>
                ) : (
                    /* Proper input structural layout wrappers */
                    <>
                        <div className={`url-input-wrapper ${error ? 'error' : ''}`}>
                            {/* SVG Link Icon decoration */}
                            <svg className="link-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                            </svg>
                            <input
                                type="text"
                                value={videoUrl}
                                onChange={(e) => setVideoUrl(e.target.value)}
                                placeholder="Paste a YT video link here..."
                                disabled={isUploading}
                            />
                        </div>
                        
                        <button type="submit" className="process-btn" disabled={isUploading}>
                            {isUploading && <div className="btn-spinner"></div>}
                            Load Video
                        </button>
                    </>
                )}
                
            </form>

            {error && <div className="error-message">{error}</div>}

            {/* Editorial Footer Formats */}
            <div className="footer-note">
            </div>
        </div>
    );
}