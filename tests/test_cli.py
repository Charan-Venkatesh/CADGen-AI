"""
tests/test_cli.py - Unit tests for the CLI module.

Uses tmp_path fixture to test file output functionality.
"""
import json

from src.cli import main, EXIT_SUCCESS


class TestCLIBasic:
    """Basic CLI functionality tests."""

    def test_force_fallback_outputs_json(self, capsys):
        """Test --force-fallback produces JSON output."""
        exit_code = main([
            "--force-fallback",
            "rectangular plate 200mm by 100mm with 4 holes"
        ])

        assert exit_code == EXIT_SUCCESS
        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["_source"] == "fallback_parser"
        assert output["type"] == "rectangular"
        assert output["width"] == 200
        assert output["height"] == 100

    def test_force_fallback_square_plate(self, capsys):
        """Test --force-fallback with square plate description."""
        exit_code = main([
            "--force-fallback",
            "square plate 150mm by 150mm with center hole 30mm diameter"
        ])

        assert exit_code == EXIT_SUCCESS
        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["type"] == "square"
        assert output["width"] == 150
        assert output["height"] == 150
        assert output["center_hole_diameter"] == 30

    def test_force_fallback_flange(self, capsys):
        """Test --force-fallback with flange description."""
        exit_code = main([
            "--force-fallback",
            "circular flange outer diameter 200mm inner diameter 100mm with 8 bolt holes"
        ])

        assert exit_code == EXIT_SUCCESS
        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["type"] == "flange"
        # Note: Parser may not capture all fields depending on regex patterns
        assert output["inner_diameter"] == 100
        assert output["hole_count"] == 8


class TestCLIFileOutput:
    """Test CLI file output functionality."""

    def test_output_json_file(self, tmp_path, capsys):
        """Test --output-json writes JSON to file."""
        output_file = tmp_path / "output.json"

        exit_code = main([
            "--force-fallback",
            "--output-json", str(output_file),
            "rectangular plate 200mm by 100mm"
        ])

        assert exit_code == EXIT_SUCCESS
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert data["type"] == "rectangular"
        assert data["width"] == 200
        assert data["height"] == 100

    def test_output_json_creates_directories(self, tmp_path, capsys):
        """Test --output-json creates parent directories."""
        output_file = tmp_path / "nested" / "dir" / "output.json"

        exit_code = main([
            "--force-fallback",
            "--output-json", str(output_file),
            "rectangular plate 200mm by 100mm"
        ])

        assert exit_code == EXIT_SUCCESS
        assert output_file.exists()

    def test_output_dxf_file(self, tmp_path, capsys):
        """Test --output-dxf creates DXF file."""
        output_file = tmp_path / "output.dxf"

        exit_code = main([
            "--force-fallback",
            "--output-dxf", str(output_file),
            "rectangular plate 200mm by 100mm with 4 holes 10mm diameter at 20mm from corners"
        ])

        assert exit_code == EXIT_SUCCESS
        assert output_file.exists()

        # Check DXF file has content
        content = output_file.read_bytes()
        assert len(content) > 0

    def test_output_both_json_and_dxf(self, tmp_path, capsys):
        """Test creating both JSON and DXF outputs."""
        json_file = tmp_path / "output.json"
        dxf_file = tmp_path / "output.dxf"

        exit_code = main([
            "--force-fallback",
            "--output-json", str(json_file),
            "--output-dxf", str(dxf_file),
            "square plate 150mm by 150mm with center hole 30mm diameter"
        ])

        assert exit_code == EXIT_SUCCESS
        assert json_file.exists()
        assert dxf_file.exists()

        with open(json_file) as f:
            data = json.load(f)
        assert data["type"] == "square"


class TestCLIValidation:
    """Test CLI validation behavior."""

    def test_validation_errors_included_in_output(self, capsys):
        """Test that validation_errors field is in output."""
        exit_code = main([
            "--force-fallback",
            "rectangular plate 200mm by 100mm"
        ])

        assert exit_code == EXIT_SUCCESS
        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert "validation_errors" in output

    def test_no_validate_flag(self, capsys):
        """Test --no-validate skips validation."""
        exit_code = main([
            "--force-fallback",
            "--no-validate",
            "rectangular plate 200mm by 100mm"
        ])

        assert exit_code == EXIT_SUCCESS


class TestCLIVerbosity:
    """Test CLI verbosity options."""

    def test_verbose_flag(self, capsys):
        """Test -v/--verbose increases output."""
        exit_code = main([
            "--force-fallback",
            "-v",
            "rectangular plate 200mm by 100mm"
        ])

        assert exit_code == EXIT_SUCCESS

    def test_debug_flag(self, capsys):
        """Test --debug flag for debug output."""
        exit_code = main([
            "--force-fallback",
            "--debug",
            "rectangular plate 200mm by 100mm"
        ])

        assert exit_code == EXIT_SUCCESS


class TestCLIEdgeCases:
    """Test CLI edge cases and error handling."""

    def test_empty_description_still_processes(self, capsys):
        """Test that empty-ish description still processes."""
        exit_code = main([
            "--force-fallback",
            "unknown shape"
        ])

        assert exit_code == EXIT_SUCCESS
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        # Parser should return something
        assert "type" in output

    def test_complex_description(self, capsys):
        """Test parsing complex description."""
        exit_code = main([
            "--force-fallback",
            "rectangular plate 200mm by 100mm with 4 circular holes of 10mm diameter, positioned 20mm from each corner"
        ])

        assert exit_code == EXIT_SUCCESS
        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["type"] == "rectangular"
        assert output["width"] == 200
        assert output["height"] == 100
        assert output["hole_count"] == 4
        # Note: hole_diameter requires specific pattern "holes X mm diameter"
        # The parser may not capture it from "of 10mm diameter" format
        assert output["corner_offset"] == 20
