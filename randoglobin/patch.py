from io import BytesIO
import struct
import random
from mnllib import CodeCommand, Variable
from mnllib.bis import Subroutine, BIS_ENCODING

from PySide6 import QtCore, QtGui, QtWidgets

from randoglobin.data_classes import LevelUpStats, MapMetadata, EnemyData
from randoglobin.treasure import get_meswin_size
from randoglobin.mnlscript_misc import create_blitty_hiding_spot
from randoglobin.mnlscript_skips import bowser_map_mods, trash_pit_skips, funny_bone_skips, cavi_cape_skips, plack_beach_skips, pump_works_skips, flame_pipe_skips, dimble_wood_skips

def skip_intro(fevent_manager, skip_peach_castle):
    if skip_peach_castle: # TO DO: fix this eventually
        fevent_manager.fevent_chunks[0x021D][0].subroutines[6] = skip_intro_1a
        fevent_manager.fevent_chunks[0x0208][0].subroutines[2] = skip_intro_1b
    else:
        fevent_manager.fevent_chunks[0x021D][0].subroutines[6] = skip_intro_0a
        fevent_manager.fevent_chunks[0x0208][0].subroutines[2] = skip_intro_0b
        if fevent_manager.fevent_chunks[0x021A][2].text_tables[0x44] is not None:
            fevent_manager.fevent_chunks[0x021A][2].text_tables[0x44].entries[2] = b"\x85By the way, I must say \xFF\x27Luigi\xFF\x20\xFF\x00is looking as dapper as ever.\xff\x11\x01\xff\x0A\x00"
            fevent_manager.fevent_chunks[0x021A][2].text_tables[0x44].textbox_sizes[2] = (27, 5)
    return fevent_manager

skip_intro_0a = Subroutine([
    CodeCommand(0x01D7, [0x00, 0x005A]),
    CodeCommand(0x01D7, [0x01, 0x005A]),
    CodeCommand(0x014B, [0x7F, -0x10, 0x0032]),
    CodeCommand(0x011E, [0x021A, 0x0190, 0x029C, 0x0000, 0x00, 0x00, 0x0000, 0x00000000, 0x00]),
    CodeCommand(0x0001),
])

skip_intro_0b = Subroutine([
    CodeCommand(0x014B, [0x7F, -0x10, 0x0020]),
    CodeCommand(0x014C),
    CodeCommand(0x01AF, [0x00]), # progress story to state 0
    CodeCommand(0x0008, [0x0001], Variable(0xE855)), # disable map star 1
    CodeCommand(0x0008, [0x0001], Variable(0xE856)), # disable map star 2
    CodeCommand(0x0008, [0x0001], Variable(0xE857)), # disable map star 3
    CodeCommand(0x0008, [0x0001], Variable(0xE858)), # disable map star 4
    CodeCommand(0x0008, [0x0001], Variable(0xE859)), # disable map star 5
    CodeCommand(0x0008, [0x0001], Variable(0xE85A)), # disable toad town star 1
    CodeCommand(0x0008, [0x0001], Variable(0xE85B)), # disable toad town star 2
    CodeCommand(0x0120, [0x0280, 0x0001, -0x00000003]),
    CodeCommand(0x0001),
])

skip_intro_1a = Subroutine([
    CodeCommand(0x01D7, [0x00, 0x005A]),
    CodeCommand(0x01D7, [0x01, 0x005A]),
    CodeCommand(0x00E8, [0x01]), # something to do with removing luigi i think
    CodeCommand(0x00F3, [0x02]), # something to do with removing luigi i think
    CodeCommand(0x01AF, [0x00]), # progress story to state 0
    CodeCommand(0x01AF, [0x01]), # progress story to state 1
    CodeCommand(0x0008, [0x0001], Variable(0xE855)), # disable map star 1
    CodeCommand(0x0008, [0x0001], Variable(0xE856)), # disable map star 2
    CodeCommand(0x0008, [0x0001], Variable(0xE857)), # disable map star 3
    CodeCommand(0x0008, [0x0001], Variable(0xE858)), # disable map star 4
    CodeCommand(0x0008, [0x0001], Variable(0xE859)), # disable map star 5
    CodeCommand(0x0008, [0x0001], Variable(0xE85A)), # disable toad town star 1
    CodeCommand(0x0008, [0x0001], Variable(0xE85B)), # disable toad town star 2
    CodeCommand(0x0008, [0x0001], Variable(0x2004)), # disable bowser's fire
    CodeCommand(0x0008, [0x0001], Variable(0x2030)), # ??? this variable is 1 at this point in the story (i think) so yeah sure why not
    CodeCommand(0x0041, [0x00000016], Variable(0x1000)), # give the player the 22 coins they missed in peach's castle
    CodeCommand(0x0008, [0x0001], Variable(0xEA6D)), # dimble wood intro: first room
    CodeCommand(0x0008, [0x0001], Variable(0xEA6E)), # dimble wood intro: boulder room
    CodeCommand(0x0008, [0x0001], Variable(0xEA6F)), # dimble wood intro: forest room
    CodeCommand(0x0008, [0x0001], Variable(0xEA7B)), # dimble wood intro: fawful tease
    CodeCommand(0x0008, [0x0001], Variable(0xEAA6)), # dimble wood intro: fawful encounter
    CodeCommand(0x01AE),
    CodeCommand(0x011E, [0x0296, 0x0000, 0x0000, 0x0000, 0x00, 0x00, 0x0001, -0x00000003, 0x00]),
    CodeCommand(0x0001),
])

