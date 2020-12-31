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
from bpy.types import Operator
from bpy.props import BoolProperty


#esta funcion devuelve los valores de tamaños de los objetos
def obDates(ob):
    vertCoord = {}
    mat = ob.matrix_world  
    for ver in ob.data.vertices:
        vertCoord[(mat @ ver.co)[axis]] = ver
    minCo = round(min(vertCoord.keys()),4)
    maxCo = round(max(vertCoord.keys()) ,4)
    siz = maxCo-minCo
    return minCo,maxCo,siz

def ObjectDistributeMeshOscurart(self, X, Y, Z):    
    global axis    
    for numb,selAxis in zip((0,1,2),(X,Y,Z)):
        if selAxis:
            axis = numb
            print(axis)

            if len(bpy.selection_osc[:]) > 1:                
                #consigo la suma de los tamaños y la lista refinada
                sumSizes= 0 #suma de los tamaños de los objetos
                masterList = []
                for ob in bpy.selection_osc:
                    masterList.append(obDates(ob))
                    sumSizes += masterList[-1][2]
                    
                primerPunto = masterList[0][0]
                ultimoPunto = masterList[-1][1]
                espacioEntre = (ultimoPunto-primerPunto)-sumSizes
                espacioDividido = espacioEntre / (len(bpy.context.selected_objects)-1)

                i = 1
                iDiferenciaAnterior = 0 
                for ob in bpy.selection_osc[1:-1]:
                    tamAnterior = masterList[i-1][2]
                    diferenciaAnterior = masterList[i][0] - masterList[i-1][1] 
                    bpy.selection_osc[i].location[axis] -= diferenciaAnterior + iDiferenciaAnterior
                    bpy.selection_osc[i].location[axis] += espacioDividido * i
                    print(diferenciaAnterior)
                    iDiferenciaAnterior += diferenciaAnterior
                    i+=1        

            else:
                self.report({'INFO'}, "Needs at least two selected objects")


class DistributeMeshOsc(Operator):
    """Distribute evenly the selected meshes in x y z"""
    bl_idname = "object.distributemesh_osc"
    bl_label = "Distribute Meshes"
    Boolx : BoolProperty(name="X")
    Booly : BoolProperty(name="Y")
    Boolz : BoolProperty(name="Z")

    def execute(self, context):
        ObjectDistributeMeshOscurart(self, self.Boolx, self.Booly, self.Boolz)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.Boolx = True
        self.Booly = True
        self.Boolz = True
        return context.window_manager.invoke_props_dialog(self)