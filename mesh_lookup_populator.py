import os
import sys
import xml.etree.ElementTree as ET


def parse_urdf_for_meshes(parent_directory):
    all_mesh_filenames = []

    # Walk through all directories within the given parent directory
    for dir_root, dirs, files in os.walk(parent_directory):
        for file in files:
            if file.endswith('.urdf') or file.endswith('.xacro'):
                urdf_file_path = os.path.join(dir_root, file)  # Use 'dir_root' for directory root
                tree = ET.parse(urdf_file_path)
                xml_root = tree.getroot()  # Use 'xml_root' for XML root element

                # Find all mesh filenames in the current URDF file
                for mesh in xml_root.findall(".//mesh"):
                    filename_attr = mesh.get('filename')
                    if filename_attr:
                        all_mesh_filenames.append(filename_attr)

    return all_mesh_filenames

def scan_and_generate_imports(directory, urdf_directory):
    subdirs = ["visual"] # removed collision for now
    imports = []
    mesh_lookup_dict = {}

    # Parse the URDF file to get mesh filenames
    mesh_filenames = parse_urdf_for_meshes(urdf_directory)

    for subdir in subdirs:
        subdir_path = os.path.join(directory, subdir)
        if os.path.isdir(subdir_path):
            for root, dirs, files in os.walk(subdir_path):
                for file in files:
                    if file.endswith(".js"):
                        relative_path = os.path.relpath(os.path.join(root, file), directory)
                        import_name = os.path.splitext(file)[0]
                        import_path = f"./MeshLoaders/{directory}/{relative_path}".replace("\\", "/")
                        imports.append(f'import {import_name} from "{import_path}"')
                        # Add to mesh_lookup_dict if the import_name matches any in mesh_filenames
                        for mesh_filename in mesh_filenames:
                            if import_name in mesh_filename:
                                mesh_lookup_dict[mesh_filename] = import_name

    # Write imports and the mesh lookup dictionary to MeshLookup.js
    with open(os.path.join(directory, "MeshLookup.js"), "w") as outfile:
        outfile.writelines([f"{line}\n" for line in imports])
        outfile.write("\nconst MeshLookupTable = {\n")
        for key, value in mesh_lookup_dict.items():
            outfile.write(f'  "{key}": {value},\n')
        outfile.write("};\n")
        outfile.write("\nconst MeshLookup = (path) => MeshLookupTable[path]();")
        outfile.write("\nexport { MeshLookupTable, MeshLookup };")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: mesh_lookup_pupolator.py <base_directory containing collision and visual folders> <urdf_directory>")
        sys.exit(1)
    
    directory = sys.argv[1]
    urdf_file = sys.argv[2]
    scan_and_generate_imports(directory, urdf_file)

