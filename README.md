# CADGen-AI

Natural Language to AutoCAD/DXF Generation System using LLM

## Project Goal
Convert engineering descriptions in plain English into ready-to-use AutoCAD DXF drawings automatically, reducing manual drafting time for standard 2D mechanical/structural parts.

## Timeline
- **Start Date:** November 12, 2025


## Technology Stack
- **Backend:** Python FastAPI
- **LLM:** OpenAI GPT-4 / HuggingFace CodeLlama
- **CAD Output:** ezdxf (Python DXF library)
- **Frontend:** Streamlit
- **Compute:** Camber Cloud
- **Development:** Camber Cloud Jupyter

## Success Criteria
- 70%+ accuracy on 15 standard 2D part test cases
- Complete end-to-end pipeline (input → LLM → DXF)
- Clean documentation and code
- Live demo capability

## Installation

```bash
# Install main dependencies
pip install -r requirements.txt

# Install development dependencies (for testing/linting)
pip install -r requirements-dev.txt
```

## CLI Usage

The CLI provides a command-line interface for extracting CAD parameters and generating DXF files.

### Basic Usage

```bash
# Extract parameters using fallback parser (no LLM required)
python -m src.cli --force-fallback "rectangular plate 200mm by 100mm with 4 holes"

# Extract parameters and generate DXF file
python -m src.cli --force-fallback --output-dxf output.dxf "rectangular plate 200mm by 100mm with 4 holes 10mm diameter at 20mm from corners"

# Save JSON output to file
python -m src.cli --force-fallback --output-json params.json "square plate 150mm by 150mm"

# Use LLM for extraction (requires model to be available)
python -m src.cli --use-llm "circular flange outer diameter 200mm inner diameter 100mm"
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--use-llm` | Use LLM for parameter extraction (requires model) |
| `--force-fallback` | Force use of rule-based parser (skip LLM) |
| `--output-json FILE` | Write JSON output to file |
| `--output-dxf FILE` | Generate DXF file from extracted parameters |
| `--no-validate` | Skip parameter validation |
| `-v, --verbose` | Enable verbose output |
| `--debug` | Enable debug output |

### Examples

```bash
# Square plate with center hole
python -m src.cli --force-fallback "square plate 150mm by 150mm with center hole 30mm diameter"

# Flange with bolt holes
python -m src.cli --force-fallback "circular flange outer diameter 200mm inner diameter 100mm with 8 bolt holes 15mm diameter on 150mm pitch circle"

# Generate both JSON and DXF
python -m src.cli --force-fallback --output-json params.json --output-dxf drawing.dxf "rectangular plate 200mm by 100mm"
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_validator.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## Linting

```bash
# Run flake8 linter
flake8 src/ tests/ --max-line-length=120
```

## Project Structure


