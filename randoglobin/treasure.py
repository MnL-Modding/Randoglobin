from io import BytesIO
import struct
import random

from mnllib import CodeCommand
from mnllib.bis import BIS_ENCODING
from PySide6 import QtCore, QtGui, QtWidgets

from randoglobin.constants import *
from randoglobin.data_classes import Treasure, ShopList, MapMetadata
from randoglobin.mnlscript_sidequests import assemble_blitty_rewards, assemble_mushroom_derby, assemble_hide_seek_toad, assemble_kuzzle_puzzles
from randoglobin.image import create_BObj_sprite, create_MObj_sprite, interpret_character, generate_sprites_from_sheet

# =========================================================================================================================

PEACH_CASTLE_INTRO_TREASURE_ENTRIES = [
    0x291, # room 0x216
    0x292, # room 0x216
    0x293, # room 0x216
    0x294, # room 0x216
    0x295, # room 0x217
]

def get_meswin_size(mes, font):
    h = 4
    v = 4

    mes = mes.replace(b"\xff\x0b\x01", b"") # unknown flag
    mes = mes.replace(b"\xff\x35", b"") # center alignment flag
    mes = mes.replace(b"\xff\x2b", b"") # blue color text flag
    mes = mes.replace(b"\xff\x20", b"") # normal color text flag
    mes = mes.replace(b"\xff\x0c\x1e", b"") # wait for 30 frames
    mes = mes.replace(b"\xff\x11\x01", b"") # stop text and create a button prompt
    mes = mes.replace(b"\xff\x0a\x00", b"") # despawn textbox and end string

    v += 2 * mes.count(b"\xff\x00") # count the line breaks
    mes_list = mes.split(b"\xff\x00") # split up each line

    if any(b"\xff" in m for m in mes_list): # check if i missed any flags
        print(mes_list)
        print("^ still has a flag")
    
    max_width = 0
    for line in mes_list:
        width = 0
        for char in line:
            if char == 0x20: width += 8 # i think this is the space size
            else: width += interpret_character(BytesIO(font), None, char)[1] # only grab the char_width from this function
            width += 1 # account for space between letters
        if width > max_width:
            max_width = width
    
    h += ((max_width + 4) // 8)

    return (h - 1, v - 1)

def randomize_treasure(parent, seed, settings, treasure_file, shops_file, fevent_manager, arm9, item_tables_offset, badge_patch_offset, map_metadata_offset, map_group_offset, treasure_data_offset, map_icon_data_offset, shop_table_offset, overlays, treasure_strings, place_text, badge_names, all_item_text, font_file, spoiler_file):
    coin_string = [None] * 6
    for i in range(6):
        if fevent_manager.fevent_chunks[0x0128][2].text_tables[0x43 + i] is not None:
            coin_string[i] = fevent_manager.fevent_chunks[0x0128][2].text_tables[0x43 + i].entries[0x2D] # "You got 10 coins!"
    
    random.seed(seed)
    save = treasure_file

    treasure_list_initial = []
    treasure_list_random = []
    badge_dict = {}

    # ----------------------------------
    treasure_list_initial, treasure_to_skip, treasure_amt = gather_all_treasure(
        [settings.rando_dig.isChecked(), settings.rando_block.isChecked(), settings.rando_brick.isChecked(), settings.rando_grass.isChecked()],
        treasure_file
    )
    treasure_list_random, _skip, _amt = gather_all_treasure(
        [settings.rando_dig.isChecked(), settings.rando_block.isChecked(), settings.rando_brick.isChecked(), settings.rando_grass.isChecked()],
        treasure_file
    )
    # ----------------------------------
    quest_rewards_random = gather_all_sidequests(
        [settings.rando_ball.isChecked(), settings.rando_hide.isChecked(), settings.rando_blitty.isChecked(), settings.rando_puzzle.isChecked()],
        fevent_manager
    )
    treasure_list_random += quest_rewards_random
    # ----------------------------------
    shop_list_random, shop_data = gather_all_shop_items(
        [settings.rando_ishop.isChecked(), settings.rando_gshop.isChecked(), settings.rando_bshop.isChecked()],
        shops_file
    )
    treasure_list_random += shop_list_random
    for i in range(0xD): # make all shops consumable type TODO: only change relevant shops
        overlays[0][shop_table_offset + 2 + (i * 36)] = 0
    for i in range(8): # fix badges in blocks
        arm9.seek(badge_patch_offset + (i * 16) + 6)
        arm9.write(b'\x02')
        arm9.seek(1, 1)
        arm9.write(b'\xD1\x01\x00\x01')
    arm9 = set_item_prices( # fix item prices TODO: make this optional
        arm9,
        item_tables_offset,
        [
            (0x2014,   400), # Heart Bean            previously:    1  coin 
            (0x2015,   400), # Special Bean          previously:    1  coin 
            (0x2016,   400), # Power Bean            previously:    1  coin 
            (0x2017,   100), # Retry Clock           previously:    1  coin 
            (0x3004,   300), # Good Badge            previously:  500 coins
            (0x3007,  5000), # Excellent!! Badge     previously:   10 coins
            (0x4001,    10), # Thin Wear             previously:    4 coins
            (0x400C, 16000), # Master Wear           previously:    4 coins
            (0x400F,  6000), # D-Star Wear           previously:    4 coins
            (0x401A,  1500), # Bro Socks             previously:    4 coins
            (0x402E,  1000), # Siphon Gloves         previously:    4 coins
            (0x4041,  3000), # Advice Patch          previously:    4 coins
            (0x4050,   200), # Challenge Medal       previously:    4 coins
            (0x405A,  9600), # Ironclad Shell        previously:    4 coins
            (0x405B,  3000), # Block Ring            previously:    4 coins
            (0x405C, 18000), # King Shell            previously:    4 coins
            (0x4066,  1500), # Block Band            previously:    4 coins
            (0x4067,  4000), # Fury Band             previously:    4 coins
            (0x406F,  1000), # Bone Fangs            previously:    4 coins
            (0x4070, 10000), # Intruder Fangs        previously:    4 coins
            (0x4071,  1500), # Block Fangs           previously:    4 coins
            (0x407D,  3000), # Treasure Ring         previously:    4 coins
        ]
    )
    # ----------------------------------
    return_list = [treasure_file, shops_file]
    # ----------------------------------

    ###################################################
    print(f"!!randomize_treasure!! total checks: {len(treasure_list_random)}")
    for treasure in treasure_list_random:
        if treasure.treasure_type == 0 or treasure.treasure_type == 5:
            treasure.max_hits = 1

        item_type = treasure.item >> 12
        if item_type != 0xF: # not coins
            item_id = treasure.item & 0xFFF
            arm9.seek(item_tables_offset + ((item_type - 1) * 4))
            arm9.seek(int.from_bytes(arm9.read(4), 'little') - 0x2004000)
            arm9.seek(item_id * [24, 24, 16, 32][item_type - 1], 1)
            string_id = int.from_bytes(arm9.read(2), 'little')
            arm9.seek(4, 1)
            treasure.sfx = int.from_bytes(arm9.read(1), 'little')
            arm9.seek(1, 1)
            treasure.obj = int.from_bytes(arm9.read(4), 'little')
            treasure.no_string = False

            treasure.textbox = []
            treasure.textbox_sizes = []
            for i in range(6):
                if fevent_manager.fevent_chunks[0x0128][2].text_tables[0x43 + i] is None:
                    treasure.textbox.append(None)
                    treasure.textbox_sizes.append(None)
                    continue

                plural = True
                if ((treasure.quantity + 1) * treasure.max_hits) == 1: plural = False

                string = fevent_manager.fevent_chunks[0x0128][2].text_tables[0x43 + i].entries[0x32] # "You got 5 Super Nuts!"
                if all_item_text[i][1][40].encode(BIS_ENCODING) in string: # "Super Nut" string
                    string = string.replace(all_item_text[i][1][40].encode(BIS_ENCODING), all_item_text[i][item_type - 1][string_id + int(plural)].encode(BIS_ENCODING), 1)
                elif all_item_text[i][1][40].lower().encode(BIS_ENCODING) in string: # for some reason, some languages don't retain proper capitalization
                    string = string.replace(all_item_text[i][1][40].lower().encode(BIS_ENCODING), all_item_text[i][item_type - 1][string_id + int(plural)].lower().encode(BIS_ENCODING), 1)
                else:
                    print(f"!!randomize_treasure!! string does not countain the 'super nuts' string in lang {i}")
                    print(fevent_manager.fevent_chunks[0x0128][2].text_tables[0x43 + i].entries[0x32])
                    print(all_item_text[i][1][40].encode(BIS_ENCODING))

                if b"5" in string:
                    string = string.replace(b"5", str((treasure.quantity + 1) * treasure.max_hits).encode(BIS_ENCODING), 1)
                else:
                    print(f"!!randomize_treasure!! string does not countain an item count in lang {i}")

                treasure.textbox.append(b"\xff\x35" + string) # align message to center, to mask any poor sizing jobs
                treasure.textbox_sizes.append(get_meswin_size(string, font_file))

        else: # coins
            treasure.sfx = 0
            treasure.no_string = True # this is true for coin amounts that can be referred to by a single coin sprite
            match [1, 5, 10, 50, 100][treasure.quantity] * treasure.max_hits:
                case 1:
                    treasure.obj = 0x01000009
                case 5:
                    treasure.obj = 0x010001F9
                case 10:
                    treasure.obj = 0x010001FA
                case 50:
                    treasure.obj = 0x010001FB
                case 100:
                    treasure.obj = 0x010001FC
                case _:
                    treasure.obj = 0x0100011E
                    treasure.no_string = False
            treasure.textbox = []
            treasure.textbox_sizes = []
            for i in range(6):
                if fevent_manager.fevent_chunks[0x0128][2].text_tables[0x43 + i] is None:
                    treasure.textbox.append(None)
                    treasure.textbox_sizes.append(None)
                    continue
                string = fevent_manager.fevent_chunks[0x0128][2].text_tables[0x43 + i].entries[0x2D] # "You got 10 coins!"
                if b"10" in string:
                    string = string.replace(b"10", str([1, 5, 10, 50, 100][treasure.quantity] * treasure.max_hits).encode(BIS_ENCODING), 1)
                else:
                    print(f"!!randomize_treasure!! string does not countain a coin count in lang {i}")
                treasure.textbox.append(b"\xff\x35" + string)
                treasure.textbox_sizes.append(get_meswin_size(string, font_file))

    ###################################################

    # ----------------------------------
    random.shuffle(treasure_list_random)
    # ----------------------------------
    return_list[1], treasure_list_random, badge_dict = assemble_all_shop_items(
        [settings.rando_ishop.isChecked(), settings.rando_gshop.isChecked(), settings.rando_bshop.isChecked()],
        shops_file,
        shop_data,
        treasure_list_random,
        treasure_strings,
        badge_dict
    )
    # ----------------------------------
    
    ###################################################

    # ----------------------------------
    random.shuffle(treasure_list_random)
    # ----------------------------------
    treasure_list_random, badge_dict = assemble_all_sidequests(
        [settings.rando_ball.isChecked(), settings.rando_hide.isChecked(), settings.rando_blitty.isChecked(), settings.rando_puzzle.isChecked()],
        fevent_manager,
        treasure_list_random,
        treasure_strings,
        badge_dict
    )
    # ----------------------------------

    ###################################################

    # ----------------------------------
    random.shuffle(treasure_list_random)
    # ----------------------------------
    for i in range(len(treasure_list_initial)):
        treasure_list_random[i].treasure_type = treasure_list_initial[i].treasure_type
        treasure_list_random[i].is_last_entry_in_room = treasure_list_initial[i].is_last_entry_in_room

        if treasure_list_initial[i].treasure_type == 0 or treasure_list_initial[i].treasure_type == 5:
            # with beans (0), this value actually represents the animation ID for the bean's visual dig spot
            # with grass (5), idk but it seems important lol
            treasure_list_random[i].max_hits = treasure_list_initial[i].max_hits
        elif treasure_list_initial[i].treasure_type != 1 and (treasure_list_random[i].item & 0xF000 != 0xF000):
            treasure_list_random[i].max_hits = 1
    # ----------------------------------
    return_list[0], treasure_list_random, badge_dict = assemble_all_treasure(
        treasure_file,
        treasure_list_random,
        treasure_to_skip,
        treasure_amt,
        overlays[1],
        overlays[2],
        overlays[3],
        map_metadata_offset,
        map_group_offset,
        treasure_data_offset,
        map_icon_data_offset,
        treasure_strings,
        place_text,
        badge_dict
    )
    # ----------------------------------

    if len(treasure_list_random) != 0:
        print(f"!!randomize_treasure!! length of remaining treasure: {len(treasure_list_random)}")
        parent.throw_error("ERROR WITH TREASURE LIST REINSERTION<br><br>REPORT THIS TO THEPURPLEANON", seed)
    
    if badge_dict: # "or" statement with all item placement dicts
        spoiler_file += "\n\n----" + treasure_strings[3] + "----"
        if badge_dict:
            for key, value in badge_dict.items():
                spoiler_file += f"\n{badge_names[(key - 0x3000) * 3]}: " + value

    arm9.seek(0)
    return *return_list, overlays[0], arm9.read(), spoiler_file, coin_string # "You got 10 coins!"


def set_item_prices(arm9, item_tables_offset, item_list):
    for item, price in item_list:
        item_type = item >> 12
        item_id = item & 0xFFF
        arm9.seek(item_tables_offset + ((item_type - 1) * 4))
        arm9.seek(int.from_bytes(arm9.read(4), 'little') - 0x2004000)
        match item_type:
            case 1: # attack items
                pass # ...don't have proper prices
            case 2: # consumable items
                arm9.seek((item_id * 24) + 12, 1)
                arm9.write(price.to_bytes(2, 'little'))
            case 3: # badge items
                arm9.seek((item_id * 16) + 12, 1)
                arm9.write(price.to_bytes(2, 'little'))
            case 4: # gear items
                arm9.seek((item_id * 32) + 12, 1)
                arm9.write(price.to_bytes(2, 'little'))
    return arm9


def gather_all_treasure(toggles, treasure_file):
    treasure_file = BytesIO(treasure_file)
    treasure_list = []
    treasure_to_skip = PEACH_CASTLE_INTRO_TREASURE_ENTRIES
    i = 0
    while True:
        if i in treasure_to_skip:
            i += 1
            continue
        treasure_file.seek(i * 12)
        treasure_read = treasure_file.read(12)
        if treasure_read == bytearray([0x00] * 12): # if treasure entry is empty
            break
        current_treasure = Treasure()
        current_treasure.from_treasure_info(treasure_read[:4])
        if current_treasure.item == 0:
            treasure_to_skip.append(i)
            i += 1
            continue

        if   toggles[0] and current_treasure.treasure_type == 0: pass # beans are enabled
        elif toggles[1] and current_treasure.treasure_type == 1: pass # "?" blocks are enabled
        elif toggles[2] and current_treasure.treasure_type in [4, 7]: pass # brick blocks are enabled
        elif toggles[3] and current_treasure.treasure_type == 5: pass # grass tufts are enabled
        else:
            treasure_to_skip.append(i)
            i += 1
            continue

        treasure_list.append(current_treasure)
        i += 1
    return treasure_list, treasure_to_skip, i

def gather_all_shop_items(toggles, shops_file):
    shop_data = ShopList(shops_file)
    treasure_list = []
    shop_list = [0, 1, 2, 1, 1, 1, 0, 1]
    for i, shop in enumerate(shop_data.shops):
        if   toggles[0] and shop_list[i] == 0: pass # item shops are enabled
        elif toggles[1] and shop_list[i] == 1: pass # gear shops are enabled
        elif toggles[2] and shop_list[i] == 2: pass # badge shop is enabled
        else: continue

        for item in shop:
            current_treasure = Treasure()
            current_treasure.from_item_id(item[0])
            treasure_list.append(current_treasure)
    return treasure_list, shop_data

def gather_all_sidequests(toggles, fevent_manager):
    treasure_list = []
    if toggles[0]:
        for command in fevent_manager.fevent_chunks[0x0128][0].subroutines[0x1C].commands: # mushroom ball derby
            if isinstance(command, CodeCommand) and (command.command_id == 0x0041 or command.command_id == 0x0044):
                current_treasure = Treasure()
                current_treasure.from_script_command(command)
                treasure_list.append(current_treasure)
    if toggles[1]:
        for command in fevent_manager.fevent_chunks[0x0129][0].subroutines[0x15].commands: # hide and seek
            if isinstance(command, CodeCommand) and (command.command_id == 0x0041 or command.command_id == 0x0044):
                current_treasure = Treasure()
                current_treasure.from_script_command(command)
                treasure_list.append(current_treasure)
    if toggles[2]:
        for command in fevent_manager.fevent_chunks[0x028D][0].subroutines[0x12].commands: # blitty rewards
            if isinstance(command, CodeCommand) and (command.command_id == 0x0041 or command.command_id == 0x0044):
                current_treasure = Treasure()
                current_treasure.from_script_command(command)
                treasure_list.append(current_treasure)
    if toggles[3]:
        for command in fevent_manager.fevent_chunks[0x0287][0].subroutines[0x13].commands: # puzzle 1 - 3
            if isinstance(command, CodeCommand) and (command.command_id == 0x0041 or command.command_id == 0x0044):
                for i in range(3):
                    current_treasure = Treasure()
                    current_treasure.from_script_command(command)
                    treasure_list.append(current_treasure)
        for command in fevent_manager.fevent_chunks[0x0287][0].subroutines[0x0D].commands: # puzzle 4
            if isinstance(command, CodeCommand) and (command.command_id == 0x0041 or command.command_id == 0x0044):
                current_treasure = Treasure()
                current_treasure.from_script_command(command)
                treasure_list.append(current_treasure)
    print(f"!!gather_all_sidequests!! length of sidequest treasure list: {len(treasure_list)}")
    return treasure_list


def assemble_all_treasure(treasure_file, treasure_list, treasure_to_skip, treasure_amt, map_data_overlay, treasure_data_overlay, map_icon_data_overlay, map_metadata_offset, map_group_offset, treasure_data_offset, map_icon_data_offset, treasure_strings, place_text, badge_dict):
    treasure_file = BytesIO(treasure_file)
    index = 0
    for i in range(treasure_amt):
        overlay3 = BytesIO(map_data_overlay)
        overlay4 = BytesIO(treasure_data_overlay)
        overlay129 = BytesIO(map_icon_data_overlay)
        if i in treasure_to_skip:
            continue
        treasure_file.seek(i * 12)
        treasure_file.write(treasure_list[index].to_treasure_info())
        if treasure_list[index].item & 0xF000 == 0x3000:
            for j in range(0x2A9):
                overlay3.seek(map_group_offset + (j * 20) + 16)
                treasure_index = int.from_bytes(overlay3.read(4), 'little')
                if treasure_index == 0xFFFFFFFF:
                    continue
                overlay4.seek(treasure_data_offset + 4 + (treasure_index * 4))
                treasure_start = int.from_bytes(overlay4.read(4), 'little')
                treasure_end = int.from_bytes(overlay4.read(4), 'little')
                if not (treasure_start <= (i * 12) and treasure_end > (i * 12)):
                    continue
                overlay3.seek(map_metadata_offset + (j * 12))
                map_meta = MapMetadata(overlay3.read(12))
                in_list = False
                for k in range(0x23):
                    overlay129.seek(map_icon_data_offset + (k * 12) + 4)
                    if map_meta.select_map in struct.unpack('<HHH', overlay129.read(6)):
                        overlay129.seek(map_icon_data_offset + (k * 12))
                        badge_dict[treasure_list[index].item] = f"{place_text[int.from_bytes(overlay129.read(2), 'little')]} - " + treasure_strings[2] + f" {hex(j)}"
                        in_list = True
                if not in_list: # inside of blubble lake is the only area not listed on the file select screen (where i've been grabbing these strings)
                    badge_dict[treasure_list[index].item] = f"{place_text[0xA]} - " + treasure_strings[2] + f" {hex(j)}"
                break
        index += 1
    treasure_file.seek(0)
    return treasure_file.read(), treasure_list[index:], badge_dict

def assemble_all_shop_items(toggles, shops_file, shop_data, treasure_list, treasure_strings, badge_dict):
    index = 0
    return_treasure = []
    shop_list = [0, 1, 2, 1, 1, 1, 0, 1]
    for i, shop in enumerate(shop_data.shops):
        if   toggles[0] and shop_list[i] == 0: pass
        elif toggles[1] and shop_list[i] == 1: pass
        elif toggles[2] and shop_list[i] == 2: pass
        else: continue

        for j, item in enumerate(shop):
            while treasure_list[index].item > 0xEFFF or treasure_list[index].item in [0x2014, 0x2015, 0x2016]: # prevent coins and beans from being in shops
                return_treasure.append(treasure_list[index])
                index += 1
            shop_data.shops[i][j][0] = treasure_list[index].item
            if treasure_list[index].item & 0xF000 == 0x3000:
                badge_dict[treasure_list[index].item] = treasure_strings[0][i]
                if shop_data.shops[i][j][1] != 0:
                    badge_dict[treasure_list[index].item] += " - " + treasure_strings[1][shop_data.shops[i][j][1] - 1]
            index += 1
    return_treasure += treasure_list[index:]
    return shop_data.pack(), return_treasure, badge_dict

def assemble_all_sidequests(toggles, fevent_manager, treasure_list, treasure_strings, badge_dict):
    if toggles[0]: treasure_list, badge_dict = assemble_mushroom_derby(fevent_manager, treasure_list, treasure_strings, badge_dict)
    if toggles[1]: treasure_list, badge_dict = assemble_hide_seek_toad(fevent_manager, treasure_list, treasure_strings, badge_dict)
    if toggles[2]: treasure_list, badge_dict = assemble_blitty_rewards(fevent_manager, treasure_list, treasure_strings, badge_dict)
    if toggles[3]: treasure_list, badge_dict = assemble_kuzzle_puzzles(fevent_manager, treasure_list, treasure_strings, badge_dict)
    return treasure_list, badge_dict

###############################################################################################################################################
###############################################################################################################################################
###############################################################################################################################################

class TreasureTab(QtWidgets.QWidget):
    def __init__(self, overlay_FObj_offsets, overlay_FObjPc_offsets, overlay_FObj, FObj_file, FObjPc_file, overlay_MObj_offsets, overlay_MObj, MObj_file):
        super().__init__()

        main_layout = QtWidgets.QGridLayout(self)

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

        line_layout.addWidget(QtWidgets.QLabel(self.tr("Randomization Pool")))

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)
        line_layout.addWidget(line)

        main_layout.addWidget(line_title, 0, 0, 1, 4)
        # ------------------------------------------

        # TODO: make the check amt dynamic

        self.rando_dig = QtWidgets.QCheckBox(self.tr("Dig Spots"))
        main_layout.addWidget(self.rando_dig, 2, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.rando_dig.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x2FD, 0, 0))
        amt = 197
        main_layout.addWidget(QtWidgets.QLabel(self.get_check_string(amt)), 3, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_block = QtWidgets.QCheckBox(self.tr('"?" Blocks'))
        main_layout.addWidget(self.rando_block, 2, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.rando_block.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0xA, 1, 0))
        amt = 276
        main_layout.addWidget(QtWidgets.QLabel(self.get_check_string(amt)), 3, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_brick = QtWidgets.QCheckBox(self.tr("Brick Blocks"))
        main_layout.addWidget(self.rando_brick, 2, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.rando_brick.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x150, 0, 0))
        amt = 149
        main_layout.addWidget(QtWidgets.QLabel(self.get_check_string(amt)), 3, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_grass = QtWidgets.QCheckBox(self.tr("Grass Tufts"))
        main_layout.addWidget(self.rando_grass, 2, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.rando_grass.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x5F, 0, 0))
        amt = 20
        main_layout.addWidget(QtWidgets.QLabel(self.get_check_string(amt)), 3, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        # ------------------------------------------
        padding = QtWidgets.QWidget()
        main_layout.addWidget(padding, 4, 0, 1, 4)
        padding.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # ------------------------------------------

        self.rando_ball = QtWidgets.QCheckBox(self.tr("Mushroom Ball Rewards"))
        main_layout.addWidget(self.rando_ball, 5, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.rando_ball.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x2EB, 0, 0))
        amt = 16
        main_layout.addWidget(QtWidgets.QLabel(self.get_check_string(amt)), 6, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_hide = QtWidgets.QCheckBox(self.tr("Hide and Seek Rewards"))
        main_layout.addWidget(self.rando_hide, 5, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.rando_hide.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x391, 12, 0))
        amt = 1
        main_layout.addWidget(QtWidgets.QLabel(self.get_check_string(amt)), 6, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        
        self.rando_blitty = QtWidgets.QCheckBox(self.tr("Blitty Rewards"))
        main_layout.addWidget(self.rando_blitty, 5, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.rando_blitty.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x318, 12, 0))
        amt = 3
        main_layout.addWidget(QtWidgets.QLabel(self.get_check_string(amt)), 6, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        
        self.rando_puzzle = QtWidgets.QCheckBox(self.tr("Kuzzle Rewards"))
        main_layout.addWidget(self.rando_puzzle, 5, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.rando_puzzle.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x354, 0, 0))
        amt = 12
        main_layout.addWidget(QtWidgets.QLabel(self.get_check_string(amt)), 6, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        # ------------------------------------------
        padding = QtWidgets.QWidget()
        main_layout.addWidget(padding, 7, 0, 1, 4)
        padding.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # ------------------------------------------

        # self.rando_node = QtWidgets.QCheckBox(self.tr("Challenge Node"))
        # main_layout.addWidget(self.rando_node, 8, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        # self.rando_node.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x374, 2, 0))
        # amt = 7
        # main_layout.addWidget(QtWidgets.QLabel(self.get_check_string(amt)), 9, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        # self.rando_bros = QtWidgets.QCheckBox(self.tr("Cholesteroad"))
        # main_layout.addWidget(self.rando_bros, 8, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        # self.rando_bros.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x373, 2, 4))
        # amt = 19
        # main_layout.addWidget(QtWidgets.QLabel(self.get_check_string(amt)), 9, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        # 
        # self.rando_brawl = QtWidgets.QCheckBox(self.tr("Broque Madame"))
        # main_layout.addWidget(self.rando_brawl, 8, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        # self.rando_brawl.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x34a, 0, 0))
        # amt = 13
        # main_layout.addWidget(QtWidgets.QLabel(self.get_check_string(amt)), 9, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        # 
        # self.rando_rank = QtWidgets.QCheckBox(self.tr("Final Rank Rewards"))
        # main_layout.addWidget(self.rando_rank, 8, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        # self.rando_rank.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x393, 5, 0))
        # amt = 2
        # main_layout.addWidget(QtWidgets.QLabel(self.get_check_string(amt)), 9, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        # # ------------------------------------------
        # padding = QtWidgets.QWidget()
        # main_layout.addWidget(padding, 10, 0, 1, 4)
        # padding.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # # ------------------------------------------

        self.rando_ishop = QtWidgets.QCheckBox(self.tr("Item Shops"))
        main_layout.addWidget(self.rando_ishop, 11, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.rando_ishop.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x26, 0, 0))
        amt = 22
        main_layout.addWidget(QtWidgets.QLabel(self.get_check_string(amt)), 12, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_gshop = QtWidgets.QCheckBox(self.tr("Gear Shops"))
        main_layout.addWidget(self.rando_gshop, 11, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.rando_gshop.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x28, 0, 0))
        amt = 37
        main_layout.addWidget(QtWidgets.QLabel(self.get_check_string(amt)), 12, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_bshop = QtWidgets.QCheckBox(self.tr("Badge Shop"))
        main_layout.addWidget(self.rando_bshop, 11, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.rando_bshop.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x29, 1, 0))
        amt = 5
        main_layout.addWidget(QtWidgets.QLabel(self.get_check_string(amt)), 12, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        # self.rando_bird = QtWidgets.QCheckBox(self.tr("Birdley"))
        # main_layout.addWidget(self.rando_bird, 11, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        # self.rando_bird.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x1AD, 0, 0))
        # amt = 1
        # main_layout.addWidget(QtWidgets.QLabel(self.get_check_string(amt)), 12, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        # ------------------------------------------
        padding = QtWidgets.QWidget()
        main_layout.addWidget(padding, 13, 0, 1, 4)
        padding.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # ------------------------------------------

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

        line_layout.addWidget(QtWidgets.QLabel(f'{self.tr("Important Items")} (NYI)'))

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)
        line_layout.addWidget(line)

        main_layout.addWidget(line_title, 14, 0, 1, 4)
        # ------------------------------------------

        self.rando_key_r = QtWidgets.QCheckBox(self.tr("Red Key"))
        main_layout.addWidget(self.rando_key_r, 17, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_key_b = QtWidgets.QCheckBox(self.tr("Blue Key"))
        main_layout.addWidget(self.rando_key_b, 17, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_key_g = QtWidgets.QCheckBox(self.tr("Green Key"))
        main_layout.addWidget(self.rando_key_g, 17, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_bill = QtWidgets.QCheckBox(self.tr("Banzai Bill"))
        main_layout.addWidget(self.rando_bill, 17, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        # ------------------------------------------
        padding = QtWidgets.QWidget()
        main_layout.addWidget(padding, 18, 0, 1, 4)
        padding.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # ------------------------------------------

        self.rando_cure_r = QtWidgets.QCheckBox(self.tr("Red Star Cure"))
        main_layout.addWidget(self.rando_cure_r, 20, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_cure_y = QtWidgets.QCheckBox(self.tr("Yellow Star Cure"))
        main_layout.addWidget(self.rando_cure_y, 20, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_cure_g = QtWidgets.QCheckBox(self.tr("Green Star Cure"))
        main_layout.addWidget(self.rando_cure_g, 20, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_stingler = QtWidgets.QCheckBox(self.tr("Stingler"))
        main_layout.addWidget(self.rando_stingler, 20, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        # ------------------------------------------
        padding = QtWidgets.QWidget()
        main_layout.addWidget(padding, 21, 0, 1, 4)
        padding.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # ------------------------------------------

        self.rando_hammer = QtWidgets.QCheckBox(self.tr("Hammer"))
        main_layout.addWidget(self.rando_hammer, 23, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_mini = QtWidgets.QCheckBox(self.tr("Mini Mario"))
        main_layout.addWidget(self.rando_mini, 23, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_spin = QtWidgets.QCheckBox(self.tr("Spin Jump"))
        main_layout.addWidget(self.rando_spin, 23, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_drill = QtWidgets.QCheckBox(self.tr("Drill Bros."))
        main_layout.addWidget(self.rando_drill, 23, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        # ------------------------------------------
        padding = QtWidgets.QWidget()
        main_layout.addWidget(padding, 24, 0, 1, 4)
        padding.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # ------------------------------------------

        self.rando_flame = QtWidgets.QCheckBox(self.tr("Flame"))
        main_layout.addWidget(self.rando_flame, 26, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_slide = QtWidgets.QCheckBox(self.tr("Sliding Punch"))
        main_layout.addWidget(self.rando_slide, 26, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_slam = QtWidgets.QCheckBox(self.tr("Body Slam"))
        main_layout.addWidget(self.rando_slam, 26, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_spike = QtWidgets.QCheckBox(self.tr("Spike Ball"))
        main_layout.addWidget(self.rando_spike, 26, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        # ------------------------------------------
        padding = QtWidgets.QWidget()
        main_layout.addWidget(padding, 27, 0, 1, 4)
        padding.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # ------------------------------------------

        self.rando_vent = QtWidgets.QCheckBox(self.tr("Air Vents"))
        main_layout.addWidget(self.rando_vent, 29, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_shell = QtWidgets.QCheckBox(self.tr("Blue Shell Blocks"))
        main_layout.addWidget(self.rando_shell, 29, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        i = 17
        sprite = QtWidgets.QLabel()
        sprite.setPixmap(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x6E, 1, 0).transformed(QtGui.QTransform().scale(2, 2)))
        main_layout.addWidget(sprite, 16 + ((i // 4) * 3), i % 4, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_vacuum = QtWidgets.QCheckBox(self.tr("Vacuum Block"))
        main_layout.addWidget(self.rando_vacuum, 29, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_badge = QtWidgets.QCheckBox(self.tr("Badges"))
        main_layout.addWidget(self.rando_badge, 29, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        # ------------------------------------------
        padding = QtWidgets.QWidget()
        main_layout.addWidget(padding, 30, 0, 1, 4)
        padding.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # ------------------------------------------

        sprites = generate_sprites_from_sheet(str(FILES_DIR / "img_key.png"), 20, (16, 16))
        for i in range(20):
            if i in [17]: continue
            sprite = QtWidgets.QLabel()
            sprite.setPixmap(sprites[i].transformed(QtGui.QTransform().scale(2, 2)))
            main_layout.addWidget(sprite, 16 + ((i // 4) * 3), i % 4, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.rando_dig.setChecked(True)
        self.rando_block.setChecked(True)
        self.rando_brick.setChecked(True)
        self.rando_grass.setChecked(True)

        self.rando_ball.setChecked(True)
        self.rando_hide.setChecked(True)
        self.rando_blitty.setChecked(True)
        self.rando_puzzle.setChecked(True)

        # self.rando_node.setEnabled(False)
        # self.rando_bros.setEnabled(False)
        # self.rando_brawl.setEnabled(False)
        # self.rando_rank.setEnabled(False)

        self.rando_ishop.setChecked(True)
        self.rando_gshop.setChecked(True)
        self.rando_bshop.setChecked(True)
        # self.rando_bird.setEnabled(False)

        self.rando_key_r.setEnabled(False)
        self.rando_key_b.setEnabled(False)
        self.rando_key_g.setEnabled(False)
        self.rando_bill.setEnabled(False)

        self.rando_cure_r.setEnabled(False)
        self.rando_cure_y.setEnabled(False)
        self.rando_cure_g.setEnabled(False)
        self.rando_stingler.setEnabled(False)

        self.rando_hammer.setEnabled(False)
        self.rando_mini.setEnabled(False)
        self.rando_spin.setEnabled(False)
        self.rando_drill.setEnabled(False)

        self.rando_flame.setEnabled(False)
        self.rando_slide.setEnabled(False)
        self.rando_slam.setEnabled(False)
        self.rando_spike.setEnabled(False)

        self.rando_vent.setEnabled(False)
        self.rando_shell.setEnabled(False)
        self.rando_vacuum.setEnabled(False)
        self.rando_badge.setEnabled(False)
    
    def get_check_string(self, amt):
        if amt == 1:
            return self.tr(f"{amt} Check")
        else:
            return self.tr(f"{amt} Checks")