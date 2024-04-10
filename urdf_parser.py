import xml.etree.ElementTree as ET
import math
import json
import sys
import re
import os 

import ast
import operator

_AXES2TUPLE = {
    'sxyz': [0, 0, 0, 0], 'sxyx': [0, 0, 1, 0], 'sxzy': [0, 1, 0, 0], 'sxzx': [0, 1, 1, 0],
    'syzx': [1, 0, 0, 0], 'syzy': [1, 0, 1, 0], 'syxz': [1, 1, 0, 0], 'syxy': [1, 1, 1, 0],
    'szxy': [2, 0, 0, 0], 'szxz': [2, 0, 1, 0], 'szyx': [2, 1, 0, 0], 'szyz': [2, 1, 1, 0],
    'rzyx': [0, 0, 0, 1], 'rxyx': [0, 0, 1, 1], 'ryzx': [0, 1, 0, 1], 'rxzx': [0, 1, 1, 1],
    'rxzy': [1, 0, 0, 1], 'ryzy': [1, 0, 1, 1], 'rzxy': [1, 1, 0, 1], 'ryxy': [1, 1, 1, 1],
    'ryxz': [2, 0, 0, 1], 'rzxz': [2, 0, 1, 1], 'rxyz': [2, 1, 0, 1], 'rzyz': [2, 1, 1, 1]
}

_NEXT_AXIS = [1, 2, 0, 1]

