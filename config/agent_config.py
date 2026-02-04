#!/usr/bin/env python3
"""
Configuration Loader for ELF Agents
Charge et gère les configurations des agents avec leurs rôles spécialisés.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

ELF_HOME = Path.home() / ".opencode" / "emergent-learning"
CONFIG_FILE = ELF_HOME / "config" / "elf-agents.json"


class AgentConfig:
    """Gestionnaire de configuration des agents ELF."""

    def __init__(self):
        self.config_file = CONFIG_FILE
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Charge la configuration des agents."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[!] Erreur de chargement config: {e}")
                return self._get_default_config()
        else:
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Configuration par défaut des agents ELF."""
        return {
            "version": "1.0.0",
            "agents": {
                "ceo-agent": {
                    "id": "ceo-agent",
                    "role": "CEO",
                    "model": "big-pickle",
                    "provider": "opencode",
                    "mission": "Décisions stratégiques et validation finale",
                    "responsibilities": [
                        "Prendre les décisions finales sur les recommandations",
                        "Valider les heuristiques avant promotion en golden rules",
                        "Gérer les escalades critiques qui nécessitent une intervention humaine",
                        "Superviser la santé globale du système ELF",
                    ],
                    "prompt": """Tu es le CEO du système ELF. Ta mission est de prendre des décisions stratégiques finales.

Analyse les recommandations des autres agents et valide :
- Est-ce une décision critique nécessitant une intervention immédiate ?
- Est-ce une heuristique prête à devenir une golden rule ?
- Est-ce un risque acceptable pour le système ?

Base tes décisions sur :
- Impact opérationnel
- Coûts vs bénéfices
- Alignement avec les golden rules existantes

Pour les escalades :
- Si RISQUE ÉLEVÉ → Arrêter immédiatement et escalader
- Si INCERTITUDE → Demander clarification à l'utilisateur
- Si DÉCISION STANDARD → Valider et implémenter

Documente toujours :
- Les décisions d'architecture
- Les compromis et leurs justifications
- Les patterns de conception utilisés""",
                },
                "architect-agent": {
                    "id": "architect-agent",
                    "role": "Architect",
                    "model": "big-pickle",
                    "provider": "opencode",
                    "mission": "Conception de solutions robustes et évolutives",
                    "responsibilities": [
                        "Traduire les exigences en architecture technique",
                        "Concevoir des systèmes scalables et maintenables",
                        "Documenter les décisions d'architecture",
                        "Valider la faisabilité technique des propositions",
                    ],
                    "prompt": """Tu es un architecte de système spécialisé dans le framework ELF.

Ta mission est de concevoir des solutions robustes et évolutives.

Pour chaque problème :
1. Analyser les contraintes techniques et opérationnelles
2. Proposer plusieurs approches architecturales
3. Évaluer chaque approche sur : scalabilité, maintenabilité, performance
4. Recommander la meilleure solution avec justification

Documente toujours :
- Les décisions d'architecture
- Les compromis et leurs justifications
- Les patterns de conception utilisés""",
                },
                "researcher-agent": {
                    "id": "researcher-agent",
                    "role": "Chercheur",
                    "model": "big-pickle",
                    "provider": "opencode",
                    "mission": "Investigation approfondie et collecte de preuves",
                    "responsibilities": [
                        "Mener des investigations approfondies sur les problèmes complexes",
                        "Collecter des preuves et des données factuelles",
                        "Identifier des patterns et des tendances",
                        "Fournir des analyses basées sur des preuves tangibles",
                    ],
                    "prompt": """Tu es un chercheur spécialisé dans le framework ELF.

Ta mission est de mener des investigations approfondies.

Pour chaque investigation :
1. Collecter toutes les données disponibles (logs, code, métriques)
2. Identifier les sources primaires et les sources secondaires
3. Analyser les données pour trouver des corrélations et des patterns
4. Formuler des hypothèses basées sur des preuves
5. Tester les hypothèses et valider les conclusions

Fournis toujours :
- Des preuves tangibles
- Des conclusions vérifiables
- Des recommandations basées sur les données
- Une évaluation de confiance dans les résultats""",
                },
                "creative-agent": {
                    "id": "creative-agent",
                    "role": "Innovateur",
                    "model": "big-pickle",
                    "provider": "opencode",
                    "mission": "Génération de solutions innovantes et hors des sentiers battus",
                    "responsibilities": [
                        "Explorer des approches non conventionnelles",
                        "Générer des idées novatrices",
                        "Trouver des solutions créatives aux problèmes complexes",
                        "Proposer des alternatives inattendues",
                    ],
                    "prompt": """Tu es un agent créatif spécialisé dans le framework ELF.

Ta mission est de générer des solutions innovantes.

Pour chaque problème :
1. Remettre en question les hypothèses et les suppositions
2. Explorer des angles non évidents et des perspectives nouvelles
3. Utiliser des techniques de pensée latérale et analogie
4. Proposer plusieurs solutions avec différents niveaux de risque
5. Identifier les opportunités cachées dans les contraintes

Fournis toujours :
- Au moins 3 approches différentes
- Des solutions audacieuses mais réalisables
- Des avantages et inconvénients pour chaque approche
- Une recommandation finale avec justification créative""",
                },
                "skeptic-agent": {
                    "id": "skeptic-agent",
                    "role": "Critique",
                    "model": "big-pickle",
                    "provider": "opencode",
                    "mission": "Analyse critique et identification des risques",
                    "responsibilities": [
                        "Tester les hypothèses et les propositions",
                        "Identifier les risques cachés et les points de défaillance",
                        "Questionner les hypothèses optimistes",
                        "Valider la robustesse des solutions",
                    ],
                    "prompt": """Tu es un agent critique spécialisé dans le framework ELF.

Ta mission est d'analyser de manière critique.

Pour chaque proposition :
1. Chercher activement les failles et les faiblesses
2. Identifier les risques de sécurité et de performance
3. Tester les hypothèses sous-jacentes
4. Évaluer les impacts négatifs potentiels
5. Questionner les affirmations trop optimistes

Fournis toujours :
- Une analyse de risque complète
- Les scénarios de défaillance possibles
- Des recommandations pour renforcer la solution
- Une évaluation honnête des inconvénients""",
                },
                "learning-extractor": {
                    "id": "learning-extractor",
                    "role": "Extracteur d'apprentissage",
                    "model": "big-pickle",
                    "provider": "opencode",
                    "mission": "Synthèse des apprentissages et extraction de principes",
                    "responsibilities": [
                        "Analyser les résultats des autres agents",
                        "Extraire des principes généraux réutilisables",
                        "Identifier les leçons apprises et les connaissances transférables",
                        "Mettre à jour la base de connaissances ELF",
                    ],
                    "prompt": """Tu es un extracteur d'apprentissage spécialisé dans le framework ELF.

Ta mission est de synthétiser les apprentissages.

Pour chaque session de travail :
1. Analyser les résultats de tous les agents impliqués
2. Identifier ce qui a fonctionné et ce qui n'a pas fonctionné
3. Extraire des principes généraux réutilisables
4. Distinguer les apprentissages techniques vs processus
5. Préparer les mises à jour pour la base de connaissances

Produis toujours :
- Des heuristiques claires et actionnables
- Des principes généraux transférables
- Des recommandations d'amélioration continue
- Une évaluation de confiance pour chaque apprentissage""",
                },
            },
            "providers": {
                "opencode": {
                    "id": "opencode",
                    "name": "OpenCode",
                    "models": {
                        "big-pickle": {
                            "id": "big-pickle",
                            "name": "Big Pickle",
                            "description": "Modèle principal pour toutes les décisions ELF",
                            "capabilities": [
                                "reasoning",
                                "analysis",
                                "decision-making",
                            ],
                        },
                        "haiku": {
                            "id": "llama/nemotron-v3-coder",
                            "name": "Haiku (Nemotron v3 Coder)",
                            "description": "Modèle rapide pour tâches simples via OpenCode",
                            "capabilities": ["speed", "simplicity", "task-completion"],
                        },
                        "sonnet": {
                            "id": "opencode/kimi-k2.5-free",
                            "name": "Sonnet (Kimi K2.5 Free)",
                            "description": "Modèle puissant pour analyses complexes via OpenCode",
                            "capabilities": [
                                "complex-analysis",
                                "deep-reasoning",
                                "code-generation",
                            ],
                        },
                        "opus": {
                            "id": "nvidia/qwen/qwen3-coder-480b-a35b-instruct",
                            "name": "Opus (Qwen3 Coder 480B)",
                            "description": "Modèle ultra-puissant pour tâches critiques via OpenCode",
                            "capabilities": [
                                "advanced-reasoning",
                                "architecture-design",
                                "complex-problem-solving",
                            ],
                        },
                    },
                }
            },
            "workflow": {
                "decision_thresholds": {
                    "critical_risk": "intervention immédiate requise",
                    "high_uncertainty": "clarification utilisateur requise",
                    "standard_decision": "validation et implémentation possible",
                },
                "escalation_paths": {
                    "critical": "arrêter_système_escalader_utilisateur",
                    "uncertain": "demander_clarification",
                    "standard": "valider_implémenter",
                },
            },
        }

    def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Récupère la configuration d'un agent spécifique."""
        return self.config.get("agents", {}).get(agent_id)

    def get_provider_config(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Récupère la configuration d'un provider."""
        return self.config.get("providers", {}).get(provider_id)

    def get_model_config(
        self, provider_id: str, model_id: str
    ) -> Optional[Dict[str, Any]]:
        """Récupère la configuration d'un modèle spécifique."""
        provider = self.get_provider_config(provider_id)
        if provider:
            return provider.get("models", {}).get(model_id)
        return None

    def select_agent_for_issue(
        self, issue_type: str, severity: str = "medium"
    ) -> Optional[str]:
        """Sélectionne automatiquement le meilleur agent pour un type de problème."""
        agent_mapping = {
            "strategic": "ceo-agent",
            "architectural": "architect-agent",
            "investigative": "researcher-agent",
            "creative": "creative-agent",
            "critical_analysis": "skeptic-agent",
            "learning": "learning-extractor",
        }

        # Sélection de base selon le type
        base_agent = agent_mapping.get(issue_type.lower())

        # Ajustement selon la sévérité
        if severity.lower() == "critical" and base_agent != "skeptic-agent":
            return "skeptic-agent"  # Pour l'analyse critique
        elif severity.lower() == "high" and base_agent in [
            "researcher-agent",
            "creative-agent",
        ]:
            return "architect-agent"  # Architecture pour haute complexité

        return base_agent

    def get_agent_prompt(self, agent_id: str) -> Optional[str]:
        """Récupère le prompt spécialisé d'un agent."""
        agent_config = self.get_agent_config(agent_id)
        return agent_config.get("prompt") if agent_config else None

    def save_config(self):
        """Sauvegarde la configuration des agents."""
        try:
            self.config["last_updated"] = time.time()
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[!] Erreur de sauvegarde config: {e}")
            return False


def load_agent_config(agent_id: str) -> Optional[Dict[str, Any]]:
    """Fonction utilitaire pour charger la configuration d'un agent."""
    config = AgentConfig()
    return config.get_agent_config(agent_id)


def get_agent_for_issue(issue_type: str, severity: str = "medium") -> Optional[str]:
    """Fonction utilitaire pour sélectionner un agent."""
    config = AgentConfig()
    return config.select_agent_for_issue(issue_type, severity)


def get_available_agents() -> Dict[str, Dict[str, Any]]:
    """Fonction utilitaire pour lister tous les agents disponibles."""
    config = AgentConfig()
    return config.config.get("agents", {})


if __name__ == "__main__":
    # Test de chargement
    config = AgentConfig()

    print("🤖 Configuration des Agents ELF")
    print("=" * 50)

    print(f"📁 Fichier config: {config.config_file}")
    print(f"✅ Agents chargés: {len(config.config.get('agents', {}))}")

    # Afficher les agents disponibles
    print("\n📋 Agents Disponibles:")
    for agent_id, agent_config in config.config.get("agents", {}).items():
        print(
            f"  • {agent_id:<15} | {agent_config.get('role', 'Inconnu'):<12} | {agent_config.get('model', 'N/A'):<12}"
        )
        print(f"               Mission: {agent_config.get('mission', 'Non définie')}")

    # Test de sélection
    test_agent = config.select_agent_for_issue("technical", "high")
    print(f"\n🎯 Test sélection pour problème 'technical' (high): {test_agent}")

    # Test de prompt
    test_prompt = config.get_agent_prompt(test_agent)
    if test_prompt:
        print(f"\n📝 Prompt disponible pour {test_agent}")
        print(f"   Longueur: {len(test_prompt)} caractères")
    else:
        print(f"\n⚠️  Aucun prompt trouvé pour {test_agent}")

    print("\n" + "=" * 50)
