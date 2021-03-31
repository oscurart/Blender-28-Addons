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
#www.oscurart.com.ar
#Eugenio Pignataro (oscurart)

bl_info = {
    "name": "Add Braid",
    "author": "Eugenio Pignataro (Oscurart)",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "location": "View3D > Add > Curve > Braid",
    "description": "Adds a Curve Braid",
    "warning": "",
    "doc_url": "",
    "category": "Add Curve",
}

import bpy
from bpy.types import Operator
from bpy.props import IntProperty
from bpy.props import FloatProperty


def BraidGen(a,length,diam,depth):
    braidSteps = {0:(0,0),
    1:(1*diam,1*diam),
    2:(1*diam,-1*diam),
    3:(0,0),
    4:(-1*diam,1*diam),
    5:(-1*diam,-1*diam)} #defino coordenadas

    #funcion en secuencia
    def avanceTrenza(max):
        abs = 0
        iB = 0
        while iB < max:
            yield (abs*diam,)+braidSteps[iB]+(1,)
            if iB != 5:
                iB += 1
            else:
                iB = 0
            abs += 1  

    temp = avanceTrenza(length) #variable con seis pasos         
    curveData = bpy.data.curves.new("braid", "CURVE")
    curveData.dimensions = "3D"
    curveOb = bpy.data.objects.new("Trenza", curveData)
    curveData.bevel_depth = depth
    spl = curveData.splines.new("NURBS")
    spl.points.add(length) # ojo este numero
    spl.use_endpoint_u = True
    bpy.context.collection.objects.link(curveOb)     

    for punto in spl.points:
        punto.co = next(temp)
        
    mod = curveOb.modifiers.new("Array", "ARRAY")  
    mod.use_constant_offset = True
    mod.use_relative_offset = False
    mod.count = 3
    mod.constant_offset_displace[0] = 2*diam

class OBJECT_OT_BraidGenOsc(bpy.types.Operator):
    """Create a Curve Braid"""
    bl_idname = "curve.braid"
    bl_label = "Create Curve Braid"
    bl_options = {"REGISTER", "UNDO"}
    Length : IntProperty(default=24,min=6)
    Diam : FloatProperty(default=1)
    Depth : FloatProperty(default=.5)

    def execute(self, context):
        BraidGen(self, self.Length, self.Diam, self.Depth)
        return {'FINISHED'}


# Registration

def add_object_button(self, context):
    self.layout.operator(
        OBJECT_OT_BraidGenOsc.bl_idname,
        text="Braid",
        icon='PLUGIN')


def register():
    bpy.utils.register_class(OBJECT_OT_BraidGenOsc)
    bpy.types.VIEW3D_MT_curve_add.append(add_object_button)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_esn_create)
    bpy.types.VIEW3D_MT_curve_add.remove(add_object_button)


if __name__ == "__main__":
    register()