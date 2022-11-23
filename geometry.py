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


def trimesh(tree):
    current_vertex_index = 0
    tree.first_vertex_index
    # Set up the vertex arrays
    vformat = GeomVertexFormat.getV3c4()
    vdata = GeomVertexData("Data", vformat, Geom.UHDynamic)
    vertex = GeomVertexWriter(vdata, 'vertex')
    normal = GeomVertexWriter(vdata, 'normal')
    color = GeomVertexWriter(vdata, 'color')
    geom = Geom(vdata)

    # Write vertex data
    for x in range(0, sidelength):
        for y in range(0, sidelength):
            # vertex_number = x * sidelength + y
            v_x, v_y, v_z = self.map_b[(x, y)]
            n_x, n_y, n_z = 0.0, 0.0, 1.0
            c_r, c_g, c_b, c_a = 0.5, 0.5, 0.5, 0.5
            vertex.addData3f(v_x, v_y, v_z)
            normal.addData3f(n_x, n_y, n_z)
            color.addData4f(c_r, c_g, c_b, c_a)

    # Add triangles
    for x in range(0, sidelength - 1):
        for y in range(0, sidelength - 1):
            # The vertex arrangement (y up, x right)
            # 2 3
            # 0 1
            v_0 = x * sidelength + y
            v_1 = x * sidelength + (y + 1)
            v_2 = (x + 1) * sidelength + y
            v_3 = (x + 1) * sidelength + (y + 1)
            if (x+y)%1 == 0: # An even square
                tris = GeomTriangles(Geom.UHStatic)
                tris.addVertices(v_0, v_2, v_3)
                tris.closePrimitive()
                geom.addPrimitive(tris)
                tris = GeomTriangles(Geom.UHStatic)
                tris.addVertices(v_3, v_1, v_0)
                tris.closePrimitive()
                geom.addPrimitive(tris)
            else: # An odd square
                tris = GeomTriangles(Geom.UHStatic)
                tris.addVertices(v_1, v_0, v_2)
                tris.closePrimitive()
                geom.addPrimitive(tris)
                tris = GeomTriangles(Geom.UHStatic)
                tris.addVertices(v_2, v_3, v_1)
                tris.closePrimitive()
                geom.addPrimitive(tris)

    # Create the actual node
    node = GeomNode('geom_node')
    node.addGeom(geom)
    
    # Remember GeomVertexWriters to adjust vertex data later
    #self.vertex_writer = vertex
    #self.color_writer = color
    self.vdata = vdata
    
    return node
