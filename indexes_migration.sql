-- Indexes manquants pour optimiser les requêtes SQL critiques
-- Généré automatiquement pour corriger les performances

-- Indexes pour la table heuristics
CREATE INDEX IF NOT EXISTS idx_heuristics_domain ON heuristics(domain);
CREATE INDEX IF NOT EXISTS idx_heuristics_confidence ON heuristics(confidence);
CREATE INDEX IF NOT EXISTS idx_heuristics_is_golden ON heuristics(is_golden);
CREATE INDEX IF NOT EXISTS idx_heuristics_updated_at ON heuristics(updated_at);
CREATE INDEX IF NOT EXISTS idx_heuristics_created_at ON heuristics(created_at);

-- Indexes pour la table learnings
CREATE INDEX IF NOT EXISTS idx_learnings_type ON learnings(type);
CREATE INDEX IF NOT EXISTS idx_learnings_domain ON learnings(domain);
CREATE INDEX IF NOT EXISTS idx_learnings_created_at ON learnings(created_at);

-- Indexes pour la table decisions
CREATE INDEX IF NOT EXISTS idx_decisions_status ON decisions(status);
CREATE INDEX IF NOT EXISTS idx_decisions_domain ON decisions(domain);
CREATE INDEX IF NOT EXISTS idx_decisions_created_at ON decisions(created_at);

-- Indexes pour la table assumptions
CREATE INDEX IF NOT EXISTS idx_assumptions_status ON assumptions(status);
CREATE INDEX IF NOT EXISTS idx_assumptions_domain ON assumptions(domain);
CREATE INDEX IF NOT EXISTS idx_assumptions_severity ON assumptions(severity);
CREATE INDEX IF NOT EXISTS idx_assumptions_created_at ON assumptions(created_at);

-- Indexes pour la table invariants
CREATE INDEX IF NOT EXISTS idx_invariants_status ON invariants(status);
CREATE INDEX IF NOT EXISTS idx_invariants_domain ON invariants(domain);
CREATE INDEX IF NOT EXISTS idx_invariants_severity ON invariants(severity);
CREATE INDEX IF NOT EXISTS idx_invariants_created_at ON invariants(created_at);

-- Indexes pour la table spike_reports
CREATE INDEX IF NOT EXISTS idx_spike_reports_domain ON spike_reports(domain);
CREATE INDEX IF NOT EXISTS idx_spike_reports_created_at ON spike_reports(created_at);

-- Indexes pour la table game_state
CREATE INDEX IF NOT EXISTS idx_game_state_user_id ON game_state(user_id);
CREATE INDEX IF NOT EXISTS idx_game_state_last_activity ON game_state(last_activity);

-- Indexes pour la table workflow_runs
CREATE INDEX IF NOT EXISTS idx_workflow_runs_workflow_name ON workflow_runs(workflow_name);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_status ON workflow_runs(status);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_phase ON workflow_runs(phase);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_created_at ON workflow_runs(created_at);

-- Indexes pour la table node_executions
CREATE INDEX IF NOT EXISTS idx_node_executions_run_id ON node_executions(run_id);
CREATE INDEX IF NOT EXISTS idx_node_executions_node_id ON node_executions(node_id);
CREATE INDEX IF NOT EXISTS idx_node_executions_status ON node_executions(status);
CREATE INDEX IF NOT EXISTS idx_node_executions_completed_at ON node_executions(completed_at);

-- Indexes pour la table trails
CREATE INDEX IF NOT EXISTS idx_trails_location ON trails(location);
CREATE INDEX IF NOT EXISTS idx_trails_agent_id ON trails(agent_id);
CREATE INDEX IF NOT EXISTS idx_trails_created_at ON trails(created_at);

-- Indexes pour la table conductor_decisions
CREATE INDEX IF NOT EXISTS idx_conductor_decisions_run_id ON conductor_decisions(run_id);
CREATE INDEX IF NOT EXISTS idx_conductor_decisions_decision_type ON conductor_decisions(decision_type);
CREATE INDEX IF NOT EXISTS idx_conductor_decisions_timestamp ON conductor_decisions(timestamp);

-- Indexes pour la table workflow_edges
CREATE INDEX IF NOT EXISTS idx_workflow_edges_from_node ON workflow_edges(from_node);
CREATE INDEX IF NOT EXISTS idx_workflow_edges_to_node ON workflow_edges(to_node);

-- Indexes pour la table system_health
CREATE INDEX IF NOT EXISTS idx_system_health_timestamp ON system_health(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_health_status ON system_health(status);

-- Indexes pour la table users
CREATE INDEX IF NOT EXISTS idx_users_github_id ON users(github_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Indexes composites pour requêtes complexes
-- Indexes composites pour heuristics
CREATE INDEX IF NOT EXISTS idx_heuristics_domain_confidence_desc ON heuristics(domain,confidence DESC);
CREATE INDEX IF NOT EXISTS idx_heuristics_is_golden_confidence_desc ON heuristics(is_golden,confidence DESC);
CREATE INDEX IF NOT EXISTS idx_heuristics_domain_updated_at_desc ON heuristics(domain,updated_at DESC);

-- Indexes composites pour learnings
CREATE INDEX IF NOT EXISTS idx_learnings_domain_created_at_desc ON learnings(domain,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_learnings_type_created_at_desc ON learnings(type,created_at DESC);

-- Indexes composites pour decisions
CREATE INDEX IF NOT EXISTS idx_decisions_status_created_at_desc ON decisions(status,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_domain_status_created_at ON decisions(domain,status,created_at);

-- Indexes composites pour assumptions
CREATE INDEX IF NOT EXISTS idx_assumptions_domain_status_created_at ON assumptions(domain,status,created_at);
CREATE INDEX IF NOT EXISTS idx_assumptions_severity_status ON assumptions(severity,status);

-- Indexes composites pour invariants
CREATE INDEX IF NOT EXISTS idx_invariants_domain_status_severity ON invariants(domain,status,severity);
CREATE INDEX IF NOT EXISTS idx_invariants_severity_status_created_at ON invariants(severity,status,created_at);

-- Indexes composites pour workflow_runs
CREATE INDEX IF NOT EXISTS idx_workflow_runs_workflow_name_created_at_desc ON workflow_runs(workflow_name,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_status_created_at_desc ON workflow_runs(status,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_phase_status ON workflow_runs(phase,status);

-- Indexes composites pour node_executions
CREATE INDEX IF NOT EXISTS idx_node_executions_run_id_completed_at_desc ON node_executions(run_id,completed_at DESC);
CREATE INDEX IF NOT EXISTS idx_node_executions_node_id_status ON node_executions(node_id,status);

-- Indexes composites pour trails
CREATE INDEX IF NOT EXISTS idx_trails_agent_id_created_at_desc ON trails(agent_id,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trails_location_created_at_desc ON trails(location,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trails_location_agent_id ON trails(location,agent_id);
