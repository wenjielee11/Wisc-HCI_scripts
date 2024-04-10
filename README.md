# Wisc-HCI_scripts
 - *Note:* To make things easy. I would suggest running all of these commands in one specified directory.To start with, at the directory where you have the scripts, you should have(and will eventually have) the following format:
```bash
\Wisc-HCI_scripts
  ...scripts.py
  \robot_name (make this folder before you start!)
      robot.urdf (You should have it in this directory when you run mesh_lookup_populator.py)
      items_tf.json (generated by urdf_parser.py)
      \meshes (make this folder before you start!)
        \all your .STL files
      \visual (make this folder before you start!)
         all .js files generated by JSXToJS.py
         all .GLB files generated by StlToGLB.py
      \collision (make this folder before you start!)
         all .js files generated by JSXToJS.py
         all .GLB files generated by StlToGLB.py
```      
At the end of this pipeline, you may remove all .jsx files (NOT .js) and the \meshes folder. Refer back to the example above when you're running the scripts!
Make sure you run the commands in the order they are described below! 
More elaborate instructions here: https://docs.google.com/document/d/1uY_VvUoeKeTYmw3gFs3MHQNbhohR8GXxMARiu9CYFX0/edit
# StlToGlb.py: STL to GLB Converter

This script converts all STL files found in a specified directory (and its subdirectories) to GLB format using Blender's Python API. 

## Requirements

- **Blender:** This script is intended to be run within Blender's Python environment.
- **Python 3.x:** Ensure Blender's Python version matches the script requirements.

## Usage

To run this script, you will need to use Blender's command-line interface. The general command format is as follows:

```bash
blender --background --python StlToGlb.py -- [base_search_dir] [base_output_dir]
```
- `blender` is the command to run Blender.
- `--background` tells Blender to run without its GUI.
- `--python` GlbToJSX.py instructs Blender to execute the given Python script.
- `--` is used to indicate that the following arguments should be passed to the script.
- `[base_search_dir]` is the relative path to the directory where the script will search for STL files.
- `[base_output_dir]` is the relative path to the directory where the script will save the converted GLB files.

## Example 
```bash
blender --background --python GlbToJSX.py -- /path/to/source /path/to/destination
```
- Note: The path will be relative to where your current working directory is, i.e. The folder at which you are calling blender.

# GlbToJSX.py: GLB to JSX Converter

This script converts all `.glb` files in a specified folder to `.jsx` components using the `gltfjsx` tool.

## Requirements

- **Node.js and npm:** Ensure you have Node.js and npm installed to use `npx` and `gltfjsx`.
- **gltfjsx:** This script relies on the `gltfjsx` tool, which can be installed via npm.

## Installation of gltfjsx

Before running the script, you must install `gltfjsx` if you haven't already. You can install it globally using npm:

```bash
npm install -g gltfjsx
```
## Usage
To use this script, navigate to the directory where the script is located and run it with Python, providing the input and output directories as arguments:
```bash
python GlbToJSX.py input_folder output_folder
```
- `input_folder` is the directory containing the .glb files you want to convert, relative to where your script is.
- `output_folder` is the directory where you want the .jsx files to be saved, relative.
## Example
```bash
python GlbToJSX.py ./models ./jsxComponents
```
This will convert all .glb files found in ./models to .jsx components and save them in the ./jsxComponents directory.
## Notes
You may change the settings of the converter at line 25 where:
```python
command = f"npx gltfjsx {full_file_path} -o {output_file_path}"
```
Usage details are in this link: https://github.com/pmndrs/gltfjsx

# JSXToJS.py: JSX to JS Converter

This Python script is designed to convert `.jsx` files to `.js` files with the ability to specify scale and rotation for the models. It searches for `.glb` file references within the `.jsx` files, modifies their import statements, and applies transformations according to the provided command-line arguments.

## Requirements

- Python 3.x installed on your system.

## How to Run the Script

### Basic Usage

To run this script, navigate to the directory containing the script and use the following command format:

```bash
python JSXToJS.py input_dir output_dir [options]
```
- `input_dir` is the directory containing your .jsx files.
- `output_dir` is the directory where you want the converted .js files to be saved.

