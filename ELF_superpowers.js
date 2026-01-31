/**
 * ELF Superpowers Plugin for OpenCode.ai
 *
 * SAFE HOOK VERSION:
 * - no await $
 * - no UI calls
 * - async fire-and-forget only
 */
import { $ } from "bun";
import { spawn } from "bun";

const PYTHON = "/home/bamer/.opencode/emergent-learning/.venv/bin/python";

function firePython(script, data) {
  const args = [ PYTHON, script ];

  if (data !== undefined) {
    args.push(JSON.stringify(data));
  }

  spawn(args, {
    stdin: "ignore",
    stdout: "ignore",
    stderr: "ignore",
  });
}

export default async (plugin) => {
  
  console.log("[ELF] 🧠 Superpowers plugin loaded");

  const ELF_DIR = "/home/bamer/.opencode/emergent-learning";
  const HOOKS_DIR = "/home/bamer/.opencode/emergent-learning/hooks";
  const LEARNING_LOOP_DIR = `${HOOKS_DIR}/learning-loop`;

  return {
    /**
     * Pre-tool learning hook
     */

    "tool.execute.before": async (input, output) => {
      const toolName = input?.tool ?? "unknown";
      console.log("[ELF] tool.execute.before hook fired for tool:", toolName );

      firePython(
        "/home/bamer/.opencode/emergent-learning/hooks/learning-loop/pre_tool_learning.py",
        { input, output, tool_name: toolName }
      );

      firePython(
        "/home/bamer/.opencode/emergent-learning/hooks/PreToolUse/semantic-memory.py",
        { input, output, tool_name: toolName }
      );
    },

    /**
     * Post-tool learning hook
     */
    "tool.execute.after": async (input, output) => {
      const toolName = input?.tool ?? "unknown";
      const payload = { input, output, tool_name: toolName };
      console.log("[ELF] tool.execute.after hook fired for tool:", toolName );

      firePython(
        "/home/bamer/.opencode/emergent-learning/hooks/learning-loop/post_tool_learning.py",
        payload
      );

      firePython(
        "/home/bamer/.opencode/emergent-learning/hooks/learning-loop/record_pheromone.py",
        payload
      );

      firePython(
        "/home/bamer/.opencode/emergent-learning/hooks/post_tool_use/sync-golden-rules.py",
        payload
      );
    },

    /* ================================
     * SESSION CREATED
     * ================================ */
    "session.created": async (input, output) => {
      console.log("[ELF] session check-in");
      
      firePython(
        "/home/bamer/.opencode/emergent-learning/query/checkin.py",
        { input, output, event: "session.created" }
      );

    },

    /* ================================
     * SESSION DELETED
     * ================================ */
    "session.deleted": async (input, output) => {
      console.log("[ELF] session checkout");
      firePython(
        "/home/bamer/.opencode/emergent-learning/query/checkout.py",
        { input, output, event: "session.deleted" }
      );
    },

    /* ================================
     * SESSION COMPACTING
     * ================================ */
    "experimental.session.compacting": async (input, output) => {
      console.log("[ELF] session compacting");

      firePython(
        "/home/bamer/.opencode/emergent-learning/hooks/PreToolUse/semantic-memory.py",
        {
          input,
          output,
          event: "session.compacting",
        }
      );
    }
  };
};
