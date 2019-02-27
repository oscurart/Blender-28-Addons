bl_info = {
    "name": "Bake PBR",
    "author": "Eugenio Pignataro (Oscurart)",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Render > Bake PBR",
    "description": "Bake PBR maps",
    "warning": "",
    "wiki_url": "",
    "category": "Render",
}



import bpy
import os

def folderCheck():
    fp = bpy.path.abspath(bpy.data.filepath)
    dirFile = os.path.dirname(fp)
    imagesFile = os.path.join(dirFile,"IMAGES")

    if not os.path.exists(imagesFile):
        os.mkdir(imagesFile)    

def setSceneOpts():
    global channels
    global channelsDict
    global sizex
    global sizey
    global selected_to_active
    
    # VARIABLES
    sizex = bpy.context.scene.bake_pbr_channels.sizex
    sizey = bpy.context.scene.bake_pbr_channels.sizey
    selected_to_active= bpy.context.scene.bake_pbr_channels.seltoact

    channelsDict = {
        "Base_Color":[True],  
        "Metallic":[False],              
        "Roughness":[False], 
        "Specular":[False], 
        "Subsurface_Color":[True],
        "Transmission":[False],    
        "Emission":[True],                  
        "Normal":[True]                     
        }   
    """    
    channelsDict ={
        "Anisotropic":[False,False],
        "Anisotropic Rotation":[False,False],
        "Base Color":[True,True],
        "Clearcoat":[False,False],
        "Clearcoat Normal":[False,True],
        "Clearcoat Roughness":[False,False],
        "IOR":[False,False],
        "Metallic":[True,False],
        "Normal":[False,True],
        "Roughness":[True,False],
        "Sheen":[False,False],
        "Sheen Tint":[False,False],
        "Specular":[False,False],
        "Specular Tint":[False,False],
        "Subsurface":[False,False],
        "Subsurface Color":[False,True],
        "Subsurface Radius":[False,True],
        "Tangent":[False,True],
        "Transmission":[False,False],
        "Transmission Roughness":[False,False]
        }        
     """   

    bpy.context.scene.render.image_settings.file_format = "OPEN_EXR"
    bpy.context.scene.render.image_settings.color_mode = "RGBA"
    bpy.context.scene.render.image_settings.exr_codec = "ZIP"
    bpy.context.scene.render.image_settings.color_depth = "16"

    #set bake options
    #bpy.context.scene.render.bake_type = "TEXTURE"
    bpy.context.scene.render.bake.use_pass_direct = 0
    bpy.context.scene.render.bake.use_pass_indirect = 0
    bpy.context.scene.render.bake.use_pass_color = 1
    bpy.context.scene.render.bake.use_selected_to_active = selected_to_active

#__________________________________________________________________________________

def mergeObjects():
    global selectedObjects
    global object 
    global selObject
    global mergeMatSlots
    #agrupo los seleccionados y el activo
    object = bpy.context.active_object
    selectedObjects = bpy.context.selected_objects[:].copy()
    selectedObjects.remove(bpy.context.active_object)
    

    # si es selected to active hago un merge de los objetos restantes
    if selected_to_active:
        obInScene = bpy.data.objects[:].copy()
        bpy.ops.object.select_all(action="DESELECT")
        for o in selectedObjects:
            o.select_set(state=True)
        bpy.context.view_layer.objects.active   = selectedObjects[0]
        bpy.ops.object.convert(target="MESH", keep_original=True)
        bpy.ops.object.select_all(action="DESELECT")
        for ob in bpy.data.objects:
            if ob not in obInScene:
                ob.select_set(True)
        selObject = bpy.context.active_object
        bpy.ops.object.join()
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True, properties=True)
    else:
        selObject=bpy.context.active_object   

    #seteo el objeto activo
    bpy.context.view_layer.objects.active   = object 
    
    #materiales en slot de objeto mergeado
    mergeMatSlots = [ms.material for ms in selObject.material_slots]