### Options
- `--scale`: Specifies the scale of the model in the format `[x,y,z]`. For example, `--scale [1,1,1]`.
- `--rotation`: Specifies the rotation of the model in the format `[x,y,z]`, where each component is an angle in radians. For example, `--rotation [0,0,0]`.
- *Note* : If you do not specify these flags, the script ignores them, and the parameters wont be added. to the JS code.

### Example Command:
```bash
python JSXToJS.py ../collision_jsx ../models/collision --scale [1,1,1] --rotation [0,0,0]
```
# mesh_lookup_populator.py : Populates a dictionary MeshLookup.js for robot-scene
This script is designed to assist in automating the process of importing mesh files from a Universal Robot Description Format (URDF) file into a JavaScript project. It scans a specified directory for JavaScript (.js) mesh loader files, generates import statements for them, and creates a lookup table that maps mesh filenames found in the URDF file to their corresponding JavaScript imports. This facilitates the dynamic loading of mesh files in web applications or other JavaScript-based projects.

This python script scans a urdf file for all entries of <mesh filename="..."> It then automatically writes the imports by appending the filename with .js, then puts the filename as a key and the resulting import as a value. For example, 
```
<mesh filename="package://p_grip_description/meshes/p_grip_2F/back_cover.STL">
```
results in 
```
import back_cover from "./MeshLoaders/./Lio/visual/back_cover.js"
const MeshLookupTable = {
 "package://p_grip_description/meshes/p_grip_2F/back_cover.STL": back_cover,
}```

## Requirements
- Python 3.x installed on your system.
### Basic Usage
To run this script, navigate to the directory containing the script:
Accepts two commands-line arguments:
- The base directory containing the visual subdirectory with the mesh loader JavaScript files.
- The path to the URDF file containing the mesh filenames.

The command to run the script looks like this:
```bash
python mesh_lookup_populator.py <base_directory> <urdf_file>
```
### Example:
Assuming your directories look like this:
```bash
/project
    /visual
       all mesh .js files generated by JSX to JS Converter
    /collision
       all mesh .js files generated by JSX to JS Converter
    robot.urdf
```
Your command should be:
```
python mesh_lookup_populator.py /path/to/project /path/to/project/robot.urdf
```
You will then find a file named MeshLookup.js at /project/MeshLookup.js
*Note*: This script is capable of generating both visual and collision Meshes. Simply change line 19 of script to include collisions.
*WIP*: adding unique names to the imports as several robots will have conflicting names, and collision visual meshes can conflict too.

# urdf_parser.py:Populates a .json file containing all tfs(joints) and items(links) of the robot. 
This Python script is designed to convert the contents of a Universal Robot Description Format (URDF) file into a structured JSON format. It specifically extracts joint and link information, including positions, rotations (expressed as quaternions), scales, and colors. The script handles URDF properties for dynamic value replacement and supports conversion from Euler angles to quaternions for rotation representation.
## Features:
- Parses URDF files to extract joints and links information.
- Handles dynamic replacement of values defined by <xacro:property> within the URDF.
- Converts rotations from Euler angles to quaternions.
- Generates a JSON file containing structured information about the robot's configuration, suitable for use in simulations, visualizations, or further processing.
## Requirements:
- Python 3.x installed on your system.
- a urdf file for your robot.
### Basic Usage:
To use the script, provide the source URDF file path and the destination JSON file path as command-line arguments:
```bash
python urdf_parser.py <source_urdf_file_path> <destination_json_file>
```
### Parameters:
Parameters
- `<source_urdf_file_path>`: Path to the URDF file to be parsed.
- `<destination_json_file>`: Path where the output JSON file will be saved.
### Example Command:
```bash
python urdf_parser.py path/to/robot.urdf path/to/tfs_items.json
```
### Output format:
The output JSON file will contain two main sections: `tfs` for joint transformations and `items` for link descriptions. Each section includes detailed information such as position, rotation, scale, and color. Rotation data is provided in quaternion format to facilitate usage in 3D environments.

# What next? Checkout: https://github.com/wenjielee11/Mesh-Test to test your robot and see if it works.

