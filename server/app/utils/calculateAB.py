from data.maps import map_map_layers
from data.maps import map_dungeon
from math import atan2, pi






def generate_regions_from_ab_combinations(grid_a, grid_b,region_value):
    """
    Generates a list of unique region codes based on combinations of values from grid_a and grid_b.
    The combination is done by shifting values from grid_b by 8 bits and merging with values from grid_a.
    The result is adjusted to ensure it fits within a 16-bit signed integer range.

    Args:
        grid_a (List[List[int]]): Grid of values for 'A' combinations, representing lower 8 bits.
        grid_b (List[List[int]]): Grid of values for 'B' combinations, representing upper 8 bits.

    Returns:
        List[int]: A list of unique region codes.
    """
    regions = set()  # Using set for better performance in membership testing

    for i in range(len(grid_a)):
        for j in range(len(grid_a[i])):
            # Convert floats to integers if necessary
            a_value = int(grid_a[i][j])
            b_value = int(grid_b[i][j])

            region = (b_value << 8) | a_value

            # Adjust if the value exceeds the max positive value for a 16-bit signed integer.
            if region > 32767:
                region = region_value - 65536  # Ensures values wrap within signed 16-bit range

            regions.add(region)

    return list(regions)  # Convert set





def determine_direction(prev_ax, prev_by, current_ax, current_by, prev_a, prev_b, current_a, current_b):
    """
    Determines the direction of movement or if the image has changed.

    Args:
    prev_ax (float or None): Previous x-coordinate.
    prev_by (float or None): Previous y-coordinate.
    current_ax (float): Current x-coordinate.
    current_by (float): Current y-coordinate.
    prev_a (int or None): Previous A index.
    prev_b (int or None): Previous B index.
    current_a (int): Current A index.
    current_b (int): Current B index.

    Returns:
    str or float: Descriptive string or angle in radians.
    """
    # Check if the image has changed
    if str(prev_a) != str(current_a) or str(prev_b) != str(current_b):
       
        return 'Image Changed'

    print(f"current_ax: {current_ax}, prev_ax: {prev_ax}")
    print(f"current_by: {current_by}, prev_by: {prev_by}")

    delta_x = float((current_ax - prev_ax if prev_ax is not None else 0.0))
    delta_y = float((current_by - prev_by if prev_by is not None else 0.0))

    print(f"delta_x: {delta_x}, delta_y: {delta_y}")
    # If no movement
    if delta_x == 0.0 and delta_y == 0.0:
        print("prevA" + str(prev_a))
        print("-ax" + str(current_ax - prev_ax))
        print("prevB" + str(prev_b))
        print("-by" + str(current_by - prev_by))
        return 'No Direction'

    # Calculate angle in degrees, then convert to radians
    angle_deg = float(atan2(-delta_y, delta_x) * (180 / pi))
    print("ANGLE" + str(float(angle_deg * (pi / 180))))
    return float(angle_deg * (pi / 180))





def position_values_a2(a):
    return [[a - 2, a - 1, a, a + 1, a + 2] for _ in range(5)]

def position_values_b2(b):
    return [[b + i] * 5 for i in range(2, -3, -1)]

def position_values_a(a):
    return [[a - 1, a, a + 1] for _ in range(3)]

def position_values_b(b):
    return [[b + 1] * 3, [b] * 3, [b - 1] * 3]

def positions_left(width):
    half_width = width / 2
    return [
        [0.0, half_width, width],
        [0.0, half_width, width],
        [0.0, half_width, width]
    ]

def positions_top(width):
    half_width = width / 2
    return [
        [0.0, 0.0, 0.0],
        [half_width, half_width, half_width],
        [width, width, width]
    ]











def path_finder(region):
    """Determines the path to image resources based on the region ID."""
    base_path = 'lib/images/minimap/'  # Corrected relative path from app/utils/
    if region >= 0:
        return base_path  # Non-dungeon path
    else:
        return base_path + 'd/'  # Dungeon path
    


def get_icon_path(type):
    # Define the base path where all images are stored
    base_path = 'lib/images/'

    if type == 1:  # fortress
        return base_path + 'fort_worldmap.png'
    elif type == 2:  # gate of ress
        return base_path + 'strut_revival_gate.png'
    elif type == 3:  # gate of glory
        return base_path + 'strut_glory_gate.png'
    elif type == 4:  # fortress small
        return base_path + 'fort_small_worldmap.png'
    elif type == 5:  # ground teleport
        return base_path + 'map_world_icontel.png'
    elif type == 6:  # tahomet
        return base_path + 'tahomet_gate.png'
    else:  # gate or any other type
        return base_path + 'xy_gate.png'