#__________________________________________________________________________________

def createTempMats():    
    global channelVector
    global selObject
    materiales = [m.material for m in selObject.material_slots]
    #compruebo los canales prendidos       
    for channel,channelVector in channelsDict.items():
        #todo lo que no sea normales
        if channel not in ["Normal","Emission"]:
            if getattr(bpy.context.scene.bake_pbr_channels,channel):  
                for mat in materiales:      
                    channelMat = mat.copy()
                    channelMat.name = "%s_%s" % (channel,mat.name) 
                    principleds = [node for node in channelMat.node_tree.nodes if node.type == "BSDF_PRINCIPLED"]
                    mixs = [node for node in channelMat.node_tree.nodes if node.type == "MIX_SHADER"]        
                    
                    #apago emisores
                    for node in channelMat.node_tree.nodes:
                        if node.type == "EMISSION":
                            node.inputs[0].default_value = (0,0,0,0)
                    
                    #conecta los valores a los mix
                    for prin in principleds:
                        if prin.inputs[channel.replace("_"," ")].is_linked:
                            channelMat.node_tree.links.new(prin.outputs['BSDF'].links[0].to_socket,prin.inputs[channel.replace("_"," ")].links[0].from_socket)
                        else:   
                            inputRGB = channelMat.node_tree.nodes.new("ShaderNodeRGB")
                            channelMat.node_tree.links.new(prin.outputs['BSDF'].links[0].to_socket,inputRGB.outputs[0])
                            if channelVector[0]: # si es float o un vector
                                inputRGB.outputs[0].default_value = prin.inputs[channel.replace("_"," ")].default_value    
                            else:
                                rgbValue = prin.inputs[channel].default_value
                                inputRGB.outputs[0].default_value = (rgbValue,rgbValue,rgbValue,1)
        #normal                       
        if channel in ["Normal","Emission"]:
            if getattr(bpy.context.scene.bake_pbr_channels,channel):  
                for mat in materiales:      
                    channelMat = mat.copy()
                    channelMat.name = "%s_%s" % (channel,mat.name)   
                    
                                                      


#__________________________________________________________________________________   
                      

def cambiaSlots(selObject, canal):
    for actualMs,originalMs in zip(selObject.material_slots,mergeMatSlots):
        actualMs.material = bpy.data.materials["%s_%s" % (canal,originalMs.name)] 

def restauraSlots(selObject):
    for actualMs,originalMs in zip(selObject.material_slots,mergeMatSlots):
        actualMs.material = bpy.data.materials[originalMs.name] 

#__________________________________________________________________________________   
    
def bake(map):   
    #crea imagen
    imgpath = "%s/IMAGES" % (os.path.dirname(bpy.data.filepath))
    img = bpy.data.images.new(map,  width=sizex, height=sizey, alpha=True,float_buffer=True)
    print ("Render: %s" % (map))
    img.colorspace_settings.name = 'Linear' 

    if not selected_to_active:        
        img.filepath = "%s/%s_%s.exr" % (imgpath, object.name, map.replace("_",""))
    else:
        img.filepath = "%s/%s_%s.exr" % (imgpath, object.active_material.name, map.replace("_",""))   
      
        
    #cambio todos los slots por el del canal
    cambiaSlots(selObject,map)
                     
    
    # creo nodos y bakeo
    if not selected_to_active:
        for activeMat in selObject.data.materials: #aca estaba el mscopy              
            # seteo el nodo
            node = activeMat.node_tree.nodes.new("ShaderNodeTexImage")
            node.image = img
            activeMat.node_tree.nodes.active = node
            node.color_space = "NONE"
            node.select = True
    else:
        activeMat = object.active_material               
        # seteo el nodo
        node = activeMat.node_tree.nodes.new("ShaderNodeTexImage")
        node.image = img
        activeMat.node_tree.nodes.active = node
        node.color_space = "NONE"
        node.select = True 
  
    if map not in ["Normal"]:
        bpy.ops.object.bake(type="EMIT")
    else:
        bpy.ops.object.bake(type="NORMAL")    
    img.save_render(img.filepath)
    bpy.data.images.remove(img)
    print ("%s Done!" % (map))
    
    #restauraSlots(selObject)

    
