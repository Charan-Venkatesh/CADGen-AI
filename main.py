# main.py
from src.generator import SimpleTemplateGenerator
from src.dxf_creator import DXFCreator
import json

def process(description, output_file="output.dxf"):
    print(f"Input: {description}")
    
    # Parse
    gen = SimpleTemplateGenerator()
    params = gen.parse_description(description)
    print(f"Parsed: {params}")
    
    # Create DXF
    creator = DXFCreator()
    result = creator.create_from_params(params, output_file)
    print(f"Created: {result}")
    
    return result

if __name__ == "__main__":
    # Test
    desc = "rectangular plate 200mm by 100mm with 4 circular holes of 10mm diameter, positioned 20mm from each corner"
    result = process(desc, "data/examples/test_case_001.dxf")
    print(f"\nSUCCESS! Pipeline working: {result}")
