from panda3d.core import VBase4
from panda3d.core import LineSegs

# stemlet_model = base.loader.load_model('models/smiley')
# stemlet_model.reparent_to(node)
# 
# stemlet_model.set_pos(0, 0, stemlet_length / 2.0)
# stemlet_model.set_sz(stemlet_length * 0.5)
# stemlet_model.set_sx(stemlet_diameter * 0.5)
# stemlet_model.set_sy(stemlet_diameter * 0.5)

# stemlet lineseg model

def line_art(stemlet_length, stemlet_diameter):
    ring_segs = 10
    ring_color = VBase4(0.7, 0.7, 0.7, 1)
    y_color = VBase4(1, 0, 0, 1)

    segs = LineSegs()
    segs.set_thickness(2.0)
    segs.set_color(1, 1, 1, 1)
    segs.move_to(0, 0, 0)
    segs.draw_to(0, 0, stemlet_length)

    # segs.set_color(ring_color)
    # for r in range(ring_segs):
    #     from_v = r / ring_segs * 2 * math.pi
    #     to_v = (r + 1) / ring_segs * 2 * math.pi
    #     segs.move_to(
    #         math.sin(from_v) * stemlet_diameter,
    #         math.cos(from_v) * stemlet_diameter,
    #         0,
    #     )
    #     segs.draw_to(
    #         math.sin(to_v) * stemlet_diameter,
    #         math.cos(to_v) * stemlet_diameter,
    #         0,
    #     )

    if y_color:
        segs.set_color(y_color)
        segs.move_to(0, 0, stemlet_length)
        segs.draw_to(0, stemlet_diameter, stemlet_length)
        
    return segs.create()
