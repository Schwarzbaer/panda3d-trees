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
from panda3d.core import GeomLines
from panda3d.core import Geom
from panda3d.core import GeomNode
from panda3d.core import NodePath

from homebrew import sd  # Stem definition enum
from homebrew import sg  # Segment enum


class GeometryData(enum.Enum):
    START_VERTEX = 1  # The number of the first vertex in this segment's geometry.


gd = GeometryData


def trimesh(stem, circle_segments=10, bark_tris=True):
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
    turtle = s[sg.TREE_ROOT][sg.TREE_ROOT_NODE].attach_new_node('turtle')

    # Add the initial circle
    for i in range(circle_segments):
        turtle.set_h(360.0 / circle_segments * i)
        v_pos = stem[sg.TREE_ROOT][sg.TREE_ROOT_NODE].get_relative_point(
            turtle,
            Vec3(0, stem[sg.ROOT_RADIUS], 0),
        )
        vertex.addData3f(v_pos)
        normal.addData3f(
            stem[sg.TREE_ROOT][sg.TREE_ROOT_NODE].get_relative_vector(
                turtle,
                Vec3(0, 1, 0),
            ),
        )
        color.addData4f(
            Vec4(0.0, 0.0, 0.0, 1),
            #    random.random(),
            #    random.random(),
            #    random.random(),
            #    1,
            #),
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
                s[sg.TREE_ROOT][sg.TREE_ROOT_NODE].get_relative_point(
                    turtle,
                    Vec3(0, s[sg.RADIUS], 0),
                ),
            )
            normal.addData3f(
                s[sg.TREE_ROOT][sg.TREE_ROOT_NODE].get_relative_vector(
                    turtle,
                    Vec3(0, 1, 0),
                ),
            )
            color.addData4f(
                Vec4(s[sg.REST_SEGMENTS] % 2,
                     s[sg.REST_SEGMENTS] % 4 // 2,
                     s[sg.REST_SEGMENTS] % 8 // 4,
                     1,
                ),
                
                # Vec4(0.8, 0.8, 0.8, 1),
                # Vec4(
                #     random.random(),
                #     random.random(),
                #     random.random(),
                #     1,
                # ),
            )
        for i in range(circle_segments):
            v_tl = own_start_index + i
            v_bl = parent_start_index + i
            v_tr = own_start_index + (i + 1) % circle_segments
            v_br = parent_start_index + (i + 1) % circle_segments

            if bark_tris:
                tris = GeomTriangles(Geom.UHStatic)
                tris.addVertices(v_tl, v_bl, v_tr)
                tris.addVertices(v_br, v_tr, v_bl)
                tris.closePrimitive()
                geom.addPrimitive(tris)
            else:
                lines = GeomLines(Geom.UHStatic)
                lines.addVertices(v_tl, v_bl)
                lines.closePrimitive()
                geom.addPrimitive(lines)
                lines.addVertices(v_tr, v_br)
                lines.closePrimitive()
                geom.addPrimitive(lines)

        segments += [(sc, own_start_index) for sc in s[sg.CONTINUATIONS]]
    
    node = GeomNode('geom_node')
    node.add_geom(geom)
    return node
