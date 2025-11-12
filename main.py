# main.py - Enhanced pipeline
from src.generator import EnhancedTemplateGenerator
from src.dxf_creator import EnhancedDXFCreator
import json

def process_test_case(test_case, output_dir="data/examples"):
    """Process a single test case"""
    tc_id = test_case['id']
    description = test_case['description']
    
    print(f"\n{'='*60}")
    print(f"Test Case {tc_id}: {test_case['category']}")
    print(f"Description: {description}")
    
    # Parse
    gen = EnhancedTemplateGenerator()
    params = gen.parse_description(description)
    print(f"Parsed: {params}")
    
    # Create DXF
    try:
        creator = EnhancedDXFCreator()
        output_file = f"{output_dir}/test_case_{tc_id:03d}.dxf"
        result = creator.create_from_params(params, output_file)
        print(f"✅ Created: {result}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def process_all_test_cases():
    """Process all test cases"""
    with open('data/test_cases.json', 'r') as f:
        data = json.load(f)
    
    print("="*60)
    print("CADGen-AI - Processing All Test Cases")
    print("="*60)
    
    success_count = 0
    total_count = len(data['test_cases'])
    
    for tc in data['test_cases']:
        if process_test_case(tc):
            success_count += 1
    
    print("\n" + "="*60)
    print(f"Results: {success_count}/{total_count} ({success_count*100//total_count}%) successful")
    print("="*60)
    
    return success_count, total_count

if __name__ == "__main__":
    success, total = process_all_test_cases()
    
    if success >= total * 0.7:  # 70% threshold
        print("\n🎉 SUCCESS! Pipeline meets 70% accuracy threshold!")
    else:
        print(f"\n⚠️  Need improvement: {success}/{total} = {success*100//total}%")
