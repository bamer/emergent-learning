/**
 * Swarm Orchestrator for OpenCode.ai
 * 
 * Coordinates the multi-agent swarm:
 * - Architect: System design and structure
 * - Researcher: Investigation and evidence
 * - Skeptic: Critical analysis and risk
 * - Creative: Innovation and possibilities
 * - Learning Extractor: Meta-learning and insights
 */

import architectAgent from './architect.js';
import researcherAgent from './researcher.js';
import skepticAgent from './skeptic.js';
import creativeAgent from './creative.js';
import learningExtractorAgent from './learning-extractor.js';

export const AGENTS = {
  architect: architectAgent,
  researcher: researcherAgent,
  skeptic: skepticAgent,
  creative: creativeAgent,
  learningExtractor: learningExtractorAgent
};

export const AGENT_ORDER = {
  analysis: ['researcher', 'architect'],
  design: ['architect', 'creative', 'skeptic'],
  implementation: ['architect', 'researcher', 'skeptic'],
  learning: ['learningExtractor', 'researcher', 'architect']
};

/**
 * Execute swarm task
 * @param {string} task - Main task description
 * @param {string} context - Optional context
 * @param {string} mode - 'analysis', 'design', 'implementation', 'learning', or 'all'
 * @returns {Promise<Object>} - Swarm results with responses from each agent
 */
export async function runSwarm(task, context = '', mode = 'all') {
  const results = {
    task,
    context,
    mode,
    timestamp: new Date().toISOString(),
    responses: {},
    summary: ''
  };

  const agentSequence = mode === 'all' 
    ? Object.keys(AGENTS)
    : (AGENT_ORDER[mode] || Object.keys(AGENTS));

  // Run agents in sequence
  for (const agentName of agentSequence) {
    const agent = AGENTS[agentName];
    if (!agent) continue;

    try {
      // In a real implementation, this would call Claude or another AI
      // For now, we structure the setup
      results.responses[agentName] = {
        name: agent.name,
        description: agent.description,
        status: 'ready',
        systemPrompt: agent.system,
        tools: agent.tools.map(t => ({ name: t.name, description: t.description }))
      };
    } catch (error) {
      results.responses[agentName] = {
        name: agent.name,
        error: error.message,
        status: 'failed'
      };
    }
  }

  results.summary = `Swarm execution completed for task: "${task}"\nAgents involved: ${agentSequence.join(', ')}`;
  
  return results;
}

/**
 * Get agent by name
 */
export function getAgent(name) {
  return AGENTS[name];
}

/**
 * Get all available agents
 */
export function getAllAgents() {
  return Object.entries(AGENTS).map(([key, agent]) => ({
    id: key,
    name: agent.name,
    description: agent.description
  }));
}

/**
 * Get recommended agent sequence for task type
 */
export function getRecommendedSequence(taskType) {
  return AGENT_ORDER[taskType] || Object.keys(AGENTS);
}

export default {
  runSwarm,
  getAgent,
  getAllAgents,
  getRecommendedSequence,
  AGENTS,
  AGENT_ORDER
};
