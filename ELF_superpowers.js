/**
 * ELF Superpowers Plugin for OpenCode.ai
 *
 * SAFE HOOK VERSION:
 * - no await $
 * - no UI calls
 * - async fire-and-forget only
 */

const ELF_DIR = "/home/bamer/.opencode/emergent-learning";
const HOOKS_DIR = "/home/bamer/.opencode/emergent-learning/hooks";
const LEARNING_LOOP_DIR = `${HOOKS_DIR}/learning-loop`;

export default async (plugin) => {
  const $ = plugin?.$;

  console.log("[ELF] 🧠 Superpowers plugin loaded");

  /**
   * Fire-and-forget runner
   */
  const runAsync = (cmd) => {
    setTimeout(() => {
      cmd().catch(() => {});
    }, 0);
  };

  return {
    /**
     * Pre-tool learning hook
     */
    "tool.execute.before": (input, output) => {
      const toolName = input?.tool || "unknown";
      console.log(`[ELF] pre-learning → ${toolName}`);

      const script = `${LEARNING_LOOP_DIR}/pre_tool_learning.py`;
      const data = { input, output, tool_name: toolName };

      runAsync(() =>
        $`python3 ${script} ${JSON.stringify(data)}`
      );
    },

    /**
     * Post-tool learning hook
     */
    "tool.execute.after": (input, output) => {
      const toolName = input?.tool || "unknown";
      console.log(`[ELF] post-learning → ${toolName}`);

      const data = { input, output, tool_name: toolName };

      runAsync(() =>
        $`python3 ${LEARNING_LOOP_DIR}/post_tool_learning.py ${JSON.stringify(data)}`
      );

      runAsync(() =>
        $`python3 ${LEARNING_LOOP_DIR}/record_pheromone.py ${JSON.stringify(data)}`
      );
    },

    /**
     * Session created
     */
    "session.created": (data) => {
      console.log("[ELF] session check-in");

      runAsync(() =>
        $`python3 ${ELF_DIR}/query/checkin.py ${JSON.stringify(data)}`
      );
    },

    /**
     * Session deleted
     */
    "session.deleted": (data) => {
      console.log("[ELF] session checkout");

      runAsync(() =>
        $`python3 ${ELF_DIR}/query/checkout.py ${JSON.stringify(data)}`
      );
    },

    /**
     * Session compacting
     */
    "experimental.session.compacting": (input, output) => {
      console.log("[ELF] session compacting");

      const data = { input, output, event: "session_compacting" };

      runAsync(() =>
        $`python3 ${HOOKS_DIR}/pre_tool_learning.py ${JSON.stringify(data)}`
      );
    }
  };
};
