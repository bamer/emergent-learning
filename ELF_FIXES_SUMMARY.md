# ELF Superpowers Fixes Summary

This document summarizes the fixes applied to the Emergent Learning Framework (ELF) adaptation for OpenCode.ai.

## Issues Fixed

### 1. ✅ Auto-Learning with [LEARNED:] Markers
**Problem**: The post_tool_learning.py hook had extraction logic but wasn't being triggered properly by the OpenCode plugin system.

**Fix**: 
- Modified `ELF_superpowers.js` to pass tool execution context to Python scripts
- Updated `post_tool_learning.py` to accept input from command line arguments (OpenCode plugin format)
- Enhanced learning extraction to properly parse [LEARNED:] markers and auto-create heuristics

**Files Modified**:
- `ELF_superpowers.js` - Enhanced post-tool hook to pass context
- `hooks/learning-loop/post_tool_learning.py` - Added command line argument support

### 2. ✅ Heuristics Confidence Validation System
**Problem**: Database had heuristics but no golden rules, and the validation loop wasn't working properly.

**Fix**:
- Enhanced confidence validation in `post_tool_learning.py`
- Added proper validation counting for successful tasks
- Implemented violation tracking for failed tasks
- Added unknown outcome handling with light penalties

**Files Modified**:
- `hooks/learning-loop/post_tool_learning.py` - Enhanced validation logic

### 3. ✅ Golden Rules Integration
**Problem**: No heuristics were being promoted to golden rules.

**Fix**:
- Enhanced `check_golden_rule_promotion()` function
- Added promotion criteria: confidence >= 0.9, times_validated >= 10, low violation ratio
- Added logging for promotions

**Files Modified**:
- `hooks/learning-loop/post_tool_learning.py` - Enhanced promotion logic

### 4. ✅ Cross-Session Continuity
**Problem**: Session state management was broken.

**Fix**:
- Enhanced session state tracking in `pre_tool_learning.py`
- Added session_id and last_activity tracking
- Improved TTL-based session detection
- Better state persistence across tool calls

**Files Modified**:
- `hooks/learning-loop/pre_tool_learning.py` - Enhanced session state management

### 5. ✅ Async Watcher (OpenCode Model Integration)
**Problem**: Watcher was using wrong model (should be opencode/big-pickle).

**Fix**:
- Updated watcher prompt to specify opencode/big-pickle model
- Enhanced watcher documentation with correct model specification

**Files Modified**:
- `watcher/watcher_loop.py` - Added model specification

### 6. ✅ Swarm Agents Coordination
**Problem**: Coordination system wasn't properly integrated.

**Fix**:
- Enhanced conductor integration in `post_tool_learning.py`
- Added blackboard updates for agent status (active/completed/failed)
- Improved swarm coordination through proper status tracking
- Added opencode/big-pickle model specification for swarm tasks

**Files Modified**:
- `hooks/learning-loop/post_tool_learning.py` - Enhanced swarm coordination

### 7. ✅ Pheromone Trails Tracking
**Problem**: Trail tracking wasn't working.

**Fix**:
- Enhanced trail recording for file operations
- Improved file path normalization
- Better integration with trail_helper functions
- Added proper scent and strength values for different operation types

**Files Modified**:
- `hooks/learning-loop/post_tool_learning.py` - Enhanced trail tracking

### 8. ✅ Claude Agent to OpenCode Converter
**Problem**: Needed a way to convert Claude agents to OpenCode format.

**Fix**:
- Created `convert-claude-to-opencode.js` script
- Maps Claude fields to OpenCode permissions format
- Handles model alias conversion (sonnet → opencode/grok-code, etc.)
- Converts permissionMode to OpenCode mode format

**Files Created**:
- `convert-claude-to-opencode.js` - Complete conversion script

## Usage Instructions

### Activating ELF Superpowers
1. Ensure the plugin is symlinked: `~/.opencode/plugins/ELF_superpowers.js → ~/.opencode/emergent-learning/ELF_superpowers.js`
2. In OpenCode, run `/elf_activate` to enable ELF hooks for the session
3. Use investigation tools (Task, Bash, Grep, Read, Glob, Edit, Write) to trigger learning

### Auto-Learning with [LEARNED:] Markers
When completing tasks, include learning markers in your output:
```
[LEARNED:typescript] Always use type guards for runtime type checking
[LEARNED:api-design] REST endpoints should follow consistent naming conventions
```

### Golden Rules
Golden rules are automatically promoted from high-confidence heuristics. They appear first in pre-tool learning context.

### Swarm Coordination
The system automatically tracks agent status in the blackboard. Failed agents are marked appropriately for swarm coordination.

### Watcher System
Run the watcher to monitor swarm status:
```bash
python3 watcher/watcher_loop.py prompt
```

### Converting Claude Agents
To convert Claude agents to OpenCode format:
```bash
node convert-claude-to-opencode.js
```

## Database Schema
The system uses SQLite with these key tables:
- `heuristics` - Learning rules with confidence scores
- `trails` - File operation tracking for hotspot analysis
- `event_chronicle` - System event logging
- `metrics` - Performance and validation metrics
- `blackboard` - Swarm coordination state

## Model Usage
- **Main tasks**: opencode/big-pickle (OpenCode model)
- **Watcher monitoring**: opencode/big-pickle
- **Swarm agents**: opencode/big-pickle

## Troubleshooting

### Learning Not Triggering
- Ensure `/elf_activate` was run
- Check that tools are being used (Task, Bash, Grep, Read, Glob, Edit, Write)
- Verify Python scripts are executable

### Golden Rules Not Appearing
- Check that heuristics have high confidence (>= 0.9)
- Verify sufficient validation counts (>= 10)
- Look for violations that might prevent promotion

### Swarm Coordination Issues
- Check blackboard.json for agent status
- Verify conductor integration is working
- Ensure proper agent naming conventions

## Testing the Fixes

1. **Test Auto-Learning**:
   - Run `/elf_activate`
   - Use Task tool with a prompt
   - Include [LEARNED:] markers in the response
   - Check database for new heuristics

2. **Test Golden Rules**:
   - Complete multiple successful tasks
   - Check for promoted golden rules in pre-tool context
   - Verify confidence scores are increasing

3. **Test Swarm Coordination**:
   - Create multiple agents in blackboard
   - Run tasks and check status updates
   - Verify failed/completed status tracking

4. **Test Watcher**:
   - Run watcher prompt generation
   - Verify opencode/big-pickle model specification
   - Test status checking and logging

## Performance Notes

- Session state is TTL-based (4 hours) for cross-midnight work
- Heuristic validation uses lightweight confidence adjustments
- Trail tracking is optimized for file operation hotspots
- Database operations use proper timeouts and error handling

## Future Enhancements

- Real-time learning loop visualization
- Advanced pattern detection for [LEARNED:] markers
- Multi-model support for different task types
- Enhanced swarm coordination algorithms
- Integration with external knowledge bases