/**
 * ELF Superpowers Plugin for OpenCode.ai
 *
 * Minimal, non-invasive hooks for ELF learning system.
 * Activates only on /elf_activate command.
 *
 * Features:
 * - Session auto check-in/check-out on session lifecycle
 * - Swarm task execution (Architect, Researcher, Skeptic, Creative)
 * - ELF activation command
 * - Python subprocess integration (no bun dependency)
 */

import os from "os";
import path from "path";
import { existsSync, promises as fs } from "fs";
import { execFile } from "child_process";
import { promisify } from "util";

const HOME_DIR = os.homedir();
const ELF_DIR = path.join(HOME_DIR, ".opencode", "emergent-learning");
const HOOKS_DIR = path.join(ELF_DIR, "hooks", "learning-loop");
const QUERY_DIR = path.join(ELF_DIR, "query");
const SCRIPTS_DIR = path.join(ELF_DIR, "scripts");

const execFileAsync = promisify(execFile);

// Global state
let sessionCheckinDone = false;
let sessionId = null;

/**
 * Execute Python script directly
 */
async function runPythonScript(scriptPath, args = []) {
  const candidates = [
    process.env.ELF_PYTHON,
    path.join(ELF_DIR, ".venv", "bin", "python"),
    path.join(ELF_DIR, ".venv", "Scripts", "python.exe"),
    "python3",
    "python"
  ].filter(Boolean);
  
  const pythonCmd = candidates.find((candidate) => existsSync(candidate)) || "python";

  try {
    const { stdout, stderr } = await execFileAsync(pythonCmd, [scriptPath, ...args], {
      encoding: 'utf-8',
      maxBuffer: 10 * 1024 * 1024,
      env: { ...process.env, ELF_BASE_PATH: ELF_DIR }
    });
    return { exitCode: 0, stdout, stderr };
  } catch (error) {
    return {
      exitCode: error.code || 1,
      stdout: error.stdout || '',
      stderr: error.stderr || error.message
    };
  }
}

