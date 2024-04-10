import bpy
import os
import sys

# Get the arguments passed to the script
argv = sys.argv
argv = argv[argv.index("--") + 1:]  # Get all args after "--"

# Base directory to search for DAE files
base_search_dir = argv[0]
# The base directory where GLB files should be saved
base_output_dir = argv[1]

def convert_dae_to_glb(source_folder, output_folder):
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if file.lower().endswith(".dae"):
                # Path to the current file
                dae_file_path = os.path.join(root, file)
                # Define the export name and path
                relative_dir = os.path.relpath(root, source_folder)
                output_dir = os.path.join(output_folder, relative_dir)
                os.makedirs(output_dir, exist_ok=True)
                export_name = os.path.splitext(file)[0] + '.glb'
                glb_file_path = os.path.join(output_dir, export_name)

                # Clear the scene
                bpy.ops.wm.read_factory_settings(use_empty=True)

                # Import DAE
                bpy.ops.wm.collada_import(filepath=dae_file_path)

                # Export to GLB
                bpy.ops.export_scene.gltf(filepath=glb_file_path, export_format='GLB')
                print(f"Converted {dae_file_path} to {glb_file_path}")

# Ensure base_output_dir is an absolute path
base_output_dir = os.path.abspath(base_output_dir)

convert_dae_to_glb(base_search_dir, base_output_dir)
