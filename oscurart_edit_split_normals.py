bl_info = {
    "name": "Edit Split Normals",
    "author": "Oscurart",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Search > Edit Slit Normals",
    "description": "Edit split normals like a mesh",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}


import bpy
from mathutils import Vector
from bpy.types import Operator
from bpy.props import FloatProperty
from bpy.props import BoolProperty
from mathutils import Vector

# CREA MESH --------------------------------------------------------
#funcion que esconde vertices pares
def hidePares(vertA):
    hv = False
    for vert in vertA:
        vert.hide = hv
        if hv == False:
            hv = True
        else:
            hv = False 

def editmesh_create(self, normalSize, onlySelected, sharp, context):
    ob = bpy.context.object.data
    mode = bpy.context.object.mode
    obMatrix = bpy.context.object.matrix_world.copy()

    bpy.ops.object.mode_set(mode="OBJECT")

    ob.calc_normals_split()

    newNormals = []
    newEdges = []
    ei = 0
    selVerts = []
    
    #guardo loops seleccionados
    selLoops = []    
    for face in ob.polygons:
        if face.select:
            for l in face.loop_indices:
                selLoops.append(l)
                        
    #sumo geometria        
    for l in ob.loops:
        i = (l.normal*normalSize) + ob.vertices[l.vertex_index].co     
        newNormals.append(i)
        newNormals.append(ob.vertices[l.vertex_index].co)
        newEdges.append([ei,ei+1])   
        
        if sharp:
            if l.index not in selLoops:
                selVerts.append(ei)
                selVerts.append(ei+1) 
        else:
            if ob.vertices[l.vertex_index].select == False :
                selVerts.append(ei)
                selVerts.append(ei+1)                     
            
        ei += 2                 

    normalEditMesh = bpy.data.meshes.new("normalEditTemp")
    normalEditObject = bpy.data.objects.new("normalEditObject",normalEditMesh)
    normalEditMesh.from_pydata(newNormals,newEdges,[])
    bpy.context.collection.objects.link(normalEditObject)

    #escondo los vertices que no son utiles
    hidePares(normalEditMesh.vertices)
    
    #escondo los no seleccionados
    if onlySelected:
        for vert in selVerts:
            normalEditObject.data.vertices[vert].hide = True
            
    normalEditObject.matrix_world = obMatrix        

class OBJECT_OT_esn_create(Operator):
    """Create Mesh Edit Split Normals"""
    bl_idname = "mesh.edit_split_normals_create"
    bl_label = "Edit Split Normals Create"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')

    normalSize: FloatProperty(
        name="Normal",
        default=1.0
        )

    onlySelected: BoolProperty(
        name="Only Selected",
        default = True
        )

    Sharp: BoolProperty(
        name="Sharp",
        default = True
        )


    def execute(self, context):
        editmesh_create(self, self.normalSize, self.onlySelected, self.Sharp, context)
        return {'FINISHED'}

# APLICA EDIT NORMALS -----------------------------------------------------

def editmesh_apply(self, context):
    ob = bpy.context.object
    mode = bpy.context.object.mode
    neo = bpy.data.objects["normalEditObject"]

    bpy.ops.object.mode_set(mode="OBJECT")

    ob.data.calc_normals_split()

    newNormals = []

    for l in ob.data.loops: 
        i = neo.data.vertices[l.index*2].co - ob.data.vertices[l.vertex_index].co
        i.normalize()     
        newNormals.append(i)
        
    ob.data.normals_split_custom_set(newNormals) 




class OBJECT_OT_esn_apply(Operator):
    """Edit Split Normals Apply"""
    bl_idname = "mesh.edit_split_normals_apply"
    bl_label = "Edit Split Normals Apply"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')


    def execute(self, context):
        editmesh_apply(self, context)
        return {'FINISHED'}


# Registration

def add_object_button(self, context):
    self.layout.operator(
        OBJECT_OT_esn_create.bl_idname,
        text="Edit Split Normals Create",
        icon='PLUGIN')
    self.layout.operator(
        OBJECT_OT_esn_apply.bl_idname,
        text="Edit Split Normals Apply",
        icon='PLUGIN')



def register():
    bpy.utils.register_class(OBJECT_OT_esn_create)
    bpy.utils.register_class(OBJECT_OT_esn_apply)
    bpy.types.VIEW3D_MT_mesh_add.append(add_object_button)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_esn_create)
    bpy.utils.unregister_class(OBJECT_OT_esn_apply)
    bpy.types.VIEW3D_MT_mesh_add.remove(add_object_button)


if __name__ == "__main__":
    register()
