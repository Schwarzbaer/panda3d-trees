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
    FOOT_RING_START_VERTEX = 1  # 
    TOP_RING_START_VERTEX  = 2  # 
    TWIST_ANGLE            = 3  # Heading accumulated throuugh stem splitting.


gd = GeometryData


def trimesh(stem, circle_segments=10, bark_tris=True):
    segments = [stem]
    current_vertex_count = 0

    while segments:
        s = segments.pop()
        current_vertex_count += circle_segments
        if sg.TREE_ROOT_NODE in s or sg.IS_NEW_BRANCH in s:        
            current_vertex_count += circle_segments
        segments += s[sg.CONTINUATIONS]
        segments += s[sg.BRANCHES]

    # Set up the vertex arrays and associated stuff.
    vformat = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData("Data", vformat, Geom.UHDynamic)
    vertex = GeomVertexWriter(vdata, 'vertex')
    normal = GeomVertexWriter(vdata, 'normal')
    color = GeomVertexWriter(vdata, 'color')
    geom = Geom(vdata)
    geom.modify_vertex_data().set_num_rows(current_vertex_count)
    turtle = NodePath('turtle')

    # We'll be placing rings of vertices around the top of each segment,
    # and around the foot of stems.
    def draw_vertex_circle(s, circle_segments, entry=sg.NODE):
        # FIXME: Create vertices, draw triangles
        turtle.reparent_to(s[entry])
        for i in range(circle_segments):
            turtle.set_h(360.0 / circle_segments * i - s[gd.TWIST_ANGLE])
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
                # Vec4(0.8, 0.8, 0.8, 1),
                # Vec4(
                #     random.random(),
                #     random.random(),
                #     random.random(),
                #     1,
                # ),
                ),
            )


    # We got through the whole tree, determine which rings a segment
    # has (each has one at the top, and stem roots one at the bottom),
    # and note the starting numbers of their runs of vertices.
    # Since segments may control their heading, we need to twist the
    # top rings counter to that, or the mesh shows hourglass shapes.
    segments = [stem]
    current_vertex_index = 0

    while segments:
        s = segments.pop()

        # Untwisting
        if sg.TREE_ROOT_NODE not in s and sg.IS_NEW_BRANCH not in s:
            parent_twist = s[sg.PARENT_SEGMENT][gd.TWIST_ANGLE]
            own_twist = s[sg.NODE].get_h()
            s[gd.TWIST_ANGLE] = parent_twist + own_twist
        else:
            s[gd.TWIST_ANGLE] = 0

        # Rings at feet of first segments of a stem
        if sg.TREE_ROOT_NODE in s or sg.IS_NEW_BRANCH in s:
            if sg.TREE_ROOT_NODE in s:
                circle_node = sg.TREE_ROOT_NODE
            else:
                circle_node = sg.NODE
            draw_vertex_circle(s, circle_segments, circle_node)
            s[gd.FOOT_RING_START_VERTEX] = current_vertex_index
            current_vertex_index += circle_segments

        # Rings at the top of stems
        draw_vertex_circle(s, circle_segments, sg.NODE)
        s[gd.TOP_RING_START_VERTEX] = current_vertex_index
        current_vertex_index += circle_segments

        # ...and don't orget about the segments that dangle from this.
        segments += s[sg.CONTINUATIONS]
        segments += s[sg.BRANCHES]

    # Now we go through all the segments again to connect the vertex
    # rings into meshes.
    tris = GeomTriangles(Geom.UHStatic)

    segments = [stem]
    while segments:
        s = segments.pop()

        own_start_index = s[gd.TOP_RING_START_VERTEX]
        if sg.TREE_ROOT_NODE in s or sg.IS_NEW_BRANCH in s:
            # This node's top ring connects to its foot ring
            parent_start_index = s[gd.FOOT_RING_START_VERTEX]
        else:
            parent_start_index = s[sg.PARENT_SEGMENT][gd.TOP_RING_START_VERTEX]

        for i in range(circle_segments):
            v_tl = own_start_index + i
            v_bl = parent_start_index + i
            v_tr = own_start_index + (i + 1) % circle_segments
            v_br = parent_start_index + (i + 1) % circle_segments

            if bark_tris:
                tris.addVertices(v_tl, v_bl, v_tr)
                tris.addVertices(v_br, v_tr, v_bl)
            else:
                lines = GeomLines(Geom.UHStatic)
                lines.addVertices(v_tl, v_bl)
                lines.closePrimitive()
                geom.addPrimitive(lines)
                lines.addVertices(v_tr, v_br)
                lines.closePrimitive()
                geom.addPrimitive(lines)

        segments += s[sg.CONTINUATIONS]
        segments += s[sg.BRANCHES]

    tris.closePrimitive()
    geom.addPrimitive(tris)

    # ...and now we pack it up all neat and tidy.
    node = GeomNode('geom_node')
    node.add_geom(geom)
    return node
