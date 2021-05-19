bl_info = {
    "name": "Mesh Cache Tools",
    "author": "Oscurart",
    "version": (1, 0, 1),
    "blender": (2, 80, 0),
    "location": "Tools > Mesh Cache Tools",
    "description": "Tools for Management Mesh Cache Process",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Import-Export"}

import bpy
import os
from bpy_extras.io_utils import ImportHelper
import struct
from bpy.app.handlers import persistent
from mathutils import Matrix
import mathutils
import math

class VIEW3D_PT_tools_meshcachetools(bpy.types.Panel):
    """Crea Panel"""
    bl_label = "MeshCacheTools"
    #bl_idname = "SCENE_PT_asd"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_context = "object_mode"
    bl_category = 'Tool'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):

        layout = self.layout
        layout.label(text="Export")
        scene = context.scene
        # Create a simple row.
        #layout.label(text=" Simple Row:")
        row = layout.row()
        row.prop(scene, "pc_pc2_folder", text="Folder")      
        row = layout.row()
        row.operator("file.set_meshcache_folder", text="Select Folder Path")
        row = layout.row()
        row.prop(scene, "pc_pc2_exclude", text="Exclude")          
        row = layout.row()        
        row.prop(scene, "frame_start")
        row.prop(scene, "frame_end")
        
        # Big render button
        #layout.label(text="Bake:")
        row = layout.row()        
        row.prop(scene, "pc_pc2_applyGenMods", text="Apply Gen Modifiers")        
        row = layout.row()        
        row.prop(scene, "pc_pc2_applyMods", text="Apply Modifiers")
        row = layout.row() 
        row.prop(scene, "pc_pc2_world_space", text="World Space")
        row = layout.row() 
        row.prop(scene, "pc_pc2_apply_collection_matrix", text="Apply Collection Matrix")        
        row = layout.row()
        row.scale_y = 3.0
        row.operator("export_shape.pc2_selection", text="BAKE")
        row = layout.row()
        layout.label(text="Import")
        row = layout.row()
        row.operator("scene.pc_auto_search_files", text="Auto Search Files")        
        #row = layout.row()
        #row.operator("object.modifier_mesh_cache_up", text="MC Modifier to Top")
        row = layout.row(align=True)
        row.operator("scene.pc_auto_load_proxy_create", text="Create List")
        row.operator("scene.pc_auto_load_proxy_remove", text="Remove List")
        
        for i in scene.pc_auto_load_proxy:
            if bpy.data.collections[i.name].library is not None:
                row = layout.row()
                row.prop(bpy.data.collections[i.name], "name", text="")
                row.prop(i, "use_auto_load", text="")        


# SET FOLDER ----------------------

def OscSetFolder(self, context, filepath):
    fp = filepath if os.path.isdir(filepath) else os.path.dirname(filepath)
    try:
        os.chdir(os.path.dirname(bpy.data.filepath))
    except Exception as e:
        self.report({'WARNING'}, "Folder could not be set: {}".format(e))
        return {'CANCELLED'}

    bpy.context.scene.pc_pc2_folder = bpy.path.relpath(fp)

    return {'FINISHED'}


class OscMeshCacheButtonSet(bpy.types.Operator, ImportHelper):
    bl_idname = "file.set_meshcache_folder"
    bl_label = "Set Mesh Cache Folder"
    filename_ext = ".txt"

    def execute(self, context):
        return OscSetFolder(self, context, self.filepath)


# EXPORT PC2 ---------------------------

def OscRemoveGenModifiers(ob,state):
    GENERATE = [
            'MULTIRES', 'ARRAY', 'BEVEL', 'BOOLEAN', 'BUILD',
            'DECIMATE', 'MASK', 'MIRROR', 'REMESH', 'SCREW',
            'SKIN', 'SOLIDIFY', 'SUBSURF', 'TRIANGULATE',
            'EDGE_SPLIT','WIREFRAME'
            ]
            
    for mod in ob.modifiers[:]:
        if mod.type in GENERATE:
            mod.show_render = state
            mod.show_viewport = state

def get_sampled_frames(start, end, sampling):
    return [math.modf(start + x * sampling) for x in range(int((end - start) / sampling) + 1)]            
            
