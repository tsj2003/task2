import { useState, useCallback, useRef } from 'react';
import GraphCanvas from './components/GraphCanvas';
import ChatPanel from './components/ChatPanel';
import NodeTooltip from './components/NodeTooltip';
import './App.css';

function App() {
  const [highlightedNodes, setHighlightedNodes] = useState(new Set());
  const [suggestedQuery, setSuggestedQuery] = useState('');
  const [selectedNode, setSelectedNode] = useState(null);
  const graphCanvasRef = useRef(null);

  const handleToolAction = (action) => {
    switch (action) {
      case 'focusChat':
        document.querySelector('.chat-input')?.focus();
        break;
      case 'fullscreen':
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen().catch(() => {});
        } else {
          document.exitFullscreen().catch(() => {});
        }
        break;
      case 'fit':
        graphCanvasRef.current?.fitToScreen();
        break;
      case 'zoom':
        graphCanvasRef.current?.zoomIn();
        break;
      case 'download':
        alert("Graph data export will be available in the next release.");
        break;
      case 'more':
        alert("Additional settings panel.");
        break;
      default:
        break;
    }
  };

  const handleReferencedEntities = useCallback((entities) => {
    const nodeIds = new Set();
    entities.forEach(e => {
      if (e.includes(':')) nodeIds.add(e);
    });
    setHighlightedNodes(nodeIds);
    setTimeout(() => setHighlightedNodes(new Set()), 8000);
  }, []);

  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node);
  }, []);

  return (
    <div className="app">
      <header className="navbar">
        <div className="navbar-left">
          <button className="icon-button" aria-label="Menu">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
          </button>
          <span className="navbar-breadcrumb">
            <span className="breadcrumb-dim">Mapping</span>
            <span className="breadcrumb-sep">/</span>
            <span className="breadcrumb-active">Order to Cash</span>
          </span>
        </div>
        <div className="navbar-right">
          <div className="dark-toolbar">
            <button className="toolbar-btn active" onClick={() => handleToolAction('focusChat')}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
              Ask AI
            </button>
            <div className="toolbar-divider"></div>
            <button className="toolbar-btn" title="Chat" onClick={() => handleToolAction('focusChat')}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            </button>
            <button className="toolbar-btn" title="Monitor" onClick={() => handleToolAction('fullscreen')}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
            </button>
            <button className="toolbar-btn" title="Crop" onClick={() => handleToolAction('fit')}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6.13 1L6 16a2 2 0 0 0 2 2h15"></path><path d="M1 6.13L16 6a2 2 0 0 1 2 2v15"></path></svg>
            </button>
            <button className="toolbar-btn" title="Zoom" onClick={() => handleToolAction('zoom')}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="11" y1="8" x2="11" y2="14"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>
            </button>
            <button className="toolbar-btn" title="Download" onClick={() => handleToolAction('download')}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            </button>
            <button className="toolbar-btn" title="More" onClick={() => handleToolAction('more')}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="1"></circle><circle cx="19" cy="12" r="1"></circle><circle cx="5" cy="12" r="1"></circle></svg>
            </button>
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="graph-section">
          {selectedNode && (
            <NodeTooltip 
              node={selectedNode} 
              onClose={() => setSelectedNode(null)} 
            />
          )}
          <GraphCanvas
            ref={graphCanvasRef}
            highlightedNodes={highlightedNodes}
            onNodeClick={handleNodeClick}
          />
        </div>

        <ChatPanel
          onReferencedEntities={handleReferencedEntities}
          suggestedQuery={suggestedQuery}
        />
      </main>
    </div>
  );
}

export default App;
