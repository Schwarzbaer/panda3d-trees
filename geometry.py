import math

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

def line_art(sd, stemlet_length, stemlet_diameter, rest_segments, style):
    segs = LineSegs()
    segs.set_thickness(2.0)
    if style.stem:
        segs.set_color(style.stem)
        segs.move_to(0, 0, 0)
        segs.draw_to(0, 0, stemlet_length)

    # Ring around base
    if style.ring:
        # Segment base ring
        segs.set_color(style.ring)
        for r in range(style.ring_segs):
            from_v = r / style.ring_segs * 2 * math.pi
            to_v = (r + 1) / style.ring_segs * 2 * math.pi
            segs.move_to(
                math.sin(from_v) * stemlet_diameter,
                math.cos(from_v) * stemlet_diameter,
                0,
            )
            segs.draw_to(
                math.sin(to_v) * stemlet_diameter,
                math.cos(to_v) * stemlet_diameter,
                0,
            )

        # Endcap ring
        if rest_segments == 1:
            for r in range(style.ring_segs):
                from_v = r / style.ring_segs * 2 * math.pi
                to_v = (r + 1) / style.ring_segs * 2 * math.pi
                segs.move_to(
                    math.sin(from_v) * stemlet_diameter,
                    math.cos(from_v) * stemlet_diameter,
                    stemlet_length,
                )
                segs.draw_to(
                    math.sin(to_v) * stemlet_diameter,
                    math.cos(to_v) * stemlet_diameter,
                    stemlet_length,
                )

    # Bark
    if style.bark:
        segs.set_color(style.bark)
        for r in range(style.ring_segs):
            lobing = 1 + math.sin(2 * math.pi * sd.lobes * r / style.ring_segs)
            v = r / style.ring_segs * 2 * math.pi
            segs.move_to(
                math.sin(v) * stemlet_diameter * lobing,
                math.cos(v) * stemlet_diameter * lobing,
                0,
            )
            segs.draw_to(
                math.sin(v) * stemlet_diameter * lobing,
                math.cos(v) * stemlet_diameter * lobing,
                stemlet_length,
            )

    # x/y indicators
    if style.xyz_at_top:
        indicator_z = stemlet_length
    else:
        indicator_z = 0.0
    if style.x:
        segs.set_color(style.x)
        segs.move_to(0, 0, indicator_z)
        segs.draw_to(stemlet_diameter, 0, indicator_z)
    if style.y:
        segs.set_color(style.y)
        segs.move_to(0, 0, indicator_z)
        segs.draw_to(0, stemlet_diameter, indicator_z)
        
    return segs.create()
