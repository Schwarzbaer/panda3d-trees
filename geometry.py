import math
import random

from panda3d.core import Vec3
from panda3d.core import Vec4
from panda3d.core import VBase4
from panda3d.core import LineSegs
from panda3d.core import GeomVertexFormat
from panda3d.core import GeomVertexData
from panda3d.core import GeomVertexWriter
from panda3d.core import GeomTriangles
from panda3d.core import Geom
from panda3d.core import GeomNode
from panda3d.core import NodePath

# stemlet_model = base.loader.load_model('models/smiley')
# stemlet_model.reparent_to(node)
# 
# stemlet_model.set_pos(0, 0, stemlet_length / 2.0)
# stemlet_model.set_sz(stemlet_length * 0.5)
# stemlet_model.set_sx(stemlet_diameter * 0.5)
# stemlet_model.set_sy(stemlet_diameter * 0.5)

# stemlet lineseg model


def skin(sheet, style):
    line_art(sheet, style)
    for child in sheet.continuations:
        skin(child, style)
    for child in sheet.children:
        skin(child, style)

def line_art(sheet, style):
    node = sheet.node
    stemlet_length = sheet.segment_length
    stemlet_diameter = sheet.segment_diameter
    rest_segments = sheet.rest_segments
    
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
            lobing = 1 + math.sin(2 * math.pi * sheet.stem_definition.lobes * r / style.ring_segs)
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
        
    node.attach_new_node(segs.create())

    for child in sheet.stem_continuations:
        line_art(child, style)
    for child in sheet.branch_children:
        line_art(child, style)


def trimesh(stem, circle_segments=10):
    # What verte ID does each segment start at?
    current_vertex_index = 0
    segments = [stem]
    while segments:
        segment = segments.pop()
        current_vertex_index += circle_segments
        segment.start_vertex_index = current_vertex_index
        segments += segment.stem_continuations

    # Set up the vertex arrays and associated stuff.
    vformat = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData("Data", vformat, Geom.UHDynamic)
    vertex = GeomVertexWriter(vdata, 'vertex')
    normal = GeomVertexWriter(vdata, 'normal')
    color = GeomVertexWriter(vdata, 'color')
    geom = Geom(vdata)
    #geom.modify_vertex_data().set_num_rows(current_vertex_index + circle_segments)
    turtle = stem.tree_root_node.attach_new_node('turtle')

    # Add the initial circle
    for i in range(circle_segments):
        turtle.set_h(360.0 / circle_segments * i)
        v_pos = stem.tree_root_node.get_relative_point(
            turtle,
            Vec3(0, stem.segment_diameter, 0),
        )
        print(v_pos)
        vertex.addData3f(v_pos)
        normal.addData3f(
            stem.tree_root_node.get_relative_vector(
                turtle,
                Vec3(0, 1, 0),
            ),
        )
        color.addData4f(
            Vec4(
                random.random(),
                random.random(),
                random.random(),
                1,
            ),
        )

    segments = [(stem, 0)]
    while segments:
        segment, parent_start_index = segments.pop()
        own_start_index = segment.start_vertex_index
        # FIXME: Create vertices, draw triangles
        turtle.reparent_to(segment.node)
        for i in range(circle_segments):
            turtle.set_h(360.0 / circle_segments * i)
            vertex.addData3f(
                stem.tree_root_node.get_relative_point(
                    turtle,
                    Vec3(0, stem.segment_diameter, stem.segment_length),
                ),
            )
            normal.addData3f(
                stem.tree_root_node.get_relative_vector(
                    turtle,
                    Vec3(0, 1, 0),
                ),
            )
            color.addData4f(
                Vec4(
                    random.random(),
                    random.random(),
                    random.random(),
                    1,
                ),
            )
        for i in range(circle_segments):
            v_tl = own_start_index + i
            v_bl = parent_start_index + i
            v_tr = own_start_index + (i + 1) % circle_segments
            v_br = parent_start_index + (i + 1) % circle_segments

            tris = GeomTriangles(Geom.UHStatic)
            tris.addVertices(v_tl, v_bl, v_tr)
            tris.addVertices(v_br, v_tr, v_bl)
            tris.closePrimitive()
            geom.addPrimitive(tris)

        segments += [(s, own_start_index) for s in segment.stem_continuations]
    
    node = GeomNode('geom_node')
    node.add_geom(geom)
    print(NodePath(node).analyze())
    return NodePath(node)
