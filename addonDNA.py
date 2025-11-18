bl_info = {
    "name": "Custom DNA Generator",
    "author": "Your Name",
    "version": (1, 3),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > DNA Tool",
    "description": "Generates a customizable DNA Double Helix with glowing text options",
    "category": "Add Mesh",
}

import bpy
import math
import mathutils
import random


# --- Property Group to store user settings ---
class DNA_Properties(bpy.types.PropertyGroup):
    # Geometry Settings (Updated Defaults from Image)
    helix_radius: bpy.props.FloatProperty(name="Helix Radius", default=2.51, min=0.1)
    pitch: bpy.props.FloatProperty(name="Pitch", default=10.0, min=0.1)
    base_pair_height: bpy.props.FloatProperty(name="Base Pair Height", default=0.78, min=0.01)
    num_base_pairs: bpy.props.IntProperty(name="Num Base Pairs", default=60, min=2)
    backbone_radius: bpy.props.FloatProperty(name="Backbone Radius", default=0.30, min=0.01)

    # Nucleotide Dimensions (Updated Defaults from Image)
    nuc_height: bpy.props.FloatProperty(
        name="Nucleotide Height", description="Vertical height (face)",
        default=0.43, min=0.01
    )
    nuc_thickness: bpy.props.FloatProperty(
        name="Nucleotide Thickness", description="Depth (Z axis)",
        default=0.1, min=0.01
    )
    rung_gap_fill: bpy.props.FloatProperty(
        name="Gap Fill", description="1.0 touches backbone",
        default=0.95, min=0.1, max=1.5
    )

    # Angles & Unwinding
    helix_start_angle: bpy.props.FloatProperty(name="Start Angle", default=0.0)
    dna_torsion_angle: bpy.props.FloatProperty(name="Torsion Angle", default=36.0)
    unwind_start: bpy.props.FloatProperty(
        name="Unwind Start %", default=0.6, min=0.0, max=1.0, subtype='FACTOR'
    )
    unwind_end: bpy.props.FloatProperty(
        name="Unwind End %", default=0.9, min=0.0, max=1.0, subtype='FACTOR'
    )

    # Label controls (Updated Defaults from Image)
    label_scale: bpy.props.FloatProperty(
        name="Label Scale", default=1.52, min=0.1, max=5.0,
        description="Global scale factor for nucleotide letters"
    )

    # Colors & Emission
    col_text: bpy.props.FloatVectorProperty(
        name="Text Color", subtype='COLOR',
        default=(1.0, 1.0, 1.0, 1.0), size=4, min=0, max=1
    )
    text_emission_strength: bpy.props.FloatProperty(
        name="Text Emission", default=1.0, min=0.0, max=100.0,
        description="Strength of the light emitted by the text"
    )

    col_a: bpy.props.FloatVectorProperty(
        name="Adenine (A)", subtype='COLOR',
        default=(0.8, 0.3, 0.3, 1), size=4, min=0, max=1
    )
    col_t: bpy.props.FloatVectorProperty(
        name="Thymine (T)", subtype='COLOR',
        default=(0.3, 0.3, 0.9, 1), size=4, min=0, max=1
    )
    col_g: bpy.props.FloatVectorProperty(
        name="Guanine (G)", subtype='COLOR',
        default=(0.3, 0.9, 0.3, 1), size=4, min=0, max=1
    )
    col_c: bpy.props.FloatVectorProperty(
        name="Cytosine (C)", subtype='COLOR',
        default=(0.9, 0.9, 0.3, 1), size=4, min=0, max=1
    )
    col_bk_a: bpy.props.FloatVectorProperty(
        name="Backbone A", subtype='COLOR',
        default=(0.9, 0.6, 0.3, 1), size=4, min=0, max=1
    )
    col_bk_b: bpy.props.FloatVectorProperty(
        name="Backbone B", subtype='COLOR',
        default=(0.6, 0.3, 0.9, 1), size=4, min=0, max=1
    )


