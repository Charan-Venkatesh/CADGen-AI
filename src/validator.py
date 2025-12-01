"""
src/validator.py - Schema validator for CAD parameters.

Uses jsonschema if available; otherwise performs conservative type checks.
"""
import logging

logger = logging.getLogger(__name__)

# CAD parameters JSON schema
CAD_PARAMS_SCHEMA = {
    "type": "object",
    "required": ["type"],
    "properties": {
        "type": {
            "type": "string",
            "enum": ["rectangular", "square", "flange", "l_bracket", "t_bracket", "triangular", "unknown"]
        },
        "width": {"type": "number", "minimum": 0},
        "height": {"type": "number", "minimum": 0},
        "outer_diameter": {"type": "number", "minimum": 0},
        "inner_diameter": {"type": "number", "minimum": 0},
        "hole_count": {"type": "integer", "minimum": 0},
        "hole_diameter": {"type": "number", "minimum": 0},
        "corner_offset": {"type": "number", "minimum": 0},
        "center_hole_diameter": {"type": "number", "minimum": 0},
        "pcd": {"type": "number", "minimum": 0},
        "fillet_radius": {"type": "number", "minimum": 0},
        "features": {"type": "array"}
    },
    "additionalProperties": True
}

# Valid shape types
VALID_TYPES = {"rectangular", "square", "flange", "l_bracket", "t_bracket", "triangular", "unknown"}


def _validate_with_jsonschema(params: dict) -> tuple[bool, list[str]]:
    """Validate params using jsonschema library."""
    import jsonschema

    errors = []
    try:
        jsonschema.validate(instance=params, schema=CAD_PARAMS_SCHEMA)
        return True, []
    except jsonschema.ValidationError as e:
        errors.append(str(e.message))
        return False, errors
    except jsonschema.SchemaError as e:
        errors.append(f"Schema error: {e.message}")
        return False, errors


def _validate_conservative(params: dict) -> tuple[bool, list[str]]:
    """Conservative type checks when jsonschema is not available."""
    errors = []

    # Check if params is a dict
    if not isinstance(params, dict):
        return False, ["params must be a dictionary"]

    # Check required 'type' field
    if "type" not in params:
        errors.append("Missing required field: 'type'")
    else:
        shape_type = params["type"]
        if not isinstance(shape_type, str):
            errors.append(f"Field 'type' must be a string, got {type(shape_type).__name__}")
        elif shape_type not in VALID_TYPES:
            errors.append(f"Invalid type '{shape_type}'. Must be one of: {', '.join(sorted(VALID_TYPES))}")

    # Check numeric fields
    numeric_fields = [
        "width", "height", "outer_diameter", "inner_diameter",
        "hole_diameter", "corner_offset", "center_hole_diameter",
        "pcd", "fillet_radius"
    ]
    for field in numeric_fields:
        if field in params:
            value = params[field]
            if not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' must be a number, got {type(value).__name__}")
            elif value < 0:
                errors.append(f"Field '{field}' must be non-negative, got {value}")

    # Check integer fields
    integer_fields = ["hole_count"]
    for field in integer_fields:
        if field in params:
            value = params[field]
            if not isinstance(value, int):
                errors.append(f"Field '{field}' must be an integer, got {type(value).__name__}")
            elif value < 0:
                errors.append(f"Field '{field}' must be non-negative, got {value}")

    # Check features array
    if "features" in params:
        if not isinstance(params["features"], list):
            errors.append(f"Field 'features' must be a list, got {type(params['features']).__name__}")

    return len(errors) == 0, errors


def validate_params(params: dict) -> tuple[bool, list[str]]:
    """
    Validate CAD parameters against the expected schema.

    Args:
        params: Dictionary containing CAD parameters.

    Returns:
        Tuple of (is_valid, errors) where:
        - is_valid: bool indicating if params pass validation
        - errors: list of validation error messages (empty if valid)
    """
    if params is None:
        return False, ["params cannot be None"]

    if not isinstance(params, dict):
        return False, [f"params must be a dictionary, got {type(params).__name__}"]

    # Check for error responses from previous parsing steps
    if "error" in params:
        return False, [f"params contains error: {params.get('error')}"]

    try:
        # Try jsonschema first
        import jsonschema  # noqa: F401
        return _validate_with_jsonschema(params)
    except ImportError:
        logger.debug("jsonschema not available, using conservative validation")
        return _validate_conservative(params)


if __name__ == "__main__":
    # Test harness
    logging.basicConfig(level=logging.DEBUG)

    test_cases = [
        # Valid cases
        {
            "name": "valid_rectangular",
            "params": {"type": "rectangular", "width": 200, "height": 100, "hole_count": 4},
            "expected_valid": True
        },
        {
            "name": "valid_flange",
            "params": {"type": "flange", "outer_diameter": 200, "inner_diameter": 100},
            "expected_valid": True
        },
        # Invalid cases
        {
            "name": "missing_type",
            "params": {"width": 200, "height": 100},
            "expected_valid": False
        },
        {
            "name": "wrong_type_string",
            "params": {"type": 123, "width": 200},
            "expected_valid": False
        },
        {
            "name": "invalid_shape_type",
            "params": {"type": "circle", "width": 200},
            "expected_valid": False
        },
        {
            "name": "negative_width",
            "params": {"type": "rectangular", "width": -100, "height": 100},
            "expected_valid": False
        },
        {
            "name": "error_response",
            "params": {"error": "parsing_failed"},
            "expected_valid": False
        }
    ]

    print("=" * 60)
    print("Validator Test Harness")
    print("=" * 60)

    passed = 0
    for tc in test_cases:
        is_valid, errors = validate_params(tc["params"])
        status = "PASS" if is_valid == tc["expected_valid"] else "FAIL"
        if status == "PASS":
            passed += 1
        print(f"\n{status}: {tc['name']}")
        print(f"  Expected valid: {tc['expected_valid']}, Got: {is_valid}")
        if errors:
            print(f"  Errors: {errors}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{len(test_cases)} tests passed")
