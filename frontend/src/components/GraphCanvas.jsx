import { useState, useEffect, useCallback, useRef, forwardRef, useImperativeHandle } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { fetchGraphFull } from '../services/api';

const ENTITY_SIZES = {
  Customer: 7,
  SalesOrder: 5,
  BillingDocument: 5,
  JournalEntry: 5,
  Payment: 5,
  Delivery: 5,
  SalesOrderItem: 3.5,
  Product: 3,
  Plant: 3,
};

// Light theme graph colors
const PRIMARY_BLUE = '#5ca9e6';
const SECONDARY_RED = '#f07b75';
const EDGE_COLOR = 'rgba(92, 169, 230, 0.35)';

const GraphCanvas = forwardRef(({ onNodeClick, highlightedNodes }, ref) => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [showGranular, setShowGranular] = useState(true);
  const [hoveredNodeId, setHoveredNodeId] = useState(null);
  const graphRef = useRef();

  useImperativeHandle(ref, () => ({
    fitToScreen: () => {
      if (graphRef.current) graphRef.current.zoomToFit(400, 50);
    },
    zoomIn: () => {
      if (graphRef.current) {
        const currentZoom = graphRef.current.zoom();
        graphRef.current.zoom(currentZoom * 1.5, 400);
      }
    }
  }));

  useEffect(() => {
    loadFullGraph();
  }, []);

  const loadFullGraph = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchGraphFull();
      // Only take a subset of nodes if the graph is too big for a smooth initial visual
      // but in this case, 797 nodes is easily handled by force graph rendering
      const nodes = data.nodes.map(n => ({
        id: n.id,
        entity_type: n.entity_type,
        connections: n.connections,
        isSuper: false,
        // Primary entities get blue, secondary (items/products) get red
        color: ['SalesOrderItem', 'Product', 'Plant'].includes(n.entity_type) ? SECONDARY_RED : PRIMARY_BLUE,
        val: ENTITY_SIZES[n.entity_type] || 3,
        ...n,
      }));
      
      const links = data.edges.map(e => ({
        source: e.source,
        target: e.target,
        relationship: e.relationship,
      }));
      
      setGraphData({ nodes, links });
      
      // Auto-zoom to fit after a short delay for physics to settle
      setTimeout(() => {
        if (graphRef.current) {
          graphRef.current.zoomToFit(400, 50);
        }
      }, 1000);
      
    } catch (err) {
      console.error('Failed to load full graph:', err);
    }
    setLoading(false);
  }, []);

  const handleNodeClick = useCallback((node) => {
    console.log("GraphCanvas captured node click:", node.id);
    if (onNodeClick) onNodeClick(node);
  }, [onNodeClick]);

  const handleNodeHover = useCallback((node) => {
    setHoveredNodeId(node ? node.id : null);
  }, []);

  const paintNode = useCallback((node, ctx, globalScale) => {
    const isHighlighted = highlightedNodes && highlightedNodes.has(node.id);
    const isHovered = hoveredNodeId === node.id;
    const size = node.val;
    
    // Highlight ring
    if (isHighlighted || isHovered) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, size + 3 + (2 / globalScale), 0, 2 * Math.PI);
      ctx.fillStyle = isHighlighted ? 'rgba(0, 122, 255, 0.2)' : 'rgba(0, 122, 255, 0.1)';
      ctx.fill();
    }

    // Main circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
    ctx.fillStyle = node.color || PRIMARY_BLUE;
    
    // Outline - ultra thin
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = Math.max(0.3 / globalScale, 0.5); 
    
    if (isHighlighted) {
      ctx.strokeStyle = '#007aff';
      ctx.lineWidth = Math.max(1.0 / globalScale, 1.0);
    }
    
    ctx.fill();
    ctx.stroke();

    // Declutter labels: show only if fully zoomed in, hovered, or selected
    if (globalScale > 1.4 || isHighlighted || isHovered) {
      const label = (node.id.split(':')[1] || '').substring(0, 12);
      ctx.font = `${4 / globalScale}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = isHighlighted || isHovered ? '#111827' : '#6b7280';
      ctx.fillText(label, node.x, node.y + size + Math.max(1.5 / globalScale, 2));
    }
  }, [highlightedNodes, hoveredNodeId]);

  return (
    <div className="graph-canvas">
      <div className="graph-controls">
        <button className="btn-white">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path></svg>
          Minimize
        </button>
        <button 
          className="btn-black"
          onClick={() => setShowGranular(!showGranular)}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
          {showGranular ? 'Hide Granular Overlay' : 'Show Granular Overlay'}
        </button>
      </div>
      
      {loading ? (
        <div className="graph-loading">
          <div className="spinner"></div>
          <p>Rendering network...</p>
        </div>
      ) : (
        <ForceGraph2D
          ref={graphRef}
          nodeRelSize={20}
          graphData={graphData}
          nodeCanvasObject={paintNode}
          nodePointerAreaPaint={(node, color, ctx, globalScale) => {
            const isHighlighted = highlightedNodes && highlightedNodes.has(node.id);
            const size = node.val;
            
            // Screen-space buffer of 8 pixels guaranteed at all zooms
            const buffer = 8 / globalScale;
            const interactionRadius = size + buffer;
            
            ctx.beginPath();
            ctx.arc(node.x, node.y, isHighlighted ? interactionRadius + 4 : interactionRadius, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
          }}
          linkColor={() => EDGE_COLOR}
          linkWidth={0.5}
          nodeVisibility={node => showGranular ? true : ['Customer', 'SalesOrder', 'BillingDocument', 'JournalEntry', 'Delivery'].includes(node.entity_type)}
          linkVisibility={link => {
            if (showGranular) return true;
            // If granular hidden, only show links between visible types
            const visibleTypes = ['Customer', 'SalesOrder', 'BillingDocument', 'JournalEntry', 'Delivery'];
            const sourceVisible = visibleTypes.includes(typeof link.source === 'object' ? link.source.entity_type : '');
            const targetVisible = visibleTypes.includes(typeof link.target === 'object' ? link.target.entity_type : '');
            return sourceVisible && targetVisible;
          }}
          // Arrow removal for airy look
          linkDirectionalArrowLength={0}
          onNodeClick={handleNodeClick}
          onNodeHover={handleNodeHover}
          backgroundColor="#ffffff"
          cooldownTicks={150}
          d3AlphaDecay={0.015}
          d3VelocityDecay={0.4}
          enableNodeDrag={true}
          enableZoomPanInteraction={true}
          minZoom={0.1}
          maxZoom={10}
        />
      )}
    </div>
  );
});

export default GraphCanvas;
