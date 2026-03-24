const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchGraphOverview() {
  const res = await fetch(`${API_BASE}/api/graph/overview`);
  if (!res.ok) throw new Error('Failed to fetch graph overview');
  return res.json();
}

export async function fetchGraphFull() {
  const res = await fetch(`${API_BASE}/api/graph/full`);
  if (!res.ok) throw new Error('Failed to fetch full graph');
  return res.json();
}

export async function fetchNodesByType(entityType, limit = 50, offset = 0) {
  const res = await fetch(`${API_BASE}/api/graph/expand/${entityType}?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error(`Failed to fetch nodes for type: ${entityType}`);
  return res.json();
}

export async function fetchNodeDetail(nodeId) {
  const res = await fetch(`${API_BASE}/api/graph/node/${encodeURIComponent(nodeId)}`);
  if (!res.ok) throw new Error(`Failed to fetch node: ${nodeId}`);
  return res.json();
}

export async function fetchNodeNeighbors(nodeId, depth = 1) {
  const res = await fetch(`${API_BASE}/api/graph/node/${encodeURIComponent(nodeId)}/neighbors?depth=${depth}`);
  if (!res.ok) throw new Error(`Failed to fetch neighbors for: ${nodeId}`);
  return res.json();
}

export async function searchNodes(query) {
  const res = await fetch(`${API_BASE}/api/graph/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error('Search failed');
  return res.json();
}

export async function sendChatMessage(message, conversationId = 'default') {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, conversation_id: conversationId }),
  });
  if (!res.ok) {
    if (res.status === 429) throw new Error('Too many requests. Please wait a moment.');
    throw new Error('Failed to send message');
  }
  return res.json();
}

export async function clearConversation(conversationId = 'default') {
  const res = await fetch(`${API_BASE}/api/chat/${conversationId}`, { method: 'DELETE' });
  return res.json();
}
