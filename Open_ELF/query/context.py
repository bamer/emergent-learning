# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO
# /home/bamer/.opencode/emergent-learning/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
Context builder mixin - builds agent context from the knowledge base (async).
"""

import sys
from datetime import datetime, timezone, timedelta
from functools import reduce
from pathlib import Path
from typing import Dict, List, Any, Optional

from peewee import fn

# Unified ELF logging (required for all ELF modules)
try:
    from Open_ELF.utils.elf_logging import get_logger, log_debug

    _LOGGER = get_logger("context")
except ImportError:
    import logging

    _LOGGER = logging.getLogger("context")

try:
    from query.models import Heuristic, Learning, get_manager
    from query.utils import AsyncTimeoutHandler
    from query.exceptions import (
        TimeoutError,
        ValidationError,
        DatabaseError,
        QuerySystemError,
    )
    from query.config_loader import (
        get_config,
        load_custom_golden_rules,
        get_always_load_categories,
    )
except ImportError:
    from models import Heuristic, Learning, get_manager
    from utils import AsyncTimeoutHandler
    from exceptions import (
        TimeoutError,
        ValidationError,
        DatabaseError,
        QuerySystemError,
    )
    from config_loader import (
        get_config,
        load_custom_golden_rules,
        get_always_load_categories,
    )

# MetaObserver is optional
META_OBSERVER_AVAILABLE = False
try:
    from meta_observer import MetaObserver

    META_OBSERVER_AVAILABLE = True
except ImportError:
    pass

# Plan-postmortem is optional
PLAN_POSTMORTEM_AVAILABLE = False
try:
    try:
        from query.plan_postmortem import (
            get_active_plans,
            get_recent_postmortems,
            format_plans_for_context,
            format_postmortems_for_context,
        )
    except ImportError:
        from plan_postmortem import (
            get_active_plans,
            get_recent_postmortems,
            format_plans_for_context,
            format_postmortems_for_context,
        )
    PLAN_POSTMORTEM_AVAILABLE = True
except ImportError:
    pass

# Project context support (optional)
PROJECT_CONTEXT_AVAILABLE = False
try:
    try:
        from query.project import (
            detect_project_context,
            ProjectContext,
            format_project_status,
        )
    except ImportError:
        from project import (
            detect_project_context,
            ProjectContext,
            format_project_status,
        )
    PROJECT_CONTEXT_AVAILABLE = True
except ImportError:
    # Define stub classes/functions to avoid "possibly unbound" errors
    def detect_project_context(path):
        """Stub when project context is unavailable."""
        return None

    class ProjectContext:
        """Stub when project context is unavailable."""

        def has_project_context(self):
            return False

        @property
        def project_name(self):
            return ""

        @property
        def elf_root(self):
            return ""

        @property
        def domains(self):
            return []

        @property
        def inheritance_chain(self):
            return []

        def get_context_md_content(self):
            return None

    def format_project_status(ctx):
        """Stub when project context is unavailable."""
        return ""


# Multi-model detection (optional)
MODEL_DETECTION_AVAILABLE = False
try:
    try:
        from query.model_detection import (
            detect_installed_models,
            format_models_for_context,
        )
    except ImportError:
        from model_detection import detect_installed_models, format_models_for_context
    MODEL_DETECTION_AVAILABLE = True
except ImportError:
    pass

# Semantic search (optional)
SEMANTIC_SEARCH_AVAILABLE = False
try:
    try:
        from query.semantic_search import SemanticSearcher
    except ImportError:
        from semantic_search import SemanticSearcher
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    # Define stub class to avoid "possibly unbound" errors
    class SemanticSearcher:
        """Stub when semantic search is unavailable."""

        @classmethod
        async def create(cls, base_path: str):
            return cls()

        async def find_relevant_heuristics(self, **kwargs):
            return []

        async def cleanup(self):
            pass


# aiosqlite (optional - for project-specific database access)
AIOSQLITE_AVAILABLE = False
try:
    import aiosqlite

    AIOSQLITE_AVAILABLE = True
except ImportError:
    aiosqlite = None  # type: ignore[assignment]


def get_depth_limits(depth: str) -> dict:
    """Get query limits based on depth level."""
    if depth == "deep":
        return {
            "heuristics": 25,
            "learnings": 25,
            "decisions": 10,
            "invariants": 10,
            "assumptions": 10,
            "spikes": 10,
            "recent_context": 10,
            "summary_truncate": 200,  # More detail in summaries
        }
    elif depth == "minimal":
        return {
            "heuristics": 0,
            "learnings": 0,
            "decisions": 0,
            "invariants": 0,
            "assumptions": 0,
            "spikes": 0,
            "recent_context": 0,
            "summary_truncate": 50,
        }
    else:  # standard
        return {
            "heuristics": 10,
            "learnings": 10,
            "decisions": 5,
            "invariants": 5,
            "assumptions": 5,
            "spikes": 5,
            "recent_context": 5,
            "summary_truncate": 100,
        }


class ContextBuilderMixin:
    """Mixin for building agent context from the knowledge base (async)."""

    db_path: str  # Inherited from QueryEngine/QueryContext
    base_path: str  # Inherited from QueryEngine/QueryContext
    current_location: Optional[str]  # Inherited from QueryEngine/QueryContext

    # Default constants (can be overridden by inheriting class)
    DEFAULT_TIMEOUT: int = 30
    MAX_TOKENS: int = 50000
    MAX_LIMIT: int = 100

    # ========== VALIDATION METHODS ==========

    def _validate_query(self, query: str) -> str:
        """Validate query string."""
        if not query or not query.strip():
            from exceptions import ValidationError

            raise ValidationError("Query cannot be empty")
        return query.strip()

    def _validate_domain(self, domain: str) -> str:
        """Validate domain string."""
        if not domain or not domain.strip():
            from exceptions import ValidationError

            raise ValidationError("Domain cannot be empty")
        return domain.strip().lower()

    def _validate_tags(self, tags: list) -> list:
        """Validate tags list."""
        if not tags:
            return []
        validated = []
        for tag in tags:
            if isinstance(tag, str) and tag.strip():
                validated.append(tag.strip())
        return validated

    def _validate_limit(self, limit: int) -> int:
        """Validate and constrain limit value."""
        if not isinstance(limit, int) or limit < 1:
            return 10
        return min(limit, self.MAX_LIMIT if hasattr(self, "MAX_LIMIT") else 100)

    # ========== HELPER METHODS ==========

    def _get_current_time_ms(self) -> int:
        """Get current time in milliseconds since epoch."""
        from datetime import datetime

        return int(datetime.now().timestamp() * 1000)

    async def _log_query(self, **kwargs):
        """Log a query (stub - implemented by QuerySystem)."""
        # Subclasses should override this or use the one from QuerySystem
        pass

    # ========== BUILD CONTEXT ==========

    async def build_context(
        self,
        task: str,
        domain: Optional[str] = None,
        tags: Optional[List[str]] = None,
        max_tokens: int = 5000,
        timeout: Optional[int] = None,
        depth: str = "standard",
    ) -> str:
        """
        Build a context string for agents with tiered retrieval (async).

        Tier 1: Golden rules (always included)
        Tier 2: Domain-specific heuristics and tag-matched learnings
        Tier 3: Recent context if tokens remain

        Depth levels control how much context is loaded:
        - minimal: Golden rules only (~500 tokens) - for quick tasks
        - standard: + domain heuristics and learnings (default)
        - deep: + experiments, ADRs, all recent learnings (~5k tokens)

        Args:
            task: Description of the task for context
            domain: Optional domain to focus on
            tags: Optional tags to match
            max_tokens: Maximum tokens to use (approximate, based on ~4 chars/token)
            timeout: Query timeout in seconds (default: 30)
            depth: Context depth level ('minimal', 'standard', 'deep')

        Returns:
            Formatted context string for agent consumption

        Raises:
            ValidationError: If inputs are invalid
            TimeoutError: If query times out
        """
        start_time = self._get_current_time_ms()
        error_msg = None
        error_code = None
        status = "success"
        result = None

        # Track counts for logging
        golden_rules_returned = 0
        heuristics_count = 0
        learnings_count = 0
        experiments_count = 0
        ceo_reviews_count = 0
        decisions_count = 0

        try:
            # Validate inputs
            task = self._validate_query(task)
            if domain:
                domain = self._validate_domain(domain)
            if tags:
                tags = self._validate_tags(tags)
            if max_tokens > self.MAX_TOKENS:
                max_tokens = self.MAX_TOKENS
            timeout = (
                timeout or self.DEFAULT_TIMEOUT * 2
            )  # Context building may take longer

            # Validate depth parameter
            if depth not in ("minimal", "standard", "deep"):
                depth = "standard"

            # Get depth-aware limits
            limits = get_depth_limits(depth)

            log_debug(
                "context",
                f"Building context (domain={domain}, tags={tags}, max_tokens={max_tokens}, depth={depth})",
            )
            async with AsyncTimeoutHandler(timeout):
                context_parts = []
                approx_tokens = 0
                max_chars = max_tokens * 4  # Rough approximation

                # Tier 0: Project Context (if in an ELF-initialized project)
                project_ctx = None
                if PROJECT_CONTEXT_AVAILABLE:
                    try:
                        # Use current_location from QueryEngine for project detection
                        from pathlib import Path

                        start_path = (
                            Path(self.current_location)
                            if hasattr(self, "current_location")
                            and self.current_location
                            else None
                        )
                        project_ctx = detect_project_context(start_path)
                        if project_ctx and project_ctx.has_project_context():
                            log_debug(
                                "context",
                                f"Detected project: {project_ctx.project_name} at {project_ctx.elf_root}",
                            )

                            # Add project header
                            context_parts.append("# TIER 0: Project Context\n\n")
                            context_parts.append(
                                f"**Project:** {project_ctx.project_name}\n"
                            )
                            context_parts.append(f"**Root:** {project_ctx.elf_root}\n")

                            if project_ctx.domains:
                                context_parts.append(
                                    f"**Domains:** {', '.join(project_ctx.domains)}\n"
                                )
                                # Use project domains if no explicit domain provided
                                if not domain and project_ctx.domains:
                                    domain = project_ctx.domains[0]
                                    log_debug(
                                        "context", f"Using project domain: {domain}"
                                    )

                            # Safely handle inheritance_chain - it may be empty list or Never type
                            inheritance_chain = project_ctx.inheritance_chain
                            if (
                                inheritance_chain
                                and hasattr(inheritance_chain, "__iter__")
                                and not isinstance(inheritance_chain, str)
                            ):
                                parents = [p.name for p in inheritance_chain]
                                context_parts.append(
                                    f"**Inherits from:** {' -> '.join(parents)}\n"
                                )

                            context_parts.append("\n")

                            # Load project context.md content
                            project_description = project_ctx.get_context_md_content()
                            if project_description:
                                context_parts.append("## Project Description\n\n")
                                if len(project_description) > 2000:
                                    project_description = (
                                        project_description[:2000] + "\n...(truncated)"
                                    )
                                context_parts.append(project_description)
                                context_parts.append("\n\n")
                                approx_tokens += len(project_description) // 4

                            context_parts.append("---\n\n")
                        else:
                            log_debug("context", "No .elf/ found - global-only mode")
                    except Exception as e:
                        log_debug("context", f"Project context detection failed: {e}")

                # Tier 1: Golden Rules (now contextual!)
                # Prepare context parameters for golden rules filtering
                golden_project_path = None
                golden_project_domains = None
                if project_ctx and project_ctx.has_project_context():
                    golden_project_path = str(project_ctx.elf_root)
                    if project_ctx.domains:
                        golden_project_domains = list(project_ctx.domains)
                        log_debug(
                            "context",
                            f"Golden rules contextual to: {golden_project_path} with domains: {golden_project_domains}",
                        )

                # For minimal depth, only load configured always_load_categories
                if depth == "minimal":
                    always_cats = get_always_load_categories()
                    golden_rules = await self.get_golden_rules(
                        categories=always_cats,
                        project_path_str=golden_project_path,
                        project_domains=golden_project_domains,
                    )
                    context_parts.append(
                        f"# TIER 1: Golden Rules ({', '.join(always_cats)})\n"
                    )
                else:
                    golden_rules = await self.get_golden_rules(
                        project_path_str=golden_project_path,
                        project_domains=golden_project_domains,
                    )
                    context_parts.append("# TIER 1: Golden Rules\n")

                # Append custom golden rules if they exist
                custom_rules = load_custom_golden_rules()
                if custom_rules:
                    context_parts.append("\n# Custom Golden Rules\n")
                    context_parts.append(custom_rules)
                    context_parts.append("\n")

                context_parts.append(golden_rules)
                context_parts.append("\n")
                approx_tokens += len(golden_rules) // 4
                golden_rules_returned = 1  # Flag that golden rules were included

                # For minimal depth, return just core golden rules (~300 tokens)
                if depth == "minimal":
                    building_header = (
                        "🏢 Building Status (minimal)\n━━━━━━━━━━━━━━━━━━\n\n"
                    )

                    # Add location awareness header
                    if hasattr(self, "current_location") and self.current_location:
                        location_info = f"**Location:** `{self.current_location}`\n\n"
                        building_header += location_info

                    # Add semantic memory availability notice
                    semantic_notice = """## 📚 Semantic Memory Available

