📊 RAPPORT D'OPTIMISATION - INDEXES AJOUTÉS
==================================================

🔸 Indexes simples ajoutés: 45
  - heuristics: 5 indexes (domain, confidence, is_golden, updated_at, created_at)
  - learnings: 3 indexes (type, domain, created_at)
  - decisions: 3 indexes (status, domain, created_at)
  - assumptions: 4 indexes (status, domain, severity, created_at)
  - invariants: 4 indexes (status, domain, severity, created_at)
  - spike_reports: 2 indexes (domain, created_at)
  - game_state: 2 indexes (user_id, last_activity)
  - workflow_runs: 4 indexes (workflow_name, status, phase, created_at)
  - node_executions: 4 indexes (run_id, node_id, status, completed_at)
  - trails: 3 indexes (location, agent_id, created_at)
  - conductor_decisions: 3 indexes (run_id, decision_type, timestamp)
  - workflow_edges: 2 indexes (from_node, to_node)
  - system_health: 2 indexes (timestamp, status)
  - users: 4 indexes (github_id, username, email, created_at)

🔸 Indexes composites ajoutés: 19
  - heuristics: 3 indexes
    • (domain,confidence DESC)
    • (is_golden,confidence DESC)
    • (domain,updated_at DESC)
  - learnings: 2 indexes
    • (domain,created_at DESC)
    • (type,created_at DESC)
  - decisions: 2 indexes
    • (status,created_at DESC)
    • (domain,status,created_at)
  - assumptions: 2 indexes
    • (domain,status,created_at)
    • (severity,status)
  - invariants: 2 indexes
    • (domain,status,severity)
    • (severity,status,created_at)
  - workflow_runs: 3 indexes
    • (workflow_name,created_at DESC)
    • (status,created_at DESC)
    • (phase,status)
  - node_executions: 2 indexes
    • (run_id,completed_at DESC)
    • (node_id,status)
  - trails: 3 indexes
    • (agent_id,created_at DESC)
    • (location,created_at DESC)
    • (location,agent_id)

🚀 BENEFICES ATTENDUS:
  • Réduction de 60-80% du temps de requête sur les colonnes indexées
  • Amélioration significative des requêtes avec ORDER BY
  • Optimisation des jointures entre tables
  • Réduction de la charge CPU pour les requêtes complexes

📈 MONITORING RECOMMANDÉ:
  • Surveiller l'utilisation des nouveaux indexes avec EXPLAIN QUERY PLAN
  • Vérifier l'espace disque utilisé par les indexes
  • Monitorer les performances avant/après déploiement