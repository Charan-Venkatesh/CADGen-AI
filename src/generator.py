# src/generator.py - Enhanced version
import re
import json

class EnhancedTemplateGenerator:
    def __init__(self):
        self.patterns = {
            # Dimensions
            'rectangle': r'rectangular?\s+(?:plate|bracket|frame)?\s*(\d+)(?:mm)?\s*(?:by|x)\s*(\d+)(?:mm)?',
            'square': r'square\s+(?:plate|bracket)?\s*(\d+)(?:mm)?',
            'circular': r'(?:circular|circle)\s+(?:outer\s+)?diameter\s+(\d+)(?:mm)?',
            'inner_diameter': r'inner\s+diameter\s+(\d+)(?:mm)?',
            
            # Holes
            'hole_count': r'(\d+)\s+(?:circular\s+)?(?:bolt\s+)?holes?',
            'hole_diameter': r'holes?\s+(\d+)(?:mm)?\s+diameter',
            'corner_offset': r'(\d+)(?:mm)?\s+(?:from|offset|at)\s+(?:each\s+)?corners?',
            'pcd': r'(\d+)(?:mm)?\s+(?:pitch\s+circle|PCD)',
            'center_hole': r'center\s+hole\s+(\d+)(?:mm)?\s+diameter',
            
            # Shapes
            'l_bracket': r'L-shaped',
            't_bracket': r'T-shaped',
            'triangular': r'triangular',
            'fillet': r'(\d+)(?:mm)?\s+radius\s+fillet',
            
            # Cutouts
            'slot': r'slot\s+(\d+)(?:mm)?\s+by\s+(\d+)(?:mm)?',
            'cutout': r'cutout\s+(\d+)(?:mm)?\s+(?:by|x|diameter)\s+(\d+)?(?:mm)?'
        }
    
    def parse_description(self, description):
        desc = description.lower()
        result = {'type': 'unknown', 'features': []}
        
        # Detect shape type
        if re.search(self.patterns['l_bracket'], desc):
            result['type'] = 'l_bracket'
        elif re.search(self.patterns['t_bracket'], desc):
            result['type'] = 't_bracket'
        elif re.search(self.patterns['triangular'], desc):
            result['type'] = 'triangular'
        elif 'flange' in desc:
            result['type'] = 'flange'
        elif 'square' in desc:
            result['type'] = 'square'
        else:
            result['type'] = 'rectangular'
        
        # Parse dimensions
        if result['type'] == 'rectangular' or result['type'] in ['l_bracket', 't_bracket']:
            rect = re.search(self.patterns['rectangle'], desc)
            if rect:
                result['width'] = int(rect.group(1))
                result['height'] = int(rect.group(2))
        
        if result['type'] == 'square':
            square = re.search(self.patterns['square'], desc)
            if square:
                result['width'] = result['height'] = int(square.group(1))
        
        if result['type'] == 'flange':
            outer = re.search(self.patterns['circular'], desc)
            inner = re.search(self.patterns['inner_diameter'], desc)
            if outer:
                result['outer_diameter'] = int(outer.group(1))
            if inner:
                result['inner_diameter'] = int(inner.group(1))
        
        # Parse holes
        holes = re.search(self.patterns['hole_count'], desc)
        if holes:
            result['hole_count'] = int(holes.group(1))
        
        diameter = re.search(self.patterns['hole_diameter'], desc)
        if diameter:
            result['hole_diameter'] = int(diameter.group(1))
        
        # Center hole
        center = re.search(self.patterns['center_hole'], desc)
        if center:
            result['center_hole_diameter'] = int(center.group(1))
        
        # Offset
        offset = re.search(self.patterns['corner_offset'], desc)
        if offset:
            result['corner_offset'] = int(offset.group(1))
        
        # PCD
        pcd = re.search(self.patterns['pcd'], desc)
        if pcd:
            result['pcd'] = int(pcd.group(1))
        
        # Fillet
        fillet = re.search(self.patterns['fillet'], desc)
        if fillet:
            result['fillet_radius'] = int(fillet.group(1))
        
        return result
    
    def test_parser(self, test_cases_file='data/test_cases.json'):
        """Test parser on all test cases"""
        with open(test_cases_file, 'r') as f:
            data = json.load(f)
        
        results = []
        for tc in data['test_cases']:
            parsed = self.parse_description(tc['description'])
            results.append({
                'id': tc['id'],
                'category': tc['category'],
                'parsed': parsed
            })
        
        return results

if __name__ == "__main__":
    gen = EnhancedTemplateGenerator()
    
    # Test on all cases
    print("Testing parser on all 20 test cases...")
    print("="*60)
    
    results = gen.test_parser()
    success_count = 0
    
    for r in results:
        print(f"\nTest Case {r['id']} ({r['category']}):")
        print(f"  Parsed: {r['parsed']}")
        if 'width' in r['parsed'] or 'outer_diameter' in r['parsed']:
            success_count += 1
            print("  ✅ Successfully parsed dimensions")
        else:
            print("  ⚠️  Missing dimensions")
    
    print("\n" + "="*60)
    print(f"Success rate: {success_count}/20 ({success_count*5}%)")
