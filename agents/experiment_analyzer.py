#!/usr/bin/env python3
"""
Experiment Analyzer Agent - Uses opencode/big-pickle to analyze and manage experiments

This agent:
- Analyzes active experiments for progress
- Recommends completion when objectives are met
- Detects patterns across experiments
- Generates insights and learnings
- Suggests optimizations

Uses OpenCode Server API (http://localhost:8888) or CLI fallback
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Import OpenCode client
try:
    from opencode_client import OpenCodeClient
except ImportError:
    # Fallback: define minimal client
    class OpenCodeClient:
        def __init__(self, model="opencode/big-pickle"):
            self.model = model
        def call(self, prompt, timeout=120):
            result = subprocess.run(
                ["opencode", "--model", self.model, "--prompt", prompt],
                capture_output=True, text=True, timeout=timeout
            )
            return result.stdout.strip() if result.returncode == 0 else None

def get_elf_base() -> Path:
    """Get ELF base path."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from query.config_loader import get_base_path
        return get_base_path()
    except:
        return Path(__file__).parent.parent

class ExperimentAnalyzer:
    """AI-powered experiment analysis using opencode/big-pickle."""
    
    def __init__(self, model: str = "opencode/big-pickle"):
        self.model = model
        self.client = OpenCodeClient(model=model)
        self.elf_base = get_elf_base()
        self.db_path = self.elf_base / "memory" / "index.db"
        self.manager_path = Path(__file__).parent.parent / "scripts" / "lib" / "experiment_manager.py"
    
    def call_opencode(self, prompt: str) -> Optional[str]:
        """Call opencode using server API or CLI."""
        return self.client.call(prompt, timeout=120)
    
    def get_experiment_data(self, exp_id: int) -> Optional[Dict[str, Any]]:
        """Get experiment data from database."""
        import subprocess
        
        try:
            result = subprocess.run(
                ["python3", str(self.manager_path), "get"],
                input=json.dumps({"id": exp_id}),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            return None
        except Exception as e:
            print(f"Error getting experiment: {e}", file=sys.stderr)
            return None
    
    def analyze_experiment(self, exp_id: int) -> Dict[str, Any]:
        """Analyze a specific experiment using AI."""
        # Get experiment details
        try:
            import sqlite3
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return {"error": "Experiment not found"}
            
            exp = dict(row)
        except Exception as e:
            return {"error": str(e)}
        
        # Build analysis prompt
        days_running = (datetime.now() - datetime.fromisoformat(exp['created_at'])).days
        
        prompt = f"""Analyze this experiment and provide insights:

## Experiment Details
- **Name**: {exp['name']}
- **Status**: {exp['status']}
- **Days Running**: {days_running}
- **Cycles Completed**: {exp.get('cycles_run', 0)}
- **Hypothesis**: {exp.get('hypothesis', 'N/A')}
- **Success Criteria**: {exp.get('success_criteria', 'Not defined')}
- **Failure Criteria**: {exp.get('failure_criteria', 'Not defined')}

## Your Analysis
1. **Progress Assessment**: Is this experiment progressing well?
2. **Completion Readiness**: Should this experiment be completed? If yes, what's the result?
3. **Risk Factors**: Are there concerning patterns or delays?
4. **Optimization**: How could this experiment be improved?
5. **Learning Extraction**: What has been learned so far?
6. **Recommendation**: Should we complete, pause, modify, or continue?

Provide a structured analysis in JSON format:
{{
    "assessment": "on_track|at_risk|stalled|ready_to_complete",
    "completion_ready": true|false,
    "recommended_result": "success|failure|inconclusive|needs_more_data",
    "confidence": 0.0-1.0,
    "key_findings": ["finding1", "finding2", ...],
    "recommendations": ["recommendation1", ...],
    "next_steps": ["step1", ...],
    "learnings": ["learning1", ...]
}}"""
        
        response = self.call_opencode(prompt)
        
        if not response:
            return {"error": "Failed to get AI analysis"}
        
        # Parse response
        try:
            # Try to extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                analysis = json.loads(response[start:end])
            else:
                analysis = {"raw_response": response}
        except json.JSONDecodeError:
            analysis = {"raw_response": response}
        
        analysis["experiment_id"] = exp_id
        analysis["experiment_name"] = exp['name']
        analysis["timestamp"] = datetime.now().isoformat()
        
        return analysis
    
    def analyze_all_active(self) -> Dict[str, Any]:
        """Analyze all active experiments."""
        try:
            import sqlite3
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM experiments WHERE status = 'active' ORDER BY created_at DESC")
            ids = [row['id'] for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            return {"error": str(e), "analyses": []}
        
        analyses = []
        for exp_id in ids:
            analysis = self.analyze_experiment(exp_id)
            analyses.append(analysis)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_analyzed": len(ids),
            "analyses": analyses,
            "summary": self._generate_summary(analyses)
        }
    
    def _generate_summary(self, analyses: List[Dict]) -> Dict[str, Any]:
        """Generate summary across all analyses."""
        summary = {
            "total": len(analyses),
            "ready_to_complete": 0,
            "at_risk": 0,
            "on_track": 0,
            "stalled": 0,
            "key_recommendations": []
        }
        
        recommendations = {}
        
        for analysis in analyses:
            if "assessment" in analysis:
                assessment = analysis["assessment"]
                if assessment == "ready_to_complete":
                    summary["ready_to_complete"] += 1
                elif assessment == "at_risk":
                    summary["at_risk"] += 1
                elif assessment == "on_track":
                    summary["on_track"] += 1
                elif assessment == "stalled":
                    summary["stalled"] += 1
            
            # Collect recommendations
            if "recommendations" in analysis:
                for rec in analysis.get("recommendations", []):
                    recommendations[rec] = recommendations.get(rec, 0) + 1
        
        # Top recommendations
        summary["key_recommendations"] = sorted(
            recommendations.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return summary
    
    def generate_report(self) -> str:
        """Generate a comprehensive analysis report."""
        results = self.analyze_all_active()
        
        if "error" in results:
            return f"Error: {results['error']}"
        
        # Format report
        report = f"""
═══════════════════════════════════════════════════════════════════════════════
                    EXPERIMENT ANALYSIS REPORT
                    {results['timestamp']}
═══════════════════════════════════════════════════════════════════════════════

📊 OVERVIEW
───────────────────────────────────────────────────────────────────────────────
Total Active Experiments: {results['summary']['total']}
  • On Track: {results['summary']['on_track']}
  • At Risk: {results['summary']['at_risk']}
  • Stalled: {results['summary']['stalled']}
  • Ready to Complete: {results['summary']['ready_to_complete']}

🎯 KEY RECOMMENDATIONS
───────────────────────────────────────────────────────────────────────────────
"""
        for rec, count in results['summary']['key_recommendations']:
            report += f"  • {rec} ({count} experiments)\n"
        
        report += "\n📋 DETAILED ANALYSES\n"
        report += "───────────────────────────────────────────────────────────────────────────────\n"
        
        for analysis in results['analyses']:
            if "error" not in analysis:
                report += f"\nExperiment #{analysis['experiment_id']}: {analysis['experiment_name']}\n"
                report += f"Assessment: {analysis.get('assessment', 'unknown').upper()}\n"
                
                if analysis.get('completion_ready'):
                    report += f"⚠️  READY TO COMPLETE - Result: {analysis.get('recommended_result')}\n"
                
                if "key_findings" in analysis:
                    report += "Key Findings:\n"
                    for finding in analysis.get('key_findings', [])[:3]:
                        report += f"  • {finding}\n"
                
                if "learnings" in analysis:
                    report += "Learnings:\n"
                    for learning in analysis.get('learnings', [])[:2]:
                        report += f"  • {learning}\n"
        
        report += "\n" + "═" * 79 + "\n"
        
        return report

def main():
    """CLI interface."""
    if len(sys.argv) < 2:
        print("Usage: experiment_analyzer.py <command> [args]", file=sys.stderr)
        print("Commands:", file=sys.stderr)
        print("  analyze <id>  - Analyze specific experiment", file=sys.stderr)
        print("  all           - Analyze all active experiments", file=sys.stderr)
        print("  report        - Generate comprehensive report", file=sys.stderr)
        sys.exit(1)
    
    analyzer = ExperimentAnalyzer()
    command = sys.argv[1]
    
    if command == "analyze" and len(sys.argv) > 2:
        exp_id = int(sys.argv[2])
        result = analyzer.analyze_experiment(exp_id)
        print(json.dumps(result, indent=2))
    
    elif command == "all":
        result = analyzer.analyze_all_active()
        print(json.dumps(result, indent=2, default=str))
    
    elif command == "report":
        report = analyzer.generate_report()
        print(report)
    
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
