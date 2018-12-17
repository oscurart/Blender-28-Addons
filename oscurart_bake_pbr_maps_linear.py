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


def setSceneOpts():
    global channels
    global sizex
    global sizey
    global selected_to_active
    
    # VARIABLES
    sizex = bpy.context.scene.bake_pbr_channels.sizex
    sizey = bpy.context.scene.bake_pbr_channels.sizey
    selected_to_active= bpy.context.scene.bake_pbr_channels.seltoact

    channels = {"metallic":["ME","GLOSSY"],
        "occlusion":["AO","AO"],
        "normal":["NM","NORMAL"],
        "emit":["EM","EMIT"],
        "roughness":["RO","ROUGHNESS"],
        "opacity":["OP","TRANSMISSION"],
        "albedo":["AT","DIFFUSE"]}

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

#__________________________________________________________________________________

def createTempMats():
    global ms
    global copyMats
    global roughMats
    global transMats
    global glossyMats
    
    #lista de materiales originales
    if not selected_to_active:
        ms = [mat.material for mat in object.material_slots]
    else:
        ms = [mat.material for mat in selObject.material_slots]  
                
    #sumo materiales copia y reemplazo slots
    for matType in ["_glossyTemp","_copyTemp","_roughnessTemp","_trans"]:
        ims = 0
        for mat in ms:
            mc = mat.copy()
            mc.name =  mat.name+matType
            if not selected_to_active:
                object.material_slots[ims].material = mc
            else:
                selObject.material_slots[ims].material = mc    
            ims += 1

    copyMats = [mat for mat in bpy.data.materials if mat.name.endswith("_copyTemp")]
    glossyMats = [mat for mat in bpy.data.materials if mat.name.endswith("_glossyTemp")]
    roughMats = [mat for mat in bpy.data.materials if mat.name.endswith("_roughnessTemp")]
    transMats = [mat for mat in bpy.data.materials if mat.name.endswith("_trans")]

#__________________________________________________________________________________

# mezcloGlossy
def mixGlossy(material):
    mat = material

    for node in mat.node_tree.nodes[:]:
        if node.type == "BSDF_PRINCIPLED":            
            nprin = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled") # nuevo principled

            mix = mat.node_tree.nodes.new("ShaderNodeMixShader")
            mat.node_tree.links.new(mix.inputs[2],nprin.outputs[0])
            mat.node_tree.links.new(mix.inputs[1],node.outputs[0]) 
            if node.inputs["Metallic"].is_linked:  
                mat.node_tree.links.new(mix.inputs[0],node.inputs['Metallic'].links[0].from_socket)    
            else:
                mix.inputs[0].default_value = node.inputs['Metallic'].default_value
            
            #copio metalico
            if node.inputs["Metallic"].is_linked:        
                mat.node_tree.links.new(mix.inputs[0],node.inputs["Metallic"].links[0].from_socket)
            mat.node_tree.links.new(node.outputs['BSDF'].links[0].to_socket,mix.outputs[0])
            
            #copio seteos de p a p
            for entrada in ["Base Color","Roughness"]:
                if node.inputs[entrada].is_linked:
                      mat.node_tree.links.new(nprin.inputs[entrada],node.inputs[entrada].links[0].from_socket)
                nprin.inputs[entrada].default_value =  node.inputs[entrada].default_value        
                                      
            node.inputs['Specular'].default_value = 0 
            node.inputs['Metallic'].default_value = 0 # ambos a cero
            nprin.inputs['Specular'].default_value = 0 
            nprin.inputs['Metallic'].default_value = 1 # nuevo prin a 1

    for link in mat.node_tree.links:
        if link.to_socket.name == "Metallic":
            mat.node_tree.links.remove(link)   


#__________________________________________________________________________________

#desmetalizar
def desmetalizar(material):
    for link in mat.node_tree.links:
        if link.to_socket.name == "Metallic":
            mat.node_tree.links.remove(link)
    for matnode in mat.node_tree.nodes:
        if matnode.type == "BSDF_PRINCIPLED":
            # desconecto metallic y seteo cero
            if matnode.inputs['Metallic'].is_linked:           
                matnode.inputs["Metallic"].default_value = 0     
                matnode.inputs["Specular"].default_value = 0    
            else:
                matnode.inputs["Metallic"].default_value = 0  
                matnode.inputs['Specular'].default_value = 0       