#__________________________________________________________________________________

def executePbr():
    #bakeo
    folderCheck()
    setSceneOpts() 
    mergeObjects()
    createTempMats()     

    for map in channelsDict.keys():  
        if getattr(bpy.context.scene.bake_pbr_channels,map):
            bake(map)  

"""
    #remuevo materiales copia
    for ma in bpy.data.materials:
        if ma.users == 0:
            bpy.data.materials.remove(ma)   
    
    #borro el merge
    if selected_to_active:
        bpy.data.objects.remove(selObject, do_unlink=True, do_id_user=True, do_ui_user=True)
  
"""    
    
class BakePbr (bpy.types.Operator):
    """Bake PBR materials"""
    bl_idname = "object.bake_pbr_maps"
    bl_label = "Bake PBR Maps"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        executePbr()
        return {'FINISHED'}       
    

#__________________________________________________________________________________



class bakeChannels(bpy.types.PropertyGroup):
    Base_Color : bpy.props.BoolProperty(name="Base Color",default=False)    
    Metallic : bpy.props.BoolProperty(name="Metallic",default=False)    
    Roughness : bpy.props.BoolProperty(name="Roughness",default=False)
    Specular : bpy.props.BoolProperty(name="Specular",default=False)   
    Subsurface_Color :  bpy.props.BoolProperty(name="Subsurface Color",default=False) 
    Transmission :  bpy.props.BoolProperty(name="Transmission",default=False)  
    Emission:  bpy.props.BoolProperty(name="Emission",default=False)          
    Normal :  bpy.props.BoolProperty(name="Normal",default=False)        
    """
    metallic : bpy.props.BoolProperty(name="Metallic",default=False)
    occlusion : bpy.props.BoolProperty(name="Occlusion",default=False)
    normal : bpy.props.BoolProperty(name="Normal",default=False)
    emit : bpy.props.BoolProperty(name="Emit",default=False)
    roughness : bpy.props.BoolProperty(name="Roughness",default=False)
    opacity : bpy.props.BoolProperty(name="Opacity",default=False)
    albedo : bpy.props.BoolProperty(name="Albedo",default=False)
    """    
    sizex : bpy.props.IntProperty(name="Size x", default= 1024)
    sizey : bpy.props.IntProperty(name="Size y", default= 1024)
    seltoact : bpy.props.BoolProperty(name="Selected to active", default= True)

bpy.utils.register_class(bakeChannels)


class LayoutDemoPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Bake PBR"
    bl_idname = "RENDER_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        # Create a simple row.
        layout.label(text=" Channels:")
        
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "Base_Color")   
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "Metallic")               
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "Roughness")   
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "Specular")    
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "Subsurface_Color")    
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "Transmission")         
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "Emission")                   
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "Normal")                                 
        """
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "metallic")
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "occlusion")
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "normal")
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "emit")
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "roughness")
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "opacity")
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "albedo")
        """        
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "sizex")    
        row.prop(scene.bake_pbr_channels, "sizey")   
        row = layout.row()
        row.prop(scene.bake_pbr_channels, "seltoact")     
        # Big render button
        row = layout.row()
        row.scale_y = 2
        row.operator("object.bake_pbr_maps")



#__________________________________________________________________________________


def register():
    bpy.types.Scene.bake_pbr_channels = bpy.props.PointerProperty(type=bakeChannels)
    bpy.utils.register_class(LayoutDemoPanel)  
    bpy.utils.register_class(BakePbr)  



def unregister():
    bpy.utils.unregister_class(LayoutDemoPanel)  
    bpy.utils.unregister_class(BakePbr)      
    bpy.utils.unregister_class(OBJECT_OT_add_object)



if __name__ == "__main__":
    register()