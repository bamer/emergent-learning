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

import { tool } from "@opencode-ai/plugin";
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
let elfActive = false;
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

  // Log helper with fallback
  const log = async (level, message) => {
    if (client?.app?.log) {
      await client.app.log({
        service: "elf-hooks",
        level,
        message
      });
    } else {
      console[level === 'error' ? 'error' : 'log'](`[ELF] ${message}`);
    }
  };

  // Lazy tool creation
  const createTools = () => {
    if (!tool) {
      console.warn("tool() is not available, tools will not be created");
      return {};
    }

    return {
      /**
       * Swarm task handler - executes task using swarm of agents
       */
      swarm_task: tool({
        description: "Execute task using swarm of agents (Architect, Researcher, Skeptic, Creative)",
        args: {
          task: { type: "string", description: "Main task description" },
          subtasks: { type: "string", description: "Optional comma-separated subtasks" }
        },
        execute: async (args) => {
          if (!elfActive) {
            return "❌ ELF not activated. Run /elf_activate first.";
          }

          const swarmScript = path.join(ELF_DIR, "coordinator", "swarm_controller.py");
          if (!existsSync(swarmScript)) {
            return "❌ Swarm controller not found";
          }

          try {
            const subtaskArgs = args.subtasks 
              ? args.subtasks.split(',').map(s => s.trim()) 
              : [];

            const result = await runPythonScript(
              swarmScript,
              ['--task', args.task, ...subtaskArgs]
            );

            if (result.exitCode === 0) {
              await log('info', `Swarm execution completed: ${args.task}`);
              return `✅ SWARM EXECUTION COMPLETE\n\n${result.stdout}`;
            } else {
              return `❌ Swarm execution failed:\n${result.stderr}`;
            }
          } catch (error) {
            await log('error', `Swarm execution error: ${error.message}`);
            return `❌ Error: ${error.message}`;
          }
        }
      }),

      /**
       * ELF activation command
       */
      elf_activate: tool({
        description: "Enable ELF learning hooks for this session",
        args: {},
        execute: async () => {
          elfActive = true;
          await log('info', "ELF hooks activated");
          return `✅ ELF activated\n\nHooks are now active for this session.\n- Session auto check-in/check-out enabled\n- Swarm agents available via /swarm_task`;
        }
      }),

      /**
       * Manual session check-in
       */
      checkin: tool({
        description: "Manually run ELF check-in script",
        args: {},
        execute: async () => {
          if (!elfActive) {
            return "❌ ELF not activated. Run /elf_activate first.";
          }

          const checkinShell = path.join(SCRIPTS_DIR, "checkin.sh");
          if (!existsSync(checkinShell)) {
            return "❌ Check-in script not found";
          }

          try {
            const { stdout, stderr } = await execFileAsync("bash", [checkinShell], {
              encoding: 'utf-8',
              env: { ...process.env, ELF_BASE_PATH: ELF_DIR }
            });

            await log('info', `Check-in completed`);
            return `✅ CHECK-IN COMPLETE\n\n${stdout}`;
          } catch (error) {
            await log('error', `Check-in error: ${error.message}`);
            return `❌ Check-in failed:\n${error.stderr || error.message}`;
          }
        }
      })
    };
  };

  return {
    /**
     * Pre-tool learning hook - runs before each tool execution
     */
    'tool:before': async (data) => {
      if (!elfActive) return;

      try {
        const preToolScript = path.join(HOOKS_DIR, "pre_tool_learning.py");
        if (existsSync(preToolScript)) {
          await runPythonScript(preToolScript, [JSON.stringify(data || {})]);
        }
      } catch (error) {
        await log('warn', `Pre-tool hook error: ${error.message}`);
      }
    },

    /**
     * Post-tool learning hook - runs after each tool execution
     * Captures learnings and records pheromone trails
     */
    'tool:after': async (data) => {
      if (!elfActive) return;

      try {
        // Post-tool learning
        const postToolScript = path.join(HOOKS_DIR, "post_tool_learning.py");
        if (existsSync(postToolScript)) {
          await runPythonScript(postToolScript, [JSON.stringify(data || {})]);
        }

        // Record pheromone trails (file access tracking)
        const pheromoneScript = path.join(HOOKS_DIR, "record_pheromone.py");
        if (existsSync(pheromoneScript)) {
          await runPythonScript(pheromoneScript, [JSON.stringify(data || {})]);
        }
      } catch (error) {
        await log('warn', `Post-tool hook error: ${error.message}`);
      }
    },

    /**
     * Session lifecycle management
     */
    'session:created': async (data) => {
      if (!elfActive) return;

      try {
        sessionId = data?.session?.id || data?.id;
        sessionCheckinDone = false;

        const checkinScript = path.join(QUERY_DIR, "checkin.py");
        if (existsSync(checkinScript)) {
          const result = await runPythonScript(checkinScript, [JSON.stringify(data || {})]);
          
          if (result.exitCode === 0) {
            sessionCheckinDone = true;
            await log('info', "ELF session activated - context loaded");
          }

          // Spawn async watcher (non-blocking)
          const autoSpawnScript = path.join(ELF_DIR, "watcher", "auto_spawn.py");
          if (existsSync(autoSpawnScript)) {
            runPythonScript(autoSpawnScript, ["--once"]).catch(() => {});
          }

          // Sync golden rules (non-blocking)
          const syncScript = path.join(QUERY_DIR, "sync_golden_rules.py");
          if (existsSync(syncScript)) {
            runPythonScript(syncScript).catch(() => {});
          }
        }
      } catch (error) {
        await log('warn', `Session check-in failed: ${error.message}`);
      }
    },

    'session:deleted': async (data) => {
      if (!elfActive || !sessionCheckinDone) return;

      try {
        const checkoutScript = path.join(QUERY_DIR, "checkout.py");
        if (existsSync(checkoutScript)) {
          await runPythonScript(checkoutScript, [JSON.stringify(data || {})]);
          await log('info', "ELF session closed - learnings recorded");
        }
      } catch (error) {
        await log('warn', `Session check-out failed: ${error.message}`);
      } finally {
        sessionId = null;
        sessionCheckinDone = false;
      }
    },

    // Tools
    tool: createTools()
  };
};
