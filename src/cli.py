#!/usr/bin/env python3
"""
src/cli.py - CLI wrapper for CAD parameter extraction and DXF generation.

Usage:
    python -m src.cli "rectangular plate 200mm by 100mm with 4 holes"
    python -m src.cli --use-llm "rectangular plate 200mm by 100mm with 4 holes"
    python -m src.cli --force-fallback "rectangular plate 200mm by 100mm with 4 holes"
    python -m src.cli --output-dxf output.dxf "rectangular plate 200mm by 100mm"
"""
import argparse
import json
import logging
import sys
from pathlib import Path

from src.generator import EnhancedTemplateGenerator
from src.dxf_creator import EnhancedDXFCreator
from src.validator import validate_params

logger = logging.getLogger(__name__)

# Exit codes
EXIT_SUCCESS = 0
EXIT_PARSE_ERROR = 1
EXIT_VALIDATION_ERROR = 2
EXIT_DXF_ERROR = 3
EXIT_GENERAL_ERROR = 4


def setup_logging(verbose: bool = False, debug: bool = False) -> None:
    """Configure logging based on verbosity level."""
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def extract_with_llm(description: str) -> dict:
    """Extract parameters using LLM client."""
    from src.llm_client import LocalLLMClient
    client = LocalLLMClient()
    return client.extract_parameters(description)


def extract_with_fallback(description: str) -> dict:
    """Extract parameters using rule-based parser only."""
    parser = EnhancedTemplateGenerator()
    result = parser.parse_description(description)
    result["_source"] = "fallback_parser"
    result["validation_errors"] = []
    return result


def create_dxf(params: dict, output_path: str) -> str:
    """Create DXF file from parameters."""
    creator = EnhancedDXFCreator()
    return creator.create_from_params(params, output_path)


def main(argv=None) -> int:
    """
    Main CLI entry point.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Extract CAD parameters from natural language and optionally generate DXF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli "rectangular plate 200mm by 100mm with 4 holes"
  python -m src.cli --use-llm "rectangular plate 200mm by 100mm"
  python -m src.cli --force-fallback --output-dxf out.dxf "square plate 150mm"
  python -m src.cli --output-json params.json "circular flange 200mm"
        """
    )

    parser.add_argument(
        "description",
        type=str,
        help="Natural language CAD description"
    )

    extraction_group = parser.add_mutually_exclusive_group()
    extraction_group.add_argument(
        "--use-llm",
        action="store_true",
        help="Use LLM for extraction (default if available)"
    )
    extraction_group.add_argument(
        "--force-fallback",
        action="store_true",
        help="Force use of rule-based parser (skip LLM)"
    )

    parser.add_argument(
        "--output-json",
        type=str,
        metavar="FILE",
        help="Write JSON output to file"
    )
    parser.add_argument(
        "--output-dxf",
        type=str,
        metavar="FILE",
        help="Generate DXF file from extracted parameters"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip parameter validation"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )

    args = parser.parse_args(argv)

    setup_logging(verbose=args.verbose, debug=args.debug)

    try:
        # Extract parameters
        logger.info(f"Processing description: {args.description}")

        if args.force_fallback:
            logger.info("Using fallback parser (forced)")
            params = extract_with_fallback(args.description)
        elif args.use_llm:
            logger.info("Using LLM extraction")
            params = extract_with_llm(args.description)
        else:
            # Default: try LLM, fallback to rule-based
            try:
                params = extract_with_llm(args.description)
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}, using fallback")
                params = extract_with_fallback(args.description)

        # Validate if requested
        if not args.no_validate:
            is_valid, errors = validate_params(params)
            if not is_valid:
                logger.error(f"Validation errors: {errors}")
                params["validation_errors"] = errors
                # Don't fail entirely - still output the params

        # Output JSON
        json_output = json.dumps(params, indent=2)

        if args.output_json:
            output_path = Path(args.output_json)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json_output)
            logger.info(f"JSON written to: {args.output_json}")
        else:
            print(json_output)

        # Generate DXF if requested
        if args.output_dxf:
            try:
                dxf_path = Path(args.output_dxf)
                dxf_path.parent.mkdir(parents=True, exist_ok=True)
                result = create_dxf(params, str(dxf_path))
                logger.info(f"DXF created: {result}")
                print(f"DXF file created: {result}", file=sys.stderr)
            except Exception as e:
                logger.error(f"DXF creation failed: {e}")
                print(f"Error creating DXF: {e}", file=sys.stderr)
                return EXIT_DXF_ERROR

        # Determine exit code based on source
        source = params.get("_source", "unknown")
        if source == "llm":
            logger.info("Extraction completed via LLM")
        else:
            logger.info("Extraction completed via fallback parser")

        return EXIT_SUCCESS

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return EXIT_GENERAL_ERROR


if __name__ == "__main__":
    sys.exit(main())