def do_export(context, props):
    folderpath = bpy.context.scene.pc_pc2_folder
    for collOb in bpy.context.selected_objects:
        for ob in collOb.instance_collection.all_objects[:]:     
            if ob.type == "MESH": 
                if bpy.context.scene.pc_pc2_exclude not in ob.name:
                    if not ob.hide_viewport:
                        if bpy.context.scene.pc_pc2_applyGenMods == False:
                            OscRemoveGenModifiers(ob,False)
                        filepath= "%s/%s_%s.pc2" % (bpy.path.abspath(folderpath), collOb.instance_collection.name,ob.name)
                        mat_x90 = mathutils.Matrix.Rotation(-math.pi/2, 4, 'X')
                        sc = bpy.context.scene
                        start = sc.frame_start
                        end = sc.frame_end
                        sampling = float(1)
                        apply_modifiers = bpy.context.scene.pc_pc2_applyMods
                        depsgraph = None
                        if apply_modifiers:
                            depsgraph = bpy.context.evaluated_depsgraph_get()
                            me = ob.evaluated_get(depsgraph).to_mesh()
                        else:
                            me = ob.to_mesh()                       
                        vertCount = len(me.vertices)
                        sampletimes = get_sampled_frames(start, end, sampling)
                        sampleCount = len(sampletimes)

                        # Create the header
                        headerFormat = '<12siiffi'
                        headerStr = struct.pack(headerFormat, b'POINTCACHE2\0',
                                                1, vertCount, start, sampling, sampleCount)

                        file = open(filepath, "wb")
                        file.write(headerStr)

                        for frame in sampletimes:
                            # stupid modf() gives decimal part first!
                            sc.frame_set(int(frame[1]), subframe=frame[0])
                            if apply_modifiers:
                                me = ob.evaluated_get(depsgraph).to_mesh()
                            else:
                                me = ob.to_mesh()

                            if len(me.vertices) != vertCount:
                                bpy.data.meshes.remove(me, do_unlink=True)
                                file.close()
                                try:
                                    remove(filepath)
                                except:
                                    empty = open(filepath, 'w')
                                    empty.write('DUMMIFILE - export failed\n')
                                    empty.close()
                                print('Export failed. Vertexcount of Object is not constant')
                                return False

                            if bpy.context.scene.pc_pc2_world_space:
                                me.transform(ob.matrix_world)
                                
                            if bpy.context.scene.pc_pc2_apply_collection_matrix:
                                me.transform(bpy.context.active_object.matrix_world)                  


                            for v in me.vertices:
                                thisVertex = struct.pack('<fff', float(v.co[0]),
                                                         float(v.co[1]),
                                                         float(v.co[2]))
                                file.write(thisVertex)

                        if apply_modifiers:
                            ob.evaluated_get(depsgraph).to_mesh_clear()
                        else:
                            me = ob.to_mesh_clear()

                        file.flush()
                        file.close()
                    print("-- %s Finished" % (ob.name))        
    return True


class OscPc2ExporterBatch(bpy.types.Operator):
    bl_idname = "export_shape.pc2_selection"
    bl_label = "Export pc2 for selected Objects"
    bl_description = "Export pc2 for selected Objects"
    bl_options = {'REGISTER', 'UNDO'}
    

    @classmethod
    def poll(cls, context):
        return(bpy.context.object.instance_collection != None)


    def execute(self, context):
        do_export(self, context)
        return {'FINISHED'}


# MODIFIER MOVE UP ----------------------------------

class OscMeshCacheUp(bpy.types.Operator):
    bl_idname = "object.modifier_mesh_cache_up"
    bl_label = "Mesh Cache To Top"
    bl_description = "Send Mesh Cache Modifiers top"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type == "MESH")

    def execute(self, context):

        actob = bpy.context.view_layer.objects.active

        for ob in bpy.context.selected_objects[:]:
            bpy.context.view_layer.objects.active = ob
            for mod in ob.modifiers[:]:
                if mod.type == "MESH_CACHE":
                    for up in range(ob.modifiers.keys().index(mod.name)):
                        bpy.ops.object.modifier_move_up(modifier=mod.name)

        bpy.context.view_layer.objects.active = actob

        return {'FINISHED'}
    
    
# AUTO LOAD --------------------------

class SearchFiles(bpy.types.Operator):
    bl_idname = "scene.pc_auto_search_files"
    bl_label = "Search pc2 files in the folder"
    
    def execute(self, context):
        pc2Files = os.listdir(bpy.path.abspath(bpy.context.scene.pc_pc2_folder))
        for coleccion in bpy.context.scene['pc_auto_load_proxy']:
            for archivo in pc2Files:
                if coleccion["name"] in archivo:
                    coleccion["use_auto_load"] = True
                    
        return {'FINISHED'} 


