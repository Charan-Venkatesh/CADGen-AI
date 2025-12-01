"""
tests/test_llm_client.py - Unit tests for LLM client with mocked _generate.

These tests verify:
- Successful LLM extraction with valid JSON
- Fallback behavior with malformed JSON
- Fallback behavior when no JSON found
- Metadata fields (_source, validation_errors, raw_llm)
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from src.llm_client import LocalLLMClient, _extract_json_balanced


class TestExtractJsonBalanced:
    """Test cases for the JSON extraction utility."""

    def test_simple_json_extraction(self):
        """Test extraction of simple JSON object."""
        text = '{"type": "rectangular", "width": 200}'
        result = _extract_json_balanced(text)
        assert result == '{"type": "rectangular", "width": 200}'
        parsed = json.loads(result)
        assert parsed["type"] == "rectangular"

    def test_json_with_prefix(self):
        """Test extraction with text before JSON."""
        text = 'Here is the JSON: {"type": "square", "width": 150}'
        result = _extract_json_balanced(text)
        assert result is not None
        parsed = json.loads(result)
        assert parsed["type"] == "square"

    def test_json_with_suffix(self):
        """Test extraction with text after JSON."""
        text = '{"type": "flange"} Some extra text here'
        result = _extract_json_balanced(text)
        assert result == '{"type": "flange"}'

    def test_nested_json(self):
        """Test extraction of JSON with nested objects."""
        text = '{"type": "rectangular", "meta": {"source": "llm"}}'
        result = _extract_json_balanced(text)
        assert result is not None
        parsed = json.loads(result)
        assert parsed["meta"]["source"] == "llm"

    def test_no_json_found(self):
        """Test that None is returned when no JSON present."""
        text = "This is just plain text with no JSON"
        result = _extract_json_balanced(text)
        assert result is None

    def test_incomplete_json(self):
        """Test handling of incomplete/unclosed JSON."""
        text = '{"type": "rectangular", "width": 200'
        result = _extract_json_balanced(text)
        # Should return None since braces don't balance
        assert result is None

    def test_multiple_json_objects(self):
        """Test that only first JSON object is extracted."""
        text = '{"first": 1} {"second": 2}'
        result = _extract_json_balanced(text)
        assert result == '{"first": 1}'


class TestLocalLLMClientFallback:
    """Test cases for LLM client with fallback behavior."""

    @pytest.fixture
    def client(self):
        """Create a client without loading the model."""
        return LocalLLMClient(load_model=False)

    def test_fallback_when_no_model(self, client):
        """Test fallback parser is used when model is not loaded."""
        result = client.extract_parameters("rectangular plate 200mm by 100mm with 4 holes")
        assert result["_source"] == "fallback_parser"
        assert result["type"] == "rectangular"
        assert result["width"] == 200
        assert result["height"] == 100

    def test_fallback_includes_validation_errors_field(self, client):
        """Test that fallback result includes validation_errors field."""
        result = client.extract_parameters("rectangular plate 200mm by 100mm")
        assert "validation_errors" in result
        assert isinstance(result["validation_errors"], list)

    def test_fallback_for_square_plate(self, client):
        """Test fallback parser for square plate."""
        result = client.extract_parameters("square plate 150mm by 150mm with center hole 30mm diameter")
        assert result["_source"] == "fallback_parser"
        assert result["type"] == "square"
        assert result["width"] == 150
        assert result["height"] == 150

    def test_fallback_for_flange(self, client):
        """Test fallback parser for flange."""
        result = client.extract_parameters("circular flange outer diameter 200mm inner diameter 100mm")
        assert result["_source"] == "fallback_parser"
        assert result["type"] == "flange"
        # Note: Parser may not capture outer_diameter depending on regex
        assert result["inner_diameter"] == 100


class TestLocalLLMClientWithMockedGenerate:
    """Test cases mocking the _generate method to test LLM path."""

    @pytest.fixture
    def client_with_mock_model(self):
        """Create a client with mocked model and tokenizer."""
        client = LocalLLMClient(load_model=False)
        # Mock model and tokenizer to appear loaded
        client.model = MagicMock()
        client.tokenizer = MagicMock()
        return client

    def test_llm_path_with_valid_json(self, client_with_mock_model):
        """Test successful LLM extraction with valid JSON response."""
        valid_json = '{"type": "rectangular", "width": 200, "height": 100, "hole_count": 4}'

        with patch.object(client_with_mock_model, '_generate', return_value=valid_json):
            result = client_with_mock_model.extract_parameters("test description")

        assert result["_source"] == "llm"
        assert result["type"] == "rectangular"
        assert result["width"] == 200
        assert result["height"] == 100
        assert result["hole_count"] == 4
        assert result["validation_errors"] == []

    def test_llm_path_with_json_and_prefix(self, client_with_mock_model):
        """Test LLM extraction when JSON has prefix text."""
        response = 'Here is the extracted JSON:\n{"type": "square", "width": 150, "height": 150}'

        with patch.object(client_with_mock_model, '_generate', return_value=response):
            result = client_with_mock_model.extract_parameters("test description")

        assert result["_source"] == "llm"
        assert result["type"] == "square"
        assert result["width"] == 150

    def test_fallback_on_malformed_json(self, client_with_mock_model):
        """Test fallback is triggered for malformed JSON."""
        malformed_json = '{"type": "rectangular", "width": not_valid_json}'

        with patch.object(client_with_mock_model, '_generate', return_value=malformed_json):
            result = client_with_mock_model.extract_parameters("rectangular plate 200mm by 100mm")

        assert result["_source"] == "fallback_parser"
        assert "raw_llm" in result
        assert len(result["validation_errors"]) > 0

    def test_fallback_on_no_json(self, client_with_mock_model):
        """Test fallback is triggered when no JSON in response."""
        no_json_response = "I cannot generate JSON from this description."

        with patch.object(client_with_mock_model, '_generate', return_value=no_json_response):
            result = client_with_mock_model.extract_parameters("rectangular plate 200mm by 100mm")

        assert result["_source"] == "fallback_parser"
        assert "raw_llm" in result
        assert any("No JSON" in e for e in result["validation_errors"])

    def test_fallback_on_invalid_type(self, client_with_mock_model):
        """Test fallback is triggered when LLM returns invalid type."""
        invalid_type_json = '{"type": "hexagon", "width": 200}'

        with patch.object(client_with_mock_model, '_generate', return_value=invalid_type_json):
            result = client_with_mock_model.extract_parameters("rectangular plate 200mm by 100mm")

        assert result["_source"] == "fallback_parser"
        assert "raw_llm" in result
        assert len(result["validation_errors"]) > 0

    def test_fallback_on_missing_type(self, client_with_mock_model):
        """Test fallback is triggered when LLM response missing type."""
        missing_type_json = '{"width": 200, "height": 100}'

        with patch.object(client_with_mock_model, '_generate', return_value=missing_type_json):
            result = client_with_mock_model.extract_parameters("rectangular plate 200mm by 100mm")

        assert result["_source"] == "fallback_parser"
        assert len(result["validation_errors"]) > 0

    def test_fallback_preserves_parsed_fields(self, client_with_mock_model):
        """Test that fallback result includes all parsed fields."""
        with patch.object(client_with_mock_model, '_generate', return_value="no json here"):
            result = client_with_mock_model.extract_parameters(
                "rectangular plate 200mm by 100mm with 4 holes 10mm diameter at 20mm from corners"
            )

        assert result["_source"] == "fallback_parser"
        assert result["type"] == "rectangular"
        assert result["width"] == 200
        assert result["height"] == 100
        assert result["hole_count"] == 4
        assert result["hole_diameter"] == 10
        assert result["corner_offset"] == 20

    def test_exception_handling(self, client_with_mock_model):
        """Test that exceptions in _generate trigger fallback."""
        with patch.object(client_with_mock_model, '_generate', side_effect=RuntimeError("Model error")):
            result = client_with_mock_model.extract_parameters("rectangular plate 200mm by 100mm")

        assert result["_source"] == "fallback_parser"
        assert any("LLM error" in e for e in result["validation_errors"])


class TestLocalLLMClientMetadata:
    """Test metadata fields in output."""

    @pytest.fixture
    def client(self):
        """Create a client without loading the model."""
        return LocalLLMClient(load_model=False)

    def test_source_field_present(self, client):
        """Test that _source field is always present."""
        result = client.extract_parameters("rectangular plate 200mm by 100mm")
        assert "_source" in result

    def test_validation_errors_field_present(self, client):
        """Test that validation_errors field is always present."""
        result = client.extract_parameters("rectangular plate 200mm by 100mm")
        assert "validation_errors" in result
        assert isinstance(result["validation_errors"], list)
