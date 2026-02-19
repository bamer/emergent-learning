"""
Context module for building agent context from the knowledge base.

This package provides modular components for context building:
- validation: Input validation for queries
- queries: Query methods for heuristics
- golden_rules: Golden rules retrieval
- knowledge: Decisions, invariants, assumptions
- experiments: Experiments and reviews

Main entry point:
    from query.context import ContextBuilderMixin

Or use individual components:
    from query.context.validation import ContextValidator
"""

# Import validation module
from .validation import (
    ContextValidator,
    validate_query,
    validate_domain,
    validate_tags,
    validate_limit,
)

# Import ContextBuilderMixin from renamed module
try:
    from query.context_builder import ContextBuilderMixin
except ImportError:
    from ..context_builder import ContextBuilderMixin

__all__ = [
    # Core
    "ContextBuilderMixin",
    # Validation
    "ContextValidator",
    "validate_query",
    "validate_domain",
    "validate_tags",
    "validate_limit",
]
