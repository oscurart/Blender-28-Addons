import bpy
import os

object = bpy.context.object
matList = [mat for mat in bpy.context.object.data.materials]
matList = list(set(matList))
imageSize = 2048
bump = False

materialSlots = [slot.material for slot in bpy.context.object.material_slots]

#---------------------------------------------------------------------------------------
#normal map previo
print("Render: NM")
imgNM = bpy.data.images.new("NM", imageSize, imageSize,  alpha=True, float_buffer=False)

for mat in matList:
    nodeNM = mat.node_tree.nodes.new("ShaderNodeTexImage")
    nodeNM.image = imgNM
    mat.node_tree.nodes.active = nodeNM

#bakeo    
bpy.ops.object.bake(type='NORMAL', pass_filter=set(), filepath="", width=imageSize, height=imageSize, margin=64, use_selected_to_active=False, cage_extrusion=0, cage_object="", normal_space='TANGENT', normal_r='POS_X', normal_g='POS_Y', normal_b='POS_Z', save_mode='INTERNAL', use_clear=False, use_cage=False, use_split_materials=False, use_automatic_name=False, uv_layer="")   
print("Done!")
#---------------------------------------------------------------------------------------

#ambient occlusion mat
imgAO = bpy.data.images.new("AO", imageSize, imageSize,  alpha=True, float_buffer=True)
occlusion = bpy.data.materials.new("Occlusion")
occlusion.use_nodes = 1
outNode = occlusion.node_tree.nodes["Material Output"]
geoNode = occlusion.node_tree.nodes.new("ShaderNodeAmbientOcclusion")
nmNode = occlusion.node_tree.nodes.new("ShaderNodeNormalMap") ##
nmImgNode = occlusion.node_tree.nodes.new("ShaderNodeTexImage") ##
nmImgNode.image = imgNM ##
if bump:
    occlusion.node_tree.links.new(geoNode.inputs[2],nmNode.outputs[0]) ##DISABLE NORMALS
nmImgNode.color_space = "NONE"
occlusion.node_tree.links.new(nmNode.inputs[1],nmImgNode.outputs[0]) ##
geoNode.inside = False
geoNode.inputs['Distance'].default_value = .2
occlusion.node_tree.links.new(outNode.inputs[0],geoNode.outputs[1])
nodeOcclusion = occlusion.node_tree.nodes.new("ShaderNodeTexImage")
nodeOcclusion.image = imgAO
occlusion.node_tree.nodes.active = nodeOcclusion
#---------------------------------------------------------------------------------------

#pointness mat
imgPointness = bpy.data.images.new("EDGES", imageSize, imageSize,  alpha=True, float_buffer=True)
pointness = bpy.data.materials.new("Pointness")
pointness.use_nodes = 1
outNode = pointness.node_tree.nodes["Material Output"]
geoNode = pointness.node_tree.nodes.new("ShaderNodeAmbientOcclusion")
geoNode.inside = True
geoNode.inputs['Distance'].default_value = .005
nmNode = pointness.node_tree.nodes.new("ShaderNodeNormalMap") ##
nmImgNode = pointness.node_tree.nodes.new("ShaderNodeTexImage") ##
nmImgNode.image = imgNM ##
if bump:
    pointness.node_tree.links.new(geoNode.inputs[2],nmNode.outputs[0]) ## DISABLE NORMALS
nmImgNode.color_space = "NONE"
pointness.node_tree.links.new(nmNode.inputs[1],nmImgNode.outputs[0]) ##
pointness.node_tree.links.new(outNode.inputs[0],geoNode.outputs[1])
nodePointness = pointness.node_tree.nodes.new("ShaderNodeTexImage")
nodePointness.image = imgPointness
pointness.node_tree.nodes.active = nodePointness


def packImage(image):
    scn = bpy.data.scenes.new('img_settings')
    scn.render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
    scn.render.image_settings.color_mode = 'RGBA'
    scn.render.image_settings.color_depth = '32'
    img_path = bpy.path.abspath('//')
    img_file = image.name+'.exr'
    image.save_render(img_path+img_file, scene=scn)
    bpy.data.scenes.remove(scn, do_unlink=True)

    bpy.data.images.remove(image)
    bpy.ops.image.open(filepath=img_path+img_file)
    image = bpy.data.images[img_file]
    image.pack()
    os.remove(img_path+img_file)    


#AO 
print("Render: AO")
#pointness material en todos los slots
for ms in object.material_slots:
    ms.material = occlusion  
#bakeo    
bpy.ops.object.bake(type='EMIT', pass_filter=set(), filepath="", width=imageSize, height=imageSize, margin=64, use_selected_to_active=False, cage_extrusion=0, cage_object="", normal_space='TANGENT', normal_r='POS_X', normal_g='POS_Y', normal_b='POS_Z', save_mode='INTERNAL', use_clear=False, use_cage=False, use_split_materials=False, use_automatic_name=False, uv_layer="")    

packImage(imgAO) #pack
print("Done!")

#POINTNESS
print("Render: Edges")
#pointness material en todos los slots
for ms in object.material_slots:
    ms.material = pointness    
#bakeo    
bpy.ops.object.bake(type='EMIT', pass_filter=set(), filepath="", width=imageSize, height=imageSize, margin=64, use_selected_to_active=False, cage_extrusion=0, cage_object="", normal_space='TANGENT', normal_r='POS_X', normal_g='POS_Y', normal_b='POS_Z', save_mode='INTERNAL', use_clear=False, use_cage=False, use_split_materials=False, use_automatic_name=False, uv_layer="")    

packImage(imgPointness) #pack
print("Done!")

#devuelvo slots materials
for i,ms in zip(materialSlots,object.material_slots):
    ms.material = i
    
    
#remuevo materiales temporales y normal
bpy.data.materials.remove(pointness) 
bpy.data.materials.remove(occlusion) 
bpy.data.images.remove(imgNM)
for mat in matList:
    for node in mat.node_tree.nodes:
        if node.type == "TEX_IMAGE":            
            if node.image == None:
                mat.node_tree.nodes.remove(node)