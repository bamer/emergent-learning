/**
 * Persistence Service - API calls for saving data to the database
 */

const API_BASE = '/api/v1/persistence';

export interface TrailData {
  location: string;
  location_type?: string;
  scent: 'discovery' | 'warning' | 'blocker' | 'hot' | 'info';
  strength?: number;
  agent_id?: string;
  message?: string;
  session_id?: string;
}

export interface HeuristicData {
  domain: string;
  rule: string;
  explanation?: string;
  confidence?: number;
  source_type?: 'auto' | 'manual' | 'ceo' | 'agent';
  is_golden?: boolean;
}

export interface TimelineEventData {
  event_type: string;
  source: string;
  summary?: string;
  data?: Record<string, any>;
  status?: string;
}

export interface LearningData {
  title: string;
  description: string;
  category?: string;
  confidence?: number;
  source?: string;
}

/**
 * Create a single trail
 */
export async function createTrail(trail: TrailData) {
  const response = await fetch(`${API_BASE}/trails`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(trail)
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create trail: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Create multiple trails in a batch
 */
export async function createTrailsBatch(trails: TrailData[]) {
  const response = await fetch(`${API_BASE}/trails/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(trails)
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create trails batch: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Create a single heuristic
 */
export async function createHeuristic(heuristic: HeuristicData) {
  const response = await fetch(`${API_BASE}/heuristics`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(heuristic)
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create heuristic: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Create multiple heuristics in a batch
 */
export async function createHeuristicsBatch(heuristics: HeuristicData[]) {
  const response = await fetch(`${API_BASE}/heuristics/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(heuristics)
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create heuristics batch: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Create a single timeline event
 */
export async function createTimelineEvent(event: TimelineEventData) {
  const response = await fetch(`${API_BASE}/timeline/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(event)
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create timeline event: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Create multiple timeline events in a batch
 */
export async function createTimelineEventsBatch(events: TimelineEventData[]) {
  const response = await fetch(`${API_BASE}/timeline/events/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(events)
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create timeline events batch: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Create a single learning
 */
export async function createLearning(learning: LearningData) {
  const response = await fetch(`${API_BASE}/learnings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(learning)
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create learning: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Create multiple learnings in a batch
 */
export async function createLearningsBatch(learnings: LearningData[]) {
  const response = await fetch(`${API_BASE}/learnings/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(learnings)
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create learnings batch: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Helper to record a discovery trail
 */
export async function recordDiscovery(
  location: string, 
  message: string, 
  agentId?: string,
  strength: number = 1
) {
  return createTrail({
    location,
    scent: 'discovery',
    message,
    agent_id: agentId,
    strength
  });
}

/**
 * Helper to record a warning trail
 */
export async function recordWarning(
  location: string, 
  message: string, 
  agentId?: string,
  strength: number = 2
) {
  return createTrail({
    location,
    scent: 'warning',
    message,
    agent_id: agentId,
    strength
  });
}

/**
 * Helper to record a blocker trail
 */
export async function recordBlocker(
  location: string, 
  message: string, 
  agentId?: string,
  strength: number = 3
) {
  return createTrail({
    location,
    scent: 'blocker',
    message,
    agent_id: agentId,
    strength
  });
}

/**
 * Helper to extract heuristics from agent response and save them
 * 
 * NOTE: All extracted heuristics are automatically:
 * - Saved to the heuristics table
 * - Embedded with Ollama (nomic-embed-text) for semantic search
 * - Indexed for retrieval
 * 
 * This captures BOTH:
 * 1. Explicit [LEARNED:domain] markers
 * 2. Implicit patterns with heuristic keywords (always, never, should, must, avoid, prefer, don't)
 */
export function extractAndSaveHeuristics(text: string, domain: string = 'general'): Promise<any> {
  const heuristics: HeuristicData[] = [];
  
  // Extract [LEARNED:domain] markers
  const learnedPattern = /\[LEARNED:([^\]]+)\](.*?)(?=\[LEARNED:|\[LEARNING:|\[LEARN:|$)/gis;
  let match;
  
  while ((match = learnedPattern.exec(text)) !== null) {
    const extractedDomain = match[1].trim().toLowerCase();
    const lesson = match[2].trim();
    
    if (lesson && lesson.length > 10) {
      heuristics.push({
        domain: extractedDomain || domain,
        rule: lesson,
        confidence: 0.6,
        source_type: 'agent'
      });
    }
  }
  
  // Also look for patterns with heuristic keywords
  const sentences = text.split(/[.!?\n]+/);
  const heuristicKeywords = ['always', 'never', 'should', 'must', 'avoid', 'prefer', 'don\'t'];
  
  for (const sentence of sentences) {
    const cleanSentence = sentence.trim();
    if (cleanSentence.length < 20 || cleanSentence.length > 300) continue;
    
    const hasKeyword = heuristicKeywords.some(kw => 
      cleanSentence.toLowerCase().includes(kw)
    );
    
    if (hasKeyword) {
      // Check if already captured
      const alreadyCaptured = heuristics.some(h => 
        cleanSentence.startsWith(h.rule.substring(0, 50))
      );
      
      if (!alreadyCaptured) {
        const words = cleanSentence.split(/\s+/);
        const potentialDomain = words[0]?.toLowerCase() || domain;
        
        heuristics.push({
          domain: potentialDomain,
          rule: cleanSentence,
          confidence: 0.4,
          source_type: 'agent'
        });
      }
    }
  }
  
  if (heuristics.length === 0) {
    return Promise.resolve({ status: 'ok', message: 'No heuristics found', count: 0 });
  }
  
  // Note: Each heuristic will be automatically embedded with Ollama on the backend
  return createHeuristicsBatch(heuristics);
}

/**
 * Auto-extract and save all learnings from any text
 * Captures explicit markers AND implicit patterns
 */
export function autoExtractLearnings(text: string, source: string = 'auto'): Promise<any> {
  const learnings: LearningData[] = [];
  
  // Extract [LEARNED:] markers
  const learnedPattern = /\[LEARNED:([^\]]+)\](.*?)(?=\[LEARNED:|\[LEARNING:|\[LEARN:|$)/gis;
  let match;
  
  while ((match = learnedPattern.exec(text)) !== null) {
    const domain = match[1].trim();
    const content = match[2].trim();
    
    if (content && content.length > 15) {
      learnings.push({
        title: `Learning: ${domain}`,
        description: content,
        category: domain,
        confidence: 0.7,
        source
      });
    }
  }
  
  // Extract patterns with learning indicators
  const sentences = text.split(/[.!?\n]+/);
  const learningIndicators = [
    'important to', 'need to', 'should', 'must', 'avoid', 
    'prefer', 'best practice', 'pattern', 'approach',
    'better to', 'recommend', 'key insight', 'discovery',
    'learning:', 'lesson:', 'takeaway:'
  ];
  
  for (const sentence of sentences) {
    const clean = sentence.trim();
    if (clean.length < 25 || clean.length > 400) continue;
    
    const hasIndicator = learningIndicators.some(ind => 
      clean.toLowerCase().includes(ind)
    );
    
    if (hasIndicator) {
      const alreadyCaptured = learnings.some(l => 
        clean.startsWith(l.description.substring(0, 30))
      );
      
      if (!alreadyCaptured) {
        const words = clean.split(/\s+/);
        const category = words.slice(0, 2).join('_').toLowerCase().replace(/[^a-z_]/g, '');
        
        learnings.push({
          title: `Auto-extracted: ${category}`,
          description: clean,
          category: category || 'general',
          confidence: 0.5,
          source
        });
      }
    }
  }
  
  if (learnings.length === 0) {
    return Promise.resolve({ status: 'ok', message: 'No learnings found', count: 0 });
  }
  
  // Note: Each learning will be automatically embedded with Ollama on the backend
  return createLearningsBatch(learnings);
}
