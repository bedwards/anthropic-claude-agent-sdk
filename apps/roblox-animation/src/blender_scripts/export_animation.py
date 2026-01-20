"""
Export animation from Blender to FBX format.

Usage:
    blender --background --python export_animation.py -- input.blend output.fbx

This script exports the active armature's animation to FBX format
compatible with anim2rbx for conversion to Roblox KeyframeSequence.
"""

import sys


def export_animation(input_file: str, output_file: str) -> None:
    """Export animation from Blender file to FBX."""
    # Import bpy here since it's only available when running in Blender
    import bpy

    # Open the input file
    bpy.ops.wm.open_mainfile(filepath=input_file)

    # Find the armature
    armature = None
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            armature = obj
            break

    if not armature:
        print("Error: No armature found in file", file=sys.stderr)
        sys.exit(1)

    # Select only the armature
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature

    # Export to FBX with animation settings
    bpy.ops.export_scene.fbx(
        filepath=output_file,
        use_selection=True,
        object_types={"ARMATURE"},
        use_armature_deform_only=True,
        add_leaf_bones=False,
        bake_anim=True,
        bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=True,
        bake_anim_step=1.0,
        bake_anim_simplify_factor=0.0,  # No simplification
    )

    print(f"Exported animation to {output_file}")


def main() -> None:
    """Parse arguments and run export."""
    # Get arguments after '--'
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        print("Usage: blender --background --python export_animation.py -- input.blend output.fbx")
        sys.exit(1)

    if len(argv) < 2:
        print("Error: Need input.blend and output.fbx arguments")
        sys.exit(1)

    input_file = argv[0]
    output_file = argv[1]

    export_animation(input_file, output_file)


if __name__ == "__main__":
    main()
