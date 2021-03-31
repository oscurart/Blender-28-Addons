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

# AUTHOR: Eugenio Pignataro (Oscurart) www.oscurart.com.ar
# USAGE: Select object and run. This script invert apply transformations to deltas.

import bpy

   
class DeltaToGlobalOt(bpy.types.Operator):
    """Convert deltas to global"""
    bl_idname = "object.delta_to_global"
    bl_label = "Delta To Global"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for ob in bpy.context.selected_objects:
            mat = ob.matrix_world
            
            ob.location = mat.to_translation()
            ob.delta_location = (0,0,0)

            if ob.rotation_mode == "QUATERNION":
                ob.rotation_quaternion = mat.to_quaternion()
                ob.delta_rotation_quaternion = (1,0,0,0)
            else:
                ob.rotation_euler = mat.to_euler()
                ob.delta_rotation_euler = (0,0,0)    

            ob.scale = mat.to_scale()
            ob.delta_scale = (1,1,1) 

        return {'FINISHED'}
