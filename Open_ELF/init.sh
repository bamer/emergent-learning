#!/bin/bash
# Open_ELF - Script d'initialisation rapide
# Usage: source init.sh

export ELF_ROOT="/home/bamer/.opencode/emergent-learning/Open_ELF"
export ELF_SCRIPTS="$ELF_ROOT/scripts"
export ELF_QUERY="$ELF_ROOT/query"
export ELF_MEMORY="$ELF_ROOT/memory"

# Alias pour les commandes fréquentes
alias elf-query="python3 $ELF_QUERY/query.py"
alias elf-record-failure="$ELF_SCRIPTS/record-failure.sh"
alias elf-record-heuristic="python3 $ELF_SCRIPTS/record-heuristic.py"
alias elf-self-test="$ELF_SCRIPTS/self-test.sh"

echo "✅ Open_ELF initialisé"
echo "📍 ELF_ROOT: $ELF_ROOT"
echo ""
echo "Commandes disponibles:"
echo "  elf-query --context"
echo "  elf-record-failure 'titre' 'domaine'"
echo "  elf-self-test"
