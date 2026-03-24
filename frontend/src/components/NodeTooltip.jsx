import { useState, useEffect } from 'react';

export default function NodeTooltip({ node, onClose }) {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  
  // Position tooltip relative to the node
  // The graph canvas can zoom/pan, but for simplicity, we'll place it centrally
  // or top-left. Let's position it statically over the graph in the CSS 
  // (top: 80px; left: 80px) since the reference screenshot shows it 
  // sitting inside the graph area, not strictly anchored.
  
  if (!node) return null;

  const entityType = node.entity_type || node.id?.split(':')[0] || 'Unknown';
  const nodeId = node.id?.split(':')[1] || node.id || '';
  
  // Filter out internal/display properties
  const skipKeys = new Set(['id', 'x', 'y', 'vx', 'vy', 'fx', 'fy', 'index', '__indexColor', 
    'color', 'val', 'isSuper', 'label', 'score', 'connections', 'entity_type']);
  
  const entries = Object.entries(node)
    .filter(([k, v]) => !skipKeys.has(k) && v !== null && v !== '' && v !== undefined)
    .map(([k, v]) => [k, typeof v === 'boolean' ? (v ? 'Yes' : 'No') : String(v)]);

  const visibleEntries = entries.slice(0, 15);
  const hiddenCount = entries.length - visibleEntries.length;

  return (
    <div className="node-tooltip" style={{ top: '80px', left: '200px' }} onClick={e => e.stopPropagation()}>
      <div className="tooltip-title">{entityType}</div>
      <div className="tooltip-row">
        <span className="tooltip-key">Entity:</span>
        <span className="tooltip-value">{entityType}</span>
      </div>
      <div className="tooltip-row" style={{ marginBottom: '4px' }}>
        <span className="tooltip-key">{entityType === 'SalesOrder' ? 'SalesOrder' : entityType === 'JournalEntry' ? 'Document' : 'ID'}:</span>
        <span className="tooltip-value">{nodeId}</span>
      </div>
      
      {visibleEntries.map(([key, value]) => (
        <div key={key} className="tooltip-row">
          <span className="tooltip-key">{key}:</span>
          <span className="tooltip-value">{value}</span>
        </div>
      ))}
      
      {hiddenCount > 0 && (
        <div className="tooltip-row" style={{ marginTop: '8px', fontStyle: 'italic', color: 'var(--text-muted)' }}>
          Additional fields hidden for readability
        </div>
      )}
      
      {node.connections !== undefined && (
        <div className="tooltip-row" style={{ marginTop: hiddenCount > 0 ? '4px' : '8px' }}>
          <span className="tooltip-key" style={{ fontWeight: 600, color: 'var(--text-main)' }}>Connections:</span>
          <span className="tooltip-value" style={{ fontWeight: 600 }}>{node.connections}</span>
        </div>
      )}
      
      {/* Hidden close button to allow clicking outside to close smoothly without X button visual clutter */}
      <button className="tooltip-close" onClick={onClose} aria-label="Close tooltip">×</button>
    </div>
  );
}