class CreaPropiedades(bpy.types.Operator):
    bl_idname = "scene.pc_auto_load_proxy_create"
    bl_label = "Create Auto Load PC Proxy List"

    def execute(self, context):
        for col in bpy.data.collections:
            if col.name not in bpy.context.scene.pc_auto_load_proxy:
                if col.library is not None:
                    i = bpy.context.scene.pc_auto_load_proxy.add()
                    i.name = col.name
                    i.use_auto_load = False
        return {'FINISHED'}    

class RemuevePropiedades(bpy.types.Operator):
    bl_idname = "scene.pc_auto_load_proxy_remove"
    bl_label = "Remove Auto Load PC Proxy List"

    def execute(self, context):
        for i in bpy.context.scene.pc_auto_load_proxy:
            bpy.context.scene.pc_auto_load_proxy.remove(0)
        return {'FINISHED'}



class OscurartMeshCacheSceneAutoLoad(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(
            name="GroupName",
            default=""
            )
    use_auto_load : bpy.props.BoolProperty(
            name="Bool",
            default=False
            )


def offDeformMods(ob):
    deformList=['ARMATURE', 'CAST', 'CURVE',
         'HOOK', 'LAPLACIANDEFORM', 'LATTICE',
         'MESH_DEFORM', 'SHRINKWRAP', 'SIMPLE_DEFORM',
         'SMOOTH', 'CORRECTIVE_SMOOTH', 'LAPLACIANSMOOTH',
         'SURFACE_DEFORM', 'WARP', 'WAVE']   
          
    for mod in ob.modifiers:
        if mod.type in deformList:
            mod.show_render = False
            mod.show_viewport = False            

@persistent
def CargaAutoLoadPC(dummy):
    zeroMat = Matrix(((1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0)))    
    for col in bpy.context.scene.pc_auto_load_proxy:
        folderpath = bpy.context.scene.pc_pc2_folder
        if col.use_auto_load:
            for ob in bpy.data.collections[col.name].all_objects:
                offDeformMods(ob) #apago modifiers deformadores
                ob.matrix_world = zeroMat
                for mod in ob.modifiers:
                    if mod.type == "MESH_CACHE":
                        pc2Path = "%s/%s_%s.pc2" % (bpy.path.abspath(folderpath),col.name,ob.name)
                        if os.path.exists(pc2Path):
                            mod.cache_format = "PC2"
                            mod.forward_axis = "POS_Y"
                            mod.up_axis = "POS_Z"
                            mod.flip_axis = set(())
                            mod.frame_start = bpy.context.scene.frame_start
                            mod.filepath = pc2Path
                        else:
                            print("Pc2 Error: %s is missing" % (ob.name) )  
                            mod.show_viewport = False
                            mod.show_render = False  


bpy.app.handlers.load_post.append(CargaAutoLoadPC)
    
# REGISTER ----------------------------

classes = (OscMeshCacheButtonSet,
    VIEW3D_PT_tools_meshcachetools,
    OscPc2ExporterBatch,
    OscMeshCacheUp,
    CreaPropiedades,
    RemuevePropiedades,
    SearchFiles
)


def register():     
    from bpy.types import Scene 
    from bpy.utils import register_class

    Scene.pc_pc2_folder = bpy.props.StringProperty(default="Set me Please!")    
    Scene.pc_pc2_exclude = bpy.props.StringProperty(default="*")
    Scene.pc_pc2_world_space = bpy.props.BoolProperty(default=True, name="World Space")
    Scene.pc_pc2_apply_collection_matrix = bpy.props.BoolProperty(default=True, name="Collection Matrix")
    Scene.pc_pc2_applyGenMods = bpy.props.BoolProperty(default=True, name="ApplyGenModifiers")
    Scene.pc_pc2_applyMods = bpy.props.BoolProperty(default=True, name="ApplyModifiers")
    bpy.utils.register_class(OscurartMeshCacheSceneAutoLoad)
    Scene.pc_auto_load_proxy = bpy.props.CollectionProperty(
                                            type=OscurartMeshCacheSceneAutoLoad
                                            )        
    for cls in classes:
        register_class(cls)   

def unregister(): 
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
        
    bpy.utils.unregister_class(OscurartMeshCacheSceneAutoLoad)	        

if __name__ == "__main__":
    register()