export default async (plugin) => {
  const client = plugin?.client;
  const $ = plugin?.$;

  // Log helper with fallback and debug info
  const log = async (level, message, extra = {}) => {
    if (client?.app?.log) {
      await client.app.log({
        service: "elf-hooks",
        level,
        message,
        extra: Object.keys(extra).length > 0 ? extra : undefined
      });
    } else {
      console[level === 'error' ? 'error' : 'log'](`[ELF] ${message}`, extra);
    }
  };

  // Record event to timeline (event_chronicle)
  const recordEvent = async (eventType, source, sourceId, summary, status = 'success', data = null) => {
    try {
      const eventScript = path.join(ELF_DIR, "query", "record_event.py");
      if (existsSync(eventScript)) {
        const eventData = {
          event_type: eventType,
          source,
          source_id: sourceId,
          summary,
          status,
          data: data ? JSON.stringify(data) : null,
          timestamp: new Date().toISOString()
        };
        
        await runPythonScript(eventScript, [JSON.stringify(eventData)]);
      }
    } catch (error) {
      // Silent fail for event recording
    }
  };

  // Debug notification for event tracking
  const debugNotify = async (eventType, scriptPath, scriptName, result = null) => {
    const timestamp = new Date().toISOString();
    const scriptExists = existsSync(scriptPath);
    const exitCode = result?.exitCode;
    const hasOutput = result?.stdout?.length > 0;
    
    const debugInfo = {
      event: eventType,
      script: scriptName,
      timestamp,
      scriptExists,
      exitCode,
      hasOutput,
      outputSize: result?.stdout?.length || 0
    };

    await log('info', `[${eventType}] Executing ${scriptName}`, debugInfo);
  };



  return {
    /**
     * Pre-tool learning hook - runs before each tool execution
     * Official hook: tool.execute.before
     */
    'tool.execute.before': async (input, output) => {
      const toolName = input?.tool || 'unknown';
      
      try {
        const preToolScript = path.join(HOOKS_DIR, "pre_tool_learning.py");
        if (existsSync(preToolScript)) {
          await log('info', `[BEFORE] Tool: ${toolName}`, { tool: toolName, inputKeys: Object.keys(input || {}) });
          
          const data = { input, output };
          const result = await runPythonScript(preToolScript, [JSON.stringify(data || {})]);
          
          await debugNotify('tool.execute.before', preToolScript, 'pre_tool_learning.py', result);
        } else {
          await log('warn', `[BEFORE] Script not found: pre_tool_learning.py`, { searchPath: preToolScript });
        }
      } catch (error) {
        await log('error', `[BEFORE] Pre-tool hook error: ${error.message}`, { tool: toolName, error: error.toString() });
      }
    },

    /**
     * Post-tool learning hook - runs after each tool execution
     * Captures learnings and records pheromone trails
     * Official hook: tool.execute.after
     */
    'tool.execute.after': async (input, output) => {
      const toolName = input?.tool || 'unknown';
      const resultStatus = output?.result?.exitCode === 0 ? 'success' : 'failed';
      
      try {
        // Post-tool learning
        const postToolScript = path.join(HOOKS_DIR, "post_tool_learning.py");
        if (existsSync(postToolScript)) {
          await log('info', `[AFTER] Tool: ${toolName} | Status: ${resultStatus}`, { 
            tool: toolName, 
            status: resultStatus,
            outputSize: output?.result?.stdout?.length || 0
          });
          
          const data = { input, output };
          const result = await runPythonScript(postToolScript, [JSON.stringify(data || {})]);
          
          await debugNotify('tool.execute.after (learning)', postToolScript, 'post_tool_learning.py', result);
          
          // Record tool execution event to timeline
          await recordEvent(
            'tool_executed',
            'opencode-plugin',
            sessionId || 'unknown',
            `Tool executed: ${toolName} (${resultStatus})`,
            resultStatus,
            { tool: toolName, exitCode: result.exitCode }
          );
        } else {
          await log('warn', `[AFTER] Script not found: post_tool_learning.py`, { searchPath: postToolScript });
        }

        // Record pheromone trails (file access tracking)
        const pheromoneScript = path.join(HOOKS_DIR, "record_pheromone.py");
        if (existsSync(pheromoneScript)) {
          const data = { input, output };
          const result = await runPythonScript(pheromoneScript, [JSON.stringify(data || {})]);
          
          await debugNotify('tool.execute.after (pheromone)', pheromoneScript, 'record_pheromone.py', result);
        } else {
          await log('warn', `[AFTER] Script not found: record_pheromone.py`, { searchPath: pheromoneScript });
        }
      } catch (error) {
        await log('error', `[AFTER] Post-tool hook error: ${error.message}`, { tool: toolName, error: error.toString() });
        await recordEvent('tool_error', 'opencode-plugin', sessionId || 'unknown', `Tool error: ${toolName}`, 'failed', { error: error.message });
      }
    },

    /**
     * Session created - Initialize ELF context when session starts
     * Official hook: session.created
     */
    'session.created': async (data) => {
      const sid = data?.session?.id || data?.id;
      
      try {
        sessionId = sid;
        sessionCheckinDone = false;

        await log('info', `[SESSION.CREATED] Starting ELF session`, { sessionId: sid });
        await recordEvent('session_created', 'opencode-plugin', sid, 'ELF session started', 'success');

        const checkinScript = path.join(QUERY_DIR, "checkin.py");
        if (existsSync(checkinScript)) {
          const result = await runPythonScript(checkinScript, [JSON.stringify(data || {})]);
          
          await debugNotify('session.created (checkin)', checkinScript, 'checkin.py', result);
          
          if (result.exitCode === 0) {
            sessionCheckinDone = true;
            await log('info', "ELF session activated - context loaded", { sessionId: sid, exitCode: 0 });
          } else {
            await log('warn', "ELF session check-in failed", { sessionId: sid, exitCode: result.exitCode });
          }

          // Spawn async watcher (non-blocking)
          const autoSpawnScript = path.join(ELF_DIR, "watcher", "auto_spawn.py");
          if (existsSync(autoSpawnScript)) {
            await log('info', "[SESSION.CREATED] Spawning watcher", { script: 'auto_spawn.py' });
            runPythonScript(autoSpawnScript, ["--once"]).catch(err => {
              log('warn', `[SESSION.CREATED] Watcher spawn failed: ${err.message}`);
            });
          }

          // Sync golden rules (non-blocking)
          const syncScript = path.join(QUERY_DIR, "sync_golden_rules.py");
          if (existsSync(syncScript)) {
            await log('info', "[SESSION.CREATED] Syncing golden rules", { script: 'sync_golden_rules.py' });
            runPythonScript(syncScript).catch(err => {
              log('warn', `[SESSION.CREATED] Golden rules sync failed: ${err.message}`);
            });
          }
        } else {
          await log('warn', `[SESSION.CREATED] Checkin script not found`, { searchPath: checkinScript });
        }
      } catch (error) {
        await log('error', `[SESSION.CREATED] Session check-in failed: ${error.message}`, { sessionId: sid, error: error.toString() });
        await recordEvent('session_error', 'opencode-plugin', sid, `Session check-in failed: ${error.message}`, 'failed');
      }
    },

    /**
     * Session deleted - Persist learnings when session ends
     * Official hook: session.deleted
     */
    'session.deleted': async (data) => {
      const sid = sessionId;
      
      if (!sessionCheckinDone) {
        await log('debug', `[SESSION.DELETED] Session not checked in, skipping checkout`, { sessionId: sid });
        return;
      }

      try {
        await log('info', `[SESSION.DELETED] Closing ELF session`, { sessionId: sid });
        await recordEvent('session_closed', 'opencode-plugin', sid, 'ELF session closed', 'success');
        
        const checkoutScript = path.join(QUERY_DIR, "checkout.py");
        if (existsSync(checkoutScript)) {
          const result = await runPythonScript(checkoutScript, [JSON.stringify(data || {})]);
          
          await debugNotify('session.deleted (checkout)', checkoutScript, 'checkout.py', result);
          await log('info', "ELF session closed - learnings recorded", { sessionId: sid, exitCode: result.exitCode });
        } else {
          await log('warn', `[SESSION.DELETED] Checkout script not found`, { searchPath: checkoutScript });
        }
      } catch (error) {
        await log('error', `[SESSION.DELETED] Session check-out failed: ${error.message}`, { sessionId: sid, error: error.toString() });
        await recordEvent('session_error', 'opencode-plugin', sid, `Session checkout failed: ${error.message}`, 'failed');
      } finally {
        sessionId = null;
        sessionCheckinDone = false;
      }
    },

    /**
     * Session compacted - Inject ELF context during session continuation
     * Official hook: experimental.session.compacting
     */
    'experimental.session.compacting': async (input, output) => {
      try {
        await log('info', `[SESSION.COMPACTING] Session continuation triggered`, { sessionId });
        
        // Inject ELF learnings and heuristics into the compaction context
        const compactScript = path.join(HOOKS_DIR, "pre_tool_learning.py");
        if (existsSync(compactScript)) {
          const data = { input, output, event: "session_compacting" };
          const result = await runPythonScript(compactScript, [JSON.stringify(data || {})]);
          
          await debugNotify('session.compacting (context inject)', compactScript, 'pre_tool_learning.py', result);
        } else {
          await log('warn', `[SESSION.COMPACTING] Compaction script not found`, { searchPath: compactScript });
        }
      } catch (error) {
        await log('error', `[SESSION.COMPACTING] Session compaction error: ${error.message}`, { sessionId, error: error.toString() });
      }
    }
  };
};
