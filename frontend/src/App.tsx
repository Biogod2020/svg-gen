import React, { useState } from 'react';
import { useStore } from './store/useStore';
import VisualStage from './components/VisualStage/VisualStage';
import Filmstrip from './components/Filmstrip';
import DownloadButton from './components/DownloadButton';
import { 
  Plus, 
  Search, 
  History as HistoryIcon, 
  HelpCircle, 
  Settings, 
  Image as ImageIcon,
  LayoutGrid,
  Sparkles,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import './styles/md3.css';
import './App.css';

const App: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [styleHints, setStyleHints] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'create' | 'history'>('create');

  const { history, currentIterationIndex, setHistory, generateStream } = useStore();
  const currentIteration = history[currentIterationIndex];

  const handleGenerate = async () => {
    if (!prompt) return;

    setIsLoading(true);
    setError(null);
    setHistory([]); // Fresh start
    
    try {
      const hintsArray = styleHints
        .split(',')
        .map(s => s.trim())
        .filter(Boolean);
        
      await generateStream(prompt, hintsArray);
      setActiveTab('create');
    } catch (err: any) {
      setError(err.message || 'Generation failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="md3-app-container">
      {/* Navigation Rail - Classic M3 Side Nav */}
      <nav className="md3-navigation-rail">
        <div className="rail-top">
          <div className="app-logo">
            <Sparkles size={28} color="var(--md-sys-color-primary)" fill="var(--md-sys-color-primary-container)" />
          </div>
          <button 
            className={`rail-fab ${isLoading ? 'loading' : ''}`} 
            onClick={() => { setPrompt(''); setHistory([]); }}
            title="New Creation"
          >
            <Plus size={24} />
          </button>
        </div>
        
        <div className="rail-center">
          <button 
            className={`rail-item ${activeTab === 'create' ? 'active' : ''}`}
            onClick={() => setActiveTab('create')}
          >
            <div className="icon-wrapper"><ImageIcon size={22} /></div>
            <span>Stage</span>
          </button>
          <button 
            className={`rail-item ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            <div className="icon-wrapper"><HistoryIcon size={22} /></div>
            <span>Timeline</span>
          </button>
          <button className="rail-item">
            <div className="icon-wrapper"><LayoutGrid size={22} /></div>
            <span>Gallery</span>
          </button>
        </div>

        <div className="rail-bottom">
          <button className="rail-item"><Settings size={22} /></button>
          <button className="rail-item"><HelpCircle size={22} /></button>
          <div className="user-profile">J</div>
        </div>
      </nav>

      {/* Main Container */}
      <main className="md3-main">
        <header className="md3-top-bar">
          <div className="search-bar-container">
            <div className="m3-search-bar">
              <Search size={20} className="search-icon" />
              <input
                type="text"
                placeholder="Describe what to generate..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
                disabled={isLoading}
              />
              {isLoading && <RefreshCw className="spin" size={20} color="var(--md-sys-color-primary)" />}
              {!isLoading && (
                 <button className="m3-generate-btn filled" onClick={handleGenerate} disabled={!prompt}>
                    <span>Create</span>
                 </button>
              )}
            </div>
          </div>
        </header>

        <section className="md3-content-area">
          {history.length > 0 ? (
            <div className="md3-stage-layout">
              {/* Central Hero Card for SVG */}
              <div className="md3-stage-card-wrapper">
                <div className="md3-stage-card card">
                  <div className="stage-top-actions">
                     <div className="iteration-badge tonal">
                        v{currentIterationIndex + 1} • {currentIteration?.vqa_results?.status || 'PENDING'}
                     </div>
                     <div className="stage-export">
                        {currentIteration && currentIteration.svg_code && (
                          <DownloadButton 
                            svgCode={currentIteration.svg_code} 
                            iterationIndex={currentIterationIndex} 
                          />
                        )}
                     </div>
                  </div>
                  <div className="stage-canvas">
                    <VisualStage />
                  </div>
                </div>
              </div>

              {/* Collapsible History Strip or Sidebar */}
              {activeTab === 'history' && (
                <aside className="md3-sidebar">
                   <div className="sidebar-title">Optimization History</div>
                   <Filmstrip />
                </aside>
              )}
            </div>
          ) : (
            <div className="md3-welcome">
               <div className="welcome-card card">
                  <h2>SVG Optimization Lab</h2>
                  <p>Harness VLM Agents to generate and refine scientifically accurate vector graphics.</p>
                  <div className="prompt-suggestions">
                    <button onClick={() => setPrompt('12-lead ECG electrode placement')}>ECG Placement</button>
                    <button onClick={() => setPrompt('Cellular membrane cross-section')}>Cell Membrane</button>
                    <button onClick={() => setPrompt('Cloud architecture with VPC and RDS')}>Cloud Infra</button>
                  </div>
               </div>
            </div>
          )}
        </section>

        <footer className="md3-footer">
          <div className="style-chips">
             <span className="chip-label">Style:</span>
             <input 
               className="chip-input" 
               placeholder="Add style hints (e.g. Flat, Apple-style...)"
               value={styleHints}
               onChange={(e) => setStyleHints(e.target.value)}
             />
          </div>
        </footer>
      </main>

      {error && (
        <div className="md3-snackbar error">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};

export default App;
