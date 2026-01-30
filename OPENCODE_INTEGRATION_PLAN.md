# 🤖 Analyse de la Structure Actuelle des Agents ELF

## 📋 **État Actuel**

### **✅ Ce qui fonctionne déjà**
- **Serveur OpenCode**: Un processus tourne (PID 577920)
- **Répertoire agents/**: Existe avec plusieurs agents
- **Dashboard**: Fonctionnel (port 8888)
- **Configuration**: Fichier JSON créé avec les rôles définis

### **🔍 Ce qui doit être amélioré**

## 🎯 **Recommandations pour Intégration OpenCode Complète**

### **1. Structure des Agents pour OpenCode**

Les agents doivent suivre cette structure pour être reconnus par OpenCode :

```
agents/
├── ceo-agent.py              # Agent CEO avec prompt spécialisé
├── architect-agent.py         # Agent Architect avec prompt spécialisé  
├── researcher-agent.py        # Agent Chercheur avec prompt spécialisé
├── creative-agent.py         # Agent Créatif avec prompt spécialisé
├── skeptic-agent.py          # Agent Critique avec prompt spécialisé
└── learning-extractor.py     # Agent Extracteur d'apprentissage avec prompt spécialisé
```

### **2. Format des Agents OpenCode**

Chaque agent doit avoir :

```python
#!/usr/bin/env python3
"""
[ROLE] Agent pour système ELF
"""

import sys
import json
from pathlib import Path

# Import du client OpenCode
try:
    from opencode import Client
except ImportError:
    print("❌ Module opencode non trouvé")
    sys.exit(1)

class [ROLE]Agent:
    def __init__(self, name="[ROLE] Agent", model="big-pickle"):
        self.name = name
        self.model = model
        
        # Connexion au serveur OpenCode
        try:
            self.client = Client()
        except Exception as e:
            print(f"❌ Erreur connexion OpenCode: {e}")
            sys.exit(1)
    
    def get_specialized_prompt(self) -> str:
        """Retourne le prompt spécialisé pour ce rôle."""
        return """
Tu es un [ROLE] spécialisé dans le framework ELF.

[Mission et responsabilités détaillées]

[Instructions spécifiques OpenCode]
- Utilise les outils OpenCode disponibles
- Accède aux APIs du serveur si nécessaire
- Enregistre les décisions dans le système ELF
"""
    
    def process_task(self, task: str, context: str = ""):
        """Traite une tâche selon le rôle spécialisé."""
        try:
            # Créer une session
            session = self.client.create_session(f"ELF {self.name}")
            
            # Envoyer le message avec le prompt spécialisé
            full_prompt = self.get_specialized_prompt() + f"\n\nTÂCHE:\n{task}\n\nCONTEXTE:\n{context}"
            
            response = session.send_message(full_prompt)
            
            print(f"✅ Tâche traitée par {self.name}")
            return response
            
        except Exception as e:
            print(f"❌ Erreur traitement tâche: {e}")
            return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python [ROLE]-agent.py '<tâche>'")
        sys.exit(1)
    
    agent = [ROLE]Agent()
    task = " ".join(sys.argv[1:])
    
    print(f"🚀 {agent.name} - Traitement: {task}")
    result = agent.process_task(task)
    
    if result:
        print(f"✅ {agent.name} - Terminé avec succès")
    else:
        print(f"❌ {agent.name} - Échec")

if __name__ == "__main__":
    main()
```

### **3. Integration avec l'Orchestrateur ELF**

L'orchestrateur doit utiliser ces agents via l'API OpenCode :

```python
# Dans l'orchestrateur
from agents.ceo_agent import CEOAgent
from agents.architect_agent import ArchitectAgent
# ... etc.

class ELFOrchestrator:
    def __init__(self):
        self.agents = {
            'ceo': CEOAgent(),
            'architect': ArchitectAgent(),
            # ... autres agents
        }
    
    def coordinate_task(self, task_type: str, task_data: dict):
        """Coordonne une tâche en utilisant les agents appropriés."""
        
        # Sélection de l'agent basé sur le type
        agent_type = self.select_agent_type(task_type)
        agent = self.agents[agent_type]
        
        # Exécuter la tâche
        result = agent.process_task(task_data.get('task'), task_data.get('context', ''))
        
        return result
```

### **4. Workflow d'Intégration**

#### **Phase 1**: Agents OpenCode
1. Créer les fichiers agents dans le bon format
2. Tester chaque agent individuellement
3. S'assurer que les prompts spécialisés fonctionnent

#### **Phase 2**: Orchestrateur Amélioré
1. Modifier l'orchestrateur pour utiliser les agents OpenCode
2. Implémenter la sélection automatique des agents
3. Ajouter la coordination avec les tableaux noirs

#### **Phase 3**: Dashboard Intégré
1. Lancer le serveur OpenCode en terminal séparée
2. Lancer le dashboard qui communique avec le serveur
3. Ajouter l'interface pour contrôler les agents

## 🛠️ **Actions Immédiates Requises**

### **Priority 1: Agents OpenCode Fonctionnels**
- [ ] Créer `ceo-agent.py` avec prompt CEO
- [ ] Créer `architect-agent.py` avec prompt Architect  
- [ ] Créer `researcher-agent.py` avec prompt Chercheur
- [ ] Créer `creative-agent.py` avec prompt Créatif
- [ ] Créer `skeptic-agent.py` avec prompt Critique
- [ ] Créer `learning-extractor.py` avec prompt Extracteur

### **Priority 2: Test Individuel**
- [ ] Tester chaque agent avec OpenCode server
- [ ] Vérifier la communication avec le serveur
- [ ] Valider les prompts spécialisés

### **Priority 3: Intégration Orchestrateur** 
- [ ] Modifier `orchestrator/restored_orchestrator.py` pour utiliser OpenCode API
- [ ] Remplacer les appels `subprocess.run` par des appels API OpenCode
- [ ] Ajouter la gestion des sessions OpenCode

### **Priority 4: Terminal Séparée**
- [ ] Finaliser le script `launch-elf-system.sh` avec terminal séparée
- [ ] Ajouter gestion des processus OpenCode
- [ ] Intégrer avec la détection automatique

## 🎯 **Résultat Attendu**

Une fois terminé :
- ✅ **Serveur OpenCode**: Terminal séparée, contrôlable
- ✅ **Agents Spécialisés**: 6 agents avec leurs rôles définis  
- ✅ **Orchestrateur Intégré**: Utilise l'API OpenCode
- ✅ **Dashboard Unifié**: Interface web unique pour tout contrôler
- ✅ **Workflow Complet**: De la détection à la décision en passant par OpenCode

---

## 📝 **Prochaines Étapes**

1. **Créer les agents OpenCode** avec les templates ci-dessus
2. **Tester individuellement** chaque agent
3. **Modifier l'orchestrateur** pour intégration OpenCode
4. **Finaliser le launcher** avec terminal séparée fonctionnelle
5. **Documenter** l'architecture complète
6. **Tester** le workflow end-to-end

Cette approche garantira une **intégration complète et professionnelle** du système ELF avec OpenCode ! 🚀