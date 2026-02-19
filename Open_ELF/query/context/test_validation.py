"""Tests for context validation module."""

import pytest
from validation import (
    ContextValidator,
    validate_query,
    validate_domain,
    validate_tags,
    validate_limit,
)


class TestContextValidator:
    """Tests for ContextValidator class."""

    # === Query Validation Tests ===

    def test_validate_query_strips_whitespace(self):
        """Query should be stripped of leading/trailing whitespace."""
        assert validate_query("  hello world  ") == "hello world"

    def test_validate_query_truncates_long_query(self):
        """Query should be truncated to MAX_QUERY_LENGTH."""
        long_query = "x" * 2000
        result = validate_query(long_query)
        assert len(result) == ContextValidator.MAX_QUERY_LENGTH

    def test_validate_query_rejects_empty(self):
        """Empty query should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_query("")

    def test_validate_query_rejects_whitespace_only(self):
        """Whitespace-only query should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_query("   ")

    def test_validate_query_rejects_none(self):
        """None query should raise ValueError."""
        with pytest.raises(ValueError):
            validate_query(None)

    # === Domain Validation Tests ===

    def test_validate_domain_lowercases(self):
        """Domain should be lowercased."""
        assert validate_domain("MyDomain") == "mydomain"

    def test_validate_domain_allows_hyphens(self):
        """Domain should allow hyphens."""
        assert validate_domain("my-domain") == "my-domain"

    def test_validate_domain_allows_underscores(self):
        """Domain should allow underscores."""
        assert validate_domain("my_domain") == "my_domain"

    def test_validate_domain_returns_empty_for_none(self):
        """None domain should return empty string."""
        assert validate_domain(None) == ""

    def test_validate_domain_returns_empty_for_empty(self):
        """Empty domain should return empty string."""
        assert validate_domain("") == ""

    def test_validate_domain_strips_whitespace(self):
        """Domain should be stripped of whitespace."""
        assert validate_domain("  domain  ") == "domain"

    def test_validate_domain_rejects_special_chars(self):
        """Domain with special characters should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid domain"):
            validate_domain("my@domain")

    # === Tags Validation Tests ===

    def test_validate_tags_lowercases(self):
        """Tags should be lowercased."""
        assert validate_tags(["TAG1", "Tag2"]) == ["tag1", "tag2"]

    def test_validate_tags_strips_whitespace(self):
        """Tags should be stripped of whitespace."""
        assert validate_tags(["  tag1  ", " tag2 "]) == ["tag1", "tag2"]

    def test_validate_tags_removes_empty(self):
        """Empty tags should be removed."""
        assert validate_tags(["tag1", "", "tag2", "   "]) == ["tag1", "tag2"]

    def test_validate_tags_returns_empty_for_none(self):
        """None tags should return empty list."""
        assert validate_tags(None) == []

    def test_validate_tags_returns_empty_for_empty(self):
        """Empty list should return empty list."""
        assert validate_tags([]) == []

    # === Limit Validation Tests ===

    def test_validate_limit_returns_default_for_none(self):
        """None limit should return default."""
        assert validate_limit(None) == ContextValidator.DEFAULT_LIMIT

    def test_validate_limit_returns_default_for_zero(self):
        """Zero limit should return default."""
        assert validate_limit(0) == ContextValidator.DEFAULT_LIMIT

    def test_validate_limit_returns_default_for_negative(self):
        """Negative limit should return default."""
        assert validate_limit(-5) == ContextValidator.DEFAULT_LIMIT

    def test_validate_limit_caps_at_max(self):
        """Limit should be capped at max_limit."""
        assert validate_limit(1000) == ContextValidator.MAX_LIMIT

    def test_validate_limit_accepts_valid(self):
        """Valid limit should be returned as-is."""
        assert validate_limit(50) == 50

    def test_validate_limit_uses_custom_max(self):
        """Custom max_limit should be respected."""
        assert validate_limit(1000, max_limit=50) == 50


class TestContextValidatorPositiveInt:
    """Tests for validate_positive_int method."""

    def test_returns_default_for_none(self):
        """None should return default."""
        assert ContextValidator.validate_positive_int(None, default=5) == 5

    def test_returns_default_for_negative(self):
        """Negative should return default."""
        assert ContextValidator.validate_positive_int(-1, default=5) == 5

    def test_returns_value_for_valid(self):
        """Valid positive int should be returned."""
        assert ContextValidator.validate_positive_int(10) == 10

    def test_caps_at_max(self):
        """Value should be capped at max_value."""
        assert ContextValidator.validate_positive_int(100, max_value=50) == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
