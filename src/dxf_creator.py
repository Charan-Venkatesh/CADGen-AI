# src/dxf_creator.py
import ezdxf

class DXFCreator:
    def __init__(self):
        self.doc = None
        self.msp = None
    
    def create_new(self):
        self.doc = ezdxf.new(dxfversion='R2010')
        self.msp = self.doc.modelspace()
        return self
    
    def add_rectangle(self, width, height):
        points = [(0, 0), (width, 0), (width, height), (0, height), (0, 0)]
        self.msp.add_lwpolyline(points)
        return self
    
    def add_corner_holes(self, width, height, offset, radius):
        positions = [
            (offset, offset),
            (width - offset, offset),
            (width - offset, height - offset),
            (offset, height - offset)
        ]
        for pos in positions:
            self.msp.add_circle(pos, radius=radius)
        return self
    
    def save(self, filename):
        self.doc.saveas(filename)
        return filename
    
    def create_from_params(self, params, output_file):
        self.create_new()
        
        if 'width' in params and 'height' in params:
            self.add_rectangle(params['width'], params['height'])
        
        if 'hole_diameter' in params and 'corner_offset' in params:
            radius = params['hole_diameter'] / 2
            self.add_corner_holes(
                params['width'],
                params['height'],
                params['corner_offset'],
                radius
            )
        
        return self.save(output_file)

if __name__ == "__main__":
    creator = DXFCreator()
    params = {'width': 200, 'height': 100, 'hole_diameter': 10, 'corner_offset': 20}
    output = creator.create_from_params(params, 'test_output.dxf')
    print(f"Created: {output}")
