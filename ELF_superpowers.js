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
      const script_semantic_memory = `/home/bamer/OPC_ELF/Emergent-Learning-Framework_ELF/.hooks-templates/PreToolUse/semantic-memory.py`;
      const data = { input, output, tool_name: toolName };

        $`python3 ${script} ${JSON.stringify(data)}`;
        $`python3 ${script_semantic_memory} ${JSON.stringify(data)}`;

    },

    /**
     * Post-tool learning hook
     */
    "tool.execute.after": async (input, output) => {
      const toolName = input?.tool || "unknown";
      console.log(`[ELF] post-learning → ${toolName}`);

      const data = { input, output, tool_name: toolName };

        $`python3 ${LEARNING_LOOP_DIR}/post_tool_learning.py ${JSON.stringify(data)}`;

        $`python3 ${LEARNING_LOOP_DIR}/record_pheromone.py ${JSON.stringify(data)}`;

        $`python3 /home/bamer/OPC_ELF/Emergent-Learning-Framework_ELF/.hooks-templates/PostToolUse/sync-golden-rules.py ${JSON.stringify(data)}`;
    },

    /**
     * Session created
     */
    "session.created": async (data) => {
      console.log("[ELF] session check-in");

        $`python3 ${ELF_DIR}/query/checkin.py ${JSON.stringify(data)}`
    },

    /**
     * Session deleted
     */
    "session.deleted": async (data) => {
      console.log("[ELF] session checkout");

  
        $`python3 ${ELF_DIR}/query/checkout.py ${JSON.stringify(data)}`
    
    },

    /**
     * Session compacting
     */
    "experimental.session.compacting": async (input, output) => {
      console.log("[ELF] session compacting");

      const data = { input, output, event: "session_compacting" };

        $`python3 ${HOOKS_DIR}/pre_tool_learning.py ${JSON.stringify(data)}`
    }
  };
};
