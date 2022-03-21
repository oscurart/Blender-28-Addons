# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

import bpy



def PeelUv(self, context):

    bpy.ops.object.mode_set(mode="OBJECT")

    ob = bpy.context.object
    actPolys= [poly for poly in bpy.context.object.data.polygons if poly.select]

    for actPoly in actPolys:


        edgeKeys = actPoly.edge_keys
        loopIndices = actPoly.loop_indices
        
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")
        
        # guardo las posiciones de los vertices del poligono para calcular la proporcion
        uno = abs((ob.data.vertices[edgeKeys[0][0]].co - ob.data.vertices[edgeKeys[0][1]].co).length)
        dos = abs((ob.data.vertices[edgeKeys[1][0]].co - ob.data.vertices[edgeKeys[1][1]].co).length)
        tres = abs((ob.data.vertices[edgeKeys[2][0]].co - ob.data.vertices[edgeKeys[2][1]].co).length)
        cuatro = abs((ob.data.vertices[edgeKeys[3][0]].co - ob.data.vertices[edgeKeys[3][1]].co).length)
        
        proporcion = (uno + tres) / (dos + cuatro)
        
        #paso a object para setear el area del uv

        ob.data.uv_layers.active.data[loopIndices[0]].uv = (0,0)
        ob.data.uv_layers.active.data[loopIndices[1]].uv = (1,0)
        ob.data.uv_layers.active.data[loopIndices[2]].uv = (1,1/proporcion)
        ob.data.uv_layers.active.data[loopIndices[3]].uv = (0,1/proporcion)
        
        actPoly.select = 1
        bpy.context.object.data.polygons.active = actPoly.index
        
      
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_linked(delimit={"SEAM"})
        bpy.ops.uv.follow_active_quads(mode="LENGTH_AVERAGE")
        bpy.ops.uv.pack_islands()
        
        bpy.ops.mesh.select_all(action="DESELECT")

        print(proporcion)

        

class PeelUnwrap(bpy.types.Operator):
    """Peel uv"""
    bl_idname = "mesh.peel_unwrap"
    bl_label = "Peel Unwrap"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.view_layer.objects.active is not None and
                context.view_layer.objects.active.type == 'MESH' and
                context.view_layer.objects.active.mode == "EDIT")


    def execute(self, context):
        PeelUv(self, context)
        return {'FINISHED'}