def calculate_position(a1, a2, b1, b2, aX, bY, calculate_left, positions):
    position = 0.0

    condition2_check_a = a1 == a2 or a1 == a2 + 1 or a1 == a2 - 1
    condition3_check_b = b1 == b2 or b1 == b2 + 1 or b1 == b2 - 1

    if condition2_check_a and condition3_check_b:
        if a1 == a2 and b1 == b2:
            # Central position
            if calculate_left:
                position = positions[1][1] + (aX * positions[1][1])
            else:
                position = positions[1][1] + (bY * positions[1][1])
        elif a1 == a2 + 1 and b1 == b2 - 1:
            # Bottom-Right
            if calculate_left:
                position = positions[0][2] + (aX * positions[1][1])
            else:
                position = positions[0][2] + (bY * positions[1][1])
        elif a1 == a2 + 1 and b1 == b2:
            # Right
            if calculate_left:
                position = positions[1][2] + (aX * positions[1][1])
            else:
                position = positions[1][2] + (bY * positions[1][1])
        elif a1 == a2 + 1 and b1 == b2 + 1:
            # Top-Right
            if calculate_left:
                position = positions[2][2] + (aX * positions[1][1])
            else:
                position = positions[2][2] + (bY * positions[1][1])
        elif a1 == a2 and b1 == b2 + 1:
            # Top
            if calculate_left:
                position = positions[2][1] + (aX * positions[1][1])
            else:
                position = positions[2][1] + (bY * positions[1][1])
        elif a1 == a2 - 1 and b1 == b2 + 1:
            # Top-Left
            if calculate_left:
                position = positions[2][0] + (aX * positions[1][1])
            else:
                position = positions[2][0] + (bY * positions[1][1])
        elif a1 == a2 - 1 and b1 == b2:
            # Left
            if calculate_left:
                position = positions[1][0] + (aX * positions[1][1])
            else:
                position = positions[1][0] + (bY * positions[1][1])
        elif a1 == a2 - 1 and b1 == b2 - 1:
            # Bottom-Left
            if calculate_left:
                position = positions[0][0] + (aX * positions[1][1])
            else:
                position = positions[0][0] + (bY * positions[1][1])
        elif a1 == a2 and b1 == b2 - 1:
            # Bottom
            if calculate_left:
                position = positions[0][1] + (aX * positions[1][1])
            else:
                position = positions[0][1] + (bY * positions[1][1])

    return position





class CalculationResult:
    def __init__(self, region, a, b, x, y, z, ax, by, x2, y2, prefix):
        self.region = region
        self.a = a
        self.b = b
        self.x = x
        self.y = y
        self.z = z
        self.ax = ax
        self.by = by
        self.x2 = x2
        self.y2 = y2
        self.prefix = prefix

def calculate_ab(region, x, y, z, a, b, ax, by, x2, y2, npc, prefix):
    if region >= 0:
        if npc:
            
            a = region_to_a_nd(region)
            b = region_to_b_nd(region)
            ax = get_npc_ax_nd(x)
            by = get_npc_ay_nd(y)
        else:
            a = get_A_ND(x)
            b = get_B_ND(y)
            ax = get_aX_ND(x)
            by = get_bY_ND(y)
    else:
        region += 65536
        if npc:
            a = get_A_D(x)
            b = get_B_D(y)
            ax = get_aX_D(x)
            by = get_bY_D(y)
        else:
            x2 = getNew_X(x, region)
            y2 = getNew_Y(y, region)
            a = get_A_D(x2)
            b = get_B_D(y2)
            ax = get_aX_D(x2)
            by = get_bY_D(y2)

        if region == 32769 and prefix is not None:
            if z <= 115:
                region = 327691
            elif z < 230:
                region = 327692
            elif z < 345:
                region = 327693
            else:
                region = 327694
       
        
        if prefix is not None and prefix == '' and region in map_map_layers.regionImagePrefixes:
           
            prefixes = map_map_layers.regionImagePrefixes[region]
            for candidate_prefix in prefixes:
                print(candidate_prefix)
                if try_load_images(candidate_prefix, a, b):
                    prefix = candidate_prefix
                    print(f"Loaded images with prefix: {prefix}")
                    break

    return CalculationResult(region, a, b, x, y, z, ax, by, x2, y2, prefix)