**You have access to semantic memory** (task-aware search through all learnings and heuristics).

**To use semantic memory in this session:**

1. **For your current task with semantic search:**
   ```
   python query.py --context "your task description" --depth standard
   ```
   Returns: Golden rules + semantically relevant heuristics matched to your task

2. **For expanded context:**
   ```
   python query.py --context "your task description" --depth deep
   ```
   Returns: Full context + semantic search + all learnings, experiments, and decisions

3. **For domain-specific context:**
   ```
   python query.py --context --domain debugging --depth standard
   ```
   Returns: Golden rules + domain-specific heuristics + semantic results

**Semantic matching works by:**
- Analyzing your task description
- Finding heuristics with similar concepts, patterns, and lessons
- Ranking by relevance (% match) and confidence level
- Prioritizing high-confidence, well-validated knowledge

**When to trigger semantic search:**
- Starting a new task or investigation
- Stuck on a problem you haven't solved before
- Need domain-specific best practices
- Building context for other agents

---

"""
                    # Add minimal semantic search to minimal mode
                    semantic_results = None
                    if (
                        SEMANTIC_SEARCH_AVAILABLE
                        and task != "Agent task context generation"
                    ):
                        try:
                            log_debug(
                                "context",
                                "Running minimal semantic search on task description",
                            )
                            searcher = await SemanticSearcher.create(
                                base_path=self.base_path
                            )
                            # Use task as semantic query with broader threshold for minimal mode
                            semantic_results = await searcher.find_relevant_heuristics(
                                task=task,
                                threshold=0.5,  # Lower threshold for broader coverage in minimal mode
                                limit=3,  # Only top 3 in minimal mode
                                domain=domain,
                                project_path=golden_project_path,  # Contextual semantic search
                            )
                            try:
                                await searcher.cleanup()
                            except Exception as e:
                                log_debug(
                                    "context", f"Semantic search cleanup failed: {e}"
                                )

                            if semantic_results:
                                context_parts.append(
                                    "\n## 🧠 Semantic Memory Match (Top Results)\n\n"
                                )
                                for h in semantic_results[:3]:
                                    score = h.get("_final_score", 0)
                                    rule = (
                                        h["rule"][:70] + "..."
                                        if len(h["rule"]) > 70
                                        else h["rule"]
                                    )
                                    entry = f"- **{rule}** ({score * 100:.0f}% match)\n"
                                    context_parts.append(entry)
                                context_parts.append("\n")
                        except Exception as e:
                            log_debug(
                                "context",
                                f"Minimal semantic search failed (non-critical): {e}",
                            )

                    context_parts.insert(
                        0,
                        f"{building_header}{semantic_notice}# Task Context\n\n{task}\n\n---\n\n",
                    )
                    result = "".join(context_parts)
                    log_debug(
                        "context",
                        f"Built minimal context with ~{len(result) // 4} tokens",
                    )
                    return result

                # Check for similar failures (early warning system)
                similar_failures = await self.find_similar_failures(task)
                if similar_failures:
                    context_parts.append("\n## Similar Failures Detected\n\n")
                    for sf in similar_failures[:3]:  # Top 3 most similar
                        context_parts.append(
                            f"- **[{sf['relevance_score'] * 100:.0f}% match] {sf['learning'].get('title', 'Unknown')}**\n"
                        )
                        if sf.get("matching_words"):
                            context_parts.append(
                                f"  Matching keywords: {sf['matching_words']}\n"
                            )
                        summary = sf["learning"].get("summary", "")
                        if summary:
                            summary = (
                                summary[:100] + "..." if len(summary) > 100 else summary
                            )
                            context_parts.append(f"  Lesson: {summary}\n")
                        context_parts.append("\n")

                # Tier 2: Query-matched content
                context_parts.append("# TIER 2: Relevant Knowledge\n\n")

                # Semantic search (if available and within token budget)
                semantic_results = None
                if SEMANTIC_SEARCH_AVAILABLE and approx_tokens < max_chars * 0.5:
                    try:
                        log_debug(
                            "context", "Running semantic search on task description"
                        )
                        searcher = await SemanticSearcher.create(
                            base_path=self.base_path
                        )
                        # Use task as semantic query
                        semantic_results = await searcher.find_relevant_heuristics(
                            task=task,
                            threshold=0.6,  # Lower threshold for broader coverage
                            limit=limits.get("heuristics", 5),
                            domain=domain,
                            project_path=golden_project_path,  # Contextual semantic search
                        )
                        try:
                            await searcher.cleanup()
                        except Exception as e:
                            log_debug("context", f"Semantic search cleanup failed: {e}")

                        if semantic_results:
                            context_parts.append(
                                "## Semantically Relevant Heuristics\n\n"
                            )
                            for h in semantic_results:
                                score = h.get("_final_score", 0)
                                entry = f"- **{h['rule']}** (semantic match: {score * 100:.0f}%, confidence: {h['confidence']:.2f})\n"
                                if h.get("explanation"):
                                    expl = (
                                        h["explanation"][:100] + "..."
                                        if len(h["explanation"]) > 100
                                        else h["explanation"]
                                    )
                                    entry += f"  {expl}\n"
                                entry += "\n"
                                context_parts.append(entry)
                                approx_tokens += len(entry) // 4
                            context_parts.append("\n")
                    except Exception as e:
                        log_debug(
                            "context", f"Semantic search failed (non-critical): {e}"
                        )

                if domain:
                    context_parts.append(f"## Domain: {domain}\n\n")
                    domain_data = await self.query_by_domain(
                        domain,
                        limit=limits["heuristics"],
                        timeout=timeout,
                        project_path=golden_project_path,  # Contextual domain query
                    )

                    if domain_data["heuristics"]:
                        context_parts.append("### Heuristics:\n")
                        # Apply relevance scoring to heuristics
                        heuristics_with_scores = []
                        for h in domain_data["heuristics"]:
                            h["_relevance"] = self._calculate_relevance_score(
                                h, task, domain
                            )
                            heuristics_with_scores.append(h)
                        heuristics_with_scores.sort(
                            key=lambda x: x.get("_relevance", 0), reverse=True
                        )

                        for h in heuristics_with_scores:
                            entry = f"- **{h['rule']}** (confidence: {h['confidence']:.2f}, validated: {h['times_validated']}x)\n"
                            entry += f"  {h['explanation']}\n\n"
                            context_parts.append(entry)
                            approx_tokens += len(entry) // 4
                        heuristics_count += len(domain_data["heuristics"])

                    if domain_data["learnings"]:
                        context_parts.append("### Recent Learnings:\n")
                        # Apply relevance scoring to learnings
                        learnings_with_scores = []
                        for l in domain_data["learnings"]:
                            l["_relevance"] = self._calculate_relevance_score(
                                l, task, domain
                            )
                            learnings_with_scores.append(l)
                        learnings_with_scores.sort(
                            key=lambda x: x.get("_relevance", 0), reverse=True
                        )

                        for l in learnings_with_scores:
                            entry = f"- **{l['title']}** ({l['type']})\n"
                            if l["summary"]:
                                entry += f"  {l['summary']}\n"
                            entry += f"  Tags: {l['tags']}\n\n"
                            context_parts.append(entry)
                            approx_tokens += len(entry) // 4
                        learnings_count += len(domain_data["learnings"])

                # Add project-specific heuristics (if in project mode)
                if (
                    PROJECT_CONTEXT_AVAILABLE
                    and project_ctx
                    and project_ctx.has_project_context()
                    and AIOSQLITE_AVAILABLE
                ):
                    try:
                        project_db = project_ctx.project_db_path
                        if project_db and project_db.exists():
                            async with aiosqlite.connect(str(project_db)) as conn:
                                async with conn.execute(
                                    """
                                    SELECT rule, explanation, domain, confidence, validation_count
                                    FROM heuristics
                                    ORDER BY confidence DESC, validation_count DESC
                                    LIMIT ?
                                """,
                                    (limits["heuristics"],),
                                ) as cursor:
                                    project_heuristics = await cursor.fetchall()

                                if project_heuristics:
                                    context_parts.append(
                                        "\n## Project-Specific Heuristics\n\n"
                                    )
                                    for h in project_heuristics:
                                        (
                                            rule,
                                            explanation,
                                            h_domain,
                                            confidence,
                                            val_count,
                                        ) = h
                                        entry = f"- **{rule}** (confidence: {confidence:.2f}"
                                        if val_count:
                                            entry += f", validated: {val_count}x"
                                        entry += ")\n"
                                        if explanation:
                                            expl = (
                                                explanation[:100] + "..."
                                                if len(explanation) > 100
                                                else explanation
                                            )
                                            entry += f"  {expl}\n"
                                        entry += "\n"
                                        context_parts.append(entry)
                                        approx_tokens += len(entry) // 4
                                    heuristics_count += len(project_heuristics)

                                async with conn.execute(
                                    """
                                    SELECT type, summary, details, domain
                                    FROM learnings
                                    ORDER BY created_at DESC
                                    LIMIT ?
                                """,
                                    (limits["learnings"],),
                                ) as cursor:
                                    project_learnings = await cursor.fetchall()

                                if project_learnings:
                                    context_parts.append(
                                        "\n## Project-Specific Learnings\n\n"
                                    )
                                    for l in project_learnings:
                                        l_type, summary, details, l_domain = l
                                        entry = f"- **{summary}** ({l_type})\n"
                                        if details:
                                            det = (
                                                details[:100] + "..."
                                                if len(details) > 100
                                                else details
                                            )
                                            entry += f"  {det}\n"
                                        entry += "\n"
                                        context_parts.append(entry)
                                        approx_tokens += len(entry) // 4
                                    learnings_count += len(project_learnings)
                    except Exception as e:
                        log_debug(
                            "context", f"Failed to load project-specific content: {e}"
                        )

                else:
                    # No domain specified - show recent heuristics across all domains
                    try:
                        m = get_manager()
                        async with m:
                            async with m.connection():
                                # Get recent non-golden heuristics (golden are in TIER 1)
                                recent_heuristics_query = (
                                    Heuristic.select()
                                    .where(
                                        (Heuristic.is_golden == False)
                                        | (Heuristic.is_golden.is_null())
                                    )
                                    .order_by(
                                        Heuristic.created_at.desc(),
                                        Heuristic.confidence.desc(),
                                    )
                                    .limit(limits["heuristics"])
                                )

                                recent_heuristics = []
                                async for h in recent_heuristics_query:
                                    recent_heuristics.append(
                                        {
                                            "rule": h.rule,
                                            "domain": h.domain,
                                            "confidence": h.confidence,
                                            "explanation": h.explanation,
                                        }
                                    )

                                if recent_heuristics:
                                    context_parts.append(
                                        "## Recent Heuristics (all domains)\n\n"
                                    )
                                    for h in recent_heuristics:
                                        h_domain = h.get("domain", "general")
                                        entry = f"- **{h['rule']}** (domain: {h_domain}, confidence: {h['confidence']:.2f})\n"
                                        if h.get("explanation"):
                                            expl = (
                                                h["explanation"][:100] + "..."
                                                if len(h["explanation"]) > 100
                                                else h["explanation"]
                                            )
                                            entry += f"  {expl}\n"
                                        entry += "\n"
                                        context_parts.append(entry)
                                        approx_tokens += len(entry) // 4
                                    heuristics_count += len(recent_heuristics)

                                # Get recent learnings across all domains
                                recent_learnings_query = (
                                    Learning.select()
                                    .order_by(Learning.created_at.desc())
                                    .limit(limits["learnings"])
                                )

                                recent_learnings = []
                                async for l in recent_learnings_query:
                                    recent_learnings.append(
                                        {
                                            "title": l.title,
                                            "type": l.type,
                                            "domain": l.domain,
                                            "summary": l.summary,
                                        }
                                    )

                                if recent_learnings:
                                    context_parts.append(
                                        "## Recent Learnings (all domains)\n\n"
                                    )
                                    for l in recent_learnings:
                                        l_domain = l.get("domain", "general")
                                        entry = f"- **{l['title']}** ({l['type']}, domain: {l_domain})\n"
                                        if l.get("summary"):
                                            summary = (
                                                l["summary"][:100] + "..."
                                                if len(l["summary"]) > 100
                                                else l["summary"]
                                            )
                                            entry += f"  {summary}\n"
                                        entry += "\n"
                                        context_parts.append(entry)
                                        approx_tokens += len(entry) // 4
                                    learnings_count += len(recent_learnings)

                    except Exception as e:
                        log_debug(
                            "context",
                            f"Failed to fetch recent heuristics/learnings: {e}",
                        )

                if tags:
                    context_parts.append(f"## Tag Matches: {', '.join(tags)}\n\n")
                    tag_results = await self.query_by_tags(
                        tags, limit=limits["learnings"], timeout=timeout
                    )

                    # Apply relevance scoring to tag results
                    tag_results_with_scores = []
                    for l in tag_results:
                        l["_relevance"] = self._calculate_relevance_score(
                            l, task, domain
                        )
                        tag_results_with_scores.append(l)
                    tag_results_with_scores.sort(
                        key=lambda x: x.get("_relevance", 0), reverse=True
                    )

                    for l in tag_results_with_scores:
                        entry = (
                            f"- **{l['title']}** ({l['type']}, domain: {l['domain']})\n"
                        )
                        if l["summary"]:
                            entry += f"  {l['summary']}\n"
                        entry += f"  Tags: {l['tags']}\n\n"
                        context_parts.append(entry)
                        approx_tokens += len(entry) // 4
                    learnings_count += len(tag_results)

                # Add decisions (ADRs) in Tier 2
                decisions = await self.get_decisions(
                    domain=domain,
                    status="accepted",
                    limit=limits["decisions"],
                    timeout=timeout,
                )
                if decisions:
                    context_parts.append("\n## Decisions (ADRs)\n\n")
                    for dec in decisions:
                        entry = f"- **{dec['title']}**"
                        if dec.get("domain"):
                            entry += f" (domain: {dec['domain']})"
                        entry += "\n"
                        if dec.get("decision"):
                            decision_text = (
                                dec["decision"][:150] + "..."
                                if len(dec["decision"]) > 150
                                else dec["decision"]
                            )
                            entry += f"  Decision: {decision_text}\n"
                        if dec.get("rationale"):
                            rationale_text = (
                                dec["rationale"][:150] + "..."
                                if len(dec["rationale"]) > 150
                                else dec["rationale"]
                            )
                            entry += f"  Rationale: {rationale_text}\n"
                        entry += "\n"
                        context_parts.append(entry)
                        approx_tokens += len(entry) // 4
                    decisions_count = len(decisions)

                # Add active plans and recent postmortems (plan-postmortem learning)
                if PLAN_POSTMORTEM_AVAILABLE:
                    try:
                        active_plans = get_active_plans(domain=domain, limit=3)
                        if active_plans:
                            plans_output = format_plans_for_context(active_plans)
                            context_parts.append("\n" + plans_output)
                            approx_tokens += len(plans_output) // 4
                        recent_postmortems = get_recent_postmortems(
                            domain=domain, limit=3
                        )
                        if recent_postmortems:
                            postmortems_output = format_postmortems_for_context(
                                recent_postmortems
                            )
                            context_parts.append("\n" + postmortems_output)
                            approx_tokens += len(postmortems_output) // 4
                    except Exception as e:
                        log_debug("context", f"Failed to fetch plans/postmortems: {e}")

                # Add invariants (what must always be true)
                invariants = await self.get_invariants(
                    domain=domain,
                    status="active",
                    limit=limits["invariants"],
                    timeout=timeout,
                )
                violated_invariants = await self.get_invariants(
                    domain=domain,
                    status="violated",
                    limit=limits["invariants"] // 2 + 1,
                    timeout=timeout,
                )

                if violated_invariants:
                    context_parts.append("\n## VIOLATED INVARIANTS\n\n")
                    for inv in violated_invariants:
                        entry = f"- **[VIOLATED {inv.get('violation_count', 0)}x] {inv['statement'][:100]}{'...' if len(inv['statement']) > 100 else ''}**\n"
                        entry += (
                            f"  Severity: {inv['severity']} | Scope: {inv['scope']}\n"
                        )
                        if inv.get("rationale"):
                            rationale_text = (
                                inv["rationale"][:100] + "..."
                                if len(inv["rationale"]) > 100
                                else inv["rationale"]
                            )
                            entry += f"  Rationale: {rationale_text}\n"
                        entry += "\n"
                        context_parts.append(entry)
                        approx_tokens += len(entry) // 4

                if invariants:
                    context_parts.append("\n## Active Invariants\n\n")
                    for inv in invariants:
                        entry = f"- **{inv['statement'][:100]}{'...' if len(inv['statement']) > 100 else ''}**"
                        if inv.get("domain"):
                            entry += f" (domain: {inv['domain']})"
                        entry += (
                            f"\n  Severity: {inv['severity']} | Scope: {inv['scope']}"
                        )
                        if inv.get("validation_type"):
                            entry += f" | Validation: {inv['validation_type']}"
                        entry += "\n\n"
                        context_parts.append(entry)
                        approx_tokens += len(entry) // 4

                # Add high-confidence active assumptions
                assumptions = await self.get_assumptions(
                    domain=domain,
                    status="active",
                    min_confidence=0.6,
                    limit=limits["assumptions"],
                    timeout=timeout,
                )
                if assumptions:
                    context_parts.append(
                        "\n## Active Assumptions (High Confidence)\n\n"
                    )
                    for assum in assumptions:
                        entry = f"- **{assum['assumption'][:100]}{'...' if len(assum['assumption']) > 100 else ''}**"
                        entry += f" (confidence: {assum['confidence']:.0%}"
                        if assum["verified_count"] > 0:
                            entry += f", verified: {assum['verified_count']}x"
                        entry += ")\n"
                        if assum.get("context"):
                            context_text = (
                                assum["context"][:100] + "..."
                                if len(assum["context"]) > 100
                                else assum["context"]
                            )
                            entry += f"  Context: {context_text}\n"
                        if assum.get("source"):
                            entry += f"  Source: {assum['source']}\n"
                        entry += "\n"
                        context_parts.append(entry)
                        approx_tokens += len(entry) // 4

                # Show challenged/invalidated assumptions as warnings
                challenged = await self.get_challenged_assumptions(
                    domain=domain, limit=limits["assumptions"] // 2 + 1, timeout=timeout
                )
                if challenged:
                    context_parts.append("\n## Challenged/Invalidated Assumptions\n\n")
                    for assum in challenged:
                        status_emoji = (
                            "INVALIDATED"
                            if assum["status"] == "invalidated"
                            else "CHALLENGED"
                        )
                        entry = f"- **[{status_emoji}] {assum['assumption'][:80]}{'...' if len(assum['assumption']) > 80 else ''}**\n"
                        entry += f"  Challenged {assum['challenged_count']}x"
                        if assum["verified_count"] > 0:
                            entry += f", verified {assum['verified_count']}x"
                        entry += f" | Confidence: {assum['confidence']:.0%}\n"
                        if assum.get("context"):
                            context_text = (
                                assum["context"][:80] + "..."
                                if len(assum["context"]) > 80
                                else assum["context"]
                            )
                            entry += f"  Original context: {context_text}\n"
                        entry += "\n"
                        context_parts.append(entry)
                        approx_tokens += len(entry) // 4

                # Add relevant spike reports (hard-won research knowledge)
                spike_reports = await self.get_spike_reports(
                    domain=domain, limit=limits["spikes"], timeout=timeout
                )
                if spike_reports:
                    context_parts.append("\n## Spike Reports (Research Knowledge)\n\n")
                    for spike in spike_reports:
                        entry = f"- **{spike['title']}**"
                        if spike.get("time_invested_minutes"):
                            entry += f" ({spike['time_invested_minutes']} min invested)"
                        entry += "\n"
                        if spike.get("topic"):
                            entry += f"  Topic: {spike['topic'][:100]}{'...' if len(spike['topic']) > 100 else ''}\n"
                        if spike.get("findings"):
                            findings_text = (
                                spike["findings"][:200] + "..."
                                if len(spike["findings"]) > 200
                                else spike["findings"]
                            )
                            entry += f"  Findings: {findings_text}\n"
                        if spike.get("gotchas"):
                            gotchas_text = (
                                spike["gotchas"][:100] + "..."
                                if len(spike["gotchas"]) > 100
                                else spike["gotchas"]
                            )
                            entry += f"  Gotchas: {gotchas_text}\n"
                        if (
                            spike.get("usefulness_score")
                            and spike["usefulness_score"] > 0
                        ):
                            entry += (
                                f"  Usefulness: {spike['usefulness_score']:.1f}/5\n"
                            )
                        entry += "\n"
                        context_parts.append(entry)
                        approx_tokens += len(entry) // 4

                # Tier 3: Recent context if tokens remain
                remaining_tokens = max_tokens - approx_tokens
                if remaining_tokens > 500:
                    context_parts.append("# TIER 3: Recent Context\n\n")
                    recent = await self.query_recent(limit=3, timeout=timeout)

                    for l in recent:
                        entry = f"- **{l['title']}** ({l['type']}, {l['created_at']})\n"
                        if l["summary"]:
                            entry += f"  {l['summary']}\n\n"
                        context_parts.append(entry)
                        approx_tokens += len(entry) // 4

                        if approx_tokens >= max_tokens:
                            break
                    learnings_count += len(recent)

                # Add active experiments
                experiments = await self.get_active_experiments(timeout=timeout)
                if experiments:
                    context_parts.append("\n# Active Experiments\n\n")
                    for exp in experiments:
                        entry = f"- **{exp['name']}** ({exp['cycles_run']} cycles)\n"
                        if exp["hypothesis"]:
                            entry += f"  Hypothesis: {exp['hypothesis']}\n\n"
                        context_parts.append(entry)
                    experiments_count = len(experiments)

                # Add pending CEO reviews
                ceo_reviews = await self.get_pending_ceo_reviews(timeout=timeout)
                if ceo_reviews:
                    context_parts.append("\n# Pending CEO Reviews\n\n")
                    for review in ceo_reviews:
                        entry = f"- **{review['title']}**\n"
                        if review["context"]:
                            entry += f"  Context: {review['context']}\n"
                        if review["recommendation"]:
                            entry += f"  Recommendation: {review['recommendation']}\n\n"
                        context_parts.append(entry)
                    ceo_reviews_count = len(ceo_reviews)

                # Session integration - load cross-session context
                try:
                    from query.session_integration import SessionIntegration

                    session_int = SessionIntegration(
                        debug=getattr(self, "debug", False)
                    )
                    session_context, _ = session_int.build_session_checkin_context()
                    if session_context:
                        context_parts.append(session_context)
                except ImportError:
                    log_debug("context", "SessionIntegration module not available")
                except Exception as e:
                    log_debug("context", f"Session integration failed: {e}")

                # Task context with building header (show depth level)
                depth_label = f" ({depth})" if depth != "standard" else ""
                building_header = (
                    f"🏢 Building Status{depth_label}\n━━━━━━━━━━━━━━━━━━\n\n"
                )

                # Add location awareness header
                if hasattr(self, "current_location") and self.current_location:
                    location_info = f"**Location:** `{self.current_location}`\n\n"
                    building_header += location_info

                # Multi-model detection (if available)
                if MODEL_DETECTION_AVAILABLE:
                    try:
                        detected_models = detect_installed_models()
                        model_info = format_models_for_context(detected_models)
                        building_header += model_info
                        log_debug(
                            "context",
                            f"Model detection successful, {len(model_info)} chars",
                        )
                    except Exception as e:
                        log_debug("context", f"Model detection failed: {e}")

                context_parts.insert(
                    0, f"{building_header}# Task Context\n\n{task}\n\n---\n\n"
                )

            result = "".join(context_parts)
            log_debug("context", f"Built context with ~{len(result) // 4} tokens")
            return result

        except TimeoutError as e:
            status = "timeout"
            error_msg = str(e)
            error_code = "QS003"
            raise
        except (ValidationError, DatabaseError, QuerySystemError) as e:
            status = "error"
            error_msg = str(e)
            error_code = getattr(e, "error_code", "QS000")
            raise
        except Exception as e:
            status = "error"
            error_msg = str(e)
            error_code = "QS000"
            raise
        finally:
            # Log the query (non-blocking)
            duration_ms = self._get_current_time_ms() - start_time
            tokens_approx = len(result) // 4 if result else 0
            total_results = (
                heuristics_count
                + learnings_count
                + experiments_count
                + ceo_reviews_count
                + decisions_count
            )

            await self._log_query(
                query_type="build_context",
                domain=domain,
                tags=",".join(tags) if tags else None,
                max_tokens_requested=max_tokens,
                results_returned=total_results,
                tokens_approximated=tokens_approx,
                duration_ms=duration_ms,
                status=status,
                error_message=error_msg,
                error_code=error_code,
                golden_rules_returned=golden_rules_returned,
                heuristics_count=heuristics_count,
                learnings_count=learnings_count,
                experiments_count=experiments_count,
                ceo_reviews_count=ceo_reviews_count,
                query_summary=f"Context build for task: {task[:50]}...",
            )

            # Record system metrics for monitoring (non-blocking)
            await self._record_system_metrics(domain=domain)

    async def _record_system_metrics(self, domain: Optional[str] = None):
        """
        Record system health metrics via MetaObserver (async).

        Called after each query to track:
        - avg_confidence: Average confidence of active heuristics
        - validation_velocity: Validations in last 24 hours
        - contradiction_rate: Contradictions / total applications
        - query_count: Incremented on each query

        This is non-blocking - errors are logged but don't propagate.
        """
        if not META_OBSERVER_AVAILABLE:
            return

        try:
            observer = MetaObserver(db_path=self.db_path)

            m = get_manager()
            async with m:
                async with m.connection():
                    query = Heuristic.select(
                        fn.COUNT(Heuristic.id).alias("heuristic_count"),
                        fn.COALESCE(
                            fn.AVG(fn.COALESCE(Heuristic.confidence, 0.5)), 0
                        ).alias("avg_confidence"),
                        fn.COALESCE(
                            fn.SUM(fn.COALESCE(Heuristic.times_validated, 0)), 0
                        ).alias("validation_count"),
                        fn.COALESCE(
                            fn.SUM(fn.COALESCE(Heuristic.times_violated, 0)), 0
                        ).alias("total_violations"),
                    )
                    if domain:
                        query = query.where(Heuristic.domain == domain)

                    result = await query.aio_scalar(as_tuple=True)
                    heuristic_count = result[0] if result else 0
                    avg_conf = result[1] if result else 0.0
                    validation_count = result[2] if result else 0
                    total_violations = result[3] if result else 0
                    total_applications = validation_count + total_violations

                    if heuristic_count > 0:
                        observer.record_metric(
                            "avg_confidence",
                            avg_conf,
                            domain=domain,
                            metadata={"heuristic_count": heuristic_count},
                        )

                    observer.record_metric(
                        "validation_velocity", validation_count, domain=domain
                    )

                    if total_applications > 0:
                        violation_rate = total_violations / total_applications
                        observer.record_metric(
                            "violation_rate", violation_rate, domain=domain
                        )

                    # Query count (simple increment)
                    observer.record_metric("query_count", 1, domain=domain)

            log_debug("context", "Recorded system metrics to meta_observer")

        except Exception as e:
            # Non-blocking: log the error but don't raise
            log_debug("context", f"Failed to record system metrics: {e}")

    def _check_system_alerts(self) -> list:
        """
        Check for system alerts via MetaObserver.

        Returns list of active alerts, or empty list if unavailable.
        This is non-blocking.
        """
        if not META_OBSERVER_AVAILABLE:
            return []

        try:
            observer = MetaObserver(db_path=self.db_path)
            return observer.check_alerts()
        except Exception as e:
            log_debug("context", f"Failed to check system alerts: {e}")
            return []

    # ========== SPIKE REPORT QUERIES ==========

    async def get_spike_reports(
        self,
        domain: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        limit: int = 10,
        timeout: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get spike reports (research/investigation knowledge) (async).

        Spike reports capture knowledge from research sessions that would otherwise
        be lost when the session ends. They preserve time-invested research findings.

        Args:
            domain: Optional domain filter
            tags: Optional list of tags to match
            search: Optional search term for title/topic/findings
            limit: Maximum number of results to return (default: 10)
            timeout: Query timeout in seconds (default: 30)

        Returns:
            List of spike report dictionaries ordered by usefulness and recency
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        log_debug(
            "context",
            f"Querying spike reports (domain={domain}, tags={tags}, limit={limit})",
        )

        start_time = self._get_current_time_ms()
        error_msg = None
        error_code = None
        query_status = "success"
        results = None

        try:
            limit = self._validate_limit(limit)

            async with AsyncTimeoutHandler(timeout):
                try:
                    m = get_manager()
                    async with m:
                        async with m.connection():
                            from models import SpikeReport

                            query = SpikeReport.select()

                            if domain:
                                domain = self._validate_domain(domain)
                                query = query.where(
                                    (SpikeReport.domain == domain)
                                    | (SpikeReport.domain.is_null())
                                )

                            if tags:
                                tags = self._validate_tags(tags)
                                # Build OR conditions using peewee's | operator
                                tag_condition = None
                                for tag in tags:
                                    condition = SpikeReport.tags.contains(tag)
                                    tag_condition = (
                                        condition
                                        if tag_condition is None
                                        else (tag_condition | condition)
                                    )
                                if tag_condition:
                                    query = query.where(tag_condition)

                            if search:
                                query = query.where(
                                    (SpikeReport.title.contains(search))
                                    | (SpikeReport.topic.contains(search))
                                    | (SpikeReport.question.contains(search))
                                    | (SpikeReport.findings.contains(search))
                                )

                            query = query.order_by(
                                SpikeReport.usefulness_score.desc(),
                                SpikeReport.created_at.desc(),
                            ).limit(limit)

                            results = []
                            async for sr in query:
                                results.append(
                                    {
                                        "id": sr.id,
                                        "title": sr.title,
                                        "topic": sr.topic,
                                        "question": sr.question,
                                        "findings": sr.findings,
                                        "gotchas": sr.gotchas,
                                        "resources": sr.resources,
                                        "time_invested_minutes": sr.time_invested_minutes,
                                        "domain": sr.domain,
                                        "tags": sr.tags,
                                        "usefulness_score": sr.usefulness_score,
                                        "access_count": sr.access_count,
                                        "created_at": sr.created_at,
                                        "updated_at": sr.updated_at,
                                    }
                                )
                except Exception as e:
                    # Table might not exist yet
                    if "no such table" in str(e).lower():
                        log_debug(
                            "context",
                            "spike_reports table does not exist yet - returning empty list",
                        )
                        return []
                    raise

            log_debug("context", f"Found {len(results)} spike reports")
            return results

        except Exception as e:
            query_status = "error"
            error_msg = str(e)
            error_code = "QS000"
            log_debug("context", f"Error querying spike reports: {e}")
            return []
        finally:
            duration_ms = self._get_current_time_ms() - start_time
            spike_count = len(results) if results else 0

            await self._log_query(
                query_type="get_spike_reports",
                domain=domain,
                limit_requested=limit,
                results_returned=spike_count,
                duration_ms=duration_ms,
                status=query_status,
                error_message=error_msg,
                error_code=error_code,
                query_summary=f"Spike reports query",
            )

    # ========== GOLDEN RULES AND HEURISTIC QUERIES ==========

    async def get_golden_rules(
        self,
        categories: Optional[List[str]] = None,
        project_path_str: Optional[str] = None,
        project_domains: Optional[List[str]] = None,
    ) -> str:
        """
        Get golden rules from database (preferred) with fallback to file.

        Fetches is_golden=True heuristics from database, which are the authoritative
        source of golden rules. Falls back to golden-rules.md if database is empty.

        Contextual mode: When project_path_str is provided, filters for project-specific
        and global golden rules relevant to the project.

        Args:
            categories: Optional list of categories to filter by.
            project_path_str: Project path for contextual filtering (None = global mode).
            project_domains: List of domains from project config for domain filtering.

        Returns:
            Formatted golden rules content
        """
        import aiofiles
        import time

        # First try to fetch from database (authoritative source)
        try:
            m = get_manager()
            async with m:
                async with m.connection():
                    # Query for golden heuristics
                    golden_query = (
                        Heuristic.select()
                        .where(Heuristic.is_golden == True)
                        .order_by(Heuristic.created_at.asc())
                    )

                    golden_rules = []
                    all_golden = []
                    async for h in golden_query:
                        all_golden.append(h)

                        # ===== SUPER GOLDEN RULES (always included) =====
                        # Super golden rules are:
                        # 1. Core domain rules ("core", "core-principles", "fundamental", "constitutional")
                        #    - These apply regardless of project location (first priority)
                        # 2. Global (project_path IS NULL) - fundamental rules that apply everywhere
                        is_super_golden = False

                        # Check if core domain (fundamental principles) - FIRST PRIORITY
                        if h.domain:
                            domain_lower = h.domain.lower()
                            core_domains = [
                                "core",
                                "core-principles",
                                "fundamental",
                                "constitutional",
                            ]
                            if any(core in domain_lower for core in core_domains):
                                is_super_golden = True
                                log_debug(
                                    "context",
                                    f"[SUPER] Domain-based: {h.rule[:50]}... (domain: {h.domain})",
                                )

                        # Check if global (NULL project_path) - SECONDARY PRIORITY
                        elif h.project_path is None:
                            is_super_golden = True
                            log_debug(
                                "context",
                                f"[SUPER] NULL path: {h.rule[:50]}... (domain: {h.domain})",
                            )

                        # Super golden rules ALWAYS included
                        if is_super_golden:
                            golden_rules.append(h)
                            continue

                        # ===== CONTEXTUAL FILTERING (non-super rules) =====
                        # 1. Filter by project_path (location awareness)
                        #    - NULL = already handled as super
                        #    - matching path = project-specific
                        #    - non-matching path = other project (exclude)
                        if project_path_str is not None and h.project_path is not None:
                            # Both non-null: check if paths match
                            from pathlib import Path

                            try:
                                heur_path = Path(h.project_path).resolve()
                                proj_path = Path(project_path_str).resolve()
                                if heur_path != proj_path:
                                    continue  # Skip heuristics from other projects
                            except Exception as e:
                                log_debug("context", f"Path comparison failed: {e}")
                                continue

                        # 2. Filter by category/domain
                        #    Priority: categories > project_domains > no filter
                        target_domains = categories or project_domains

                        if target_domains:
                            if not h.domain:
                                continue  # Skip rules without domain when filtering requested

                            # Match domain by substring (e.g., "core" matches "core-principles")
                            target_domains_lower = [d.lower() for d in target_domains]
                            domain_lower = h.domain.lower()
                            if any(dom in domain_lower for dom in target_domains_lower):
                                golden_rules.append(h)
                                log_debug(
                                    "context",
                                    f"[PROJECT] Including: {h.rule[:50]}... (domain: {h.domain})",
                                )
                        else:
                            # No domain filter: include all location-matching rules
                            golden_rules.append(h)
                            log_debug(
                                "context",
                                f"[PROJECT] Including: {h.rule[:50]}... (no domain filter)",
                            )

                    # Format golden rules for display
                    if golden_rules:
                        lines = ["# Golden Rules\n"]
                        lines.append(
                            "These are proven principles with high confidence. They are ALWAYS loaded into context.\n"
                        )
                        lines.append("\n---\n")

                        for idx, rule in enumerate(golden_rules, 1):
                            lines.append(f"\n## {idx}. {rule.rule}\n")
                            if rule.explanation:
                                lines.append(f"> {rule.explanation}\n")
                            lines.append(f"\n**Confidence:** {rule.confidence:.2f}")
                            lines.append(f" | **Validations:** {rule.times_validated}x")
                            if rule.domain:
                                lines.append(f" | **Category:** {rule.domain}")
                            lines.append("\n")
                            lines.append("\n---\n")

                        return "".join(lines)

        except Exception as e:
            # CRITICAL: Always log errors - never silent failures
            _LOGGER = _LOGGER if "_LOGGER" in locals() else logging.getLogger("context")
            _LOGGER.error(
                f"Failed to fetch golden rules from database: {e}", exc_info=True
            )
            log_debug("context", f"Failed to fetch golden rules from database: {e}")

        # Fallback to golden-rules.md file
        golden_rules_path = Path(self.base_path) / "memory" / "golden-rules.md"

        if not golden_rules_path.exists():
            log_debug("context", f"Golden rules file not found at {golden_rules_path}")
            return "# Golden Rules\n\nNo golden rules have been established yet."

        cache_key = str(golden_rules_path)
        now = time.time()

        # Simple caching
        if (
            hasattr(self, "_golden_rules_cache")
            and cache_key in self._golden_rules_cache
        ):
            cached_time = getattr(self, "_golden_rules_cache_time", {}).get(
                cache_key, 0
            )
            if now - cached_time < 300:  # 5 minute cache
                content = self._golden_rules_cache[cache_key]
                if not categories:
                    return content

        try:
            async with aiofiles.open(golden_rules_path, "r", encoding="utf-8") as f:
                content = await f.read()

            # Cache the content
            if not hasattr(self, "_golden_rules_cache"):
                self._golden_rules_cache = {}
                self._golden_rules_cache_time = {}
            self._golden_rules_cache[cache_key] = content
            self._golden_rules_cache_time[cache_key] = now

            if not categories:
                return content

            # Filter by category
            import re

            categories_lower = [c.lower() for c in categories]
            lines = content.split("\n")
            result_lines = []
            in_rule = False
            current_rule_lines = []
            include_current = False
            header_ended = False

            for line in lines:
                if re.match(r"^## \d+\.", line):
                    if in_rule and include_current:
                        result_lines.extend(current_rule_lines)
                    in_rule = True
                    current_rule_lines = [line]
                    include_current = False
                    header_ended = True
                elif in_rule:
                    current_rule_lines.append(line)
                    if line.startswith("**Category:**"):
                        category_match = re.search(r"\*\*Category:\*\*\s*(.+)", line)
                        if category_match:
                            rule_category = category_match.group(1).strip().lower()
                            if rule_category in categories_lower:
                                include_current = True
                elif not header_ended:
                    result_lines.append(line)

            if in_rule and include_current:
                result_lines.extend(current_rule_lines)

            # If filtering returned nothing, return the full content
            filtered_result = "\n".join(result_lines).strip()
            if not filtered_result:
                return content
            return filtered_result

        except Exception as e:
            # CRITICAL: Always log errors - never silent failures
            _LOGGER.error(
                f"Failed to read golden rules from file {golden_rules_path}: {e}",
                exc_info=True,
            )
            log_debug("context", f"Golden rules file read failed: {e}")
            return f"# Error Reading Golden Rules\n\nError: {str(e)}"

    async def query_by_domain(
        self,
        domain: str,
        limit: int = 10,
        timeout: Optional[int] = None,
        project_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get heuristics and learnings for a specific domain (async).

        Now supports contextual filtering by project_path!

        Args:
            domain: The domain to query
            limit: Maximum number of results
            timeout: Query timeout in seconds
            project_path: Optional project path for contextual filtering

        Returns:
            Dictionary containing heuristics and learnings for the domain
        """
        timeout = timeout or self.DEFAULT_TIMEOUT

        async with AsyncTimeoutHandler(timeout):
            m = get_manager()
            async with m:
                async with m.connection():
                    # Build heuristics query with optional project filtering
                    heuristics_query = Heuristic.select().where(
                        Heuristic.domain == domain
                    )

                    # Apply project filter if specified (include global + project-specific)
                    if project_path is not None:
                        heuristics_query = heuristics_query.where(
                            (Heuristic.project_path.is_null())
                            | (Heuristic.project_path == project_path)
                        )

                    heuristics_query = heuristics_query.order_by(
                        Heuristic.confidence.desc(),
                        Heuristic.times_validated.desc(),
                    ).limit(limit)

                    heuristics = []
                    async for h in heuristics_query:
                        heuristics.append(h.__data__.copy())

                    # Build learnings query with optional project filtering
                    learnings_query = Learning.select().where(Learning.domain == domain)

                    # Apply project filter if specified (include global + project-specific)
                    if project_path is not None:
                        learnings_query = learnings_query.where(
                            (Learning.project_path.is_null())
                            | (Learning.project_path == project_path)
                        )

                    learnings_query = learnings_query.order_by(
                        Learning.created_at.desc()
                    ).limit(limit)

                    learnings = []
                    async for l in learnings_query:
                        learnings.append(l.__data__.copy())

        return {
            "domain": domain,
            "heuristics": heuristics,
            "learnings": learnings,
            "count": {"heuristics": len(heuristics), "learnings": len(learnings)},
        }

    async def query_by_tags(
        self, tags: List[str], limit: int = 10, timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get learnings matching specified tags (async).

        Args:
            tags: List of tags to search for
            limit: Maximum number of results
            timeout: Query timeout in seconds

        Returns:
            List of learnings matching any of the tags
        """
        timeout = timeout or self.DEFAULT_TIMEOUT

        async with AsyncTimeoutHandler(timeout):
            m = get_manager()
            async with m:
                async with m.connection():
                    # Build tag conditions using peewee's | operator
                    tag_condition = None
                    for tag in tags:
                        condition = Learning.tags.contains(tag)
                        tag_condition = (
                            condition
                            if tag_condition is None
                            else (tag_condition | condition)
                        )

                    query = (
                        Learning.select()
                        .where(tag_condition)
                        .order_by(Learning.created_at.desc())
                        .limit(limit)
                    )
                    results = []
                    async for l in query:
                        results.append(l.__data__.copy())

        return results

    def _calculate_relevance_score(
        self, entry: Dict[str, Any], task: str, domain: Optional[str] = None
    ) -> float:
        """
        Calculate a simple relevance score based on keyword matching.

        Args:
            entry: Dictionary with rule/title and content
            task: The task description
            domain: Optional domain for additional scoring

        Returns:
            Relevance score (0.0 - 1.0)
        """
        task_words = set(task.lower().split())

        # Get text to score
        if "rule" in entry:
            text = f"{entry['rule']} {entry.get('explanation', '')}".lower()
        elif "title" in entry:
            text = f"{entry['title']} {entry.get('summary', '')} {entry.get('content', '')}".lower()
        else:
            return 0.0

        entry_words = set(text.split())
        overlap = len(task_words & entry_words)

        # Normalize by task word count
        if len(task_words) > 0:
            score = overlap / len(task_words)
        else:
            score = 0.0

        # Boost for domain match
        if domain and entry.get("domain") == domain:
            score = min(score * 1.5, 1.0)

        return score

    # ========== LEARNING QUERIES ==========

    async def query_recent(
        self,
        type_filter: Optional[str] = None,
        limit: int = 10,
        timeout: Optional[int] = None,
        days: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Get recent learnings, optionally filtered by type (async).

        Args:
            type_filter: Optional type filter (e.g., 'incident', 'success')
            limit: Maximum number of results
            timeout: Query timeout in seconds
            days: Only return learnings from the last N days

        Returns:
            List of recent learnings
        """
        timeout = timeout or self.DEFAULT_TIMEOUT

        async with AsyncTimeoutHandler(timeout):
            cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
                days=days
            )

            m = get_manager()
            async with m:
                async with m.connection():
                    query = Learning.select()
                    if type_filter:
                        query = query.where(
                            (Learning.type == type_filter)
                            & (Learning.created_at >= cutoff)
                        )
                    else:
                        query = query.where(Learning.created_at >= cutoff)

                    query = query.order_by(Learning.created_at.desc()).limit(limit)
                    results = []
                    async for l in query:
                        results.append(l.__data__.copy())

        return results

    async def find_similar_failures(
        self, task_description: str, limit: int = 5, timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Find failures similar to a task description using keyword matching (async).

        Args:
            task_description: Description of the current task
            limit: Maximum number of similar failures to return
            timeout: Query timeout in seconds

        Returns:
            List of similar failure records with relevance scores
        """
        timeout = timeout or self.DEFAULT_TIMEOUT

        async with AsyncTimeoutHandler(timeout):
            m = get_manager()
            async with m:
                async with m.connection():
                    query = (
                        Learning.select()
                        .where(Learning.type == "failure")
                        .order_by(Learning.created_at.desc())
                        .limit(100)
                    )

                    failures = []
                    async for f in query:
                        failures.append(f)

        # Score each failure by keyword overlap
        task_words = set(task_description.lower().split())
        scored = []

        for failure in failures:
            title = (failure.title or "").lower()
            summary = (failure.summary or "").lower()
            content_words = set(title.split() + summary.split())

            overlap = len(task_words & content_words)
            if overlap > 0:
                scored.append(
                    {
                        "learning": failure.__data__.copy(),
                        "relevance_score": overlap / max(len(task_words), 1),
                        "matching_words": overlap,
                    }
                )

        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored[:limit]

    # ========== DECISION QUERIES ==========

    async def get_decisions(
        self,
        domain: Optional[str] = None,
        status: str = "accepted",
        limit: int = 10,
        timeout: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get architecture decisions (ADRs), optionally filtered by domain (async).

        Args:
            domain: Optional domain filter
            status: Decision status filter
            limit: Maximum number of results
            timeout: Query timeout in seconds

        Returns:
            List of decision dictionaries
        """
        timeout = timeout or self.DEFAULT_TIMEOUT

        async with AsyncTimeoutHandler(timeout):
            m = get_manager()
            async with m:
                async with m.connection():
                    from models import Decision

                    query = Decision.select().where(Decision.status == status)

                    if domain:
                        query = query.where(
                            (Decision.domain == domain) | (Decision.domain.is_null())
                        )

                    query = query.order_by(Decision.created_at.desc()).limit(limit)
                    results = []
                    async for d in query:
                        results.append(d.__data__.copy())

        return results

    # ========== INVARIANT QUERIES ==========

    async def get_invariants(
        self,
        domain: Optional[str] = None,
        status: str = "active",
        scope: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 10,
        timeout: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get invariants, optionally filtered by domain, status, scope, or severity (async).

        Args:
            domain: Optional domain filter
            status: Invariant status filter
            scope: Scope filter
            severity: Severity filter
            limit: Maximum number of results
            timeout: Query timeout in seconds

        Returns:
            List of invariant dictionaries
        """
        timeout = timeout or self.DEFAULT_TIMEOUT

        async with AsyncTimeoutHandler(timeout):
            try:
                from models import Invariant

                m = get_manager()
                async with m:
                    async with m.connection():
                        query = Invariant.select()

                        if status:
                            query = query.where(Invariant.status == status)

                        if domain:
                            query = query.where(
                                (Invariant.domain == domain)
                                | (Invariant.domain.is_null())
                            )

                        if scope:
                            query = query.where(Invariant.scope == scope)

                        if severity:
                            query = query.where(Invariant.severity == severity)

                        query = query.order_by(Invariant.created_at.desc()).limit(limit)

                        results = []
                        async for inv in query:
                            results.append(
                                {
                                    "id": inv.id,
                                    "statement": inv.statement,
                                    "rationale": inv.rationale,
                                    "domain": inv.domain,
                                    "scope": inv.scope,
                                    "severity": inv.severity,
                                    "status": inv.status,
                                    "created_at": inv.created_at,
                                }
                            )
            except Exception as e:
                if "no such table" in str(e).lower():
                    return []
                raise

        return results

    # ========== ASSUMPTION QUERIES ==========

    async def get_assumptions(
        self,
        domain: Optional[str] = None,
        status: str = "active",
        min_confidence: float = 0.0,
        limit: int = 10,
        timeout: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get assumptions, optionally filtered by domain and status (async).

        Args:
            domain: Optional domain filter
            status: Assumption status filter
            min_confidence: Minimum confidence threshold
            limit: Maximum number of results
            timeout: Query timeout in seconds

        Returns:
            List of assumption dictionaries
        """
        timeout = timeout or self.DEFAULT_TIMEOUT

        async with AsyncTimeoutHandler(timeout):
            try:
                from models import Assumption

                m = get_manager()
                async with m:
                    async with m.connection():
                        query = Assumption.select().where(
                            (Assumption.status == status)
                            & (Assumption.confidence >= min_confidence)
                        )

                        if domain:
                            query = query.where(
                                (Assumption.domain == domain)
                                | (Assumption.domain.is_null())
                            )

                        query = query.order_by(
                            Assumption.confidence.desc(), Assumption.created_at.desc()
                        ).limit(limit)

                        results = []
                        async for a in query:
                            results.append(
                                {
                                    "id": a.id,
                                    "assumption": a.assumption,
                                    "context": a.context,
                                    "source": a.source,
                                    "confidence": a.confidence,
                                    "status": a.status,
                                    "domain": a.domain,
                                    "verified_count": a.verified_count,
                                    "challenged_count": a.challenged_count,
                                    "last_verified_at": a.last_verified_at,
                                    "created_at": a.created_at,
                                }
                            )
            except Exception as e:
                if "no such table" in str(e).lower():
                    return []
                raise

        return results

    async def get_challenged_assumptions(
        self,
        domain: Optional[str] = None,
        limit: int = 10,
        timeout: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get challenged or invalidated assumptions as warnings (async).

        Args:
            domain: Optional domain filter
            limit: Maximum number of results
            timeout: Query timeout in seconds

        Returns:
            List of challenged/invalidated assumption dictionaries
        """
        timeout = timeout or self.DEFAULT_TIMEOUT

        async with AsyncTimeoutHandler(timeout):
            try:
                from models import Assumption

                m = get_manager()
                async with m:
                    async with m.connection():
                        query = Assumption.select().where(
                            Assumption.status.in_(["challenged", "invalidated"])
                        )

                        if domain:
                            query = query.where(
                                (Assumption.domain == domain)
                                | (Assumption.domain.is_null())
                            )

                        query = query.order_by(
                            Assumption.challenged_count.desc(),
                            Assumption.created_at.desc(),
                        ).limit(limit)

                        results = []
                        async for a in query:
                            results.append(
                                {
                                    "id": a.id,
                                    "assumption": a.assumption,
                                    "context": a.context,
                                    "source": a.source,
                                    "confidence": a.confidence,
                                    "status": a.status,
                                    "domain": a.domain,
                                    "verified_count": a.verified_count,
                                    "challenged_count": a.challenged_count,
                                    "created_at": a.created_at,
                                }
                            )
            except Exception as e:
                if "no such table" in str(e).lower():
                    return []
                raise

        return results

    # ========== EXPERIMENT AND CEO REVIEW QUERIES ==========

    async def get_active_experiments(
        self, timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List all active experiments (async).

        Args:
            timeout: Query timeout in seconds

        Returns:
            List of active experiments
        """
        timeout = timeout or self.DEFAULT_TIMEOUT

        async with AsyncTimeoutHandler(timeout):
            try:
                from models import Experiment

                m = get_manager()
                async with m:
                    async with m.connection():
                        query = (
                            Experiment.select()
                            .where(Experiment.status == "active")
                            .order_by(Experiment.created_at.desc())
                        )
                        results = []
                        async for e in query:
                            results.append(e.__data__.copy())
            except Exception as e:
                if "no such table" in str(e).lower():
                    return []
                raise

        return results

    async def get_pending_ceo_reviews(
        self, timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List all pending CEO reviews (async).

        Args:
            timeout: Query timeout in seconds

        Returns:
            List of pending CEO reviews
        """
        timeout = timeout or self.DEFAULT_TIMEOUT

        async with AsyncTimeoutHandler(timeout):
            try:
                from models import CeoReview

                m = get_manager()
                async with m:
                    async with m.connection():
                        query = (
                            CeoReview.select()
                            .where(CeoReview.status == "pending")
                            .order_by(CeoReview.created_at.desc())
                        )
                        results = []
                        async for r in query:
                            results.append(r.__data__.copy())
            except Exception as e:
                if "no such table" in str(e).lower():
                    return []
                raise

        return results