def safe_eval(expr, variables):
    allowed_operators = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.BitXor: operator.xor,
        ast.USub: operator.neg
    }

    def eval_(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            return allowed_operators[type(node.op)](eval_(node.left), eval_(node.right))
        elif isinstance(node, ast.UnaryOp):
            return allowed_operators[type(node.op)](eval_(node.operand))
        elif isinstance(node, ast.Name):
            if node.id in variables:
                return variables[node.id]
            else:
                raise NameError(f"Name {node.id} is not defined")
        else:
            raise TypeError(node)

    expr_ast = ast.parse(expr, mode='eval').body
    return eval_(expr_ast)

# Parses a given input string and replaces the ${...} value. Use this if you have a weird format like:
# <origin xyz="${camera_link *0.05} 0 0" rpy="0 0 0"/> where <xacro:property name="camera_link" value="0.05" />
def parseString(input_string: str, property_table):
    pattern = r'\$\{(.*?)\}'

    # Add more default properties to swap if you encounter errors. 
    # Lio is special and refuses to define their property values normally.
    property_table['pi'] = str(math.pi)
    
    def replace_match(match):
        expression = match.group(1)
        for var in re.findall(r'[a-zA-Z_][a-zA-Z_0-9]*', expression):
            if var in property_table:
                # Attempt to replace variable names with their values, converting to str for eval
                expression = expression.replace(var, property_table[var])
        try:
            # Evaluate the expression and replace in the input string
            result = str(safe_eval(expression, property_table))

            return result
        except Exception as e:
            print(f"Error evaluating expression '{expression}': {e}")
            return match.group(0)  # Return the original string if error

    # Replace all matches in the input string
    result_string = re.sub(pattern, replace_match, input_string)
    return result_string



def quaternion_from_euler(ai, aj, ak, axes='sxyz'):
    firstaxis, parity, repetition, frame = _AXES2TUPLE[axes.lower()]
    i = firstaxis + 1
    j = _NEXT_AXIS[i + parity - 1] + 1
    k = _NEXT_AXIS[i - parity] + 1

    if frame:
        ai, ak = ak, ai
    if parity:
        aj = -aj

    ai, aj, ak = ai / 2.0, aj / 2.0, ak / 2.0
    ci, si = math.cos(ai), math.sin(ai)
    cj, sj = math.cos(aj), math.sin(aj)
    ck, sk = math.cos(ak), math.sin(ak)
    cc, cs = ci * ck, ci * sk
    sc, ss = si * ck, si * sk

    quaternion = [None, None, None, None]
    if repetition:
        quaternion[0] = cj * (cc - ss)
        quaternion[i] = cj * (cs + sc)
        quaternion[j] = sj * (cc + ss)
        quaternion[k] = sj * (cs - sc)
    else:
        quaternion[0] = cj * cc + sj * ss
        quaternion[i] = cj * sc - sj * cs
        quaternion[j] = cj * ss + sj * cc
        quaternion[k] = cj * cs - sj * sc

    if parity:
        quaternion[j] *= -1

    return quaternion

def parse_urdf_for_joints(urdf_content, is_main):
    # Parse the URDF XML content
    root = ET.fromstring(urdf_content)
    joints_info = {}
    # Define the namespace
    namespace = {'xacro': 'http://www.ros.org/wiki/xacro'}

    # Find all xacro:property elements
    property_elements = root.findall('.//xacro:property', namespaces=namespace)
    property_table = {}
    # getting all external properties to parse
    for property in property_elements:
        property_table[property.get('name')] = property.get('value')
    # print(property_table)
     # Maps for parent-child relationships and tracking all links
    parents = set()
    children = set()
    parent_count = {}

    # Find all <joint> elements
    joints = root.findall('joint')
    for joint in joints:
        joint_name = joint.get('name')
        # print(joint_name)
        if joint.find('origin') is None: 
            continue
        origin =  joint.find('origin').attrib
        parent = joint.find('parent').get('link')
        child = joint.find('child').get('link')

        # Populate the parent_child_map and all_links set
        parents.add(parent)
        children.add(child)
        if parent in parent_count:
            parent_count[parent] += 1
        else:
            parent_count[parent] = 1

        # Check if the urdf specifies a property value to be replaced.
        xyz = list(map(float, parseString(origin['xyz'], property_table).split()))
        rpy = list(map(float, parseString(origin.get('rpy', '0 0 0').strip(), property_table).split()))

        # Convert from Euler angles (rpy) to quaternion
        quaternion = quaternion_from_euler(rpy[0], rpy[1], rpy[2], "sxyz")

        joints_info[child] = {
            'frame': parent,
            'position': {'x': xyz[0], 'y': xyz[1], 'z': xyz[2]},
            'rotation': {'w': quaternion[0], 'x': quaternion[1], 'y': quaternion[2], 'z': quaternion[3]},
            'scale': {'x': 1, 'y': 1, 'z': 1}
        }

    # Add base_link information
    if is_main:
        # Identify the base_link
        potential_base_links = (parents - children) if (parents - children) else None
        base_link = None
        highest_count = -1
        if potential_base_links is not None:
            for link in potential_base_links:
                count = parent_count.get(link, 0)
                if count > highest_count:
                    base_link = link
                    highest_count = count

            joints_info[base_link] = {
                'frame': "world",
                'position': {'x': 0, 'y': 0, 'z': 0},
                'rotation': {'w': 1, 'x': 0, 'y': 0, 'z': 0},
                'scale': {'x': 1, 'y': 1, 'z': 1}
            }
            print("base_link identified as: "+ str(base_link))
    return joints_info

def parse_urdf_for_links(urdf_content):
    root = ET.fromstring(urdf_content)
    links = root.findall('.//link')
    materials = root.findall('.//material')
    items = {}  # New dictionary to populate
    # Find all xacro:property elements
    namespace = {'xacro': 'http://www.ros.org/wiki/xacro'}
    property_elements = root.findall('.//xacro:property', namespaces=namespace)
    property_table = {}
    # getting all external properties to parse
    for property in property_elements:
        property_table[property.get('name')] = property.get('value')
    # Create a materials map
    materials_map = {}
    # Change your predefined geometry shape mapping here. In the scenario of Lio,
    # box = cube
    predefined_mapping = {
        "box": "cube",
        "cylinder": "cylinder",
        "sphere": "sphere",
    }

    for material in materials:
        name = material.get('name')
        if material.find('color') is not None:
            color = list(map(float, material.find('color').get('rgba').split()))
            materials_map[name] = {"r": color[0], "g": color[1], "b": color[2], "a": color[3]}

    
    for link in links:
        link_name = link.get('name')
        # print(link_name)
        visual = link.find('visual')
        geometry = None
        scale = None
        if visual is not None and visual.find('geometry/mesh') is not None:
            mesh = visual.find('geometry/mesh')
            geometry = mesh.get('filename')
            if mesh.get('scale'):
                scale = list(map(float, parseString(mesh.get('scale'), property_table).split()))
        elif visual is not None and visual.find("geometry") is not None:
            for shape in predefined_mapping:
                if visual.find('geometry/'+shape) is not None:
                    geometry = predefined_mapping[shape]
                    size_node = visual.find(f"geometry/{shape}")
                    if shape == "box" and size_node is not None:
                            size = list(map(float, parseString(size_node.get('size'), property_table).split()))
                            scale = [size[0], size[1], size[2]]  # Update scale based on size
                    break  # Exit loop after finding the first matching shape
                   

        if link_name is not None and visual is not None and geometry is not None:
            color = {"r": 1, "g": 1, "b": 1, "a": 1}  # Default color
            # Check if color is defined directly
            if visual.find('material/color') is not None:
                arr_color = list(map(float, visual.find('material/color').get('rgba').split()))
                color = {"r":arr_color[0], "g":arr_color[1], "b":arr_color[2], "a":arr_color[3]}
            elif visual.find('material') is not None and materials_map.get(visual.find('material').get('name')):
                # Use material name to find color
                color = materials_map[visual.find('material').get('name')]
                
            
            # Check if origin is present
            origin = visual.find('origin')
            xyz = [0.0, 0.0, 0.0]
            rpy = [0.0, 0.0, 0.0]

            if origin is not None:
                xyz = list(map(float, origin.get('xyz', '0 0 0').split()))
                rpy = list(map(float, parseString(origin.get('rpy', '0 0 0'), property_table).split()))
            items[link_name] = {
                "shape": geometry,
                "name": link_name,
                "frame": link_name,
                "position": {"x": xyz[0], "y": xyz[1], "z": xyz[2]},
                "rotation": {"w": 1, "x": rpy[0], "y": rpy[1], "z": rpy[2]},
                "color": color,
                "scale": {"x": scale[0], "y": scale[1], "z": scale[2]} if scale else {"x": 1, "y": 1, "z": 1},
                "highlight": False
            }

        elif link_name is not None:
            items[link_name] = {
                "shape": geometry,
                "name": link_name,
                "frame": link_name,
                "position": {"x": 0, "y": 0, "z": 0},
                "rotation": {"w": 1, "x": 0, "y": 0, "z": 0},
                "color": "",
                "scale": {"x": 1, "y": 1, "z": 1},
                "highlight": False
            }
    return items

def read_urdf_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        sys.exit(1)

def read_urdf_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def write_to_json_file(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def main():
    if len(sys.argv) != 4:
        print("Usage: python urdf_parser.py <parent_directory_path> <destination_json_file> <main_urdf_name>")
        sys.exit(1)
    
    parent_directory_path = sys.argv[1]
    destination_json_file_path = sys.argv[2]
    main_file = sys.argv[3]
    
    # Initialize the dictionaries to store combined information from all URDF files
    combined_tfs = {}  # For joints_info
    combined_items = {}  # For links_info

    # Iterate over all directories starting from the parent directory
    for root, dirs, files in os.walk(parent_directory_path):
        print(f"walking through {str(dirs)}")
        for file in files:
            if file.endswith('.urdf') or file.endswith(".xacro"):
                print(f"converting {file}...")
                find_base = main_file == file
                urdf_file_path = os.path.join(root, file)
                urdf_content = read_urdf_file(urdf_file_path)
                
                # Assuming parse_urdf_for_joints and parse_urdf_for_links are defined
                joints_info = parse_urdf_for_joints(urdf_content, find_base)
                links_info = parse_urdf_for_links(urdf_content)

                # Merge the current file's joints and links info into the combined dictionaries
                for key, value in joints_info.items():
                    if key not in combined_tfs:
                        combined_tfs[key] = value
                for key, value in links_info.items():
                    if key not in combined_items:
                        combined_items[key] = value

    # Prepare the final dictionary with only 'tfs' and 'items' keys
    final_urdf_info = {
        'tfs': combined_tfs,
        'items': combined_items
    }

    # Write the aggregated information to a single JSON file
    write_to_json_file(final_urdf_info, destination_json_file_path)
    print(f"All URDF information has been aggregated into 'tfs' and 'items' and written to {destination_json_file_path}")

if __name__ == "__main__":
    main()