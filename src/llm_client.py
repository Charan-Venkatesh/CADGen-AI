"""
src/llm_client.py - Deterministic, validated LLM client for CAD parameter extraction.

Features:
- Deterministic generation (do_sample=False, temperature=0.0, top_k=1, top_p=1.0)
- Strict prompt instructing model to return exactly one JSON object
- Balanced brace extractor for JSON parsing
- Schema validation via validator.validate_params
- Fallback to rule-based parser if LLM fails
- Metadata in output (_source, raw_llm, validation_errors)
"""
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from src.validator import validate_params  # noqa: E402
from src.generator import EnhancedTemplateGenerator  # noqa: E402

# Default seed for reproducibility
DEFAULT_SEED = 42


def _extract_json_balanced(text: str) -> Optional[str]:
    """
    Extract the first JSON object from text using balanced brace matching.

    Args:
        text: Raw text potentially containing JSON

    Returns:
        JSON string if found, None otherwise
    """
    # Find first opening brace
    start = text.find('{')
    if start == -1:
        return None

    brace_count = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                return text[start:i + 1]

    return None


class LocalLLMClient:
    """
    Deterministic LLM client for CAD parameter extraction.

    Uses a local HuggingFace model with deterministic generation settings.
    Falls back to rule-based parser on validation failures.
    """

    def __init__(
        self,
        model_name: str = "codellama/CodeLlama-7b-Instruct-hf",
        seed: int = DEFAULT_SEED,
        max_new_tokens: int = 200,
        load_model: bool = True
    ):
        """
        Initialize the LLM client.

        Args:
            model_name: HuggingFace model identifier
            seed: Random seed for reproducibility
            max_new_tokens: Maximum tokens to generate
            load_model: If False, skip model loading (for testing)
        """
        self.model_name = model_name
        self.seed = seed
        self.max_new_tokens = max_new_tokens
        self.tokenizer = None
        self.model = None
        self._fallback_parser = EnhancedTemplateGenerator()

        if load_model:
            self._load_model()

    def _load_model(self):
        """Load the model and tokenizer."""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("transformers not available, LLM will not work")
            return

        if not TORCH_AVAILABLE:
            logger.warning("torch not available, LLM will not work")
            return

        logger.info(f"Loading model: {self.model_name}")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            logger.info("Model loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _build_prompt(self, description: str) -> str:
        """
        Build a strict prompt for CAD parameter extraction.

        Args:
            description: Natural language CAD description

        Returns:
            Formatted prompt string
        """
        return f"""You are a CAD parameter extraction system. Extract parameters from the description below.

IMPORTANT: Return EXACTLY ONE valid JSON object with no additional text, explanation, or examples.

Valid JSON keys:
- type: one of "rectangular", "square", "flange", "l_bracket", "t_bracket", "triangular"
- width: number in mm (for rectangular/square plates)
- height: number in mm (for rectangular/square plates)
- outer_diameter: number in mm (for flanges)
- inner_diameter: number in mm (for flanges)
- hole_count: integer number of holes
- hole_diameter: number in mm
- corner_offset: number in mm (distance from corners)
- center_hole_diameter: number in mm
- pcd: number in mm (pitch circle diameter)
- fillet_radius: number in mm

Description: {description}

JSON:"""

    def _generate(self, prompt: str) -> str:
        """
        Generate text from the model with deterministic settings.

        Args:
            prompt: Input prompt

        Returns:
            Generated text (only new tokens, prompt excluded)
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call _load_model() or initialize with load_model=True")

        # Set seed for reproducibility
        if TORCH_AVAILABLE:
            torch.manual_seed(self.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(self.seed)

        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt")
        if self.model.device.type != "cpu":
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        prompt_length = inputs["input_ids"].shape[1]

        # Generate with deterministic settings
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                temperature=0.0,
                top_k=1,
                top_p=1.0,
                pad_token_id=self.tokenizer.eos_token_id
            )

        # Decode only generated tokens (exclude prompt)
        generated_tokens = outputs[0][prompt_length:]
        result = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)

        return result

    def extract_parameters(self, description: str) -> dict:
        """
        Extract CAD parameters from a natural language description.

        Args:
            description: Natural language CAD description

        Returns:
            Dictionary with CAD parameters and metadata:
            - _source: 'llm' or 'fallback_parser'
            - raw_llm: Raw LLM output (only on debug/failure)
            - validation_errors: List of validation errors (if any)
        """
        result = {
            "_source": "fallback_parser",
            "validation_errors": []
        }

        # Try LLM extraction if model is available
        if self.model is not None and self.tokenizer is not None:
            prompt = self._build_prompt(description)

            try:
                raw_output = self._generate(prompt)
                logger.debug(f"Raw LLM output: {raw_output[:500]}")

                # Extract JSON from output
                json_str = _extract_json_balanced(raw_output)

                if json_str is None:
                    logger.warning("No JSON object found in LLM output")
                    result["raw_llm"] = raw_output[:500]
                    result["validation_errors"].append("No JSON object found in LLM output")
                else:
                    try:
                        params = json.loads(json_str)

                        # Validate parsed params
                        is_valid, errors = validate_params(params)

                        if is_valid:
                            # Success! Return LLM result
                            params["_source"] = "llm"
                            params["validation_errors"] = []
                            return params
                        else:
                            logger.warning(f"LLM output failed validation: {errors}")
                            result["raw_llm"] = raw_output[:500]
                            result["validation_errors"] = errors

                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON from LLM: {e}")
                        result["raw_llm"] = raw_output[:500]
                        result["validation_errors"].append(f"JSON decode error: {str(e)}")

            except Exception as e:
                logger.error(f"LLM extraction failed: {e}")
                result["validation_errors"].append(f"LLM error: {str(e)}")
        else:
            logger.info("Model not available, using fallback parser")

        # Fallback to rule-based parser
        logger.info("Falling back to rule-based parser")
        fallback_result = self._fallback_parser.parse_description(description)

        # Merge fallback result with metadata
        for key, value in fallback_result.items():
            if key not in ("_source", "validation_errors", "raw_llm"):
                result[key] = value

        return result


if __name__ == "__main__":
    # Deterministic test harness
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("=" * 60)
    print("LocalLLMClient Deterministic Test Harness")
    print("=" * 60)

    # Check if we should skip model loading (for CI environments)
    skip_model = os.environ.get("SKIP_MODEL_LOADING", "").lower() in ("1", "true", "yes")

    if skip_model:
        print("\nSKIP_MODEL_LOADING is set, testing with fallback parser only")
        client = LocalLLMClient(load_model=False)
    else:
        print("\nAttempting to load model (set SKIP_MODEL_LOADING=1 to skip)")
        try:
            client = LocalLLMClient()
        except Exception as e:
            print(f"Model loading failed: {e}")
            print("Continuing with fallback parser test...")
            client = LocalLLMClient(load_model=False)

    test_cases = [
        "rectangular plate 200mm by 100mm with 4 holes of 10mm diameter at 20mm from corners",
        "square plate 150mm by 150mm with center hole 30mm diameter",
        "circular flange outer diameter 200mm inner diameter 100mm with 8 bolt holes"
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"Test {i}: {test}")
        result = client.extract_parameters(test)
        print(f"Source: {result.get('_source', 'unknown')}")
        print(f"Result: {json.dumps(result, indent=2)}")

    print("\n" + "=" * 60)
    print("All tests complete!")