#destransparentizar
def destransparentizar(material):
    for link in mat.node_tree.links:
        if link.to_socket.name == "Transmission":
            mat.node_tree.links.remove(link)
    for matnode in mat.node_tree.nodes:
        if matnode.type == "BSDF_PRINCIPLED":
            # desconecto metallic y seteo cero
            if matnode.inputs['Transmission'].is_linked:           
                matnode.inputs["Transmission"].default_value = 0       
            else:
                matnode.inputs["Transmission"].default_value = 0  


#saca todos los speculares
def desespecular(material):
    for matnode in material.node_tree.nodes:
        if matnode.type == "BSDF_PRINCIPLED":
            matnode.inputs["Specular"].default_value = 0 
  

#base color a 1
def baseColorA1(material):
    for link in mat.node_tree.links:
        if link.to_socket.name == "Base Color":
            mat.node_tree.links.remove(link)      
    for node in mat.node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            node.inputs['Base Color'].default_value= (1,1,1,1)    
  
#cambia slots
def cambiaSlots(objeto,sufijo):
    for ms in objeto.material_slots:
        ms.material = bpy.data.materials[ms.material.name.rpartition("_")[0]+sufijo] 

#__________________________________________________________________________________

def removeMatProps():
    global mat
    #saco los metales en las copias de copy  
    for mat in copyMats: 
        desmetalizar(mat)    
        destransparentizar(mat)

        
    #saco los metales en las copias de glossy    
    for mat in glossyMats: 
        desespecular(mat)                     
        mixGlossy(mat) 
        destransparentizar(mat)
        
    #llevo a uno los base color de roughness  
    for mat in roughMats: 
        desespecular(mat)                     
        baseColorA1(mat)
        destransparentizar(mat)

    # saco metales para transmisiones
    for mat in transMats:     
        desmetalizar(mat)   
        desespecular(mat)   
        baseColorA1(mat) 
    
#__________________________________________________________________________________   
    
def bake(map):                       
    #crea imagen
    imgpath = "%s/IMAGES" % (os.path.dirname(bpy.data.filepath))
    img = bpy.data.images.new(channels[map][0],  width=sizex, height=sizey, alpha=True,float_buffer=True)
    print ("Render: %s" % (channels[map][1]))
    img.colorspace_settings.name = 'Linear' 
  
    if not selected_to_active:        
        img.filepath = "%s/%s_%s.exr" % (imgpath, object.name, channels[map][0])
    else:
        img.filepath = "%s/%s_%s.exr" % (imgpath, object.active_material.name, channels[map][0])   
        
    #cambio materiales
    if channels[map][0] == "ME":
          cambiaSlots(selObject,"_glossyTemp")   
          
    if channels[map][0] == "RO":
          cambiaSlots(selObject,"_roughnessTemp") 

    if channels[map][0] in ["AT","AO","NM","EM","OP"]:
          cambiaSlots(selObject,"_copyTemp")       
          
    if channels[map][0] in ["OP"]:
          cambiaSlots(selObject,"_trans")                        
         
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
  

    bpy.ops.object.bake(type=channels[map][1])
    img.save_render(img.filepath)
    bpy.data.images.remove(img)
    print ("%s Done!" % (channels[map][1]))
    
#__________________________________________________________________________________

def executePbr():
    #bakeo
    setSceneOpts() 
    mergeObjects()
    createTempMats()
    removeMatProps() 
    for map in channels.keys():
        if getattr(bpy.context.scene.bake_pbr_channels,map):
            bake(map)  

       
    #restauro material slots    
    for matSlot,rms in zip(selObject.material_slots,ms):
        matSlot.material = rms

    #remuevo materiales copia
    for ma in copyMats+glossyMats+roughMats+transMats:
        bpy.data.materials.remove(ma)        

      
    #borro el merge
    if selected_to_active:
        bpy.data.objects.remove(selObject, do_unlink=True, do_id_user=True, do_ui_user=True)
    
    
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
    metallic = bpy.props.BoolProperty(name="Metallic",default=False)
    occlusion = bpy.props.BoolProperty(name="Occlusion",default=False)
    normal = bpy.props.BoolProperty(name="Normal",default=False)
    emit = bpy.props.BoolProperty(name="Emit",default=False)
    roughness = bpy.props.BoolProperty(name="Roughness",default=False)
    opacity = bpy.props.BoolProperty(name="Opacity",default=False)
    albedo = bpy.props.BoolProperty(name="Albedo",default=False)
    sizex = bpy.props.IntProperty(name="Size x", default= 1024)
    sizey = bpy.props.IntProperty(name="Size y", default= 1024)
    seltoact = bpy.props.BoolProperty(name="Selected to active", default= True)

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