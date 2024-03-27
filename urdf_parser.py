import xml.etree.ElementTree as ET
import math
import json
import sys
import re
_AXES2TUPLE = {
    'sxyz': [0, 0, 0, 0], 'sxyx': [0, 0, 1, 0], 'sxzy': [0, 1, 0, 0], 'sxzx': [0, 1, 1, 0],
    'syzx': [1, 0, 0, 0], 'syzy': [1, 0, 1, 0], 'syxz': [1, 1, 0, 0], 'syxy': [1, 1, 1, 0],
    'szxy': [2, 0, 0, 0], 'szxz': [2, 0, 1, 0], 'szyx': [2, 1, 0, 0], 'szyz': [2, 1, 1, 0],
    'rzyx': [0, 0, 0, 1], 'rxyx': [0, 0, 1, 1], 'ryzx': [0, 1, 0, 1], 'rxzx': [0, 1, 1, 1],
    'rxzy': [1, 0, 0, 1], 'ryzy': [1, 0, 1, 1], 'rzxy': [1, 1, 0, 1], 'ryxy': [1, 1, 1, 1],
    'ryxz': [2, 0, 0, 1], 'rzxz': [2, 0, 1, 1], 'rxyz': [2, 1, 0, 1], 'rzyz': [2, 1, 1, 1]
}

_NEXT_AXIS = [1, 2, 0, 1]

# Parses a given input string and replaces the ${...} value. Use this if you have a weird format like:
# <origin xyz="${camera_link} 0 0" rpy="0 0 0"/> where <xacro:property name="camera_link" value="0.05" />
def parseString(input_string:str, property_table):
    words = input_string.split(' ')
    pattern = r'\${(.*?)}'  # Regular expression pattern to match "${...}"

    for i, word in enumerate(words):
        match = re.search(pattern, word)
        if match:
            words[i] = property_table[match.group(1)]

    return ' '.join(words)


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

def parse_urdf_for_joints(urdf_content):
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
        # Check if the urdf specifies a property value to be replaced.
        xyz = list(map(float, parseString(origin['xyz'], property_table).split(' ')))
        rpy = list(map(float, origin.get('rpy', '0 0 0').strip().split(' ')))

        # Convert from Euler angles (rpy) to quaternion
        quaternion = quaternion_from_euler(rpy[0], rpy[1], rpy[2], "sxyz")

        joints_info[child] = {
            'frame': parent,
            'position': {'x': xyz[0], 'y': xyz[1], 'z': xyz[2]},
            'rotation': {'w': quaternion[0], 'x': quaternion[1], 'y': quaternion[2], 'z': quaternion[3]},
            'scale': {'x': 1, 'y': 1, 'z': 1}
        }

    # Add base_link information
    joints_info["base_link"] = {
        'frame': "world",
        'position': {'x': 0, 'y': 0, 'z': 0},
        'rotation': {'w': 1, 'x': 0, 'y': 0, 'z': 0},
        'scale': {'x': 1, 'y': 1, 'z': 1}
    }

    return joints_info

def parse_urdf_for_links(urdf_content):
    root = ET.fromstring(urdf_content)
    links = root.findall('.//link')
    materials = root.findall('.//material')
    items = {}  # New dictionary to populate

    # Create a materials map
    materials_map = {}

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
                scale = list(map(float, mesh.get('scale').split()))
        
        if link_name is not None and visual is not None and geometry is not None:
            color = {"r": 1, "g": 1, "b": 1, "a": 1}  # Default color
            # Check if color is defined directly
            if visual.find('material/color') is not None:
                color = list(map(float, visual.find('material/color').get('rgba').split()))
            elif visual.find('material') is not None and materials_map.get(visual.find('material').get('name')):
                # Use material name to find color
                color = materials_map[visual.find('material').get('name')]
            
            # Check if origin is present
            origin = visual.find('origin')
            xyz = [0.0, 0.0, 0.0]
            rpy = [0.0, 0.0, 0.0]

            if origin is not None:
                xyz = list(map(float, origin.get('xyz', '0 0 0').split()))
                rpy = list(map(float, origin.get('rpy', '0 0 0').split()))

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

    return items

def read_urdf_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        sys.exit(1)

def write_to_json_file(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def main():
    if len(sys.argv) != 3:
        print("Usage: python urdf_parser.py <source_urdf_file_path> <destination_json_file>")
        sys.exit(1)
    
    source_urdf_file_path = sys.argv[1]
    destination_json_file_path = sys.argv[2]

    urdf_content = read_urdf_file(source_urdf_file_path)
    joints_info = parse_urdf_for_joints(urdf_content)
    links_info = parse_urdf_for_links(urdf_content)

    # Combine joints and links info into a single dictionary
    urdf_info = {
        'tfs': joints_info,
        'items': links_info
    }

    write_to_json_file(urdf_info, destination_json_file_path)
    print(f"URDF information has been written to {destination_json_file_path}")

if __name__ == "__main__":
    main()