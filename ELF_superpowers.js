/**
 * ELF Superpowers Hook Plugin for OpenCode.ai
 *
 * Minimal, non-invasive hooks for ELF learning system.
 * Activates only on /elf_activate command.
 *
 * Location: ~/.opencode/emergent-learning/ELF_superpowers.js
 * Symlink: ~/.opencode/plugins/ELF_superpowers.js → ELF root
 *
 * Features:
 * - Pre/post-tool learning hooks (auto-extract [LEARNED:] markers)
 * - Auto check-in/check-out on session lifecycle
 * - Lazy activation (no contamination until /elf_activate)
 * - Uses Python subprocess for ELF scripts (no bun dependency)
 */

import { tool } from "@opencode-ai/plugin";
import os from "os";
import path from "path";
import { existsSync, promises as fs } from "fs";
import { execFile, spawn } from "child_process";
import { promisify } from "util";

const HOME_DIR = os.homedir();
const OPENCODE_DIR = process.env.OPENCODE_DIR || path.join(HOME_DIR, ".opencode");
const ELF_DIR = path.join(HOME_DIR, ".opencode", "emergent-learning");

// Paths
const HOOKS_DIR = path.join(ELF_DIR, "hooks", "learning-loop");
const QUERY_DIR = path.join(ELF_DIR, "src", "query");

const pickPython = () => {
  const candidates = [
    process.env.ELF_PYTHON,
    path.join(ELF_DIR, ".venv", "bin", "python"),
    path.join(ELF_DIR, ".venv", "Scripts", "python.exe"),
    "python3",
    "python"
  ].filter(Boolean);
  return candidates.find((candidate) => existsSync(candidate)) || "python";
};

const PYTHON_CMD = pickPython();
const execFileAsync = promisify(execFile);

/**
 * Execute Python script directly (no shell/bun dependency)
 * 
 * Uses Node's execFile to spawn Python process directly with proper
 * environment. Captures stdout/stderr for logging and error handling.
 */
