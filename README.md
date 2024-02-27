# Wisc-HCI_scripts

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
 
