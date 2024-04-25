
from ..utils import var
from ..utils import calculateAB
from data.maps import map_npcos
from data.maps import map_tps_pos
from data.maps import map_regions_id_name
from .. import socketio  # Import the socketio instance


#Images
base_path = 'lib/images/'
npcImage =  base_path + 'mm_sign_npc.jpg'
charImage = base_path + 'mm_sign_character.png'
monsterImage = base_path + 'mm_sign_monster.jpg'
ptImage = base_path + 'mm_sign_party.jpg'
ptImageSelected = base_path + 'mm_sign_party2.jpg'
pplImage = base_path + 'mm_sign_otherplayer.jpg'
defaultImage = base_path + 'DEFAULTMAP.png'


prevA = None
prevB = None
prevAX = None
prevBY = None
rotationAngle = float(0)
lastDirection = 'No Direction'

def calculate_map_data(character_name,job_name, server_name ,character,width):
    global prevA
    global prevB
    global prevAX
    global prevBY
    global rotationAngle
    global lastDirection
    
    backgroundChanged = False
    
    
   
    npcPositions = []
    tpsPositions = []
    monstersPositions = []
    ptPositions = []
    selectedPositions = []
    pplPositions = []
    trainingPosition = []
    charPosition = []
    region_name = ''
    images = []
    #char initials

    region = character['position']['region']
    x = character['position']['x']
    y = character['position']['y']
    z = character['position']['z']
    path = calculateAB.path_finder(region)
    a = 0
    b = 0
    x2 = 0
    y2 = 0
    aX = 0
    bY = 0
    prefix = ''

    
    try:
        # Attempt to fetch the region name directly
        region_name = map_regions_id_name.idNameMapp[str(region)]
    except KeyError:
        # If direct fetch fails, try with adjusted region key
        try:
            adjusted_region = region - 65536
            region_name = map_regions_id_name.idNameMapp[str(adjusted_region)]
        except KeyError:
            # If both attempts fail, return an empty string
            region_name = ""

    #training area initials
    xTr = character["training_area"]['x']
    yTr = character["training_area"]['y']
    zTr = character["training_area"]['z']
    regionTr = character["training_area"]['region']
    radius = character["training_area"]['radius']
    aTr = 0
    bTr = 0
    x2Tr = 0
    y2Tr = 0
    axTr = 0
    byTr = 0

    #mobs initials
    monsters = character['monsters']
    xM = 0
    yM = 0
    regionM = 0
    aM = 0
    bM = 0
    axM = 0
    byM = 0
    x2M = 0
    y2M = 0

    #party initials
    party = character['party']
    isPartyNotEmpty = bool(party)
    xPt = 0
    yPt = 0
    regionPt = 0
    aPt = 0
    bPt = 0
    axPt = 0
    byPt = 0
    x2Pt = 0
    y2Pt = 0

    #other players initials
    ppl = {}
    xPpl = 0
    yPpl = 0
    regionPpl = 0
    aPpl = 0
    bPpl = 0
    axPpl = 0
    byPpl = 0
    x2Ppl = 0
    y2Ppl = 0




    #calculate

    ##for tr
    tr = calculateAB.calculate_ab(regionTr,xTr,yTr,zTr,aTr,bTr,axTr,byTr,x2Tr,y2Tr,False, prefix = None)

    ##for char
    print("char"+ prefix)
    char = calculateAB.calculate_ab( region,x, y, z,a,b,aX,bY,x2,y2,False, prefix= prefix)


    #grid

    gridA = calculateAB.position_values_a(char.a)
    gridB = calculateAB.position_values_b(char.b)
    posLeft = calculateAB.positions_left(width)
    posTop = calculateAB.positions_top(width)

    lastDirection = calculateAB.determine_direction(prevAX,prevBY,char.ax,char.by,prevA,prevB, char.a,char.b )
    
    if isinstance(lastDirection, float):
        rotationAngle = lastDirection

    
    def has_a_or_b_changed():
        return prevA != char.a or prevB != char.b
    
            # Determine if there has been a change
    a_or_b_changed = has_a_or_b_changed()

    # Set animation duration based on whether there was a change
    animation_duration = 0 if a_or_b_changed else 300
    
    prevAX = char.ax
    prevBY = char.by
 
    prevA = char.a
    prevB = char.b

    offsetX = width * -char.by /2 
    offsetY = width * -char.ax /2

   


    for i in range(3):  # iterating over three rows
        for j in range(3):  # iterating over three columns
            image_path = f"{path}{char.prefix}{int(gridA[i][j])}x{int(gridB[i][j])}.jpg"
            # Create a dictionary for each image with its path and positions
            item = {
                'image': image_path,
                'left': posLeft[i][j],
                'top': posTop[i][j]
            }
            images.append(item)


    regionCombinations = calculateAB.generate_regions_from_ab_combinations(gridA, gridB,char.region)




    #TRAINING AREA CALCULATE
    for r in regionCombinations:
      
        
        
        if regionTr == int(r):
            # Check proximity conditions
            condition2CheckaTr = tr.a in [char.a- 1, char.a, char.a + 1]
            condition3CheckbTr = tr.b in [char.b - 1, char.b, char.b + 1]
            
            if condition2CheckaTr and condition3CheckbTr:
                # Calculate positions
                left = calculateAB.calculate_position(tr.a, char.a, tr.b, char.b, tr.ax, tr.by, True, posLeft)
                bottom = calculateAB.calculate_position(tr.a, char.a, tr.b, char.b, tr.ax, tr.by, False, posTop)
                
                # Set position with radius in the dictionary
                trainingPosition.append({
                    'left': left - radius,  # Adjust to center the circle
                    'bottom': bottom - radius,
                    'radius': radius
                })
                

    #PARTY CALCULATE
    for key, value in party.items():
        xPt = value['x']
        yPt = value['y']
        regionPt = value['region']
        playerName = value['name']

        # Calculate position for each party member
        pt = calculateAB.calculate_ab(regionPt, xPt, yPt, 0, aPt, bPt, axPt, byPt, x2Pt, y2Pt, False, None)

        # Check proximity conditions
        condition1CheckaNpc = pt.a in [char.a - 1, char.a, char.a + 1]
        condition2CheckbNpc = pt.b in [char.b - 1, char.b, char.b + 1]

        if condition1CheckaNpc and condition2CheckbNpc:
            # Calculate left and bottom positions
            left = calculateAB.calculate_position(pt.a, char.a, pt.b, char.b, pt.ax, pt.by, True, posLeft)
            bottom = calculateAB.calculate_position(pt.a, char.a, pt.b, char.b, pt.ax, pt.by, False, posTop)
            if playerName != character_name and job_name != playerName:
                # Append the calculated positions to ptPositions

                pt_entry = {
                    'playerName': playerName,
                    'left': left,
                    'bottom': bottom,
                    'image': ptImage,
                  

                }
                ptPositions.append(pt_entry)


    #mobs calculate
    for key, value in monsters.items():
        xM = value['x']
        yM = value['y']
        regionM = value['region']

        # Calculate the AB position for the monster
        monster = calculateAB.calculate_ab(regionM, xM, yM, 0, aM, bM, axM, byM, x2M, y2M, False, None)

        # Check if the monster is in proximity to the character
        condition1CheckaNpc = monster.a in [char.a - 1, char.a, char.a + 1]
        condition2CheckbNpc = monster.b in [char.b - 1, char.b, char.b + 1]

        if condition1CheckaNpc and condition2CheckbNpc:
            left = calculateAB.calculate_position(monster.a, char.a, monster.b, char.b, monster.ax, monster.by, True, posLeft)
            bottom = calculateAB.calculate_position(monster.a, char.a, monster.b, char.b, monster.ax, monster.by, False, posTop)

            # Append the position and the path of the monster image
            monster_entry = {                
                'left': left,
                'bottom': bottom,
                'image': monsterImage
               }
            monstersPositions.append(monster_entry)

    #ppl calculate
    for key, value in ppl.items():
        regionPpl = int(value.get('Region ID', 0))
        xPpl = float(value['posx'])
        yPpl = float(value['posy'])

        # Adjust region if necessary
        if regionPpl > 32767:
            regionPpl -= 65536

        # Calculate the AB position for the other player
        otherP = calculateAB.calculate_ab(regionPpl, xPpl, yPpl, 0, aPpl, bPpl, axPpl, byPpl, x2Ppl, y2Ppl, True, None)

        # Check proximity conditions
        condition1CheckaNpc = otherP.a in [char.a - 1, char.a, char.a + 1]
        condition2CheckbNpc = otherP.b in [char.b - 1, char.b, char.b + 1]

        if condition1CheckaNpc and condition2CheckbNpc:
            left = calculateAB.calculate_position(otherP.a, char.a, otherP.b, char.b, otherP.ax, otherP.by, True, posLeft)
            bottom = calculateAB.calculate_position(otherP.a, char.a, otherP.b, char.b, otherP.ax, otherP.by, False, posTop)

            # Append the calculated positions along with the image path
            ppl_entry = {
                'left': left,
                'bottom': bottom,
                "image": pplImage

            }
            pplPositions.append(ppl_entry)

    #npc calculate
    for r in regionCombinations:
        
        if str(r) in map_npcos.npcPos:
            print(str(r) + "found")
            npcs_in_region = map_npcos.npcPos[str(r)]

            for npc in npcs_in_region:
                
                x_npc = float(npc['x'])
                y_npc = float(npc['y'])
                z_npc = float(npc['z'])
                npc_region = int(npc['region'])
                a_npc = b_npc = int(0)
                x2_npc = y2_npc = ax_npc = by_npc = float(0)
                
                # Assume calculate_ab and calculate_position are defined functions
                vendor = calculateAB.calculate_ab(npc_region, x_npc, y_npc, z_npc, a_npc, b_npc, ax_npc, by_npc, x2_npc, y2_npc, True, prefix = None)

                condition1CheckaNpc = vendor.a in [char.a - 1, char.a, char.a + 1]
                condition2CheckbNpc = vendor.b in [char.b - 1, char.b, char.b + 1]
                
                if condition1CheckaNpc and condition2CheckbNpc:
                    left = calculateAB.calculate_position(vendor.a, char.a, vendor.b, char.b, vendor.ax, vendor.by, True, posLeft)
                    bottom = calculateAB.calculate_position(vendor.a, char.a, vendor.b, char.b, vendor.ax, vendor.by, False, posTop)
                    
                    npc_entry = {
                        'left': left,
                        'bottom': bottom,
                        "image": npcImage,
                    }
                    npcPositions.append(npc_entry)
                    print(npcPositions)
    #tp calculate
    for r in regionCombinations:
        
        if str(r) in map_tps_pos.tpsPos: 
           
            tps_in_region = map_tps_pos.tpsPos[str(r)]
            
            for tp in tps_in_region:
                x_tp = float(tp['x'])
                y_tp = float(tp['y'])
                z_tp = float(tp['z'])
                tp_region = int(tp['region'])
                type = int(tp['type'])
                
                a_tp = b_tp = x2_tp = y2_tp = ax_tp = by_tp = 0  # Initialize to default values

                # Calculate the AB position for the teleport
                tport = calculateAB.calculate_ab(tp_region, x_tp, y_tp, z_tp, a_tp, b_tp, ax_tp, by_tp, x2_tp, y2_tp, True, prefix = None)

                # Check proximity conditions
                condition1_check_tp = tport.a in [char.a - 1, char.a, char.a + 1]
                condition2_check_tp = tport.b in [char.b - 1, char.b, char.b + 1]
                
                if condition1_check_tp and condition2_check_tp:
                   
                    left = calculateAB.calculate_position(tport.a, char.a, tport.b, char.b, tport.ax, tport.by, True, posLeft) - 8.5
                    bottom = calculateAB.calculate_position(tport.a, char.a, tport.b, char.b, tport.ax, tport.by, False, posTop) - 8.5

                    pathTp = calculateAB.get_icon_path(type)  # Assuming a function to determine path from type
                   
                    teleport_entry = {
                        'left': left,
                        'bottom': bottom,
                        'image':pathTp
                    }
                    tpsPositions.append(teleport_entry)
                    print(tpsPositions)


    #char position
    left = posLeft[1][1] + (char.ax * posLeft[1][1])
    bottom = posTop[1][1] + (char.by * posTop[1][1])
    
    charPosition.append({
        'left':left,
        'bottom': bottom,
        "image": charImage
     
    })
    # Include more calculations as needed
    return {
       
        "npcPos": npcPositions, 
            "tpsPos": tpsPositions,
            "mobPos": monstersPositions,
            "ptPos": ptPositions,
            "pplPos": pplPositions,
            "trPos": trainingPosition,
            "charPos": charPosition,
            "regionName": region_name,
            "images": images,
            "animationD": animation_duration,
            "offsetX": offsetX,
            "offsetY": offsetY,
            "rotationAngle": rotationAngle,
            "defaultImage": defaultImage,
            
         
    }



def map_engine(character_name, server_name, width):
    # Construct the key from character_name and server_name
    key = f"{character_name}/{server_name}"
    
    # Access the data directly using the constructed key
    character_data = var.statz_data.get(key)
    
    # Check if we have data for the given key
    if character_data:
        job_name = character_data['job_name']
        result = calculate_map_data(character_name, job_name, server_name, character_data, width)
        return result
    else:
        # Return an empty dictionary if no data found for the key
        return {}



@socketio.on('map')
def handle_map_data(payload):
    print(f"Received map_data from")  # Log the socket ID
    print(payload)  # Debug print the received payload

    character_name = payload['character']
    print(character_name)
    server_name = payload['server']
    width = payload['width']
    print(width)
    result = map_engine(character_name, server_name, width)
    socketio.emit('map_data',result)
    print('emitted')