# --- The Operator (The Logic) ---
class MESH_OT_generate_dna(bpy.types.Operator):
    """Generates the DNA Structure"""
    bl_idname = "mesh.generate_dna"
    bl_label = "Generate DNA"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.dna_tool_props
        self.generate_dna(context, props)
        return {'FINISHED'}

    def get_or_create_material(self, name, color_rgba, emission_strength=0.0):
        """Create a CLEAN flat-color Principled material with optional Emission."""
        if name in bpy.data.materials:
            mat = bpy.data.materials[name]
        else:
            mat = bpy.data.materials.new(name=name)

        mat.use_nodes = True

        # Clear any previous nodes
        nodes = mat.node_tree.nodes
        nodes.clear()

        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (300, 0)
        mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

        # Set Base Color
        bsdf.inputs['Base Color'].default_value = color_rgba
        bsdf.inputs['Roughness'].default_value = 0.2

        # Handle Emission (Check for Blender 4.0+ naming vs older naming)
        if emission_strength > 0:
            # Try "Emission Color" (4.0+) first, fall back to "Emission"
            if 'Emission Color' in bsdf.inputs:
                bsdf.inputs['Emission Color'].default_value = color_rgba
                bsdf.inputs['Emission Strength'].default_value = emission_strength
            elif 'Emission' in bsdf.inputs:
                bsdf.inputs['Emission'].default_value = color_rgba
                bsdf.inputs['Emission Strength'].default_value = emission_strength

        return mat

    def create_helical_curve(self, name, points, radius, material, collection):
        curve_data = bpy.data.curves.new(name, type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.resolution_u = 4
        curve_data.bevel_depth = radius
        curve_data.bevel_resolution = 6
        curve_data.use_fill_caps = True

        spline = curve_data.splines.new('NURBS')
        spline.points.add(len(points) - 1)

        for i, coord in enumerate(points):
            spline.points[i].co = (coord.x, coord.y, coord.z, 1.0)

        spline.use_endpoint_u = True

        curve_obj = bpy.data.objects.new(name, curve_data)
        if material:
            curve_obj.data.materials.append(material)

        collection.objects.link(curve_obj)
        return curve_obj

    def create_cube(self, loc, rot, scale, material, collection):
        mesh = bpy.data.meshes.new('Nucleotide_Mesh')
        obj = bpy.data.objects.new('Nucleotide', mesh)

        # Create mesh data for a cube manually
        verts = [(-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5),
                 (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)]
        faces = [(0, 1, 3, 2), (2, 3, 7, 6), (6, 7, 5, 4), (4, 5, 1, 0), (2, 6, 4, 0), (7, 3, 1, 5)]

        mesh.from_pydata(verts, [], faces)
        mesh.update()

        obj.location = loc
        obj.rotation_euler = rot
        obj.scale = scale

        if material:
            obj.data.materials.append(material)

        collection.objects.link(obj)
        return obj

    # --- create cube + double-sided labels for each nucleotide ---
    def create_nucleotide_with_label(self, base_label, loc, rot, scale, material_nuc, material_text, collection, props):
        """Create the nucleotide cube and double-sided 3D text labels."""
        
        # 1. Create the Cube (Nucleotide)
        nuc_obj = self.create_cube(loc, rot, scale, material_nuc, collection)
        nuc_obj.name = f"Nucleotide_{base_label}"

        # 2. Helper to create text
        def create_text_obj(suffix, offset_local, align_vec_z):
            # Calculate World Position of the label
            rot_mat = rot.to_matrix()
            offset_world = rot_mat @ offset_local
            text_loc = loc + offset_world
            
            # Create Text Curve
            text_curve = bpy.data.curves.new(f"NucText_{base_label}_{suffix}", type='FONT')
            text_curve.body = base_label
            text_curve.align_x = 'CENTER'
            text_curve.align_y = 'CENTER'
            text_curve.extrude = 0.02 * scale[2] * props.label_scale

            t_obj = bpy.data.objects.new(f"NucLabel_{base_label}_{suffix}", text_curve)
            t_obj.location = text_loc
            
            # --- ORIENTATION FIX ---
            # Cube Z is the tangential face normal.
            cube_normal = rot_mat.col[2] 
            
            # Depending on front/back, we flip the target normal
            target_z = cube_normal * align_vec_z # Vector
            target_y = mathutils.Vector((0, 0, 1)) # World Up
            target_x = target_y.cross(target_z) # Right vector
            
            # Re-orthogonalize Y
            target_y = target_z.cross(target_x)
            
            # Create rotation matrix from columns
            mat_rot = mathutils.Matrix((target_x, target_y, target_z)).transposed()
            t_obj.rotation_euler = mat_rot.to_euler()

            # Scale Text
            text_size = scale[0] * 0.6 * props.label_scale
            t_obj.scale = (text_size, text_size, text_size)

            if material_text:
                t_obj.data.materials.append(material_text)
            
            collection.objects.link(t_obj)
            return t_obj

        # 3. Create Front and Back Text
        create_text_obj("Front", mathutils.Vector((0, 0, scale[2]*0.51)), 1.0)
        create_text_obj("Back", mathutils.Vector((0, 0, -scale[2]*0.51)), -1.0)

        return nuc_obj

    def generate_dna(self, context, props):
        # Cleanup old collection
        dna_collection_name = "DNA_Double_Helix"
        if dna_collection_name in bpy.data.collections:
            dna_collection = bpy.data.collections[dna_collection_name]
            for obj in dna_collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
        else:
            dna_collection = bpy.data.collections.new(dna_collection_name)
            context.scene.collection.children.link(dna_collection)

        # Materials Setup
        mats = {}
        mats['A'] = self.get_or_create_material("DNA_Adenine", props.col_a)
        mats['T'] = self.get_or_create_material("DNA_Thymine", props.col_t)
        mats['G'] = self.get_or_create_material("DNA_Guanine", props.col_g)
        mats['C'] = self.get_or_create_material("DNA_Cytosine", props.col_c)
        mats['Backbone_A'] = self.get_or_create_material("DNA_Backbone_A", props.col_bk_a)
        mats['Backbone_B'] = self.get_or_create_material("DNA_Backbone_B", props.col_bk_b)
        
        # Text Material with Emission
        mats['Text'] = self.get_or_create_material(
            "DNA_Text_Color", 
            props.col_text, 
            emission_strength=props.text_emission_strength
        )

        # Calculation Variables
        initial_rotation_step_rad = math.radians(props.dna_torsion_angle)
        unwind_start_index = int(props.num_base_pairs * props.unwind_start)
        unwind_end_index = int(props.num_base_pairs * props.unwind_end)

        points_a = []
        points_b = []
        accumulated_angle = props.helix_start_angle

        for i in range(props.num_base_pairs):
            z_pos = i * props.base_pair_height

            # Unwinding Logic
            current_rotation_step = initial_rotation_step_rad
            if i >= unwind_start_index and i < unwind_end_index:
                factor = (i - unwind_start_index) / (unwind_end_index - unwind_start_index)
                current_rotation_step = initial_rotation_step_rad * (1.0 - factor)
            elif i >= unwind_end_index:
                current_rotation_step = 0.0

            accumulated_angle += current_rotation_step

            x_a = props.helix_radius * math.cos(accumulated_angle)
            y_a = props.helix_radius * math.sin(accumulated_angle)
            loc_a = mathutils.Vector((x_a, y_a, z_pos))

            x_b = props.helix_radius * math.cos(accumulated_angle + math.pi)
            y_b = props.helix_radius * math.sin(accumulated_angle + math.pi)
            loc_b = mathutils.Vector((x_b, y_b, z_pos))

            points_a.append(loc_a)
            points_b.append(loc_b)

            # Rotation Logic for Nucleotides
            vec_ab = loc_b - loc_a
            distance = vec_ab.length
            angle_z = math.atan2(vec_ab.y, vec_ab.x) + (math.pi / 2)
            rot_align_z = mathutils.Euler((0, 0, angle_z), 'XYZ').to_matrix()
            rot_flip_y = mathutils.Euler((0, math.pi / 2, 0), 'XYZ').to_matrix()
            final_rot = (rot_align_z @ rot_flip_y).to_euler()

            # Random Base Pair
            pair_choice = random.choice(['AT', 'TA', 'GC', 'CG'])

            if pair_choice == 'AT':
                label_a, label_b = 'A', 'T'
                mat_nuc_a, mat_nuc_b = mats['A'], mats['T']
            elif pair_choice == 'TA':
                label_a, label_b = 'T', 'A'
                mat_nuc_a, mat_nuc_b = mats['T'], mats['A']
            elif pair_choice == 'GC':
                label_a, label_b = 'G', 'C'
                mat_nuc_a, mat_nuc_b = mats['G'], mats['C']
            elif pair_choice == 'CG':
                label_a, label_b = 'C', 'G'
                mat_nuc_a, mat_nuc_b = mats['C'], mats['G']

            rung_length = (distance / 2) * props.rung_gap_fill
            pos_nuc_a = loc_a + (vec_ab * 0.25)
            pos_nuc_b = loc_a + (vec_ab * 0.75)

            scale_nuc = (props.nuc_height, rung_length, props.nuc_thickness)

            # Create Nucleotides
            self.create_nucleotide_with_label(
                label_a, pos_nuc_a, final_rot, scale_nuc, mat_nuc_a, mats['Text'], dna_collection, props
            )
            self.create_nucleotide_with_label(
                label_b, pos_nuc_b, final_rot, scale_nuc, mat_nuc_b, mats['Text'], dna_collection, props
            )

        self.create_helical_curve("Backbone_Strand_A", points_a, props.backbone_radius, mats['Backbone_A'], dna_collection)
        self.create_helical_curve("Backbone_Strand_B", points_b, props.backbone_radius, mats['Backbone_B'], dna_collection)


# --- The Panel (The UI) ---
class VIEW3D_PT_dna_gen(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "DNA Generator"
    bl_idname = "VIEW3D_PT_dna_gen"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DNA Tool'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.dna_tool_props

        box = layout.box()
        box.label(text="Geometry Parameters")
        box.prop(props, "helix_radius")
        box.prop(props, "pitch")
        box.prop(props, "base_pair_height")
        box.prop(props, "num_base_pairs")
        box.prop(props, "backbone_radius")

        box = layout.box()
        box.label(text="Nucleotide Size")
        box.prop(props, "nuc_height")
        box.prop(props, "nuc_thickness")
        box.prop(props, "rung_gap_fill")

        box = layout.box()
        box.label(text="Rotation & Unwinding")
        box.prop(props, "helix_start_angle")
        box.prop(props, "dna_torsion_angle")
        box.prop(props, "unwind_start", slider=True)
        box.prop(props, "unwind_end", slider=True)

        box = layout.box()
        box.label(text="Labels & Emission")
        box.prop(props, "label_scale")
        box.prop(props, "col_text") 
        box.prop(props, "text_emission_strength")

        box = layout.box()
        box.label(text="Base Colors")
        row = box.row()
        row.prop(props, "col_a")
        row.prop(props, "col_t")
        row = box.row()
        row.prop(props, "col_g")
        row.prop(props, "col_c")

        box.label(text="Backbone Colors")
        row = box.row()
        row.prop(props, "col_bk_a")
        row.prop(props, "col_bk_b")

        layout.separator()
        layout.operator("mesh.generate_dna", icon='MESH_DATA')


# --- Registration ---
classes = (
    DNA_Properties,
    MESH_OT_generate_dna,
    VIEW3D_PT_dna_gen,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.dna_tool_props = bpy.props.PointerProperty(type=DNA_Properties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.dna_tool_props


if __name__ == "__main__":
    register()