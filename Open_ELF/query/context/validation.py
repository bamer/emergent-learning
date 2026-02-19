"""Validation helpers for context queries.

This module provides validation methods used by the ContextBuilderMixin
to validate query parameters, domains, tags, and limits.

Example:
    from query.context.validation import ContextValidator

    query = ContextValidator.validate_query("  my query  ")
    # Returns: "my query"
"""

from typing import List, Optional


class ContextValidator:
    """Validation methods for context queries.

    Provides static methods for validating and sanitizing input parameters
    used in context queries.
    """

    # Maximum allowed query length
    MAX_QUERY_LENGTH = 1000

    # Maximum allowed limit
    MAX_LIMIT = 500

    # Default limit when not specified
    DEFAULT_LIMIT = 100

    @staticmethod
    def validate_query(query: str) -> str:
        """Validate and sanitize query string.

        Args:
            query: The query string to validate.

        Returns:
            Sanitized query string.

        Raises:
            ValueError: If query is empty or None.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        return query.strip()[: ContextValidator.MAX_QUERY_LENGTH]

    @staticmethod
    def validate_domain(domain: Optional[str]) -> str:
        """Validate domain string.

        Args:
            domain: The domain to validate.

        Returns:
            Lowercase domain string or empty string.

        Raises:
            ValueError: If domain contains invalid characters.
        """
        if not domain:
            return ""

        domain = domain.strip()

        # Allow alphanumeric, hyphens, underscores
        normalized = domain.replace("-", "").replace("_", "")
        if normalized and not normalized.isalnum():
            raise ValueError(f"Invalid domain: {domain}")

        return domain.lower()

    @staticmethod
    def validate_tags(tags: Optional[List[str]]) -> List[str]:
        """Validate and normalize tags.

        Args:
            tags: List of tags to validate.

        Returns:
            List of normalized, lowercase tags.
        """
        if not tags:
            return []

        return [tag.lower().strip() for tag in tags if tag and tag.strip()]

    @staticmethod
    def validate_limit(
        limit: Optional[int],
        max_limit: Optional[int] = None,
        default: Optional[int] = None,
    ) -> int:
        """Validate limit parameter.

        Args:
            limit: The limit to validate.
            max_limit: Maximum allowed limit (defaults to class MAX_LIMIT).
            default: Default limit if invalid (defaults to class DEFAULT_LIMIT).

        Returns:
            Validated limit between 1 and max_limit.
        """
        max_limit = max_limit or ContextValidator.MAX_LIMIT
        default = default or ContextValidator.DEFAULT_LIMIT

        if limit is None or limit < 1:
            return default

        return min(limit, max_limit)

    @staticmethod
    def validate_positive_int(
        value: Optional[int], default: int = 0, max_value: Optional[int] = None
    ) -> int:
        """Validate a positive integer.

        Args:
            value: The value to validate.
            default: Default if value is None or negative.
            max_value: Maximum allowed value.

        Returns:
            Validated positive integer.
        """
        if value is None or value < 0:
            return default

        if max_value is not None:
            return min(value, max_value)

        return value


# Module-level convenience functions
def validate_query(query: str) -> str:
    """Convenience function for query validation."""
    return ContextValidator.validate_query(query)


def validate_domain(domain: Optional[str]) -> str:
    """Convenience function for domain validation."""
    return ContextValidator.validate_domain(domain)


def validate_tags(tags: Optional[List[str]]) -> List[str]:
    """Convenience function for tags validation."""
    return ContextValidator.validate_tags(tags)


def validate_limit(limit: Optional[int], max_limit: Optional[int] = None) -> int:
    """Convenience function for limit validation."""
    return ContextValidator.validate_limit(limit, max_limit)
