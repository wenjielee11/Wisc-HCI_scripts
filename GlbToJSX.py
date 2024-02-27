import os
import subprocess
import argparse

def convert_glb_to_jsx(folder_path, output_path):
    """
    Converts all .glb files in the specified folder to .jsx components using gltfjsx.
    
    Parameters:
    - folder_path: The path to the folder containing .glb files.
    """
    # Check if the folder exists
    if not os.path.isdir(folder_path):
        print(f"The folder '{folder_path}' does not exist.")
        return
    os.makedirs(output_path, exist_ok=True)
    # Iterate over all files in the folder
    for file in os.listdir(folder_path):
        # Check if the file is a .glb file
        if file.endswith(".glb"):
            # Construct the full path to the file
            full_file_path = os.path.join(folder_path, file)
            output_file_path = os.path.join(output_path,os.path.splitext(file)[0] + ".jsx")
            # Construct the command to be executed
            command = f"npx gltfjsx {full_file_path} -o {output_file_path} -I"
            print(f"Converting {file}...")
            try:
                # Execute the command
                subprocess.run(command, check=True, shell=True)
                print(f"Conversion successful for {file}")
            except subprocess.CalledProcessError as e:
                print(f"Error converting {file}: {e}")

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Convert GLB files to JSX components.")
    parser.add_argument("input_folder", type=str, help="Input folder containing .glb files.")
    parser.add_argument("output_folder", type=str, help="Output folder for the converted .jsx files.")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Call the conversion function with the provided arguments
    convert_glb_to_jsx(args.input_folder, args.output_folder)
