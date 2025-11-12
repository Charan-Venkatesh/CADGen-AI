# test_dxf_creation.py
import ezdxf
from ezdxf import colors

def create_test_plate():
    print("Creating DXF document...")
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()
    
    # Draw rectangle
    print("Drawing rectangle 200x100mm...")
    points = [(0, 0), (200, 0), (200, 100), (0, 100), (0, 0)]
    msp.add_lwpolyline(points, dxfattribs={'color': colors.RED})
    
    # Add 4 holes
    print("Adding 4 holes...")
    hole_positions = [(20, 20), (180, 20), (180, 80), (20, 80)]
    for pos in hole_positions:
        msp.add_circle(pos, radius=5, dxfattribs={'color': colors.BLUE})
    
    # Add text
    print("Adding text...")
    msp.add_text("TEST PLATE 200x100", dxfattribs={'height': 5}).set_placement((50, 45))
    
    # Save
    output_file = "data/examples/test_plate_001.dxf"
    doc.saveas(output_file)
    print(f"SUCCESS! DXF created: {output_file}")
    
    # Verify
    doc_verify = ezdxf.readfile(output_file)
    entity_count = len(list(doc_verify.modelspace()))
    print(f"Verification: {entity_count} entities (expected 6)")
    
    return entity_count == 6

if __name__ == "__main__":
    print("="*60)
    print("CADGen-AI - DXF Creation Test")
    print("="*60)
    success = create_test_plate()
    if success:
        print("ALL TESTS PASSED!")
    print("="*60)