async function runPythonScript(scriptPath, args = []) {
  try {
    const { stdout, stderr } = await execFileAsync(PYTHON_CMD, [scriptPath, ...args], {
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

// Global state
let elfActive = false;
let sessionCheckinDone = false;
let sessionId = null;

/**
 * Record pheromone trails from tool execution
 * Tracks which files were accessed/modified
 */
async function recordPheromoneTrail(toolInput, HOOKS_DIR) {
  const pheromoneScript = path.join(HOOKS_DIR, "record_pheromone.py");
  
  // Only record for tools that access files
  const fileTouchingTools = ['Read', 'Grep', 'Bash', 'create_file', 'edit_file'];
  const toolName = toolInput.tool_name || toolInput.tool || '';
  
  if (fileTouchingTools.some(t => toolName.includes(t))) {
    const context = {
      tool_name: toolName,
      tool_input: toolInput.tool_input || toolInput.input || '',
      timestamp: new Date().toISOString()
    };
    
    if (existsSync(pheromoneScript)) {
      try {
        await runPythonScript(pheromoneScript, [JSON.stringify(context)]);
      } catch (error) {
        // Silently fail - pheromone is nice-to-have, not critical
      }
    }
  }
}

export const ELFHooksPlugin = async ({ client, $ }) => {
  return {
    /**
     * Pre-tool hook - runs before each tool
     * Only active if ELF is enabled
     */
    "tool.execute.before": async (input, output) => {
      if (!elfActive) return;

      try {
        const preToolScript = path.join(HOOKS_DIR, "pre_tool_learning.py");
        if (existsSync(preToolScript)) {
          await runPythonScript(preToolScript);
        }
      } catch (error) {
        await client.app.log({
          service: "elf-hooks",
          level: "warn",
          message: `Pre-tool hook error: ${error.message}`
        });
      }
    },

    /**
     * Post-tool hook - runs after each tool
     * Captures learnings from tool output + records pheromone trails
     */
    "tool.execute.after": async (input) => {
      if (!elfActive) return;

      try {
        const postToolScript = path.join(HOOKS_DIR, "post_tool_learning.py");
        if (existsSync(postToolScript)) {
          // Pass the tool execution context to the Python script
          const hookInput = {
            tool_name: input.tool_name || input.tool,
            tool_input: input.tool_input || input.input,
            tool_output: input.tool_output || input.output,
            timestamp: new Date().toISOString()
          };
          
          await runPythonScript(postToolScript, [JSON.stringify(hookInput)]);
        }
        
        // Record pheromone trails (file access tracking)
        await recordPheromoneTrail(input, HOOKS_DIR);
        
      } catch (error) {
        await client.app.log({
          service: "elf-hooks",
          level: "warn",
          message: `Post-tool hook error: ${error.message}`
        });
      }
    },

    /**
     * Session lifecycle hooks
     * Auto check-in on session.created, auto check-out on session.deleted
     * Also syncs golden rules and spawns async watcher
     */
    event: async ({ event }) => {
      if (!elfActive) return;

      const getSessionId = () => {
        return event.properties?.info?.id ||
               event.properties?.sessionID ||
               event.session?.id ||
               event.sessionID ||
               event.properties?.session?.id;
      };

      const currentSessionId = getSessionId();

      // Auto check-in on session create
      if (event.type === "session.created") {
        sessionId = currentSessionId;
        sessionCheckinDone = false;

        try {
          const checkinScript = path.join(QUERY_DIR, "query.py");
          const result = await runPythonScript(checkinScript, ["--context"]);
          
          if (result.exitCode === 0) {
            sessionCheckinDone = true;
            await client.app.log({
              service: "elf-hooks",
              level: "info",
              message: "ELF session activated - context loaded"
            });
          }
          
          // Sync golden rules on session start (non-blocking)
          const syncScript = path.join(QUERY_DIR, "sync_golden_rules.py");
          if (existsSync(syncScript)) {
            runPythonScript(syncScript).catch(() => {});  // Fire and forget
          }
          
          // Spawn async watcher (non-blocking)
          const autoSpawnScript = path.join(ELF_DIR, "watcher", "auto_spawn.py");
          if (existsSync(autoSpawnScript)) {
            runPythonScript(autoSpawnScript, ["--once"]).catch(() => {});  // Fire and forget
          }
          
        } catch (error) {
          await client.app.log({
            service: "elf-hooks",
            level: "warn",
            message: `Session check-in failed: ${error.message}`
          });
        }
      }

      // Auto check-out on session delete
      if (event.type === "session.deleted" && sessionCheckinDone) {
        try {
          const checkoutScript = path.join(QUERY_DIR, "checkout.py");
          await runPythonScript(checkoutScript, ["--auto", "--final"]);
          
          await client.app.log({
            service: "elf-hooks",
            level: "info",
            message: "ELF session closed - learnings recorded"
          });
        } catch (error) {
          await client.app.log({
            service: "elf-hooks",
            level: "warn",
            message: `Session check-out failed: ${error.message}`
          });
        }

        sessionId = null;
        sessionCheckinDone = false;
      }
    },

    tool: {
      /**
       * Swarm task handler - triggers swarm agent execution
       * Called when task is created/executed
       */
      swarm_task: tool({
        description: "Execute task using swarm of agents (Architect, Researcher, Skeptic, Creative)",
        args: {
          task: { type: "string", description: "Main task description" },
          subtasks: { type: "string", description: "Optional comma-separated subtasks" }
        },
        execute: async (args, ctx) => {
          if (!elfActive) {
            return "❌ ELF not activated. Run /elf_activate first.";
          }

          const swarmScript = path.join(ELF_DIR, "coordinator", "swarm_controller.py");
          if (!existsSync(swarmScript)) {
            return "❌ Swarm controller not found";
          }

          try {
            // Prepare subtasks argument
            const subtaskArgs = args.subtasks 
              ? ['--subtasks', ...args.subtasks.split(',')] 
              : [];

            const result = await runPythonScript(
              swarmScript,
              ['--task', args.task, ...subtaskArgs]
            );

            if (result.exitCode === 0) {
              await client.app.log({
                service: "elf-hooks",
                level: "info",
                message: `Swarm execution completed: ${args.task}`
              });

              return `✅ SWARM EXECUTION COMPLETE\n\n${result.stdout}`;
            } else {
              return `❌ Swarm execution failed:\n${result.stderr}`;
            }
          } catch (error) {
            await client.app.log({
              service: "elf-hooks",
              level: "error",
              message: `Swarm execution error: ${error.message}`
            });

            return `❌ Error: ${error.message}`;
          }
        }
      }),

      /**
       * Single activation command
       * Enables ELF hooks for this session
       */
      elf_activate: tool({
        description: "Enable ELF learning hooks for this session",
        args: {},
        execute: async (args, ctx) => {
          elfActive = true;
          
          await client.app.log({
            service: "elf-hooks",
            level: "info",
            message: "ELF hooks activated"
          });

          return `✅ ELF activated\n\nHooks are now active for this session.\n- Pre/post-tool learning enabled\n- Session auto check-in/check-out enabled\n- Swarm agents available via /swarm_task`;
        }
      })
    }
  };
};
