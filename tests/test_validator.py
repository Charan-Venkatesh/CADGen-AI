"""
tests/test_validator.py - Unit tests for the validator module.
"""
from src.validator import validate_params, VALID_TYPES


class TestValidateParams:
    """Test cases for validate_params function."""

    def test_valid_rectangular_params(self):
        """Test validation of valid rectangular plate parameters."""
        params = {
            "type": "rectangular",
            "width": 200,
            "height": 100,
            "hole_count": 4,
            "hole_diameter": 10,
            "corner_offset": 20
        }
        is_valid, errors = validate_params(params)
        assert is_valid is True
        assert errors == []

    def test_valid_square_params(self):
        """Test validation of valid square plate parameters."""
        params = {
            "type": "square",
            "width": 150,
            "height": 150,
            "center_hole_diameter": 30
        }
        is_valid, errors = validate_params(params)
        assert is_valid is True
        assert errors == []

    def test_valid_flange_params(self):
        """Test validation of valid flange parameters."""
        params = {
            "type": "flange",
            "outer_diameter": 200,
            "inner_diameter": 100,
            "hole_count": 8,
            "hole_diameter": 15,
            "pcd": 150
        }
        is_valid, errors = validate_params(params)
        assert is_valid is True
        assert errors == []

    def test_valid_minimal_params(self):
        """Test validation with only required type field."""
        params = {"type": "rectangular"}
        is_valid, errors = validate_params(params)
        assert is_valid is True
        assert errors == []

    def test_valid_unknown_type(self):
        """Test validation with unknown type (allowed in schema)."""
        params = {"type": "unknown", "features": []}
        is_valid, errors = validate_params(params)
        assert is_valid is True
        assert errors == []

    def test_missing_type_field(self):
        """Test validation fails when type is missing."""
        params = {"width": 200, "height": 100}
        is_valid, errors = validate_params(params)
        assert is_valid is False
        assert len(errors) > 0
        # Check error mentions 'type'
        assert any("type" in e.lower() for e in errors)

    def test_invalid_type_value(self):
        """Test validation fails for invalid type value."""
        params = {"type": "circle"}  # Not a valid type
        is_valid, errors = validate_params(params)
        assert is_valid is False
        assert len(errors) > 0

    def test_wrong_type_for_type_field(self):
        """Test validation fails when type is not a string."""
        params = {"type": 123}
        is_valid, errors = validate_params(params)
        assert is_valid is False
        assert len(errors) > 0

    def test_negative_width(self):
        """Test validation fails for negative width."""
        params = {"type": "rectangular", "width": -100, "height": 100}
        is_valid, errors = validate_params(params)
        assert is_valid is False
        assert len(errors) > 0

    def test_negative_hole_count(self):
        """Test validation fails for negative hole_count."""
        params = {"type": "rectangular", "hole_count": -4}
        is_valid, errors = validate_params(params)
        assert is_valid is False
        assert len(errors) > 0

    def test_wrong_type_for_numeric_field(self):
        """Test validation fails when numeric field is string."""
        params = {"type": "rectangular", "width": "two hundred"}
        is_valid, errors = validate_params(params)
        assert is_valid is False
        assert len(errors) > 0

    def test_error_in_params(self):
        """Test validation fails when params contain error key."""
        params = {"error": "parsing_failed", "raw": "some output"}
        is_valid, errors = validate_params(params)
        assert is_valid is False
        assert any("error" in e.lower() for e in errors)

    def test_none_params(self):
        """Test validation fails for None params."""
        is_valid, errors = validate_params(None)
        assert is_valid is False
        assert len(errors) > 0

    def test_non_dict_params(self):
        """Test validation fails for non-dict params."""
        is_valid, errors = validate_params("not a dict")
        assert is_valid is False
        assert len(errors) > 0

    def test_float_dimensions(self):
        """Test validation accepts float dimensions."""
        params = {"type": "rectangular", "width": 200.5, "height": 100.25}
        is_valid, errors = validate_params(params)
        assert is_valid is True
        assert errors == []

    def test_features_array(self):
        """Test validation with features array."""
        params = {"type": "rectangular", "features": ["slot", "fillet"]}
        is_valid, errors = validate_params(params)
        assert is_valid is True
        assert errors == []

    def test_features_wrong_type(self):
        """Test validation fails when features is not an array."""
        params = {"type": "rectangular", "features": "slot"}
        is_valid, errors = validate_params(params)
        assert is_valid is False
        assert len(errors) > 0


class TestValidTypes:
    """Test cases for VALID_TYPES constant."""

    def test_all_documented_types_valid(self):
        """Test that all documented types are in VALID_TYPES."""
        expected = {"rectangular", "square", "flange", "l_bracket", "t_bracket", "triangular", "unknown"}
        assert VALID_TYPES == expected

    def test_each_type_validates(self):
        """Test that each valid type passes validation."""
        for shape_type in VALID_TYPES:
            params = {"type": shape_type}
            is_valid, errors = validate_params(params)
            assert is_valid is True, f"Type '{shape_type}' should be valid"
