from ...data.maps.map_map_layers import regionImagePrefixes
from ...data.maps.map_dungeon import imagesMapD 










def position_values_a2(a):
    return [[a - 2, a - 1, a, a + 1, a + 2] for _ in range(5)]

def position_values_b2(b):
    return [[b + i] * 5 for i in range(2, -3, -1)]

def position_values_a(a):
    return [[a - 1, a, a + 1] for _ in range(3)]

def position_values_b(b):
    return [[b + 1] * 3, [b] * 3, [b - 1] * 3]
class CalculationResult:
    def __init__(self, region, a, b, x, y, z, aX, bY, X2, Y2, prefix=None):
        self.region = region
        self.a = a
        self.b = b
        self.x = x
        self.y = y
        self.z = z
        self.aX = aX
        self.bY = bY
        self.X2 = X2
        self.Y2 = Y2
        self.prefix = prefix














class CalculationResult:
    def __init__(self, region, a, b, x, y, z, ax, by, x2, y2, prefix=None):
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

def calculate_ab(region, x, y, z, a, b, ax, by, x2, y2, npc, prefix=None):
    if region >= 0:
        if npc:
            a = get_A_ND(region)
            b = get_B_ND(region)
            ax = get_aX_ND(x)
            by = get_bY_ND(y)
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

        if region == 32769 and prefix:
            if z <= 115:
                region = 327691
            elif z < 230:
                region = 327692
            elif z < 345:
                region = 327693
            else:
                region = 327694

        if prefix and region in regionImagePrefixes:
            prefixes = regionImagePrefixes.get(region, [])
            for candidate_prefix in prefixes:
                if try_load_images(candidate_prefix, a, b):
                    prefix = candidate_prefix
                    print(f"Loaded images with prefix: {prefix}")
                    break

    return CalculationResult(region, a, b, x, y, z, ax, by, x2, y2, prefix)

def try_load_images(prefix, a, b):
    # Construct the image dimension key as a string
    axb_value = f"{a}x{b}"
    # Check if the prefix exists and the specific dimension is included
    return prefix in imagesMapD and axb_value in imagesMapD[prefix]



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


