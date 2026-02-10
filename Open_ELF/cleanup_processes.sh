#!/bin/bash
# Cleanup script - Kill zombie processes and prepare for testing

YELLOW='\033[1;33m'
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== ELF Process Cleanup Script ===${NC}"
echo ""

# 1. Kill language servers (bash-language-server, pyright)
echo -e "${YELLOW}1. Killing language servers (bash-language-server, pyright)...${NC}"
LANGUAGE_SERVER_PIDS=$(ps aux | grep -E "bash-language-server|pyright" | grep -v grep | awk '{print $2}')
if [ -n "$LANGUAGE_SERVER_PIDS" ]; then
    echo "Killing: $LANGUAGE_SERVER_PIDS"
    kill $LANGUAGE_SERVER_PIDS 2>/dev/null
    sleep 2
    # Force kill if still running
    LANGUAGE_SERVER_PIDS=$(ps aux | grep -E "bash-language-server|pyright" | grep -v grep | awk '{print $2}')
    if [ -n "$LANGUAGE_SERVER_PIDS" ]; then
        kill -9 $LANGUAGE_SERVER_PIDS 2>/dev/null
    fi
    echo -e "${GREEN}✅ Language servers killed${NC}"
else
    echo -e "${GREEN}✅ No language servers running${NC}"
fi
echo ""

# 2. Stop old unified_orchestrator instances
echo -e "${YELLOW}2. Stopping old unified_orchestrator instances...${NC}"
ORCHESTRATOR_PIDS=$(ps aux | grep "orchestrator/unified_orchestrator.py" | grep -v grep | awk '{print $2}')
if [ -n "$ORCHESTRATOR_PIDS" ]; then
    echo "Killing: $ORCHESTRATOR_PIDS"
    kill $ORCHESTRATOR_PIDS 2>/dev/null
    sleep 1
    kill -9 $ORCHESTRATOR_PIDS 2>/dev/null
    echo -e "${GREEN}✅ Unified Orchestrator killed${NC}"
else
    echo -e "${GREEN}✅ No Unified Orchestrator running${NC}"
fi
echo ""

# 3. Clean up dashboard instances (multiple vite servers)
echo -e "${YELLOW}3. Stopping duplicate dashboard instances...${NC}"
VITE_PIDS=$(ps aux | grep "node_modules/.bin/vite" | grep -v grep | awk '{print $2}')
if [ -n "$VITE_PIDS" ]; then
    echo "Killing Vite servers: $VITE_PIDS"
    kill $VITE_PIDS 2>/dev/null
    sleep 1
    kill -9 $VITE_PIDS 2>/dev/null
    echo -e "${GREEN}✅ Dashboard Vite servers killed${NC}"
else
    echo -e "${GREEN}✅ No duplicate Vite servers${NC}"
fi
echo ""

# 4. Clean up start-elf-system.sh wrappers
echo -e "${YELLOW}4. Stopping start-elf-system.sh wrappers...${NC}"
SHELL_PIDS=$(ps aux | grep "start-elf-system.sh" | grep -v grep | awk '{print $2}')
if [ -n "$SHELL_PIDS" ]; then
    echo "Killing: $SHELL_PIDS"
    kill $SHELL_PIDS 2>/dev/null
    echo -e "${GREEN}✅ Shell wrappers killed${NC}"
else
    echo -e "${GREEN}✅ No shell wrappers${NC}"
fi
echo ""

# 5. Check current RAM usage
echo -e "${YELLOW}5. Current RAM usage:${NC}"
free -h
echo ""

# 6. Show remaining ELF processes
echo -e "${YELLOW}6. Remaining ELF processes (should be minimal):${NC}"
ps aux | grep -E "(opencode|orchestrator|event_bridge|sentinel|python.*ELF)" | grep -v grep | \
    awk -F' ' '{printf "%5s %6s %5s %-60s %6s %6s\n", $2, $3"%", $4, $11, $9, $10}'
echo ""

# 7. Check OpenCode server
echo -e "${YELLOW}7. OpenCode server status:${NC}"
if pgrep -f "opencode --port 4096" > /dev/null; then
    OPCODE_PID=$(pgrep -f "opencode --port 4096")
    echo -e "${GREEN}✅ OpenCode server running (PID: $OPCODE_PID)${NC}"
else
    echo -e "${RED}❌ OpenCode server NOT running${NC}"
fi
echo ""

# 8. Check OpenCode health
echo -e "${YELLOW}8. OpenCode server health:${NC}"
curl -s http://localhost:4096/ -o /dev/null -w "%{http_code}" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ OpenCode server responding (HTTP 200)${NC}"
else
    echo -e "${RED}❌ OpenCode server NOT responding${NC}"
fi
echo ""

echo -e "${GREEN}=== Cleanup Complete ===${NC}"
echo ""
echo "Ready to restart services!"
echo ""
echo "To test the new architecture:"
echo "  cd /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator"
echo "  python event_bridge.py start"
echo "  # In another terminal:"
echo "  python unified_orchestrator.py start"
