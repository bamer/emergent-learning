"""
Input validation functions for the Query System.

All validation functions raise ValidationError on invalid input.
"""

import re
from typing import List

# Import ValidationError with fallback for script execution
try:
    from .exceptions import ValidationError
except ImportError:
    from exceptions import ValidationError


# Validation constants
MAX_DOMAIN_LENGTH = 100
MAX_QUERY_LENGTH = 10000
MAX_TAG_COUNT = 50
MAX_TAG_LENGTH = 50
MIN_LIMIT = 1
MAX_LIMIT = 1000
DEFAULT_TIMEOUT = 30
MAX_TOKENS = 50000

# Garbage domains to reject (common words that are clearly not valid domains)
GARBAGE_DOMAINS = {
    "the",
    "these",
    "those",
    "this",
    "that",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "as",
    "is",
    "was",
    "are",
    "were",
    "been",
    "be",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "must",
    "shall",
    "can",
    "need",
    "dare",
    "ought",
    "used",
    "it",
    "its",
    "they",
    "them",
    "their",
    "we",
    "our",
    "you",
    "your",
    "he",
    "she",
    "him",
    "her",
    "his",
    # Also add any single-character domains
    # These will be handled by the minimum length check
}


def validate_domain(domain: str) -> str:
    """
    Validate and normalize domain string.

    Automatically normalizes domains by:
    - Converting spaces to hyphens
    - Converting to lowercase
    - Removing invalid characters
    - Rejecting garbage/common words

    Args:
        domain: Domain to validate

    Returns:
        Validated and normalized domain string

    Raises:
        ValidationError: If domain is empty, too short, or garbage
    """
    if not domain:
        raise ValidationError(
            "Domain cannot be empty. Provide a valid domain name. [QS001]"
        )

    # Normalize: strip whitespace, convert to lowercase
    normalized = domain.strip().lower()

    # Replace spaces with hyphens
    normalized = normalized.replace(" ", "-")

    # Replace multiple consecutive hyphens with single hyphen
    normalized = re.sub(r"-+", "-", normalized)

    # Remove any remaining invalid characters (keep only alphanumeric, hyphen, underscore, dot)
    normalized = re.sub(r"[^a-z0-9\-_.]", "", normalized)

    if len(normalized) > MAX_DOMAIN_LENGTH:
        raise ValidationError(
            f"Domain exceeds maximum length of {MAX_DOMAIN_LENGTH} characters. "
            f"Use a shorter domain name. [QS001]"
        )

    if not normalized:
        raise ValidationError(
            f"Domain '{domain}' contains only invalid characters. "
            f"Use alphanumeric characters, hyphens, underscores, or dots. [QS001]"
        )

    # Reject garbage domains (common words that are clearly not valid domains)
    if normalized in GARBAGE_DOMAINS:
        raise ValidationError(
            f"Domain '{normalized}' is not a valid domain. "
            f"It appears to be a common word. Use a descriptive domain like 'debugging', 'api', 'frontend'. [QS001]"
        )

    # Reject single-character domains (too short to be meaningful)
    if len(normalized) < 2:
        raise ValidationError(
            f"Domain '{normalized}' is too short. "
            f"Use a descriptive domain name (minimum 2 characters). [QS001]"
        )

    return normalized


def validate_limit(limit: int) -> int:
    """
    Validate limit parameter.

    Args:
        limit: Limit to validate

    Returns:
        Validated limit

    Raises:
        ValidationError: If limit is invalid
    """
    if not isinstance(limit, int):
        raise ValidationError(
            f"Limit must be an integer, got {type(limit).__name__}. [QS001]"
        )

    if limit < MIN_LIMIT:
        raise ValidationError(
            f"Limit must be at least {MIN_LIMIT}. Got: {limit}. [QS001]"
        )

    if limit > MAX_LIMIT:
        raise ValidationError(
            f"Limit exceeds maximum of {MAX_LIMIT}. "
            f"Use a smaller limit or process results in batches. [QS001]"
        )

    return limit


def validate_tags(tags: List[str]) -> List[str]:
    """
    Validate tags list.

    Args:
        tags: List of tags to validate

    Returns:
        Validated tags list

    Raises:
        ValidationError: If tags are invalid
    """
    if not isinstance(tags, list):
        raise ValidationError(
            f"Tags must be a list, got {type(tags).__name__}. [QS001]"
        )

    if len(tags) > MAX_TAG_COUNT:
        raise ValidationError(
            f"Too many tags (max {MAX_TAG_COUNT}). "
            f"Reduce number of tags or query in batches. [QS001]"
        )

    validated_tags = []
    for tag in tags:
        tag = tag.strip()
        if not tag:
            continue

        if len(tag) > MAX_TAG_LENGTH:
            raise ValidationError(
                f"Tag '{tag[:20]}...' exceeds maximum length of {MAX_TAG_LENGTH}. [QS001]"
            )

        # Allow Unicode alphanumeric characters, hyphen, underscore, and dot
        if not re.match(r"^[\w\-\.]+$", tag, re.UNICODE):
            raise ValidationError(
                f"Tag '{tag}' contains invalid characters. "
                f"Use only alphanumeric (including Unicode), hyphen, underscore, and dot. [QS001]"
            )

        validated_tags.append(tag)

    if not validated_tags:
        raise ValidationError("No valid tags provided after filtering. [QS001]")

    return validated_tags


def validate_query(query: str) -> str:
    """
    Validate query string.

    Args:
        query: Query string to validate

    Returns:
        Validated query string

    Raises:
        ValidationError: If query is invalid
    """
    if not query:
        raise ValidationError("Query string cannot be empty. [QS001]")

    if len(query) > MAX_QUERY_LENGTH:
        raise ValidationError(
            f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters. "
            f"Reduce query size. [QS001]"
        )

    return query.strip()
