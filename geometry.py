import math
import random
import enum

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

from tree_generation import sd  # Stem definition enum
from tree_generation import sg  # Segment enum

# stemlet_model = base.loader.load_model('models/smiley')
# stemlet_model.reparent_to(node)
# 
# stemlet_model.set_pos(0, 0, stemlet_length / 2.0)
# stemlet_model.set_sz(stemlet_length * 0.5)
# stemlet_model.set_sx(stemlet_diameter * 0.5)
# stemlet_model.set_sy(stemlet_diameter * 0.5)

# stemlet lineseg model


class GeometryData(enum.Enum):
    START_VERTEX = 1  # The number of the first vertex in this segment's geometry.


gd = GeometryData

    
def trimesh(stem, circle_segments=10):
    # What vertex ID does each segment start at?
    current_vertex_index = 0
    segments = [stem]
    while segments:
        s = segments.pop()
        current_vertex_index += circle_segments
        s[gd.START_VERTEX] = current_vertex_index
        segments += s[sg.CONTINUATIONS]

    # Set up the vertex arrays and associated stuff.
    vformat = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData("Data", vformat, Geom.UHDynamic)
    vertex = GeomVertexWriter(vdata, 'vertex')
    normal = GeomVertexWriter(vdata, 'normal')
    color = GeomVertexWriter(vdata, 'color')
    geom = Geom(vdata)
    #geom.modify_vertex_data().set_num_rows(current_vertex_index + circle_segments)
    turtle = s[sg.TREE_ROOT_NODE].attach_new_node('turtle')

    # Add the initial circle
    for i in range(circle_segments):
        turtle.set_h(360.0 / circle_segments * i)
        v_pos = s[sg.TREE_ROOT_NODE].get_relative_point(
            turtle,
            Vec3(0, s[sg.DEFINITION][sd.RADIUS], 0),
        )
        vertex.addData3f(v_pos)
        normal.addData3f(
            s[sg.TREE_ROOT_NODE].get_relative_vector(
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
        s, parent_start_index = segments.pop()
        own_start_index = s[gd.START_VERTEX]
        # FIXME: Create vertices, draw triangles
        turtle.reparent_to(s[sg.NODE])
        for i in range(circle_segments):
            turtle.set_h(360.0 / circle_segments * i)
            vertex.addData3f(
                s[sg.TREE_ROOT_NODE].get_relative_point(
                    turtle,
                    Vec3(0, s[sg.DEFINITION][sd.RADIUS], 0),
                ),
            )
            normal.addData3f(
                s[sg.TREE_ROOT_NODE].get_relative_vector(
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

        segments += [(sc, own_start_index) for sc in s[sg.CONTINUATIONS]]
    
    node = GeomNode('geom_node')
    node.add_geom(geom)
    return node
