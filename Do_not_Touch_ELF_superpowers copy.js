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


  return {
    /**
     * Pre-tool learning hook
     */
    "tool.execute.before": async (input, output) => {
      const toolName = input?.tool || "unknown";
      console.log(`[ELF] pre-learning → ${toolName}`);

      const script = `${LEARNING_LOOP_DIR}/pre_tool_learning.py`;
      const data = { input, output, tool_name: toolName };

      try {
        $`python3 ${script} '${JSON.stringify(data)}'`;
      } catch (error) {
        console.error(`[ELF] Error in pre-tool hook: ${error.message}`);
      }

    },

    /**
     * Post-tool learning hook
     */
    "tool.execute.after": async (input, output) => {
      const toolName = input?.tool || "unknown";
      console.log(`[ELF] post-learning → ${toolName}`);

      const data = { input, output, tool_name: toolName };

      try {
        $`python3 ${LEARNING_LOOP_DIR}/post_tool_learning.py '${JSON.stringify(data)}'`;
        $`python3 ${LEARNING_LOOP_DIR}/record_pheromone.py '${JSON.stringify(data)}'`;
        $`python3 ${HOOKS_DIR}/post_tool_use/sync-golden-rules.py '${JSON.stringify(data)}'`;
      } catch (error) {
        console.error(`[ELF] Error in post-tool hook: ${error.message}`);
      }
    },

    /**
     * Session created
     */
    "session.created": async (data) => {
      console.log("[ELF] session check-in");

      try {
        $`python3 ${ELF_DIR}/query/checkin.py '${JSON.stringify(data)}'`;
      } catch (error) {
        console.error(`[ELF] Error in session check-in: ${error.message}`);
      }
    },

    /**
     * Session deleted
     */
    "session.deleted": async (data) => {
      console.log("[ELF] session checkout");

      try {
        $`python3 ${ELF_DIR}/query/checkout.py '${JSON.stringify(data)}'`;
      } catch (error) {
        console.error(`[ELF] Error in session check-out: ${error.message}`);
      }

    },

    /**
     * Session compacting
     */
    "experimental.session.compacting": async (input, output) => {
      console.log("[ELF] session compacting");

      const data = { input, output, event: "session_compacting" };

      try {
        $`python3 ${HOOKS_DIR}/pre_tool_learning.py '${JSON.stringify(data)}'`;
      } catch (error) {
        console.error(`[ELF] Error in session compacting: ${error.message}`);
      }
    }
  };
};