def try_load_images(prefix, a, b):
    # Construct the image dimension key as a string
    axb_value = f"{int(a)}x{int(b)}"
    # Removing the last underscore only if it exists and is the last character
    if prefix.endswith('_'):
        modified_prefix = prefix[:-1]
    else:
        modified_prefix = prefix
    # Check if the prefix exists and the specific dimension is included
    return modified_prefix in map_dungeon.imagesMapD and axb_value in map_dungeon.imagesMapD[modified_prefix]



def isInTrainingArea(characterPosition, trainingArea):
    if not characterPosition or not trainingArea:
        return False

    radius = trainingArea['radius']

    if characterPosition['region'] == trainingArea['region']:
        if characterPosition['region'] >= 0:
            # For non-dungeon
            charAX = get_aX_ND(characterPosition['x'])
            charBY = get_bY_ND(characterPosition['y'])
            charA = get_A_ND(characterPosition['x'])
            charB = get_B_ND(characterPosition['y'])

            trainingAX = get_aX_ND(trainingArea['x'])
            trainingBY = get_bY_ND(trainingArea['y'])
            trainingA = get_A_ND(trainingArea['x'])
            trainingB = get_B_ND(trainingArea['y'])

            return (charA == trainingA and
                    charB == trainingB and
                    abs(charAX - trainingAX) <= radius and
                    abs(charBY - trainingBY) <= radius)

        else:
            # For dungeon
            charX2 = getNew_X(characterPosition['x'], characterPosition['region'])
            charY2 = getNew_Y(characterPosition['y'], characterPosition['region'])
            charAX = get_aX_D(charX2)
            charBY = get_bY_D(charY2)
            charA = get_A_D(charX2)
            charB = get_B_D(charY2)

            trainingX2 = getNew_X(trainingArea['x'], trainingArea['region'])
            trainingY2 = getNew_Y(trainingArea['y'], trainingArea['region'])
            trainingAX = get_aX_D(trainingX2)
            trainingBY = get_bY_D(trainingY2)
            trainingA = get_A_D(trainingX2)
            trainingB = get_B_D(trainingY2)

            return (charA == trainingA and
                    charB == trainingB and
                    abs(charAX - trainingAX) <= radius/200 and
                    abs(charBY - trainingBY) <= radius/200)
    
    return False



def region_to_a_nd(region):
    """Extract the 'A' value from the region code by applying a bitwise AND to get the lowest byte."""
    return region & 0xFF

def region_to_b_nd(region):
    """Extract the 'B' value from the region code by shifting right by 8 bits to move the second lowest byte to the lowest byte position."""
    return region >> 8

def get_npc_ax_nd(x):
    """Calculate the NPC 'aX' value for Non-Dungeon based on the given x-coordinate."""
    return (256 / 1920 * x) / 256 - 0.015

def get_npc_ay_nd(y):
    """Calculate the NPC 'bY' value for Non-Dungeon based on the given y-coordinate."""
    return (256 / 1920 * y) / 256 - 0.04


# GET A NON DUNGEON
def get_A_ND(x):
    return int(x / 192 + 135)

# GET B NON DUNGEON
def get_B_ND(y):
    return int(y / 192 + 92)

# GET A DUNGEON
def get_A_D(x):
    return (128 * 192 + x / 10) // 192

# GET B DUNGEON
def get_B_D(y):
    return (128 * 192 + y / 10) // 192

# GET aX NON DUNGEON
def get_aX_ND(x):
    return (x / 192 + 135) - (x / 192 + 135) // 1 - 0.015

# GET bY NON DUNGEON
def get_bY_ND(y):
    return (y / 192 + 92) - (y / 192 + 92) // 1 - 0.04

# GET aX DUNGEON
def get_aX_D(x):
    value = (128 * 192 + x / 10) / 192
    return value - value // 1 - 0.015

# GET bY DUNGEON
def get_bY_D(y):
    value = (128 * 192 + y / 10) / 192
    return value - value // 1 - 0.04

# GET newX
def getNew_X(x, region):
    return 10 * (x - ((region & 255) - 128) * 192)

# GET newY
def getNew_Y(y, region):
    return 10 * (y - ((region >> 8) - 128) * 192)

