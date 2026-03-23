import React, { useState } from 'react';
import useStore from './store/useStore';
import VisualStage from './components/VisualStage/VisualStage';
import Filmstrip from './components/Filmstrip';
import DebugDrawer from './components/DebugDrawer';
import { Send, Settings, Terminal, RefreshCw, AlertCircle } from 'lucide-react';
import './styles/md3.css';
import './App.css';

const App: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [styleHints, setStyleHints] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { history, setHistory, toggleDrawer, isDrawerOpen } = useStore();

  const handleGenerate = async () => {
    if (!prompt) return;

    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, style_hints: styleHints }),
      });

      if (!response.ok) {
        throw new Error('Generation failed. Please try again.');
      }

      const data = await response.json();
      if (data.history) {
        setHistory(data.history);
      } else if (data.svg) {
        // Fallback for single result
        setHistory([{
          iteration: 0,
          svg_code: data.svg,
          vqa_results: {
            status: data.vqa_status || 'PASS',
            score: 100,
            issues: [],
            suggestions: [],
            summary: 'Single result generated'
          },
          thoughts: data.caption || ''
        }]);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-left">
          <div className="logo-icon">S</div>
          <h1>SVG Optimization Lab</h1>
        </div>
        <div className="header-right">
          <button className="icon-btn" title="Settings"><Settings size={20} /></button>
          <button 
            className={`icon-btn ${isDrawerOpen ? 'active' : ''}`} 
            onClick={toggleDrawer}
            title="Toggle Debug Drawer"
          >
            <Terminal size={20} />
          </button>
        </div>
      </header>

      <main className="app-main">
        <div className="main-content">
          <div className="stage-area">
            {history.length > 0 ? (
              <VisualStage />
            ) : (
              <div className="empty-stage">
                {isLoading ? (
                  <div className="loading-state">
                    <RefreshCw className="spin" size={48} />
                    <p>Agent is thinking and drawing...</p>
                  </div>
                ) : (
                  <div className="welcome-state">
                    <h2>Ready to Create</h2>
                    <p>Describe what you want to generate, and our VLM Agent will handle the rest.</p>
                  </div>
                )}
              </div>
            )}
          </div>
          
          <div className="input-area">
            <div className="input-card card">
              <div className="input-row">
                <textarea
                  placeholder="Describe your SVG (e.g., 'A modern cloud architecture diagram')..."
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  disabled={isLoading}
                />
                <button 
                  className="primary generate-btn" 
                  onClick={handleGenerate}
                  disabled={isLoading || !prompt}
                >
                  {isLoading ? <RefreshCw className="spin" size={18} /> : <Send size={18} />}
                  <span>Generate</span>
                </button>
              </div>
              <div className="style-hints-row">
                <input
                  type="text"
                  placeholder="Style hints (e.g., 'Flat design, Google Blue colors')"
                  value={styleHints}
                  onChange={(e) => setStyleHints(e.target.value)}
                  disabled={isLoading}
                />
              </div>
            </div>
          </div>

          <div className="filmstrip-area">
            <Filmstrip />
          </div>
        </div>

        <DebugDrawer />
      </main>

      {error && (
        <div className="error-toast">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};

export default App;
