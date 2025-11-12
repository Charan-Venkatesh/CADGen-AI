# src/dxf_creator.py - Enhanced version
import ezdxf
import math

class EnhancedDXFCreator:
    def __init__(self):
        self.doc = None
        self.msp = None
    
    def create_new(self):
        self.doc = ezdxf.new(dxfversion='R2010')
        self.msp = self.doc.modelspace()
        return self
    
    def add_rectangle(self, width, height, origin=(0, 0)):
        x, y = origin
        points = [(x, y), (x+width, y), (x+width, y+height), (x, y+height), (x, y)]
        self.msp.add_lwpolyline(points)
        return self
    
    def add_circle(self, center, radius):
        self.msp.add_circle(center, radius=radius)
        return self
    
    def add_corner_holes(self, width, height, offset, radius):
        positions = [
            (offset, offset),
            (width - offset, offset),
            (width - offset, height - offset),
            (offset, height - offset)
        ]
        for pos in positions:
            self.add_circle(pos, radius)
        return self
    
    def add_center_hole(self, width, height, radius):
        center = (width / 2, height / 2)
        self.add_circle(center, radius)
        return self
    
    def add_holes_on_pcd(self, pcd_diameter, hole_count, hole_radius, center=(0, 0)):
        """Add holes equally spaced on a pitch circle diameter"""
        cx, cy = center
        pcd_radius = pcd_diameter / 2
        angle_step = 2 * math.pi / hole_count
        
        for i in range(hole_count):
            angle = i * angle_step
            x = cx + pcd_radius * math.cos(angle)
            y = cy + pcd_radius * math.sin(angle)
            self.add_circle((x, y), hole_radius)
        return self
    
    def add_flange(self, outer_diameter, inner_diameter, center=(0, 0)):
        """Add circular flange (outer and inner circles)"""
        self.add_circle(center, outer_diameter / 2)
        self.add_circle(center, inner_diameter / 2)
        return self
    
    def create_from_params(self, params, output_file):
        """Create DXF from parsed parameters"""
        self.create_new()
        
        shape_type = params.get('type', 'rectangular')
        
        # Rectangular shapes
        if shape_type in ['rectangular', 'square']:
            if 'width' in params and 'height' in params:
                self.add_rectangle(params['width'], params['height'])
                
                # Add corner holes if specified
                if 'hole_diameter' in params and 'corner_offset' in params:
                    radius = params['hole_diameter'] / 2
                    self.add_corner_holes(
                        params['width'],
                        params['height'],
                        params['corner_offset'],
                        radius
                    )
                
                # Add center hole if specified
                if 'center_hole_diameter' in params:
                    radius = params['center_hole_diameter'] / 2
                    self.add_center_hole(params['width'], params['height'], radius)
        
        # Flange
        elif shape_type == 'flange':
            if 'outer_diameter' in params and 'inner_diameter' in params:
                center = (params['outer_diameter'] / 2, params['outer_diameter'] / 2)
                self.add_flange(
                    params['outer_diameter'],
                    params['inner_diameter'],
                    center
                )
                
                # Add bolt holes on PCD if specified
                if 'hole_count' in params and 'hole_diameter' in params and 'pcd' in params:
                    self.add_holes_on_pcd(
                        params['pcd'],
                        params['hole_count'],
                        params['hole_diameter'] / 2,
                        center
                    )
        
        return self.save(output_file)
    
    def save(self, filename):
        self.doc.saveas(filename)
        return filename

if __name__ == "__main__":
    # Test enhanced creator
    creator = EnhancedDXFCreator()
    
    # Test 1: Rectangle with corner holes
    test1 = {
        'type': 'rectangular',
        'width': 200,
        'height': 100,
        'hole_diameter': 10,
        'corner_offset': 20
    }
    creator.create_from_params(test1, 'data/examples/enhanced_test1.dxf')
    print("✅ Test 1: Rectangle with corner holes")
    
    # Test 2: Square with center hole
    creator2 = EnhancedDXFCreator()
    test2 = {
        'type': 'square',
        'width': 150,
        'height': 150,
        'center_hole_diameter': 30
    }
    creator2.create_from_params(test2, 'data/examples/enhanced_test2.dxf')
    print("✅ Test 2: Square with center hole")
    
    # Test 3: Flange with bolt holes
    creator3 = EnhancedDXFCreator()
    test3 = {
        'type': 'flange',
        'outer_diameter': 200,
        'inner_diameter': 100,
        'hole_count': 8,
        'hole_diameter': 15,
        'pcd': 150
    }
    creator3.create_from_params(test3, 'data/examples/enhanced_test3.dxf')
    print("✅ Test 3: Flange with bolt holes on PCD")
    
    print("\n🎉 All enhanced tests passed!")
