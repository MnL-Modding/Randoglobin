from io import BytesIO
import struct
import random

from PySide6 import QtCore, QtGui, QtWidgets

from randoglobin.constants import *
from randoglobin.data_classes import Treasure, ShopList, MapMetadata
from randoglobin.image import create_BObj_sprite, create_MObj_sprite

# =========================================================================================================================

PEACH_CASTLE_INTRO_TREASURE_ENTRIES = [
    0x291, # room 0x216
    0x292, # room 0x216
    0x293, # room 0x216
    0x294, # room 0x216
    0x295, # room 0x217
]

def randomize_treasure(parent, seed, settings, treasure_file, shops_file, arm9, item_tables_offset, badge_patch_offset, map_metadata_offset, map_group_offset, treasure_data_offset, map_icon_data_offset, overlays, treasure_strings, place_text, badge_names, spoiler_file): # TO DO: figure out what energy hold coins do
    random.seed(seed)
    randomize_treasure_spots = settings.rando_junk.isChecked()
    randomize_shop_items = settings.rando_shop.isChecked()
    save = treasure_file

    treasure_list_initial = []
    treasure_list_random = []
    badge_dict = {}

    # ----------------------------------
    if randomize_treasure_spots:
        treasure_list_initial, treasure_to_skip = gather_all_treasure(treasure_file)
        treasure_list_random, _null = gather_all_treasure(treasure_file)
    # ----------------------------------
    if randomize_shop_items:
        shop_list_random, shop_data = gather_all_shop_items(shops_file)
        treasure_list_random += shop_list_random
        for i in range(0xD): # make all shops consumable type
            overlays[0][0x2C804 + 2 + (i * 36)] = 0
        for i in range(8): # fix badges in blocks
            arm9.seek(badge_patch_offset + (i * 16) + 6)
            arm9.write(b'\x02')
            arm9.seek(1, 1)
            arm9.write(b'\x00\x02\x00\x01')
        arm9 = set_item_prices( # fix item prices
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

    # ----------------------------------
    random.shuffle(treasure_list_random)
    # ----------------------------------
    if randomize_shop_items:
        return_list[1], treasure_list_random, badge_dict = assemble_all_shop_items(
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
    for i in range(len(treasure_list_initial)):
        treasure_list_random[i].treasure_type = treasure_list_initial[i].treasure_type
        treasure_list_random[i].is_last_entry_in_room = treasure_list_initial[i].is_last_entry_in_room

        if treasure_list_initial[i].treasure_type == 0:
            treasure_list_random[i].max_hits = treasure_list_initial[i].max_hits # with beans, this value actually represents the animation ID for the bean's visual dig spot
        else:
            treasure_list_random[i].max_hits = 1
    # ----------------------------------
    if randomize_treasure_spots:
        return_list[0], treasure_list_random, badge_dict = assemble_all_treasure(
            treasure_file,
            treasure_list_random,
            treasure_to_skip,
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
        parent.throw_error("ERROR WITH TREASURE LIST REINSERTION<br><br>REPORT THIS TO THEPURPLEANON", seed)
    
    if randomize_shop_items: # "or" statement with all rando options, except junk
        spoiler_file += "\n\n----" + treasure_strings[3] + "----"
    if randomize_shop_items: # shop only
        for key, value in badge_dict.items():
            spoiler_file += f"\n{badge_names[(key - 0x3000) * 3]}: " + value
    
    arm9.seek(0)
    return *return_list, overlays[0], arm9.read(), spoiler_file


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


def gather_all_treasure(treasure_file):
    treasure_amt = 0x2AD
    treasure_file = BytesIO(treasure_file)
    treasure_list = []
    treasure_to_skip = PEACH_CASTLE_INTRO_TREASURE_ENTRIES
    for i in range(treasure_amt):
        if i in treasure_to_skip:
            continue
        treasure_file.seek(i * 12)
        current_treasure = Treasure()
        current_treasure.from_treasure_info(treasure_file.read(4))
        if current_treasure.item == 0:
            treasure_to_skip.append(i)
            continue
        treasure_list.append(current_treasure)
    return treasure_list, treasure_to_skip

def gather_all_shop_items(shops_file):
    shop_data = ShopList(shops_file)
    treasure_list = []
    for shop in shop_data.shops:
        for item in shop:
            current_treasure = Treasure()
            current_treasure.from_item_id(item[0])
            treasure_list.append(current_treasure)
    return treasure_list, shop_data


def assemble_all_treasure(treasure_file, treasure_list, treasure_to_skip, map_data_overlay, treasure_data_overlay, map_icon_data_overlay, map_metadata_offset, map_group_offset, treasure_data_offset, map_icon_data_offset, treasure_strings, place_text, badge_dict):
    treasure_amt = 0x2AD
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
                for k in range(0x23):
                    overlay129.seek(map_icon_data_offset + (k * 12) + 4)
                    if map_meta.select_map in struct.unpack('<HHH', overlay129.read(6)):
                        overlay129.seek(map_icon_data_offset + (k * 12))
                        badge_dict[treasure_list[index].item] = f"{place_text[int.from_bytes(overlay129.read(2), 'little')]} - " + treasure_strings[2] + f" {hex(j)}"
                break
        index += 1
    treasure_file.seek(0)
    return treasure_file.read(), treasure_list[index:], badge_dict

def assemble_all_shop_items(shops_file, shop_data, treasure_list, treasure_strings, badge_dict):
    index = 0
    return_treasure = []
    for i, shop in enumerate(shop_data.shops):
        for j, item in enumerate(shop):
            while treasure_list[index].item > 0x4FFF or treasure_list[index].item in [0x2014, 0x2015, 0x2016]: # prevent coins and beans from being in shops
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

###############################################################################################################################################
###############################################################################################################################################
###############################################################################################################################################

class TreasureTab(QtWidgets.QWidget):
    def __init__(self, overlay_FObj_offsets, overlay_FObjPc_offsets, overlay_FObj, FObj_file, FObjPc_file, overlay_MObj_offsets, overlay_MObj, MObj_file):
        super().__init__()

        main_layout = QtWidgets.QVBoxLayout(self)

        self.rando_junk = QtWidgets.QCheckBox(self.tr("Randomize Junk Treasure Spots"))
        main_layout.addWidget(self.rando_junk, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.rando_junk.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x26, 0, 0))

        self.rando_shop = QtWidgets.QCheckBox(self.tr("Randomize Shop Items"))
        self.rando_shop.checkStateChanged.connect(self.shop_check_state_changed)
        main_layout.addWidget(self.rando_shop, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.rando_shop.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x29, 1, 0))

        # ------------------------------------------
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line)
        # ------------------------------------------

        main_layout.addWidget(QtWidgets.QLabel(self.tr("Important items that are in the randomization pool:")), alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        spoiler_demo = QtWidgets.QWidget()
        spoiler_demo_layout = QtWidgets.QVBoxLayout(spoiler_demo)

        # badges ----------------------------------------------------------------------------------
        self.badge_frame = QtWidgets.QFrame()
        category_layout = QtWidgets.QHBoxLayout(self.badge_frame)

        tex = create_MObj_sprite(
            overlay_MObj_offsets,
            overlay_MObj,
            MObj_file,
            0x20, 16, 0)
        #tex = tex.transformed(QtGui.QTransform().scale(2, 2))
        img = QtWidgets.QLabel()
        img.setPixmap(tex)
        category_layout.addWidget(img)

        string = self.tr("Badges")
        category_layout.addWidget(QtWidgets.QLabel(string))

        tex = create_MObj_sprite(
            overlay_MObj_offsets,
            overlay_MObj,
            MObj_file,
            0x20, 12, 0)
        #tex = tex.transformed(QtGui.QTransform().scale(2, 2))
        img = QtWidgets.QLabel()
        img.setPixmap(tex)
        category_layout.addWidget(img)

        spoiler_demo_layout.addWidget(self.badge_frame, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        # key items -------------------------------------------------------------------------------
        self.key_frame = QtWidgets.QFrame()
        category_layout = QtWidgets.QHBoxLayout(self.key_frame)

        tex = create_MObj_sprite(
            overlay_FObj_offsets,
            overlay_FObj,
            FObj_file,
            0xAA, 0, 0)
        #tex = tex.transformed(QtGui.QTransform().scale(2, 2))
        img = QtWidgets.QLabel()
        img.setPixmap(tex)
        category_layout.addWidget(img)

        string = self.tr("Key Items")
        string += " - " + self.tr("NOT YET IMPLEMENTED")
        category_layout.addWidget(QtWidgets.QLabel(string))

        tex = create_MObj_sprite(
            overlay_FObj_offsets,
            overlay_FObj,
            FObj_file,
            0x36, 2, 0)
        #tex = tex.transformed(QtGui.QTransform().scale(2, 2))
        img = QtWidgets.QLabel()
        img.setPixmap(tex)
        category_layout.addWidget(img)

        spoiler_demo_layout.addWidget(self.key_frame, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        # cures -------------------------------------------------------------------------------
        self.cure_frame = QtWidgets.QFrame()
        category_layout = QtWidgets.QHBoxLayout(self.cure_frame)

        tex = create_MObj_sprite(
            overlay_FObjPc_offsets,
            overlay_FObj,
            FObjPc_file,
            0xDF, 1, 21)
        #tex = tex.transformed(QtGui.QTransform().scale(2, 2))
        img = QtWidgets.QLabel()
        img.setPixmap(tex)
        category_layout.addWidget(img)

        string = self.tr("Star Cures")
        string += " - " + self.tr("NOT YET IMPLEMENTED")
        category_layout.addWidget(QtWidgets.QLabel(string))

        tex = create_MObj_sprite(
            overlay_FObj_offsets,
            overlay_FObj,
            FObj_file,
            0x26D, 0, 0)
        #tex = tex.transformed(QtGui.QTransform().scale(2, 2))
        img = QtWidgets.QLabel()
        img.setPixmap(tex)
        category_layout.addWidget(img)

        spoiler_demo_layout.addWidget(self.cure_frame, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        # field abilities -------------------------------------------------------------------------
        self.ability_frame = QtWidgets.QFrame()
        category_layout = QtWidgets.QHBoxLayout(self.ability_frame)

        tex = create_MObj_sprite(
            overlay_FObjPc_offsets,
            overlay_FObj,
            FObjPc_file,
            0x26, 12, 0)
        #tex = tex.transformed(QtGui.QTransform().scale(2, 2))
        img = QtWidgets.QLabel()
        img.setPixmap(tex)
        category_layout.addWidget(img)

        string = self.tr("Field Abilities")
        string += " - " + self.tr("NOT YET IMPLEMENTED")
        category_layout.addWidget(QtWidgets.QLabel(string))

        tex = create_MObj_sprite(
            overlay_FObj_offsets,
            overlay_FObj,
            FObj_file,
            0x113, 0, 0)
        #tex = tex.transformed(QtGui.QTransform().scale(2, 2))
        img = QtWidgets.QLabel()
        img.setPixmap(tex)
        category_layout.addWidget(img)

        spoiler_demo_layout.addWidget(self.ability_frame, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(spoiler_demo)

        # ------------------------------------------
        padding = QtWidgets.QWidget()
        main_layout.addWidget(padding)
        padding.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.rando_junk.setChecked(True)
        self.rando_shop.setChecked(True)

        self.key_frame.setEnabled(False)
        self.cure_frame.setEnabled(False)
        self.ability_frame.setEnabled(False)
    
    def shop_check_state_changed(self):
        self.badge_frame.setEnabled(self.rando_shop.isChecked())