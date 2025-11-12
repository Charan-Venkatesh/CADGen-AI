# src/generator.py
import re

class SimpleTemplateGenerator:
    def __init__(self):
        self.patterns = {
            'rectangle': r'(\d+)(?:mm)?\s*(?:by|x)\s*(\d+)(?:mm)?',
            'holes': r'(\d+)\s*(?:circular\s+)?holes?',
            'hole_diameter': r'(\d+)(?:mm)?\s+diameter',
            'corner_offset': r'(\d+)(?:mm)?\s+from\s+(?:each\s+)?corner'
        }
    
    def parse_description(self, description):
        desc = description.lower()
        result = {}
        
        # Parse dimensions
        rect = re.search(self.patterns['rectangle'], desc)
        if rect:
            result['width'] = int(rect.group(1))
            result['height'] = int(rect.group(2))
        
        # Parse holes
        holes = re.search(self.patterns['holes'], desc)
        if holes:
            result['hole_count'] = int(holes.group(1))
        
        # Parse hole diameter
        diameter = re.search(self.patterns['hole_diameter'], desc)
        if diameter:
            result['hole_diameter'] = int(diameter.group(1))
        
        # Parse offset
        offset = re.search(self.patterns['corner_offset'], desc)
        if offset:
            result['corner_offset'] = int(offset.group(1))
        
        return result

if __name__ == "__main__":
    gen = SimpleTemplateGenerator()
    test = "rectangular plate 200mm by 100mm with 4 circular holes of 10mm diameter, positioned 20mm from each corner"
    print("Input:", test)
    print("Parsed:", gen.parse_description(test))
