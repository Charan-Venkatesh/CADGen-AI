from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json
import re

class LocalLLMClient:
    def __init__(self, model_name="codellama/CodeLlama-7b-Instruct-hf"):
        print(f"Loading model: {model_name}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        print("Model loaded successfully!")
    
    def extract_parameters(self, description):
        prompt = f"""Extract CAD parameters as JSON from this description:

Description: {description}

Return ONLY valid JSON with these keys:
- type: "rectangular", "square", or "flange"
- width: number in mm
- height: number in mm
- hole_count: number of holes
- hole_diameter: hole size in mm
- corner_offset: offset from corners in mm

JSON:"""
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=150,  # Shorter to avoid extra examples
            temperature=0.1,
            do_sample=True
        )
        
        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract FIRST JSON object only
        try:
            # Find first { after "JSON:"
            json_start = result.find('JSON:')
            if json_start != -1:
                json_start = result.find('{', json_start)
            else:
                json_start = result.find('{')
            
            if json_start == -1:
                raise ValueError("No JSON found")
            
            # Find matching closing brace
            brace_count = 0
            json_end = json_start
            for i in range(json_start, len(result)):
                if result[i] == '{':
                    brace_count += 1
                elif result[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            json_str = result[json_start:json_end]
            params = json.loads(json_str)
            return params
            
        except Exception as e:
            print(f"Warning: Could not parse JSON from LLM: {e}")
            print(f"Raw output: {result[:500]}")
            return {"error": "parsing_failed", "raw": result[:500]}

if __name__ == "__main__":
    print("="*60)
    print("Testing Local LLM Client")
    print("="*60)
    
    client = LocalLLMClient()
    
    test_cases = [
        "rectangular plate 200mm by 100mm with 4 holes of 10mm diameter at 20mm from corners",
        "square plate 150mm by 150mm with center hole 30mm diameter",
        "circular flange outer diameter 200mm inner diameter 100mm with 8 bolt holes"
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test}")
        result = client.extract_parameters(test)
        print(f"Result: {json.dumps(result, indent=2)}")
    
    print("\n" + "="*60)
    print("All tests complete!")