skip_intro_1b = Subroutine([
    CodeCommand(0x0120, [0x0295, 0x0002, -0x00000003]),
    CodeCommand(0x0001),
])

def remove_enemies(seed, locations_to_remove, fevent_manager, map_data_overlay, treasure_data_overlay, map_icon_data_overlay, map_metadata_offset, map_group_offset, treasure_data_offset, map_icon_data_offset, font_file, key_item_text, place_text, key_item_text_local, blitty_strings, spoiler_file):
    overlay3 = BytesIO(map_data_overlay)
    overlay4 = BytesIO(treasure_data_overlay)
    overlay129 = BytesIO(map_icon_data_overlay)

    for command in fevent_manager.fevent_chunks[0x0030][0].subroutines[4].commands:
        if isinstance(command, CodeCommand) and command.command_id == 0x0063:
            if command.arguments[0] >= len(fevent_manager.fevent_chunks[0x0030][0].header.actors):
                command.arguments[0] = 0 # this fixes one very specific issue in one very specific scenario but it's whatever lol
    
    valid_enemy_locations = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], []] # one sublist for every enemy type
    enemy_objects = [ # object ID and palette ID of each enemy (because dark trashures use the normal trashure object bc fuck me ig)
        (0x02000027, 0x02000022),
        (0x0200000C, 0x0200000A),
        (0x02000008, 0x02000007),
        (0x02000018, 0x02000017),
        (0x0200000F, 0x0200000C),
        (0x0200001A, 0x02000014),
        (0x0200001F, 0x02000018),
        (0x02000013, 0x0200000E),
        (0x0200001C, 0x0200001A),
        (0x0200002A, 0x02000025),
        (0x0200002D, 0x02000027),
        (0x0200002E, 0x02000028),
        (0x0200002F, 0x02000029),
        (0x02000018, 0x02000032),
        (0x02000031, 0x0200002B),
    ]
    jailgoon_replacement = [0x0200002B, 0x0200002A] # if the found object ID matches the first entry, make it count as the second (since jailgoons can be either object)
    
    if locations_to_remove[1]: # outside bowser enemies are removed, and blitty quest needs to be redone
        for i, chunk_triple in enumerate(fevent_manager.fevent_chunks):
            if chunk_triple[1] is None:
                continue

            for j, actor in enumerate(chunk_triple[1].header.actors):
                if actor[3] >> 16 == 0xFFFF: # has no enemy flag, therefore is probably not an enemy
                    continue

                obj = chunk_triple[1].header.sprite_groups[(actor[2] & 0xFF) // 2]
                pal = chunk_triple[1].header.palettes[((actor[2] >> 8) & 0xFF)]
                if obj == jailgoon_replacement[0]: obj = jailgoon_replacement[1]

                for k, enemy_obj in enumerate(enemy_objects):
                    if obj == enemy_obj[0] and pal == enemy_obj[1]:
                        valid_enemy_locations[k].append((i, j))
    
        blitty_rooms = set()
        blitty_objects = [0x01000325, 0x01000327, 0x01000328] * 5
        random.seed(seed)
        random.shuffle(blitty_objects)

        spoiler_file += "\n\n----" + blitty_strings[1] + "----"
        for i in range(15):
            blitty_hiding_spot = [] # room id, xzy coords, blitty flag, key menu flag, blitty object, init sub id

            hiding_location = random.choice(valid_enemy_locations[i])
            while (hiding_location[0] in blitty_rooms) or (hiding_location[0] == 0x30):
                hiding_location = random.choice(valid_enemy_locations[i])
            blitty_rooms.add(hiding_location[0])
            blitty_hiding_spot.append(hiding_location[0]) # room id

            actor = fevent_manager.fevent_chunks[hiding_location[0]][1].header.actors[hiding_location[1]]
            hiding_spot_coords = (
                actor[0] & 0xFFFF,
                actor[0] >> 16,
                actor[1] & 0xFFFF,
            )
            blitty_hiding_spot.append(hiding_spot_coords) # xzy coords

            blitty_hiding_spot.append(0xE8C9 + i) # blitty flag
            blitty_hiding_spot.append(0xEAAA + i) # key menu flag
            blitty_hiding_spot.append(blitty_objects[i]) # blitty object
            blitty_hiding_spot.append(actor[2] >> 16) # init sub id

            strings = []
            string_sizes = []

            for j in range(6):
                if key_item_text[j] == []:
                    strings.append(None)
                    string_sizes.append(None)
                    continue

                string = b"\xff\x35" + key_item_text[j][0x44 + (i * 2)].encode(BIS_ENCODING) + b"\xff\x0c\x1e\xff\x11\x01\xff\n\x00"
                strings.append(string)
                string_sizes.append(get_meswin_size(string, font_file))

            blitty_hiding_spot.append(strings)
            blitty_hiding_spot.append(string_sizes)

            create_blitty_hiding_spot(fevent_manager, *blitty_hiding_spot)

            overlay3.seek(map_metadata_offset + (hiding_location[0] * 12))
            map_meta = MapMetadata(overlay3.read(12))
            location = 0xA # inside of blubble lake is the only area not listed on the file select screen (where i've been grabbing these strings)
            for j in range(0x23):
                overlay129.seek(map_icon_data_offset + (j * 12) + 4)
                if map_meta.select_map in struct.unpack('<HHH', overlay129.read(6)):
                    overlay129.seek(map_icon_data_offset + (j * 12))
                    location = int.from_bytes(overlay129.read(2), 'little')

            spoiler_file += f"\n{place_text[location]} - {blitty_strings[0]} {hex(hiding_location[0])} - {key_item_text_local[0x44 + (i * 2)]}"

    for i, chunk_triple in enumerate(fevent_manager.fevent_chunks):
        if not chunk_triple[1]:
            continue

        overlay3.seek(map_metadata_offset + (i * 12))
        map_meta = MapMetadata(overlay3.read(12))
        outside_bowser = True

        # the following is fugly as hell but i cannot be bothered to fix it
        for k in range(0x23):
            overlay129.seek(map_icon_data_offset + (k * 12) + 4)

            if map_meta.select_map in struct.unpack('<HHH', overlay129.read(6)):
                overlay129.seek(map_icon_data_offset + (k * 12) + 10)

                if (int.from_bytes(overlay129.read(2), 'little') == 1):
                    outside_bowser = False

                    if locations_to_remove[0]:
                        fevent_manager.fevent_chunks[i] = (chunk_triple[0], None, chunk_triple[2])
        
        if outside_bowser and locations_to_remove[1] and (i not in blitty_rooms):
            fevent_manager.fevent_chunks[i] = (chunk_triple[0], None, chunk_triple[2])

    return spoiler_file

def multiply_exp(overlay_data, monster_table_offset, mult):
    overlay_data = BytesIO(overlay_data)
    overlay_data.seek(monster_table_offset)
    length_test = overlay_data.read()
    for i in range(len(length_test) // 0x24):
        overlay_data.seek(monster_table_offset + (i * 0x24) + 22)
        exp = int.from_bytes(overlay_data.read(2), 'little')
        exp = int(exp * mult)
        overlay_data.seek(-2, 1)
        overlay_data.write(min(exp, 9999).to_bytes(2, 'little'))
    overlay_data.seek(0)
    return overlay_data.read()

def challenge_medal_mode(overlay_data, monster_table_offset):
    overlay_data = BytesIO(overlay_data)
    overlay_data.seek(monster_table_offset)
    length_test = overlay_data.read()
    overlay_data.seek(monster_table_offset)
    mon_list = []
    for i in range(len(length_test) // 0x24):
        mon_list.append(EnemyData(overlay_data.read(0x24)))
    overlay_data.seek(monster_table_offset)
    for i in range(len(length_test) // 0x24):
        mon_list[i].HP = round(mon_list[i].HP * 1.5)
        mon_list[i].POW = round(min(mon_list[i].POW * 2.5, 999))
        mon_list[i].DEF = round(min(mon_list[i].DEF * 1.5, 999))
        mon_list[i].coins = round(min(mon_list[i].coins * 1.5, 9999))
        overlay_data.write(mon_list[i].pack())
    overlay_data.seek(0)
    return overlay_data.read()

def change_start_level(fevent_manager, target_levels, arm9_data, table_offsets):
    arm9 = BytesIO(arm9_data)

    level_up = []
    for i in range(3):
        arm9.seek(table_offsets[i])

        exp = 0
        for j in range(target_levels[i] - 1):
            exp += LevelUpStats(arm9.read(12)).EXP

        level_target_stats = LevelUpStats(arm9.read(12))

        level_up.append(CodeCommand(0x0046, [i,  0, level_target_stats.HP]))
        level_up.append(CodeCommand(0x0046, [i,  7, level_target_stats.HP]))
        level_up.append(CodeCommand(0x0046, [i,  1, level_target_stats.SP]))
        level_up.append(CodeCommand(0x0046, [i,  9, level_target_stats.SP]))
        level_up.append(CodeCommand(0x0046, [i,  2, level_target_stats.POW]))
        level_up.append(CodeCommand(0x0046, [i,  3, level_target_stats.DEF]))
        level_up.append(CodeCommand(0x0046, [i,  4, level_target_stats.SPEED]))
        level_up.append(CodeCommand(0x0046, [i,  5, level_target_stats.STACHE]))
        level_up.append(CodeCommand(0x0046, [i, 17, exp]))
    
    if target_levels[1] >= 40:
        level_up.append(CodeCommand(0x0044, [0x3007, 1], Variable(0x1001))) # add rainbow rank reward
    if target_levels[2] >= 40:
        level_up.append(CodeCommand(0x0044, [0x4070, 1], Variable(0x1001))) # add final boss rank reward
    
    fevent_manager.fevent_chunks[0x01FD][0].subroutines[1].commands[:0] = level_up
    
    return fevent_manager

def open_worldify(fevent_manager, debug_mode, map_data_overlay, map_metadata_offset):
    if False: # this ain't ready
        # TO DO: unlock chakroads
        # TO DO: un-break joint tower
        # TO DO: lock stingler areas behind the stingler
        # TO DO: lock bumpsy 1's side entrance behind the banzai bill
        # TO DO: remove cutscenes where bowser gets downed

        # TO DO: make shiftable
        # # disable the bowser map from "revealing" new maps
        # fevent_manager.fevent_chunks[0x001B][0].subroutines[30] = Subroutine([
        #     Command(0x0001),
        # ])

        fast_travel = [ # TO DO: unblock the toad town pipe
            # TO DO: figure out why sequence breaking softlocks (E99B maybe?)
            CodeCommand(0x0008, [0x0001], Variable(0xE98A)), # pipe yard unlock
            CodeCommand(0x0008, [0x0001], Variable(0xEBD7)), # pipe yard toadbert
            CodeCommand(0x0008, [0x0001], Variable(0xEBD8)), # pipe yard wisdurm
            CodeCommand(0x0008, [0x0001], Variable(0xEBDB)), # pipe yard wall 1
            CodeCommand(0x0008, [0x0001], Variable(0xEBDC)), # pipe yard wall 2
            CodeCommand(0x0008, [0x0001], Variable(0xEBDD)), # pipe yard wall 3
        ]

        fevent_manager.fevent_chunks[0x01FD][0].subroutines[1].commands[:0] = fast_travel
        fevent_manager.fevent_chunks[0x0215][0].subroutines[0].commands[:0] = fast_travel # for debugging only

    # unlock all bowser maps
    for command in fevent_manager.fevent_chunks[0x01FB][0].subroutines[1].commands:
        if command.result_variable is not None:
            if command.result_variable.number == 0x605C:
                command.arguments[0] = 0xA
    
    # for subroutine in fevent_manager.fevent_chunks[0x1B][0].subroutines:
    #     for command in subroutine.commands:
    #         if isinstance(command, CodeCommand) and command.command_id == 0x011E and command.arguments[0] == 0x284:
    #             print("wow")
    #             command.arguments[0] = 0x1c

    skip_stuff(fevent_manager, debug_mode)

    # fix an issue of the broque shop map not being uncovered on the minimap
    overlay3 = BytesIO(map_data_overlay)
    overlay3.seek(map_metadata_offset + (12 * 0x46))
    metadata = overlay3.read(12)
    overlay3.seek(map_metadata_offset + (12 * 0x28D))
    overlay3.write(metadata)

    overlay3.seek(0)

    return overlay3.read()


def skip_stuff(fevent_manager, debug_mode):
    field_skips = [
        CodeCommand(0x0002, [0x00, Variable(0xE852), 0x01, 0x01, 0x14]), # skip the funny bone shit if funny bone is already completed
        CodeCommand(0x0008, [0x0001], Variable(0xE88A)), # the bros cannot leave through pipe yard due to reaction
        CodeCommand(0x0008, [0x0002], Variable(0x6020)), # make funny bone react

        CodeCommand(0x0008, [0x0001], Variable(0x200B)), # misc: bros attacks block
        CodeCommand(0x0008, [0x0001], Variable(0x200D)), # misc: brawl attacks block
        CodeCommand(0x0008, [0x0001], Variable(0x2024)), # misc: shell guard
        CodeCommand(0x0008, [0x000A], Variable(0x605C)), # misc: all bowser maps

        CodeCommand(0x0008, [0x0001], Variable(0xE89D)), # trash pit: starlow discovery
        CodeCommand(0x0008, [0x0001], Variable(0xE8A0)), # trash pit: luigi discovery
        CodeCommand(0x0008, [0x0001], Variable(0xE8A7)), # trash pit: hammer discovery
        CodeCommand(0x0008, [0x0001], Variable(0xEA99)), # trash pit: escape

        CodeCommand(0x0008, [0x0001], Variable(0xE850)), # funny bone: first visit
        CodeCommand(0x0008, [0x0001], Variable(0xE851)), # funny bone: examine nerve

        CodeCommand(0x0008, [0x0001], Variable(0xE7D7)), # toad square: first visit
        CodeCommand(0x0008, [0x0001], Variable(0xE7D8)), # toad square: consumable shop first visit
        CodeCommand(0x0008, [0x0001], Variable(0xE7D9)), # toad square: gear shop first visit
        CodeCommand(0x0008, [0x0001], Variable(0xE712)), # toad square: healing globin first visit

        CodeCommand(0x0008, [0x0001], Variable(0xE727)), # challenge node: first visit
        CodeCommand(0x0008, [0x0001], Variable(0xE70B)), # challenge node: cholesteroad first visit
        CodeCommand(0x0008, [0x0001], Variable(0xE728)), # challenge node: cholesteroad notification: jump helmet
        CodeCommand(0x0008, [0x0001], Variable(0xE729)), # challenge node: cholesteroad notification: you who cannon
        CodeCommand(0x0008, [0x0001], Variable(0xE72A)), # challenge node: cholesteroad notification: super bouncer
        CodeCommand(0x0008, [0x0001], Variable(0xE72B)), # challenge node: cholesteroad notification: spin pipe
        CodeCommand(0x0008, [0x0001], Variable(0xE72C)), # challenge node: cholesteroad notification: magic window
        CodeCommand(0x0008, [0x0001], Variable(0xE70D)), # challenge node: gauntlet first visit
        CodeCommand(0x0008, [0x0001], Variable(0xE72D)), # challenge node: gauntlet notification: class 1
        CodeCommand(0x0008, [0x0001], Variable(0xE72E)), # challenge node: gauntlet notification: class 2
        CodeCommand(0x0008, [0x0001], Variable(0xE72F)), # challenge node: gauntlet notification: class 3
        CodeCommand(0x0008, [0x0001], Variable(0xE730)), # challenge node: gauntlet notification: class 4
        CodeCommand(0x0008, [0x0001], Variable(0xE731)), # challenge node: gauntlet notification: class 5
        CodeCommand(0x0008, [0x0001], Variable(0xE732)), # challenge node: gauntlet notification: class 6
        CodeCommand(0x0008, [0x0001], Variable(0xE733)), # challenge node: gauntlet notification: class 7

        CodeCommand(0x0008, [0x0001], Variable(0xEA7C)), # cavi cape cave: movement tutorial
        CodeCommand(0x0008, [0x0001], Variable(0xEA84)), # cavi cape cave: bowser whinging about his lack of flames
        CodeCommand(0x0008, [0x0001], Variable(0xEAED)), # cavi cape cave: chakroad tutorial

        CodeCommand(0x0008, [0x0001], Variable(0xE94B)), # plack beach: broggy encounter
        CodeCommand(0x0008, [0x0001], Variable(0xEB8F)), # plack beach: sea pipe statue tree 1
        CodeCommand(0x0008, [0x0001], Variable(0xEB90)), # plack beach: sea pipe statue tree 2
        CodeCommand(0x0008, [0x0001], Variable(0xEB91)), # plack beach: sea pipe statue tree 3
        CodeCommand(0x0008, [0x0001], Variable(0xEB92)), # plack beach: sea pipe statue tree 4
        CodeCommand(0x0008, [0x0001], Variable(0xEB93)), # plack beach: sea pipe statue tree 5
        CodeCommand(0x0008, [0x0001], Variable(0xEB94)), # plack beach: sea pipe statue tree 6

        CodeCommand(0x0008, [0x0001], Variable(0xE946)), # arm center: first visit
        CodeCommand(0x0008, [0x0001], Variable(0xEB5A)), # arm center: upgrade notification

        CodeCommand(0x0008, [0x0001], Variable(0xE745)), # pump works: first visit
        CodeCommand(0x0008, [0x0001], Variable(0xEB8E)), # pump works: bowser feels sloshy

        CodeCommand(0x0008, [0x0001], Variable(0xE957)), # dimble wood: first wiggler wall
        CodeCommand(0x0008, [0x0001], Variable(0xE956)), # dimble wood: broque encounter
        CodeCommand(0x0008, [0x0001], Variable(0xEAE0)), # dimble wood: blitty request
        CodeCommand(0x0008, [0x0001], Variable(0xE963)), # dimble wood: remove the pillars around the chakroad
        CodeCommand(0x0008, [0x0001], Variable(0xEA4B)), # dimble wood: big brick 1
        CodeCommand(0x0008, [0x0001], Variable(0xEA4C)), # dimble wood: big brick 2
        CodeCommand(0x0008, [0x0001], Variable(0xEA4D)), # dimble wood: big brick 3
        CodeCommand(0x0008, [0x0001], Variable(0xEA4E)), # dimble wood: big brick 4
        CodeCommand(0x0008, [0x0001], Variable(0xEA4F)), # dimble wood: big brick 5
        CodeCommand(0x0008, [0x0001], Variable(0xEA50)), # dimble wood: big brick 6
        CodeCommand(0x0008, [0x0001], Variable(0xEA51)), # dimble wood: big brick 7
        CodeCommand(0x0008, [0x0001], Variable(0xEA52)), # dimble wood: big brick 8
        CodeCommand(0x0008, [0x0001], Variable(0xEA53)), # dimble wood: big brick 9
    ]

    if debug_mode:
        field_skips.extend([
            CodeCommand(0x0008, [0x0001], Variable(0x2001)), # mario hammer
            CodeCommand(0x0008, [0x0001], Variable(0x2000)), # luigi hammer
            CodeCommand(0x0008, [0x0001], Variable(0x2002)), # spin bros
            CodeCommand(0x0008, [0x0001], Variable(0x2003)), # drill bros
            CodeCommand(0x0008, [0x0000], Variable(0x2004)), # bowser flame
            CodeCommand(0x0008, [0x0001], Variable(0x2005)), # sliding haymaker
            CodeCommand(0x0008, [0x0001], Variable(0x2006)), # body slam
            CodeCommand(0x0008, [0x0001], Variable(0x2007)), # spike ball
            CodeCommand(0x0008, [0x0001], Variable(0x200C)), # badges
            CodeCommand(0x0008, [0x0001], Variable(0x200E)), # vacuum block
            CodeCommand(0x0008, [0x0001], Variable(0x2025)), # blue shell
            CodeCommand(0x0008, [0x0001], Variable(0x202D)), # air vents
            
            # CodeCommand(0x0008, [0x0001], Variable(0xE843)), # stingler (visual)
            # CodeCommand(0x0008, [0x0001], Variable(0xE844)), # banzai bill (visual)
            # CodeCommand(0x0008, [0x0001], Variable(0xE848)), # cure 1 (visual)
            # CodeCommand(0x0008, [0x0001], Variable(0xE849)), # cure 2 (visual)
            # CodeCommand(0x0008, [0x0001], Variable(0xE84A)), # cure 3 (visual)
            # CodeCommand(0x0008, [0x0001], Variable(0xE84C)), # key r (visual)
            # CodeCommand(0x0008, [0x0001], Variable(0xE84D)), # key g (visual)
            # CodeCommand(0x0008, [0x0001], Variable(0xE84E)), # key b (visual)

            # CodeCommand(0x0008, [0x0001], Variable(0x2038)), # stingler (check)
            # CodeCommand(0x0008, [0x0001], Variable(0x2039)), # banzai bill (check)
            # CodeCommand(0x0008, [0x0001], Variable(0x203A)), # cure 1 (check)
            # CodeCommand(0x0008, [0x0001], Variable(0x203B)), # cure 2 (check)
            # CodeCommand(0x0008, [0x0001], Variable(0x203C)), # cure 3 (check)
            # CodeCommand(0x0008, [0x0001], Variable(0x203D)), # key r (check)
            # CodeCommand(0x0008, [0x0001], Variable(0x203E)), # key g (check)
            # CodeCommand(0x0008, [0x0001], Variable(0x203F)), # key b (check)
        ])
    
    fevent_manager.fevent_chunks[0x01FD][0].subroutines[1].commands[:0] = field_skips
    fevent_manager.fevent_chunks[0x0215][0].subroutines[0].commands[:0] = field_skips # for debugging only

    # -----------------------------------------------------------------------------------------------
    # cutscene skips

    # ideas for the future maybe:
    # - finally fix the trash pit intro
    # - add a fight that appears in place of the tutorial midbus fight
    # - add a fight that appears in place of the tutorial broque fight
    # - add a fight that appears in place of the tutorial broggy fight
    # - make the attack pieces optional on the route to get the trash pit hammer check
    # - add boss refights
    # - make sure the overworld doesn't break if you travel through it as the bros before bowser
    # - make sure the overworld doesn't break if you travel through it as spike ball bowser
    # - attack blocks in trash pit and pump works
    # - chakroad scripting
    # - make sure to not let rafts give or take away bowser's flame
    # - make broque not appear if you haven't met him on the beach yet
    # - abilities and key items to return to:
    #   - hammer (trash pit)
    #   - mini mario (pump works)
    #   - bowser flame (plack beach)
    #   - vacuum block (plack beach)
    #   - banzai bill (dimble wood)

    # Q1 ----------------------------------
    bowser_map_mods(fevent_manager)
    trash_pit_skips(fevent_manager)
    funny_bone_skips(fevent_manager)
    cavi_cape_skips(fevent_manager) # for every time you meet fawful, set var 0xEA8F = 1 to prevent him from flying by here if the player skips it somehow
    plack_beach_skips(fevent_manager) # for every time broque appears, check var 0xE943 == 1 to see if he has been rescued from plack beach or not
    pump_works_skips(fevent_manager)
    flame_pipe_skips(fevent_manager)
    dimble_wood_skips(fevent_manager)

    # Q2 ----------------------------------
    #   don't forget to not let slide punch be automatically enabled by the fawful theater cutscene
    # Q3 ----------------------------------
    # Q4 ----------------------------------

    # -----------------------------------------------------------------------------------------------
    # battle tutorial skips

    # trash pit: skip mario counterattack tutorial
    for command in fevent_manager.fevent_chunks[0x0210][0].subroutines[2].commands:
        if command.command_id == 0x195 and command.arguments[0] == 0x1001:
            command.arguments[0] = 0x1004
            command.arguments[2] = 0x0005 # not *exactly* sure what this does but it fixes an issue with fleeing the battle

    # trash pit: skip duo counterattack tutorial
    for command in fevent_manager.fevent_chunks[0x0207][0].subroutines[2].commands:
        if command.command_id == 0x195 and command.arguments[0] == 0x1002:
            command.arguments[0] = 0x1005
            command.arguments[2] = 0x0005 # not *exactly* sure what this does but it fixes an issue with fleeing the battle

    # trash pit: special attack tutorial + replace elite goombules
    for command in fevent_manager.fevent_chunks[0x0214][0].subroutines[1].commands:
        if command.command_id == 0x195 and command.arguments[0] == 0x1003:
            command.arguments[0] = 0x1005
            command.arguments[2] = 0x0005 # not *exactly* sure what this does but it fixes an issue with fleeing the battle
    fevent_manager.fevent_chunks[0x0214][0].header.sprite_groups[6] = 0x02000005
    fevent_manager.fevent_chunks[0x0214][0].header.palettes[3] = 0x02000004

    # trash pit: hammer tutorial
    for command in fevent_manager.fevent_chunks[0x021C][0].subroutines[3].commands:
        if command.command_id == 0x195 and command.arguments[0] == 0x1009:
            command.arguments[0] = 0x1007
            command.arguments[2] = 0x0005 # not *exactly* sure what this does but it fixes an issue with fleeing the battle

###############################################################################################################################################
###############################################################################################################################################
###############################################################################################################################################

class ExtrasTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QtWidgets.QVBoxLayout(self)

        # ------------------------------------------
        line_title = QtWidgets.QWidget()
        line_title.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        line_layout = QtWidgets.QHBoxLayout(line_title)
        line_layout.setContentsMargins(0, 11, 0, 11)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)
        line_layout.addWidget(line)

        line_layout.addWidget(QtWidgets.QLabel(self.tr("Quality of Life")))

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)
        line_layout.addWidget(line)

        main_layout.addWidget(line_title)
        # ------------------------------------------

        qol = QtWidgets.QWidget()
        qol_layout = QtWidgets.QGridLayout(qol)
        main_layout.addWidget(qol)

        # ------------------------------------------
        line_title = QtWidgets.QWidget()
        line_title.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        line_layout = QtWidgets.QHBoxLayout(line_title)
        line_layout.setContentsMargins(0, 11, 0, 11)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)
        line_layout.addWidget(line)

        line_layout.addWidget(QtWidgets.QLabel(self.tr("Extra Stuff")))

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)
        line_layout.addWidget(line)

        main_layout.addWidget(line_title)
        # ------------------------------------------

        extra = QtWidgets.QWidget()
        extra_layout = QtWidgets.QGridLayout(extra)
        main_layout.addWidget(extra)
        
        # ------------------------------------------
        line_title = QtWidgets.QWidget()
        line_title.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        line_layout = QtWidgets.QHBoxLayout(line_title)
        line_layout.setContentsMargins(0, 11, 0, 11)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)
        line_layout.addWidget(line)

        line_layout.addWidget(QtWidgets.QLabel(self.tr("Challenges")))

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)
        line_layout.addWidget(line)

        main_layout.addWidget(line_title)
        # ------------------------------------------

        challenges = QtWidgets.QWidget()
        challenges_layout = QtWidgets.QGridLayout(challenges)
        main_layout.addWidget(challenges)

        # ------------------------------------------
        line_title = QtWidgets.QWidget()
        line_title.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        line_layout = QtWidgets.QHBoxLayout(line_title)
        line_layout.setContentsMargins(0, 11, 0, 11)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)
        line_layout.addWidget(line)

        line_layout.addWidget(QtWidgets.QLabel(self.tr("Silly Stuff")))

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)
        line_layout.addWidget(line)

        main_layout.addWidget(line_title)
        # ------------------------------------------

        silly = QtWidgets.QWidget()
        silly_layout = QtWidgets.QGridLayout(silly)
        main_layout.addWidget(silly)

        # ------------------------------------------
        line_title = QtWidgets.QWidget()
        line_title.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        line_layout = QtWidgets.QHBoxLayout(line_title)
        line_layout.setContentsMargins(0, 11, 0, 11)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)
        line_layout.addWidget(line)

        line_layout.addWidget(QtWidgets.QLabel(self.tr("Chaos Randomization")))

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)
        line_layout.addWidget(line)

        main_layout.addWidget(line_title)
        # ------------------------------------------

        chaos = QtWidgets.QWidget()
        chaos_layout = QtWidgets.QGridLayout(chaos)
        main_layout.addWidget(chaos)
        
        # ------------------------------------------
        # ------------------------------------------

        self.unlinear = QtWidgets.QCheckBox(self.tr("Skip Story and Tutorials"))
        self.unlinear.setStyleSheet("QCheckBox { text-decoration: underline; }")
        self.unlinear.setToolTip(self.tr("Shortens and removes various cutscenes to\nallow for a smoother gameplay experience."))
        qol_layout.addWidget(self.unlinear, 0, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.no_music = QtWidgets.QCheckBox(self.tr("Disable All Music"))
        qol_layout.addWidget(self.no_music, 0, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.unlinear.setChecked(True)
        self.no_music.setChecked(False)
        
        # ------------------------------------------

        self.endless_arm = QtWidgets.QCheckBox(self.tr("Endless Arm Center"))
        self.endless_arm.setStyleSheet("QCheckBox { text-decoration: underline; }")
        self.endless_arm.setToolTip(self.tr("Adds an endless mode for Arm Center.\n(Available after clearing Arm Center once)"))
        extra_layout.addWidget(self.endless_arm, 0, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.debug_mode = QtWidgets.QCheckBox(self.tr("Start With All Abilities"))
        self.debug_mode.setStyleSheet("QCheckBox { text-decoration: underline; }")
        self.debug_mode.setToolTip(self.tr("Grants you all abilities from the start.\n(Enter Trash Pit at any time to retrigger)"))
        #extra_layout.addWidget(self.debug_mode, 0, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.endless_arm.setChecked(True)
        self.debug_mode.setChecked(False)
        
        # ------------------------------------------

        self.challenge_medal = QtWidgets.QCheckBox(self.tr("Challenge Medal Mode"))
        self.challenge_medal.setStyleSheet("QCheckBox { text-decoration: underline; }")
        self.challenge_medal.setToolTip(self.tr("Applies Challenge Medal effects to enemies permanently.\n\n1.5x HP • 1.5x DEF • 1.5x Coins • 2.5x POW"))
        challenges_layout.addWidget(self.challenge_medal, 0, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.impossible = QtWidgets.QCheckBox(self.tr("IMPOSSIBLE MODE"))
        self.impossible.setStyleSheet("QCheckBox { text-decoration: underline; }")
        self.impossible.setToolTip(self.tr("Doubles the speed of some enemy attacks.\n\nInspired by Skelux's original IMPOSSIBLE MODE mod."))
        challenges_layout.addWidget(self.impossible, 0, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.challenge_medal.setChecked(False)
        self.impossible.setChecked(False)