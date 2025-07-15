import random
import struct
from io import BytesIO

if '__compiled__' not in globals():
    import rustimport.import_hook

from PySide6 import QtCore, QtGui, QtWidgets
from functools import partial
from mnllib.bis import compress, decompress

from randoglobin.constants import *
from randoglobin.image import create_BObj_sprite, create_MObj_sprite, create_textbox
from randoglobin.rust import modify_maps

# ============================================================================================================================

def randomize_colors(parent, seed, settings, arm9_file, arm9_palette_offset, bobj_files, bobj_overlays, bobj_offsets, eobj_files, eobj_overlays, eobj_offsets, fobj_files, fobj_overlays, fobj_offsets, mobj_files, mobj_overlays, mobj_offsets, fmap_file, fmap_offsets, spoiler_file, palette_string, player_names, treasure_info):
    random.seed(seed)
    if settings.use_custom_colors.isChecked():
        bros_colors = [
            settings.mario_color_0.currentIndex(), # mario's hat color
            settings.mario_color_1.currentIndex(), # mario's overalls color
            settings.luigi_color_0.currentIndex(), # luigi's hat color
            settings.luigi_color_1.currentIndex(), # luigi's overalls color
            settings.mario_color_inv.isChecked(), # whether to swap mario's colors
            settings.luigi_color_inv.isChecked(), # whether to swap luigi's colors
        ]
        koopa_colors = [
            settings.koopa_color_0.currentIndex(), # bowser's skin color
            settings.koopa_color_1.currentIndex(), # bowser's shell color
            settings.koopa_color_2.currentIndex(), # bowser's face color
            settings.koopa_color_3.currentIndex(), # bowser's hair color
        ]
    else:
        if settings.default_buttons.isChecked():
            bros_colors = [
                random.randint(0, len(PAL_0_CHOICES) - 1), # mario's hat color
                random.randint(0, len(PAL_1_CHOICES) - 1), # mario's overalls color
                random.randint(0, len(PAL_0_CHOICES) - 1), # luigi's hat color
                random.randint(0, len(PAL_1_CHOICES) - 1), # luigi's overalls color
                bool(random.randint(0, 1)), # whether to swap mario's colors
                bool(random.randint(0, 1)), # whether to swap luigi's colors
            ]
        else:
            _bros = random.sample(range(len(PAL_0_CHOICES)), 2) # ensure both bros' UI color wouldn't be the same
            bros_colors = [
                _bros[0], # mario's hat color
                random.randint(0, len(PAL_1_CHOICES) - 1), # mario's overalls color
                _bros[1], # luigi's hat color
                random.randint(0, len(PAL_1_CHOICES) - 1), # luigi's overalls color
                bool(random.randint(0, 1)), # whether to swap mario's colors
                bool(random.randint(0, 1)), # whether to swap luigi's colors
            ]
        koopa_colors = [
            random.randint(0, len(PAL_KP_0_CHOICES) - 1), # bowser's skin color
            random.randint(0, len(PAL_KP_1_CHOICES) - 1), # bowser's shell color
            random.randint(0, len(PAL_KP_2_CHOICES) - 1), # bowser's face color
            random.randint(0, len(PAL_KP_3_CHOICES) - 1), # bowser's hair color
        ]
    
        if not settings.swap_colors_allowed.isChecked():
            bros_colors[4] = False
            bros_colors[5] = False
    
    arm9_file = assign_text_colors(
        bros_colors,
        koopa_colors,
        settings.default_buttons.isChecked(),
        arm9_file,
        arm9_palette_offset)

    bobj_files = assign_bobj_colors(
        bros_colors,
        koopa_colors,
        settings.default_buttons.isChecked(),
        bobj_files,
        bobj_overlays,
        bobj_offsets,
    )

    eobj_files = assign_eobj_colors(
        bros_colors,
        koopa_colors,
        settings.default_buttons.isChecked(),
        eobj_files,
        eobj_overlays,
        eobj_offsets,
    )

    fobj_files = assign_fobj_colors(
        bros_colors,
        koopa_colors,
        settings.default_buttons.isChecked(),
        fobj_files,
        fobj_overlays[0],
        fobj_offsets,
    )

    mobj_files = assign_mobj_colors(
        bros_colors,
        koopa_colors,
        settings.default_buttons.isChecked(),
        mobj_files,
        mobj_overlays,
        mobj_offsets,
    )

    overlay3 = bytearray(fobj_overlays[0])
    if not settings.default_buttons.isChecked():
        mario_pal_2 = struct.pack('<5H', *generate_color_lists(PAL_2_CHOICES[bros_colors[0]]))
        luigi_pal_2 = struct.pack('<5H', *generate_color_lists(PAL_2_CHOICES[bros_colors[2]]))

        fobj_overlays[1] = bytearray(fobj_overlays[1])

        fmap_file = modify_maps(
            bytes(fmap_file),
            bytes(treasure_info),
            overlay3,
            bytearray(fobj_overlays[1]),
            mario_pal_2,
            luigi_pal_2,
        )

    spoiler_file += "\n\n----" + palette_string + "----\n"
    spoiler_file += f"{player_names[0]}: \n"
    spoiler_file += f"{PaletteTab.tr("Primary Color")}: {settings.PAL_0_NAMES[bros_colors[0]]}\n"
    spoiler_file += f"{PaletteTab.tr("Secondary Color")}: {settings.PAL_1_NAMES[bros_colors[1]]}\n"
    if bros_colors[4]:
        spoiler_file += f"{PaletteTab.tr("Swap Colors")} = {PaletteTab.tr("True")}\n\n"
    else:
        spoiler_file += f"{PaletteTab.tr("Swap Colors")} = {PaletteTab.tr("False")}\n\n"
    
    spoiler_file += f"{player_names[1]}: \n"
    spoiler_file += f"{PaletteTab.tr("Primary Color")}: {settings.PAL_0_NAMES[bros_colors[2]]}\n"
    spoiler_file += f"{PaletteTab.tr("Secondary Color")}: {settings.PAL_1_NAMES[bros_colors[3]]}\n"
    if bros_colors[5]:
        spoiler_file += f"{PaletteTab.tr("Swap Colors")} = {PaletteTab.tr("True")}\n\n"
    else:
        spoiler_file += f"{PaletteTab.tr("Swap Colors")} = {PaletteTab.tr("False")}\n\n"
    
    spoiler_file += f"{player_names[2]}: \n"
    spoiler_file += f"{PaletteTab.tr("Skin")}: {settings.PAL_KP_0_NAMES[koopa_colors[0]]}\n"
    spoiler_file += f"{PaletteTab.tr("Shell")}: {settings.PAL_KP_1_NAMES[koopa_colors[1]]}\n"
    spoiler_file += f"{PaletteTab.tr("Face")}: {settings.PAL_KP_2_NAMES[koopa_colors[2]]}\n"
    spoiler_file += f"{PaletteTab.tr("Hair")}: {settings.PAL_KP_3_NAMES[koopa_colors[3]]}"

    return arm9_file, *bobj_files, *eobj_files, *fobj_files, *mobj_files, fmap_file, spoiler_file, overlay3

# ============================================================================================================================

def assign_text_colors(bros_colors, koopa_colors, default_buttons, arm9_file, palette_offset):
    if default_buttons:
        return arm9_file

    text_pal_0a = struct.pack('<2H', *generate_color_lists(PAL_TEXT_CHOICES[0][bros_colors[0]][0]))
    text_pal_0b = struct.pack('<2H', *generate_color_lists(PAL_TEXT_CHOICES[0][bros_colors[0]][1]))
    text_pal_1a = struct.pack('<2H', *generate_color_lists(PAL_TEXT_CHOICES[0][bros_colors[2]][0]))
    text_pal_1b = struct.pack('<2H', *generate_color_lists(PAL_TEXT_CHOICES[0][bros_colors[2]][1]))
    text_pal_2a = struct.pack('<2H', *generate_color_lists(PAL_TEXT_CHOICES[1][koopa_colors[0]][0]))
    text_pal_2b = struct.pack('<2H', *generate_color_lists(PAL_TEXT_CHOICES[1][koopa_colors[0]][1]))

    arm9 = BytesIO(arm9_file)
    arm9.seek(palette_offset)

    arm9.seek(8 * 2, 1)
    arm9.write(text_pal_1a)
    arm9.write(text_pal_2a)
    arm9.seek(2 * 2, 1)
    arm9.write(text_pal_0a)
    arm9.seek(8 * 2, 1)
    arm9.write(text_pal_1b)
    arm9.write(text_pal_2b)
    arm9.seek(2 * 2, 1)
    arm9.write(text_pal_0b)

    arm9.seek(0)
    return arm9.read()

def assign_bobj_colors(bros_colors, koopa_colors, default_buttons, bobj_file, overlay_data, overlay_offsets): # bobjpc, bobjmon, bobjui | filedata, palette groups
    mario_pal_0 = struct.pack('<4H', *generate_color_lists(PAL_0_CHOICES[bros_colors[0]]))
    mario_pal_1 = struct.pack('<4H', *generate_color_lists(PAL_1_CHOICES[bros_colors[1]]))
    if bros_colors[4]:
        mario_pal_0, mario_pal_1 = mario_pal_1, mario_pal_0

    luigi_pal_0 = struct.pack('<4H', *generate_color_lists(PAL_0_CHOICES[bros_colors[2]]))
    luigi_pal_1 = struct.pack('<4H', *generate_color_lists(PAL_1_CHOICES[bros_colors[3]]))
    if bros_colors[5]:
        luigi_pal_0, luigi_pal_1 = luigi_pal_1, luigi_pal_0
        
    koopa_pal_0 = struct.pack('<10H', *generate_color_lists(PAL_KP_0_CHOICES[koopa_colors[0]]))
    koopa_pal_0A = struct.pack('<3H', *generate_color_lists(PAL_KP_0A_CHOICES[koopa_colors[0]]))
    koopa_pal_1 = struct.pack('<4H', *generate_color_lists(PAL_KP_1_CHOICES[koopa_colors[1]]))
    koopa_pal_2 = struct.pack('<4H', *generate_color_lists(PAL_KP_2_CHOICES[koopa_colors[2]]))
    koopa_pal_3 = struct.pack('<3H', *generate_color_lists(PAL_KP_3_CHOICES[koopa_colors[3]]))

    mario_pal_2 = struct.pack('<5H', *generate_color_lists(PAL_2_CHOICES[bros_colors[0]]))
    if bros_colors[4]:
        mario_pal_2a = struct.pack('<7H', *generate_color_lists(PAL_2A_CHOICES[bros_colors[0]] + PAL_2C_CHOICES[bros_colors[1]]))
    else:
        mario_pal_2a = struct.pack('<7H', *generate_color_lists(PAL_2A_CHOICES[bros_colors[0]] + PAL_2B_CHOICES[bros_colors[0]]))
    luigi_pal_2 = struct.pack('<5H', *generate_color_lists(PAL_2_CHOICES[bros_colors[2]]))
    if bros_colors[5]:
        luigi_pal_2a = struct.pack('<7H', *generate_color_lists(PAL_2A_CHOICES[bros_colors[2]] + PAL_2C_CHOICES[bros_colors[3]]))
    else:
        luigi_pal_2a = struct.pack('<7H', *generate_color_lists(PAL_2A_CHOICES[bros_colors[2]] + PAL_2B_CHOICES[bros_colors[2]]))
    koopa_pal_4 = struct.pack('<5H', *generate_color_lists(PAL_KP_4_CHOICES[koopa_colors[0]]))
    koopa_pal_4a = struct.pack('<1H', *generate_color_lists(PAL_KP_4A_CHOICES[koopa_colors[0]]))

    red_pal_0 = struct.pack('<6H', *generate_color_lists(RED_0))
    red_pal_1 = struct.pack('<3H', *generate_color_lists(RED_1))

    bobjpc_file = BytesIO(bobj_file[0])
    bobjmon_file = BytesIO(bobj_file[1])
    bobjui_file = BytesIO(bobj_file[2])
    overlay_data_file = BytesIO(overlay_data[0])
    overlay_data_group = BytesIO(overlay_data[1])

    overlay_data_group.seek(overlay_offsets[0][1] + (0x5 * 4)) # bros and bows
    overlay_data_file.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

    bobjpc_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x11 * 2))
    bobjpc_file.write(mario_pal_1)
    bobjpc_file.write(mario_pal_0)
    bobjpc_file.seek(0x38 * 2, 1)
    bobjpc_file.write(luigi_pal_1)
    bobjpc_file.write(luigi_pal_0)
    bobjpc_file.seek(0x29 * 2, 1)
    bobjpc_file.write(koopa_pal_0)
    bobjpc_file.write(koopa_pal_2)
    bobjpc_file.write(koopa_pal_1)
    bobjpc_file.write(koopa_pal_3)
    bobjpc_file.seek(0x6 * 2, 1)
    bobjpc_file.write(koopa_pal_0A)
    bobjpc_file.seek(0x12 * 2, 1)
    bobjpc_file.write(koopa_pal_0)
    bobjpc_file.write(koopa_pal_2)
    bobjpc_file.write(koopa_pal_1)
    bobjpc_file.write(koopa_pal_3)
    bobjpc_file.seek(0x6 * 2, 1)
    bobjpc_file.write(koopa_pal_0A)

    for i in [0xD, 0x13, 0x15, 0x1C]: # trash bros X, jump helmet bros, super bouncer bros, trash bros
        overlay_data_group.seek(overlay_offsets[0][1] + (i * 4))
        overlay_data_file.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjpc_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x11 * 2))
        bobjpc_file.write(mario_pal_1)
        bobjpc_file.write(mario_pal_0)
        bobjpc_file.seek(0x38 * 2, 1)
        bobjpc_file.write(luigi_pal_1)
        bobjpc_file.write(luigi_pal_0)

    for i in [0x1, 0x18]: # giant bowser
        overlay_data_group.seek(overlay_offsets[0][1] + (i * 4))
        overlay_data_file.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjpc_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x1 * 2))
        bobjpc_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 14, 15, 16, 17, 18, 19]]))
        bobjpc_file.seek(0xE * 2, 1)
        bobjpc_file.write(bytes([koopa_pal_0[i] for i in [16, 17]]))
        bobjpc_file.write(koopa_pal_2)
        bobjpc_file.write(koopa_pal_3)
        bobjpc_file.seek(0x3 * 2, 1)
        bobjpc_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 14, 15, 16, 17]]))
        bobjpc_file.write(koopa_pal_1)
        bobjpc_file.write(koopa_pal_0A)
        bobjpc_file.seek(0x8 * 2, 1)
        bobjpc_file.write(bytes([koopa_pal_0[i] for i in [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]]))
        bobjpc_file.seek(0x6 * 2, 1)
        bobjpc_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7]]))
        bobjpc_file.write(bytes([koopa_pal_0[i] for i in [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]]))
        bobjpc_file.seek(0x5 * 2, 1)
        bobjpc_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 14, 15, 16, 17, 18, 19]]))
        bobjpc_file.seek(0xE * 2, 1)
        bobjpc_file.write(bytes([koopa_pal_0[i] for i in [16, 17]]))
        bobjpc_file.write(koopa_pal_2)
        bobjpc_file.write(koopa_pal_3)
        bobjpc_file.seek(0x3 * 2, 1)
        bobjpc_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 14, 15, 16, 17]]))
        bobjpc_file.write(koopa_pal_1)
        bobjpc_file.write(koopa_pal_0A)
    
    overlay_data_group.seek(overlay_offsets[1][1] + (0x15 * 4)) # mario nose guy
    overlay_data_file.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

    bobjmon_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x8 * 2))
    bobjmon_file.write(bytes([mario_pal_0[i] for i in [0, 1, 2, 3, 4, 5]]))
    
    overlay_data_group.seek(overlay_offsets[1][1] + (0x16 * 4)) # luigi nose guy
    overlay_data_file.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

    bobjmon_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x8 * 2))
    bobjmon_file.write(bytes([luigi_pal_0[i] for i in [0, 1, 2, 3, 4, 5]]))

    overlay_data_group.seek(overlay_offsets[1][1] + (0x55 * 4)) # wisdurm bros faces
    overlay_data_file.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

    bobjmon_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x11 * 2))
    bobjmon_file.write(mario_pal_1)
    bobjmon_file.write(mario_pal_0)
    bobjmon_file.seek(0x18 * 2, 1)
    bobjmon_file.write(luigi_pal_1)
    bobjmon_file.write(luigi_pal_0)

    overlay_data_group.seek(overlay_offsets[1][1] + (0x6B * 4)) # enemy bowser
    overlay_data_file.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

    bobjmon_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x82 * 2))
    bobjmon_file.write(koopa_pal_0)
    bobjmon_file.write(koopa_pal_2)
    bobjmon_file.write(koopa_pal_1)
    bobjmon_file.write(koopa_pal_3)
    bobjmon_file.seek(0x6 * 2, 1)
    bobjmon_file.write(koopa_pal_0A)
    bobjmon_file.seek(0x12 * 2, 1)
    bobjmon_file.write(koopa_pal_0)
    bobjmon_file.write(koopa_pal_2)
    bobjmon_file.write(koopa_pal_1)
    bobjmon_file.write(koopa_pal_3)
    bobjmon_file.seek(0x6 * 2, 1)
    bobjmon_file.write(koopa_pal_0A)

    overlay_data_group.seek(overlay_offsets[1][1] + (0x85 * 4)) # trash luigi projectile
    overlay_data_file.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

    bobjmon_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x21 * 2))
    bobjmon_file.write(luigi_pal_1)
    bobjmon_file.write(luigi_pal_0)

    for i in [0x8C, 0x8D, 0xC6, 0xCC]: # red
        overlay_data_group.seek(overlay_offsets[1][1] + (i * 4))
        overlay_data_file.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjmon_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4)
        bobjmon_file.seek(0x6 * 2, 1)
        bobjmon_file.write(red_pal_0)
        bobjmon_file.seek(0xC * 2, 1)
        bobjmon_file.write(red_pal_1)

    overlay_data_group.seek(overlay_offsets[1][1] + (0xD0 * 4)) # giant enemy bowser
    overlay_data_file.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

    bobjmon_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x1 * 2))
    bobjmon_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 14, 15, 16, 17, 18, 19]]))
    bobjmon_file.seek(0xE * 2, 1)
    bobjmon_file.write(bytes([koopa_pal_0[i] for i in [16, 17]]))
    bobjmon_file.write(koopa_pal_2)
    bobjmon_file.write(koopa_pal_3)
    bobjmon_file.seek(0x3 * 2, 1)
    bobjmon_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 14, 15, 16, 17]]))
    bobjmon_file.write(koopa_pal_1)
    bobjmon_file.write(koopa_pal_0A)
    bobjmon_file.seek(0x8 * 2, 1)
    bobjmon_file.write(bytes([koopa_pal_0[i] for i in [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]]))
    bobjmon_file.seek(0x6 * 2, 1)
    bobjmon_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7]]))
    bobjmon_file.write(bytes([koopa_pal_0[i] for i in [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]]))
    bobjmon_file.seek(0x5 * 2, 1)
    bobjmon_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 14, 15, 16, 17, 18, 19]]))
    bobjmon_file.seek(0xE * 2, 1)
    bobjmon_file.write(bytes([koopa_pal_0[i] for i in [16, 17]]))
    bobjmon_file.write(koopa_pal_2)
    bobjmon_file.write(koopa_pal_3)
    bobjmon_file.seek(0x3 * 2, 1)
    bobjmon_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 14, 15, 16, 17]]))
    bobjmon_file.write(koopa_pal_1)

    for i in [0x19, 0xD7]: # durmite, durmite x
        overlay_data_group.seek(overlay_offsets[1][1] + (i * 4))
        overlay_data_file.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjmon_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x21 * 2))
        bobjmon_file.write(mario_pal_1)
        bobjmon_file.write(luigi_pal_1)

    for i in [0x80, 0xE3]: # trash luigi, trash luigi x
        overlay_data_group.seek(overlay_offsets[1][1] + (i * 4))
        overlay_data_file.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjmon_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x15 * 2))
        bobjmon_file.write(bytes([luigi_pal_0[i] for i in [0, 1, 2, 3, 4, 5]]))

    overlay_data_group.seek(overlay_offsets[2][1] + (0x7 * 4)) # bros icons
    overlay_data_file.seek(overlay_offsets[2][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

    bobjui_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x2 * 2))
    bobjui_file.write(mario_pal_0)
    bobjui_file.seek(0xC * 2, 1)
    bobjui_file.write(luigi_pal_0)

    overlay_data_group.seek(overlay_offsets[2][1] + (0x9 * 4)) # badge meter icons
    overlay_data_file.seek(overlay_offsets[2][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

    bobjui_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x12 * 2))
    bobjui_file.write(mario_pal_0)
    bobjui_file.seek(0xC * 2, 1)
    bobjui_file.write(luigi_pal_0)

    if not default_buttons:
        overlay_data_group.seek(overlay_offsets[0][1] + (0x9 * 4)) # yoo who cannon
        overlay_data_file.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjpc_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x2 * 2))
        if bros_colors[4]:
            bobjpc_file.write(bytes([mario_pal_1[i] for i in [0, 1, 4, 5]]))
        else:
            bobjpc_file.write(bytes([mario_pal_0[i] for i in [0, 1, 4, 5]]))
        if bros_colors[5]:
            bobjpc_file.write(bytes([luigi_pal_1[i] for i in [0, 1, 4, 5]]))
        else:
            bobjpc_file.write(bytes([luigi_pal_0[i] for i in [0, 1, 4, 5]]))

        overlay_data_group.seek(overlay_offsets[1][1] + (0x6e * 4)) # memory m
        overlay_data_file.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjmon_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x9 * 2))
        bobjmon_file.write(bytes([mario_pal_2a[i] for i in [10, 11]]))
        bobjmon_file.write(bytes([mario_pal_0[i] for i in [0, 1, 2, 3]]))
        bobjmon_file.write(bytes([mario_pal_1[i] for i in [0, 1, 2, 3]]))

        overlay_data_group.seek(overlay_offsets[1][1] + (0x6f * 4)) # memory l
        overlay_data_file.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjmon_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x9 * 2))
        bobjmon_file.write(bytes([luigi_pal_2a[i] for i in [10, 11]]))
        bobjmon_file.write(bytes([luigi_pal_0[i] for i in [0, 1, 2, 3]]))
        bobjmon_file.write(bytes([luigi_pal_1[i] for i in [0, 1, 2, 3]]))

        overlay_data_group.seek(overlay_offsets[1][1] + (0x73 * 4)) # memory m bricks
        overlay_data_file.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjmon_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x1 * 2))
        bobjmon_file.write(bytes([mario_pal_2a[i] for i in [0, 1]]))
        if bros_colors[4]:
            bobjmon_file.write(mario_pal_1)
        else:
            bobjmon_file.write(mario_pal_0)

        overlay_data_group.seek(overlay_offsets[1][1] + (0xbe * 4)) # memory l bricks
        overlay_data_file.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjmon_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x1 * 2))
        bobjmon_file.write(bytes([luigi_pal_2a[i] for i in [0, 1]]))
        if bros_colors[5]:
            bobjmon_file.write(luigi_pal_1)
        else:
            bobjmon_file.write(luigi_pal_0)

        overlay_data_group.seek(overlay_offsets[1][1] + (0x77 * 4)) # piranha plant orbs
        overlay_data_file.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjmon_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x2 * 2))
        bobjmon_file.write(bytes([mario_pal_2a[i] for i in [4, 5]]))
        if bros_colors[4]:
            bobjmon_file.write(bytes([mario_pal_1[i] for i in [0, 1]]))
        else:
            bobjmon_file.write(bytes([mario_pal_0[i] for i in [0, 1]]))
        bobjmon_file.write(bytes([mario_pal_2a[i] for i in [6, 7]]))
        if bros_colors[4]:
            bobjmon_file.write(bytes([mario_pal_1[i] for i in [2, 3, 4, 5]]))
        else:
            bobjmon_file.write(bytes([mario_pal_0[i] for i in [2, 3, 4, 5]]))
        bobjmon_file.seek(0xB * 2, 1)
        bobjmon_file.write(bytes([luigi_pal_2a[i] for i in [4, 5]]))
        if bros_colors[5]:
            bobjmon_file.write(bytes([luigi_pal_1[i] for i in [0, 1]]))
        else:
            bobjmon_file.write(bytes([luigi_pal_0[i] for i in [0, 1]]))
        bobjmon_file.write(bytes([luigi_pal_2a[i] for i in [6, 7]]))
        if bros_colors[5]:
            bobjmon_file.write(bytes([luigi_pal_1[i] for i in [2, 3, 4, 5]]))
        else:
            bobjmon_file.write(bytes([luigi_pal_0[i] for i in [2, 3, 4, 5]]))

        overlay_data_group.seek(overlay_offsets[1][1] + (0xdb * 4)) # memory mx
        overlay_data_file.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjmon_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x9 * 2))
        bobjmon_file.write(bytes([mario_pal_2a[i] for i in [10, 11]]))
        bobjmon_file.write(bytes([mario_pal_0[i] for i in [0, 1, 2, 3]]))

        overlay_data_group.seek(overlay_offsets[1][1] + (0xdc * 4)) # memory lx
        overlay_data_file.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjmon_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x9 * 2))
        bobjmon_file.write(bytes([luigi_pal_2a[i] for i in [10, 11]]))
        bobjmon_file.write(bytes([luigi_pal_0[i] for i in [0, 1, 2, 3]]))

        overlay_data_group.seek(overlay_offsets[2][1] + (0x0 * 4)) # PiT buttons
        overlay_data_file.seek(overlay_offsets[2][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjui_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x17 * 2))
        bobjui_file.write(mario_pal_2)
        bobjui_file.seek(0xB * 2, 1)
        bobjui_file.write(luigi_pal_2)

        overlay_data_group.seek(overlay_offsets[2][1] + (0x2 * 4)) # big buttons
        overlay_data_file.seek(overlay_offsets[2][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjui_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x2 * 2))
        bobjui_file.write(mario_pal_2)
        bobjui_file.write(luigi_pal_2)
        bobjui_file.seek(0x5 * 2, 1)
        bobjui_file.write(koopa_pal_4)

        overlay_data_group.seek(overlay_offsets[2][1] + (0xB * 4)) # counterattack buttons
        overlay_data_file.seek(overlay_offsets[2][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjui_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x7 * 2))
        bobjui_file.write(mario_pal_2)
        bobjui_file.seek(0x6 * 2, 1)
        bobjui_file.write(koopa_pal_4)
        bobjui_file.write(luigi_pal_2)

        overlay_data_group.seek(overlay_offsets[2][1] + (0x1E * 4)) # hit markers
        overlay_data_file.seek(overlay_offsets[2][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjui_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x10 * 2))
        bobjui_file.write(bytes([mario_pal_2[i] for i in [6, 7, 8, 9]]))
        bobjui_file.write(bytes([mario_pal_2a[i] for i in [8, 9]]))
        bobjui_file.write(bytes([luigi_pal_2[i] for i in [6, 7, 8, 9]]))
        bobjui_file.write(bytes([luigi_pal_2a[i] for i in [8, 9]]))
        bobjui_file.write(bytes([koopa_pal_4[i] for i in [6, 7, 8, 9]]))
        bobjui_file.write(bytes([koopa_pal_4a[i] for i in [0, 1]]))

        overlay_data_group.seek(overlay_offsets[2][1] + (0x1F * 4)) # roulette A button
        overlay_data_file.seek(overlay_offsets[2][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjui_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x7 * 2))
        bobjui_file.write(bytes([mario_pal_2[i] for i in [6, 7, 4, 5, 0, 1]]))

        overlay_data_group.seek(overlay_offsets[2][1] + (0x23 * 4)) # selection buttons
        overlay_data_file.seek(overlay_offsets[2][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjui_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x2 * 2))
        bobjui_file.write(koopa_pal_4)
        bobjui_file.write(mario_pal_2)
        bobjui_file.seek(0xB * 2, 1)
        bobjui_file.write(luigi_pal_2)

        overlay_data_group.seek(overlay_offsets[2][1] + (0x25 * 4)) # badges A/B prompts
        overlay_data_file.seek(overlay_offsets[2][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjui_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x48 * 2))
        bobjui_file.write(bytes([luigi_pal_2[i] for i in [2, 3, 4, 5, 6, 7, 8, 9]]))
        bobjui_file.write(bytes([mario_pal_2[i] for i in [2, 3, 4, 5, 6, 7, 8, 9]]))

        overlay_data_group.seek(overlay_offsets[2][1] + (0x31 * 4)) # post-giant-battle screen
        overlay_data_file.seek(overlay_offsets[2][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjui_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0xCB * 2))
        bobjui_file.write(koopa_pal_4)

        overlay_data_group.seek(overlay_offsets[2][1] + (0x5C * 4)) # B button prompt
        overlay_data_file.seek(overlay_offsets[2][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobjui_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x7 * 2))
        bobjui_file.write(luigi_pal_2)

    overlay_data_group.seek(overlay_offsets[2][1] + (0x3D * 4)) # giant bowser head
    overlay_data_file.seek(overlay_offsets[2][0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

    bobjui_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x16 * 2))
    bobjui_file.write(bytes([koopa_pal_0[i] for i in [16, 17]]))
    bobjui_file.write(koopa_pal_2)
    bobjui_file.write(koopa_pal_3)
    bobjui_file.seek(0x3 * 2, 1)
    bobjui_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 14, 15, 16, 17, 18, 19]]))
    bobjui_file.seek(0x4 * 2, 1)
    bobjui_file.write(bytes([koopa_pal_0A[i] for i in [2, 3, 4, 5]]))

    bobjpc_file.seek(0)
    bobjmon_file.seek(0)
    bobjui_file.seek(0)
    return [bobjpc_file.read(), bobjmon_file.read(), bobjui_file.read()]

def assign_eobj_colors(bros_colors, koopa_colors, default_buttons, eobjsave_file, overlay_data, overlay_offsets): # filedata, palette groups
    mario_pal_0 = struct.pack('<4H', *generate_color_lists(PAL_0_CHOICES[bros_colors[0]]))
    mario_pal_1 = struct.pack('<4H', *generate_color_lists(PAL_1_CHOICES[bros_colors[1]]))
    if bros_colors[4]:
        mario_pal_0, mario_pal_1 = mario_pal_1, mario_pal_0

    luigi_pal_0 = struct.pack('<4H', *generate_color_lists(PAL_0_CHOICES[bros_colors[2]]))
    luigi_pal_1 = struct.pack('<4H', *generate_color_lists(PAL_1_CHOICES[bros_colors[3]]))
    if bros_colors[5]:
        luigi_pal_0, luigi_pal_1 = luigi_pal_1, luigi_pal_0
        
    koopa_pal_0 = struct.pack('<10H', *generate_color_lists(PAL_KP_0_CHOICES[koopa_colors[0]]))
    koopa_pal_0A = struct.pack('<3H', *generate_color_lists(PAL_KP_0A_CHOICES[koopa_colors[0]]))
    koopa_pal_1 = struct.pack('<4H', *generate_color_lists(PAL_KP_1_CHOICES[koopa_colors[1]]))
    koopa_pal_2 = struct.pack('<4H', *generate_color_lists(PAL_KP_2_CHOICES[koopa_colors[2]]))
    koopa_pal_3 = struct.pack('<3H', *generate_color_lists(PAL_KP_3_CHOICES[koopa_colors[3]]))

    mario_pal_2 = struct.pack('<5H', *generate_color_lists(PAL_2_CHOICES[bros_colors[0]]))
    luigi_pal_2 = struct.pack('<5H', *generate_color_lists(PAL_2_CHOICES[bros_colors[2]]))
    koopa_pal_4 = struct.pack('<5H', *generate_color_lists(PAL_KP_4_CHOICES[koopa_colors[0]]))

    mario_pal_2_dark = struct.pack('<5H', *generate_darkened_color_lists(PAL_2_CHOICES[bros_colors[0]]))
    luigi_pal_2_dark = struct.pack('<5H', *generate_darkened_color_lists(PAL_2_CHOICES[bros_colors[2]]))
    koopa_pal_4_dark = struct.pack('<5H', *generate_darkened_color_lists(PAL_KP_4_CHOICES[koopa_colors[0]]))

    eobjsave_file = BytesIO(eobjsave_file)
    overlay_data_file = BytesIO(overlay_data[0])
    overlay_data_group = BytesIO(overlay_data[1])

    overlay_data_group.seek(overlay_offsets[1] + (0xB * 4)) # bros
    overlay_data_file.seek(overlay_offsets[0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

    eobjsave_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x11 * 2))
    eobjsave_file.write(mario_pal_1)
    eobjsave_file.write(mario_pal_0)
    eobjsave_file.seek(0x38 * 2, 1)
    eobjsave_file.write(luigi_pal_1)
    eobjsave_file.write(luigi_pal_0)

    for i in [0x1, 0x5]: # save file char, save file map char
        overlay_data_group.seek(overlay_offsets[1] + (i * 4))
        overlay_data_file.seek(overlay_offsets[0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        eobjsave_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x12 * 2))
        eobjsave_file.write(mario_pal_0)
        eobjsave_file.seek(0xC * 2, 1)
        eobjsave_file.write(luigi_pal_0)
        eobjsave_file.seek(0xC * 2, 1)
        eobjsave_file.write(bytes([koopa_pal_2[i] for i in [0, 1, 4, 5]]))
        eobjsave_file.write(koopa_pal_3)
        eobjsave_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 16, 17]]))
    
    if not default_buttons:
        overlay_data_group.seek(overlay_offsets[1] + (0x14 * 4)) # UI buttons
        overlay_data_file.seek(overlay_offsets[0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        eobjsave_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x20 * 2))
        eobjsave_file.write(mario_pal_2)
        eobjsave_file.write(luigi_pal_2)
        eobjsave_file.seek(0x6 * 2, 1)
        eobjsave_file.write(mario_pal_2_dark)
        eobjsave_file.write(luigi_pal_2_dark)
        eobjsave_file.seek(0x6 * 2, 1)
        eobjsave_file.write(koopa_pal_4)
        eobjsave_file.seek(0xB * 2, 1)
        eobjsave_file.write(koopa_pal_4_dark)

    eobjsave_file.seek(0)
    return [eobjsave_file.read()]

def assign_fobj_colors(bros_colors, koopa_colors, default_buttons, fobj_files, overlay_data, overlay_offsets): # fobj, fobjpc, fobjmon | filedata, palette groups
    mario_pal_0 = struct.pack('<4H', *generate_color_lists(PAL_0_CHOICES[bros_colors[0]]))
    mario_pal_1 = struct.pack('<4H', *generate_color_lists(PAL_1_CHOICES[bros_colors[1]]))
    if bros_colors[4]:
        mario_pal_0, mario_pal_1 = mario_pal_1, mario_pal_0

    luigi_pal_0 = struct.pack('<4H', *generate_color_lists(PAL_0_CHOICES[bros_colors[2]]))
    luigi_pal_1 = struct.pack('<4H', *generate_color_lists(PAL_1_CHOICES[bros_colors[3]]))
    if bros_colors[5]:
        luigi_pal_0, luigi_pal_1 = luigi_pal_1, luigi_pal_0
        
    koopa_pal_0 = struct.pack('<10H', *generate_color_lists(PAL_KP_0_CHOICES[koopa_colors[0]]))
    koopa_pal_0A = struct.pack('<3H', *generate_color_lists(PAL_KP_0A_CHOICES[koopa_colors[0]]))
    koopa_pal_1 = struct.pack('<4H', *generate_color_lists(PAL_KP_1_CHOICES[koopa_colors[1]]))
    koopa_pal_2 = struct.pack('<4H', *generate_color_lists(PAL_KP_2_CHOICES[koopa_colors[2]]))
    koopa_pal_3 = struct.pack('<3H', *generate_color_lists(PAL_KP_3_CHOICES[koopa_colors[3]]))

    mario_pal_2 = struct.pack('<5H', *generate_color_lists(PAL_2_CHOICES[bros_colors[0]]))
    if bros_colors[4]:
        mario_pal_2a = struct.pack('<7H', *generate_color_lists(PAL_2A_CHOICES[bros_colors[0]] + PAL_2C_CHOICES[bros_colors[1]]))
    else:
        mario_pal_2a = struct.pack('<7H', *generate_color_lists(PAL_2A_CHOICES[bros_colors[0]] + PAL_2B_CHOICES[bros_colors[0]]))
    luigi_pal_2 = struct.pack('<5H', *generate_color_lists(PAL_2_CHOICES[bros_colors[2]]))
    if bros_colors[5]:
        luigi_pal_2a = struct.pack('<7H', *generate_color_lists(PAL_2A_CHOICES[bros_colors[2]] + PAL_2C_CHOICES[bros_colors[3]]))
    else:
        luigi_pal_2a = struct.pack('<7H', *generate_color_lists(PAL_2A_CHOICES[bros_colors[2]] + PAL_2B_CHOICES[bros_colors[2]]))
    koopa_pal_4 = struct.pack('<5H', *generate_color_lists(PAL_KP_4_CHOICES[koopa_colors[0]]))

    mario_pal_2_dark = struct.pack('<5H', *generate_darkened_color_lists(PAL_2_CHOICES[bros_colors[0]]))
    luigi_pal_2_dark = struct.pack('<5H', *generate_darkened_color_lists(PAL_2_CHOICES[bros_colors[2]]))
    koopa_pal_4_dark = struct.pack('<5H', *generate_darkened_color_lists(PAL_KP_4_CHOICES[koopa_colors[0]]))

    red_pal_0 = struct.pack('<6H', *generate_color_lists(RED_0))
    red_pal_1 = struct.pack('<3H', *generate_color_lists(RED_1))
    red_pal_2 = struct.pack('<2H', *generate_color_lists(RED_2))

    fobj_file = BytesIO(fobj_files[0])
    fobjpc_file = BytesIO(fobj_files[1])
    fobjmon_file = BytesIO(fobj_files[2])
    overlay_data = BytesIO(overlay_data)

    overlay_data.seek(overlay_offsets[0][1] + (0x35 * 4)) # randoglobin
    overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4)
    fobj_file.write(struct.pack('<16H', *generate_color_lists(RANDOGLOBIN)))

    overlay_data.seek(overlay_offsets[0][1] + (0x1DB * 4)) # map icons
    overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x11 * 2))
    fobj_file.write(mario_pal_1)
    fobj_file.write(mario_pal_0)
    fobj_file.seek(0x38 * 2, 1)
    fobj_file.write(luigi_pal_1)
    fobj_file.write(luigi_pal_0)
    fobj_file.seek(0x29 * 2, 1)
    fobj_file.write(koopa_pal_0)
    fobj_file.write(koopa_pal_2)
    fobj_file.write(koopa_pal_1)
    fobj_file.write(koopa_pal_3)
    fobj_file.seek(0x6 * 2, 1)
    fobj_file.write(koopa_pal_0A)

    overlay_data.seek(overlay_offsets[0][1] + (0x59 * 4)) # rump command boat side view
    overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x2 * 2))
    fobj_file.write(bytes([mario_pal_2a[i] for i in [12, 13]]))
    fobj_file.seek(0x2 * 2, 1)
    fobj_file.write(bytes([mario_pal_0[i] for i in [0, 1, 2, 3, 4, 5]]))
    fobj_file.seek(0xA * 2, 1)
    fobj_file.write(bytes([luigi_pal_2a[i] for i in [12, 13]]))
    fobj_file.seek(0x2 * 2, 1)
    fobj_file.write(bytes([luigi_pal_0[i] for i in [0, 1, 2, 3, 4, 5]]))

    overlay_data.seek(overlay_offsets[0][1] + (0x96 * 4)) # rump command boat top view
    overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x11 * 2))
    fobj_file.write(mario_pal_1)
    fobj_file.write(mario_pal_0)
    fobj_file.seek(0x18 * 2, 1)
    fobj_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7]]))
    fobj_file.seek(0x1C * 2, 1)
    fobj_file.write(luigi_pal_1)
    fobj_file.write(luigi_pal_0)
    fobj_file.seek(0x29 * 2, 1)
    fobj_file.write(bytes([mario_pal_2a[i] for i in [12, 13]]))
    fobj_file.write(bytes([luigi_pal_2a[i] for i in [12, 13]]))

    overlay_data.seek(overlay_offsets[0][1] + (0x110 * 4)) # idk but there's bros sprites here
    overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x11 * 2))
    fobj_file.write(mario_pal_1)
    fobj_file.write(mario_pal_0)
    fobj_file.seek(0x38 * 2, 1)
    fobj_file.write(luigi_pal_1)
    fobj_file.write(luigi_pal_0)

    overlay_data.seek(overlay_offsets[0][1] + (0x12e * 4)) # sockop mario
    overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x18 * 2))
    fobj_file.write(mario_pal_0)

    overlay_data.seek(overlay_offsets[0][1] + (0x192 * 4)) # chest minigame bowser
    overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x2 * 2))
    fobj_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 4, 5, 14, 15]]))
    fobj_file.write(bytes([koopa_pal_1[i] for i in [0, 1, 0, 1, 2, 3, 4, 5, 6, 7]]))
    fobj_file.write(bytes([koopa_pal_0A[i] for i in [0, 1, 2, 3]]))

    overlay_data.seek(overlay_offsets[0][1] + (0x195 * 4)) # save file map char
    overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x2 * 2))
    fobj_file.write(bytes([koopa_pal_2[i] for i in [0, 1, 4, 5]]))
    fobj_file.write(koopa_pal_3)
    fobj_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 16, 17]]))

    overlay_data.seek(overlay_offsets[0][1] + (0x1A6 * 4)) # miracle cure mario hands
    overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x1 * 2))
    fobj_file.write(mario_pal_0)
    fobj_file.seek(0x6 * 2, 1)
    fobj_file.write(bytes([mario_pal_2a[i] for i in [10, 11]]))

    overlay_data.seek(overlay_offsets[0][1] + (0x1D5 * 4)) # chest minigame bowser
    overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x13 * 2))
    fobj_file.write(bytes([koopa_pal_0[i] for i in [10, 11, 12, 13, 14, 15]]))
    fobj_file.write(koopa_pal_1)
    fobj_file.write(bytes([koopa_pal_3[i] for i in [0, 1, 2, 3]]))

    for i in [0x16C, 0x16E, 0x1C5]: # red # 0x174; 0x167, 0x16F
        overlay_data.seek(overlay_offsets[0][1] + (i * 4))
        overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x6 * 2))
        fobj_file.write(red_pal_0)
        fobj_file.seek(0x11 * 2, 1)
        fobj_file.write(red_pal_1)
    
    overlay_data.seek(overlay_offsets[0][1] + (0x191 * 4)) # red
    overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x5 * 2))
    fobj_file.write(bytes([red_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]))
    
    overlay_data.seek(overlay_offsets[0][1] + (0x196 * 4)) # red
    overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x2 * 2))
    fobj_file.write(bytes([red_pal_0[i] for i in [2, 3, 6, 7]]))
    fobj_file.write(bytes([red_pal_2[i] for i in [2, 3]]))
    fobj_file.write(bytes([red_pal_1[i] for i in [2, 3, 4, 5]]))
    
    overlay_data.seek(overlay_offsets[0][1] + (0x1D5 * 4)) # red
    overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x6 * 2))
    fobj_file.write(bytes([red_pal_0[i] for i in [2, 3, 4, 5, 6, 7, 8, 9]]))
    fobj_file.write(bytes([red_pal_2[i] for i in [0, 1]]))

    overlay_data.seek(overlay_offsets[1][1] + (0x0 * 4)) # regular char
    overlay_data.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobjpc_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x11 * 2))
    fobjpc_file.write(mario_pal_1)
    fobjpc_file.write(mario_pal_0)
    fobjpc_file.seek(0x18 * 2, 1)
    fobjpc_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7]]))
    fobjpc_file.seek(0x1C * 2, 1)
    fobjpc_file.write(luigi_pal_1)
    fobjpc_file.write(luigi_pal_0)
    fobjpc_file.seek(0x29 * 2, 1)
    fobjpc_file.write(koopa_pal_0)
    fobjpc_file.write(koopa_pal_2)
    fobjpc_file.write(koopa_pal_1)
    fobjpc_file.write(koopa_pal_3)
    fobjpc_file.seek(0x6 * 2, 1)
    fobjpc_file.write(koopa_pal_0A)

    for i in [0x1, 0x3, 0x7, 0xC, 0x13, 0x14, 0x15]: # floor bowser 1, safe bowser, fire ball bowser, vacuum shroom bowser, floor bowser 2, floor bowser 3, tiny falling bowser
        overlay_data.seek(overlay_offsets[1][1] + (i * 4))
        overlay_data.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        fobjpc_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x82 * 2))
        fobjpc_file.write(koopa_pal_0)
        fobjpc_file.write(koopa_pal_2)
        fobjpc_file.write(koopa_pal_1)
        fobjpc_file.write(koopa_pal_3)
        fobjpc_file.seek(0x6 * 2, 1)
        fobjpc_file.write(koopa_pal_0A)

    overlay_data.seek(overlay_offsets[1][1] + (0x4 * 4)) # sockop bros
    overlay_data.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobjpc_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x11 * 2))
    fobjpc_file.write(mario_pal_1)
    fobjpc_file.write(mario_pal_0)
    fobjpc_file.seek(0x38 * 2, 1)
    fobjpc_file.write(luigi_pal_1)
    fobjpc_file.write(luigi_pal_0)

    overlay_data.seek(overlay_offsets[1][1] + (0xD * 4)) # red face vacuum scene bowser
    overlay_data.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobjpc_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x82 * 2))
    fobjpc_file.write(koopa_pal_0)
    fobjpc_file.write(koopa_pal_2)
    fobjpc_file.write(koopa_pal_1)
    fobjpc_file.write(koopa_pal_3)
    fobjpc_file.seek(0x6 * 2, 1)
    fobjpc_file.write(koopa_pal_0A)
    fobjpc_file.seek(0x12 * 2, 1)
    fobjpc_file.write(bytes([koopa_pal_0[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 16, 17, 18, 19]]))
    fobjpc_file.seek(0x1A * 2, 1)
    fobjpc_file.write(koopa_pal_0)
    fobjpc_file.write(koopa_pal_2)
    fobjpc_file.write(koopa_pal_1)
    fobjpc_file.write(koopa_pal_3)
    fobjpc_file.seek(0x4 * 2, 1)
    fobjpc_file.write(koopa_pal_0A)

    overlay_data.seek(overlay_offsets[1][1] + (0xE * 4)) # ball bowser 2
    overlay_data.seek(overlay_offsets[1][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobjpc_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x82 * 2))
    fobjpc_file.write(koopa_pal_0)
    fobjpc_file.write(koopa_pal_2)
    fobjpc_file.write(koopa_pal_1)
    fobjpc_file.write(koopa_pal_3)
    fobjpc_file.seek(0x5 * 2, 1)
    fobjpc_file.write(koopa_pal_0A)

    overlay_data.seek(overlay_offsets[2][1] + (0xFE * 4)) # mario nose guy
    overlay_data.seek(overlay_offsets[2][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    fobjmon_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x8 * 2))
    fobjmon_file.write(bytes([mario_pal_0[i] for i in [0, 1, 2, 3, 4, 5]]))

    if not default_buttons:
        overlay_data.seek(overlay_offsets[0][1] + (0x1 * 4)) # HUD
        overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x2 * 2))
        fobj_file.write(mario_pal_2)
        fobj_file.seek(0x4 * 2, 1)
        fobj_file.write(koopa_pal_4)
        fobj_file.seek(0x2 * 2, 1)
        fobj_file.write(mario_pal_2_dark)
        fobj_file.seek(0x4 * 2, 1)
        fobj_file.write(koopa_pal_4_dark)
        fobj_file.seek(0x2 * 2, 1)
        fobj_file.write(luigi_pal_2)
        fobj_file.seek(0xB * 2, 1)
        fobj_file.write(luigi_pal_2_dark)

        overlay_data.seek(overlay_offsets[0][1] + (0x2 * 4)) # buttons
        overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x20 * 2))
        fobj_file.write(mario_pal_2)
        fobj_file.write(luigi_pal_2)
        fobj_file.seek(0x6 * 2, 1)
        fobj_file.write(mario_pal_2_dark)
        fobj_file.write(luigi_pal_2_dark)
        fobj_file.seek(0x6 * 2, 1)
        fobj_file.write(koopa_pal_4)
        fobj_file.seek(0xB * 2, 1)
        fobj_file.write(koopa_pal_4_dark)

        overlay_data.seek(overlay_offsets[0][1] + (0x57 * 4)) # rump command orbs
        overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x1 * 2))
        fobj_file.write(bytes([mario_pal_2a[i] for i in [2, 3, 4, 5]]))
        if bros_colors[4]:
            fobj_file.write(bytes([mario_pal_1[i] for i in [0, 1, 4, 5]]))
        else:
            fobj_file.write(bytes([mario_pal_0[i] for i in [0, 1, 4, 5]]))
        fobj_file.write(bytes([luigi_pal_2a[i] for i in [2, 3, 4, 5]]))
        if bros_colors[5]:
            fobj_file.write(bytes([luigi_pal_1[i] for i in [0, 1, 4, 5]]))
        else:
            fobj_file.write(bytes([luigi_pal_0[i] for i in [0, 1, 4, 5]]))

        overlay_data.seek(overlay_offsets[0][1] + (0x58 * 4)) # rump command reticle (might be unused tbh)
        overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x1 * 2))
        fobj_file.write(bytes([mario_pal_2a[i] for i in [4, 5]]))
        if bros_colors[4]:
            fobj_file.write(bytes([mario_pal_1[i] for i in [0, 1]]))
        else:
            fobj_file.write(bytes([mario_pal_0[i] for i in [0, 1]]))
        fobj_file.seek(0x3 * 2, 1)
        fobj_file.write(bytes([luigi_pal_2a[i] for i in [4, 5]]))
        if bros_colors[5]:
            fobj_file.write(bytes([luigi_pal_1[i] for i in [0, 1]]))
        else:
            fobj_file.write(bytes([luigi_pal_0[i] for i in [0, 1]]))

        overlay_data.seek(overlay_offsets[0][1] + (0x87 * 4)) # 99 block
        overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0xB * 2))
        fobj_file.write(bytes([mario_pal_2[i] for i in [6, 7]]))
        fobj_file.write(bytes([luigi_pal_2[i] for i in [6, 7]]))

        overlay_data.seek(overlay_offsets[0][1] + (0x121 * 4)) # memory m
        overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x9 * 2))
        fobj_file.write(bytes([mario_pal_2a[i] for i in [10, 11]]))
        fobj_file.write(bytes([mario_pal_0[i] for i in [0, 1, 2, 3]]))
        fobj_file.write(bytes([mario_pal_1[i] for i in [0, 1, 2, 3]]))

        overlay_data.seek(overlay_offsets[0][1] + (0x122 * 4)) # memory l
        overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x9 * 2))
        fobj_file.write(bytes([luigi_pal_2a[i] for i in [10, 11]]))
        fobj_file.write(bytes([luigi_pal_0[i] for i in [0, 1, 2, 3]]))
        fobj_file.write(bytes([luigi_pal_1[i] for i in [0, 1, 2, 3]]))

        overlay_data.seek(overlay_offsets[0][1] + (0x1B2 * 4)) # B button prompt
        overlay_data.seek(overlay_offsets[0][0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        fobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0xC * 2))
        fobj_file.write(bytes([luigi_pal_2[i] for i in [2, 3, 4, 5, 6, 7, 8, 9]]))

    fobj_file.seek(0)
    fobjpc_file.seek(0)
    fobjmon_file.seek(0)
    return [fobj_file.read(), fobjpc_file.read(), fobjmon_file.read()]

def assign_mobj_colors(bros_colors, koopa_colors, default_buttons, mobj_file, overlay_data, overlay_offsets): # filedata, palette groups
    mario_pal_0 = struct.pack('<4H', *generate_color_lists(PAL_0_CHOICES[bros_colors[0]]))
    mario_pal_1 = struct.pack('<4H', *generate_color_lists(PAL_1_CHOICES[bros_colors[1]]))
    if bros_colors[4]:
        mario_pal_0, mario_pal_1 = mario_pal_1, mario_pal_0

    luigi_pal_0 = struct.pack('<4H', *generate_color_lists(PAL_0_CHOICES[bros_colors[2]]))
    luigi_pal_1 = struct.pack('<4H', *generate_color_lists(PAL_1_CHOICES[bros_colors[3]]))
    if bros_colors[5]:
        luigi_pal_0, luigi_pal_1 = luigi_pal_1, luigi_pal_0
        
    koopa_pal_0 = struct.pack('<10H', *generate_color_lists(PAL_KP_0_CHOICES[koopa_colors[0]]))
    koopa_pal_0A = struct.pack('<3H', *generate_color_lists(PAL_KP_0A_CHOICES[koopa_colors[0]]))
    koopa_pal_1 = struct.pack('<4H', *generate_color_lists(PAL_KP_1_CHOICES[koopa_colors[1]]))
    koopa_pal_2 = struct.pack('<4H', *generate_color_lists(PAL_KP_2_CHOICES[koopa_colors[2]]))
    koopa_pal_3 = struct.pack('<3H', *generate_color_lists(PAL_KP_3_CHOICES[koopa_colors[3]]))

    mario_pal_2 = struct.pack('<5H', *generate_color_lists(PAL_2_CHOICES[bros_colors[0]]))
    if bros_colors[4]:
        mario_pal_2a = struct.pack('<7H', *generate_color_lists(PAL_2A_CHOICES[bros_colors[0]] + PAL_2C_CHOICES[bros_colors[1]]))
    else:
        mario_pal_2a = struct.pack('<7H', *generate_color_lists(PAL_2A_CHOICES[bros_colors[0]] + PAL_2B_CHOICES[bros_colors[0]]))
    luigi_pal_2 = struct.pack('<5H', *generate_color_lists(PAL_2_CHOICES[bros_colors[2]]))
    if bros_colors[5]:
        luigi_pal_2a = struct.pack('<7H', *generate_color_lists(PAL_2A_CHOICES[bros_colors[2]] + PAL_2C_CHOICES[bros_colors[3]]))
    else:
        luigi_pal_2a = struct.pack('<7H', *generate_color_lists(PAL_2A_CHOICES[bros_colors[2]] + PAL_2B_CHOICES[bros_colors[2]]))
    koopa_pal_4 = struct.pack('<5H', *generate_color_lists(PAL_KP_4_CHOICES[koopa_colors[0]]))

    mobj_file = BytesIO(mobj_file)
    overlay_data = BytesIO(overlay_data)

    overlay_data.seek(overlay_offsets[1] + (0x6 * 4)) # badge meter bros faces
    overlay_data.seek(overlay_offsets[0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    mobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x12 * 2))
    mobj_file.write(mario_pal_0)
    mobj_file.seek(0xC * 2, 1)
    mobj_file.write(luigi_pal_0)

    overlay_data.seek(overlay_offsets[1] + (0xC * 4)) # splash screen char
    overlay_data.seek(overlay_offsets[0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    mobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x11 * 2))
    mobj_file.write(mario_pal_1)
    mobj_file.write(mario_pal_0)
    mobj_file.seek(0x38 * 2, 1)
    mobj_file.write(luigi_pal_1)
    mobj_file.write(luigi_pal_0)
    mobj_file.seek(0x29 * 2, 1)
    mobj_file.write(koopa_pal_0)
    mobj_file.write(koopa_pal_2)
    mobj_file.write(koopa_pal_1)
    mobj_file.write(koopa_pal_3)
    mobj_file.seek(0x6 * 2, 1)
    mobj_file.write(koopa_pal_0A)

    overlay_data.seek(overlay_offsets[1] + (0x6D * 4)) # bowser X
    overlay_data.seek(overlay_offsets[0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

    mobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x12 * 2))
    mobj_file.write(koopa_pal_0)
    mobj_file.write(koopa_pal_2)
    mobj_file.write(koopa_pal_1)
    mobj_file.write(koopa_pal_3)
    mobj_file.seek(0x6 * 2, 1)
    mobj_file.write(koopa_pal_0A)

    if not default_buttons:
        for i in [0x11, 0x5B]: # A button prompts
            overlay_data.seek(overlay_offsets[1] + (i * 4))
            overlay_data.seek(overlay_offsets[0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

            mobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0xB * 2))
            mobj_file.write(mario_pal_2)

        overlay_data.seek(overlay_offsets[1] + (0x14 * 4)) # badges A/B prompts
        overlay_data.seek(overlay_offsets[0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        mobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x48 * 2))
        mobj_file.write(bytes([luigi_pal_2[i] for i in [2, 3, 4, 5, 6, 7, 8, 9]]))
        mobj_file.write(bytes([mario_pal_2[i] for i in [2, 3, 4, 5, 6, 7, 8, 9]]))

        overlay_data.seek(overlay_offsets[1] + (0x38 * 4)) # equip icons
        overlay_data.seek(overlay_offsets[0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        mobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x1 * 2))
        mobj_file.write(bytes([koopa_pal_4[i] for i in [6, 7]]))
        mobj_file.write(bytes([luigi_pal_2[i] for i in [6, 7]]))
        mobj_file.write(bytes([mario_pal_2[i] for i in [6, 7]]))

        overlay_data.seek(overlay_offsets[1] + (0x54 * 4)) # button prompts
        overlay_data.seek(overlay_offsets[0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        mobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x2 * 2))
        mobj_file.write(mario_pal_2)
        mobj_file.write(luigi_pal_2)
        mobj_file.seek(0x5 * 2, 1)
        mobj_file.write(koopa_pal_4)

        overlay_data.seek(overlay_offsets[1] + (0x5A * 4)) # small A button prompt
        overlay_data.seek(overlay_offsets[0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        mobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0xC * 2))
        mobj_file.write(bytes([mario_pal_2[i] for i in [2, 3, 4, 5, 6, 7, 8, 9]]))

        overlay_data.seek(overlay_offsets[1] + (0x69 * 4)) # B button prompt
        overlay_data.seek(overlay_offsets[0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        mobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x7 * 2))
        mobj_file.write(luigi_pal_2)

        overlay_data.seek(overlay_offsets[1] + (0x71 * 4)) # memory mx
        overlay_data.seek(overlay_offsets[0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        mobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x9 * 2))
        mobj_file.write(bytes([mario_pal_2a[i] for i in [10, 11]]))
        mobj_file.write(bytes([mario_pal_0[i] for i in [0, 1, 2, 3]]))

        overlay_data.seek(overlay_offsets[1] + (0x72 * 4)) # memory lx
        overlay_data.seek(overlay_offsets[0] + (int.from_bytes(overlay_data.read(2), 'little') * 4) + 4)

        mobj_file.seek(int.from_bytes(overlay_data.read(4), 'little') + 4 + (0x9 * 2))
        mobj_file.write(bytes([luigi_pal_2a[i] for i in [10, 11]]))
        mobj_file.write(bytes([luigi_pal_0[i] for i in [0, 1, 2, 3]]))

    mobj_file.seek(0)
    return [mobj_file.read()]

# ============================================================================================================================

PAL_0_CHOICES = [ # bros shirts
    "#f82808 #d81800 #b80000 #900028", # shirt - mario
    "#10d880 #10a050 #008050 #105040", # shirt - luigi
    "#f8d810 #e0a800 #c08800 #906000", # shirt - wario
    "#8828e0 #6808d0 #5008b0 #380880", # shirt - waluigi
    "#ffffff #e0e8f0 #b8c0d0 #8088a0", # shirt - fire mario
    "#70d0f8 #48b0ff #2090ff #0060f0", # shirt - ice luigi
    "#ff9000 #d86800 #b04800 #883000", # shirt - misc 1
    "#ffe898 #ffc868 #f8a840 #e88028", # shirt - misc 2
]

PAL_1_CHOICES = [ # bros pants
    "#2840f8 #1028d8 #0818a8 #000070", # pants - mario
    "#383080 #282070 #281850 #201038", # pants - luigi
    "#c000d8 #9800b8 #680088 #480068", # pants - wario
    "#303040 #202038 #101020 #080820", # pants - waluigi
    "#b80010 #900018 #680020 #500020", # pants - fire mario
    "#10a050 #007830 #005830 #004028", # pants - ice luigi
    "#f088e0 #e860c8 #e030b0 #c01088", # pants - misc 1
    "#883800 #702800 #501800 #381000", # pants - misc 2
]

PAL_2_CHOICES = [ # bros button
    "#980040 #c00000 #d80000 #f81810 #ff7d45", # button - mario
    "#009020 #00b020 #00d840 #18f868 #a8f878", # button - luigi
    "#986800 #b89000 #d0a800 #f8d800 #f8f080", # button - wario
    "#5000b8 #6000d0 #7008e8 #8820f8 #b048f8", # button - waluigi
    "#606878 #90a0a8 #a8b8c0 #d0e0e8 #ffffff", # button - fire mario
    "#0070e8 #20a0ff #58c0ff #80d0ff #b8e8ff", # button - ice luigi
    "#a63500 #c75d00 #ef7b00 #f79c14 #f7c624", # button - misc 1
    "#c86818 #f0a830 #f8c850 #f8d870 #fff0a8", # button - misc 2
]

PAL_2A_CHOICES = [ # bros extra
    "#ff5820 #ffc8c8 #ff8870 #e81800 #ffc090", # extra - mario
    "#50f8b0 #d0ffe8 #90ffc8 #08c870 #e0ffc0", # extra - luigi
    "#ffe850 #ffffb8 #fff868 #e8c000 #ffffff", # extra - wario
    "#b048f8 #f0b8ff #c068f8 #7818e0 #e090ff", # extra - waluigi
    "#f0f0f8 #b8c0d0 #e0e8f0 #f0f0f8 #e0e8f0", # extra - fire mario
    "#90e8ff #e0ffff #a0f0ff #58c0ff #ffffff", # extra - ice luigi
    "#ffa838 #ffe0a0 #ffc058 #f08000 #ffe890", # extra - misc 1
    "#fff0c0 #ffffd8 #ffffd8 #ffd880 #ffffff", # extra - misc 2
]

PAL_2B_CHOICES = [ # bros extra - primary
    " #ff5820 #ff8870", # extra - mario
    " #50f8b0 #90ffc8", # extra - luigi
    " #ffe850 #fff868", # extra - wario
    " #b048f8 #c068f8", # extra - waluigi
    " #f0f0f8 #e0e8f0", # extra - fire mario
    " #90e8ff #a0f0ff", # extra - ice luigi
    " #ffa838 #ffc058", # extra - misc 1
    " #fff0c0 #ffffd8", # extra - misc 2
]

PAL_2C_CHOICES = [ # bros extra - alt
    " #5870ff #8090ff", # extra - mario
    " #5048a8 #5860c8", # extra - luigi
    " #e840e8 #f070e8", # extra - wario
    " #484850 #606068", # extra - waluigi
    " #e02828 #e85050", # extra - fire mario
    " #20c860 #40f078", # extra - ice luigi
    " #ffa8e8 #ffc8ff", # extra - misc 1
    " #b85810 #d07030", # extra - misc 2
]


PAL_KP_0_CHOICES = [ # koopa skin
    "#f7e7ae #e7be6d #cf963c #b67d24 #ffe70c #f7b60c #d78e00 #9e6514 #754500 #452400", # skin - bowser
    "#90a0c0 #6878a8 #506088 #405080 #6078c0 #4060b8 #305098 #284070 #202858 #101830", # skin - dark bowser
    "#e0f098 #b0d868 #80c848 #508040 #50d868 #38a048 #208028 #186018 #104818 #083010", # skin - king koopa
    "#ffffff #f0e0d0 #d0c0a8 #b0a890 #ffffff #f0e0d0 #d0c0a8 #a89868 #686040 #404028", # skin - dry bowser
    "#f8b0b0 #f890a0 #f87090 #a82858 #f83870 #e02870 #c02070 #802058 #601840 #380828", # skin - midbus
    "#ffc0a8 #ff9880 #ff4848 #e02030 #f86050 #f01810 #c00818 #900820 #601020 #400818", # skin - king dedede
    "#ffe0d0 #f8c098 #c88870 #a06850 #ff9820 #e07000 #c85800 #884000 #682808 #401810", # skin - meowser
    "#f0c0e8 #e098d0 #d078b0 #a05088 #e888d8 #e060c0 #d038a8 #b01880 #780850 #480828", # skin - birdo
]

PAL_KP_0A_CHOICES = [ # koopa shell orange bits
    "#e7751c #c75524 #ae3c14", # shell rings - bowser
    "#484848 #303030 #202020", # shell rings - dark bowser
    "#ffe848 #e8b810 #a06000", # shell rings - king koopa
    "#f03000 #c02800 #801800", # shell rings - dry bowser
    "#484848 #303030 #202020", # shell rings - midbus
    "#f8f8f8 #c8d0d0 #90a0a8", # shell rings - king dedede
    "#f82808 #c81000 #900028", # shell rings - meowser
    "#f82808 #c81000 #900028", # shell rings - birdo
]

PAL_KP_1_CHOICES = [ # koopa shell
    "#1c9645 #0c8634 #0c6d24 #1c5534", # shell - bowser
    "#4060b8 #305098 #284070 #183050", # shell - dark bowser
    "#404050 #303040 #202038 #181830", # shell - dry bowser
    "#e0d000 #c8a000 #b08000 #905808", # shell - midbus
    "#f82820 #d00010 #a80018 #800020", # shell - king dedede
    "#40d8ff #00a8f8 #0080c8 #105088", # shell - misc 1
    "#9800d8 #7000b8 #580890 #380878", # shell - misc 2
    "#ff7810 #d86000 #b04800 #903000", # shell - misc 3
]

PAL_KP_2_CHOICES = [ # koopa face
    "#4dae00 #3c8e00 #1c6d00 #004500", # face - bowser
    "#4060b8 #305098 #284070 #183050", # face - dark bowser
    "#f0e0d0 #d0c0a8 #a89868 #686040", # face - dry bowser
    "#f83870 #e02870 #c02070 #802058", # face - midbus
    "#e888d8 #e060c0 #d038a8 #b01880", # face - birdo
    "#ff9820 #e07000 #c85800 #884000", # face - meowser
    "#f8e008 #f0b008 #d08800 #986010", # face - misc 1
    "#404050 #303040 #202038 #181830", # face - misc 2
]

PAL_KP_3_CHOICES = [ # koopa hair
    "#f73400 #c72c00 #861c00", # hair - bowser
    "#484848 #303030 #202020", # hair - dark bowser
    "#ffe848 #e8b810 #a06000", # hair - king koopa
    "#ff8020 #d85800 #883000", # hair - super mario world
    "#f8f8f8 #c8d0d0 #607880", # hair - meowser
    "#58d0ff #08a8ff #0070c0", # hair - misc 1
    "#2838c0 #183090 #102058", # hair - misc 2
    "#f84078 #e00058 #900040", # hair - misc 3
]

PAL_KP_4_CHOICES = [ # koopa button
    "#a63500 #c75d00 #ef7b00 #f79c14 #f7c624", # button - bowser
    "#203078 #384890 #4860b0 #6878d0 #7898e0", # button - dark bowser
    "#009020 #00b020 #00d840 #18f868 #a8f878", # button - king koopa
    "#606878 #90a0a8 #a8b8c0 #d0e0e8 #ffffff", # button - dry bowser
    "#881860 #b82078 #d82078 #f04898 #f880b8", # button - midbus
    "#980040 #c00000 #d80000 #f81810 #ff7d45", # button - king dedede
    "#701800 #c03000 #f05000 #ff7020 #ff9848", # button - meowser
    "#881878 #c020a0 #d840b8 #e070c0 #f8a0e0", # button - misc
]

PAL_KP_4A_CHOICES = [ # koopa extra
    "#ffe890", # extra - bowser
    "#b8d8ff", # extra - dark bowser
    "#e0ffc0", # extra - king koopa
    "#ffffff", # extra - dry bowser
    "#ffc0d0", # extra - midbus
    "#ffc090", # extra - king dedede
    "#ffd0b0", # extra - meowser
    "#ffd8ff", # extra - misc
]


PAL_TEXT_CHOICES = [ # text highlight colors | PAL_TEXT_CHOICES[player character][target color][textbox type]
    [    # bros colors | field light, field dark
        ["#f80000 #f8d0d0", "#f80030 #682050"],
        ["#00c000 #e0f8d8", "#00e800 #286048"],
        ["#ffc400 #fff7ba", "#ffe818 #454233"],
        ["#bb30f8 #eae0f0", "#c23eff #482c6e"],
        ["#3058f8 #e0f0f0", "#20b8f8 #305088"],
        ["#6dddff #d8f8f1", "#6debff #355a71"],
        ["#f87800 #f8e0c0", "#f89838 #684858"],
        ["#c6a75f #f3e3be", "#f8d870 #5d5143"],
    ], [ # bows colors | field light, field dark
        ["#f87800 #f8e0c0", "#f89838 #684858"],
        ["#49609e #dae4ff", "#4060b8 #344269"],
        ["#00c000 #e0f8d8", "#00e800 #286048"],
        ["#3058f8 #e0f0f0", "#20b8f8 #305088"],
        ["#f04898 #f7d0da", "#ff60aa #6a3b71"],
        ["#f80000 #f8d0d0", "#f80030 #682050"],
        ["#b2560f #f3d6b0", "#e76014 #653939"],
        ["#ff92e5 #ffdee4", "#ff7ee0 #7c3c86"],
    ]
]


PRESETS = [
    [0, 7, 4, 5, False, False],
    [0, 3, 1, 3, False, False],
    [5, 6, 1, 2, True , False],
    [2, 4, 2, 5, False, False],
    [4, 4, 5, 5, False, False],
    [0, 3, 1, 6, True , True ],
    [2, 2, 3, 3, False, False],
    [6, 7, 7, 7, True , True ],
]

PRESETS_KP = [
    [1, 0, 1, 2],
    [6, 0, 0, 3],
    [1, 1, 1, 1],
    [4, 3, 3, 1],
    [3, 2, 2, 0],
    [6, 2, 5, 4],
    [2, 0, 0, 2],
    [7, 4, 4, 0],
]


RANDOGLOBIN = "#ff92e5 #ffffff #ffc9d3 #f8ca11 #fffd74 #084b39 #de0023 #ff5b60 #00754a #098640 #029d57 #14bb59 #41ed6e #a6fbb7 #4d4d4d #000000"
RED_0 = "#ff6058 #ff3028 #d81018 #901818 #700810 #380800"
RED_1 = "#00ffff #00ffff #00ffff"
RED_2 = "#007f7f #7fffff"

def generate_color_lists(pal_list):
    bgr555 = []
    for string in pal_list.split():
        wow = bytearray(bytes.fromhex(string.lstrip("#")))
        bgr555_entry = 0
        for i in range(3):
            bgr555_entry += (wow[i] >> 3) << (i * 5)
        bgr555.append(bgr555_entry)
    return bgr555

def generate_darkened_color_lists(pal_list):
    bgr555 = []
    for string in pal_list.split():
        wow = bytearray(bytes.fromhex(string.lstrip("#")))
        bgr555_entry = 0
        for i in range(3):
            wow[i] >>= 1
            bgr555_entry += (wow[i] >> 3) << (i * 5)
        bgr555.append(bgr555_entry)
    return bgr555

###############################################################################################################################################
###############################################################################################################################################
###############################################################################################################################################

class PaletteTab(QtWidgets.QWidget):
    def __init__(self, overlay_BObj_offsets, overlay_BObj, BObj_file, overlay_FObj_offsets, overlay_FObj, FObj_file, textbox_pal, textbox_graph, font_file, latin_font_file, help_text):
        super().__init__()

        self.set_constants()

        main_layout = QtWidgets.QVBoxLayout(self)

        self.overlay_BObj_offsets = overlay_BObj_offsets
        self.overlay_BObj = overlay_BObj
        self.BObj_file = BObj_file

        self.overlay_FObj_offsets = overlay_FObj_offsets
        self.overlay_FObj = overlay_FObj
        self.FObj_file = FObj_file

        self.textbox_pal = textbox_pal
        self.textbox_graph = textbox_graph
        self.font_file = font_file
        self.latin_font_file = latin_font_file
        self.help_text = help_text

        self.default_buttons = QtWidgets.QCheckBox(self.tr("UI Elements and Targeted Attacks are Default Colors"))
        main_layout.addWidget(self.default_buttons, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.default_buttons.setIcon(create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x4, 2, 0))

        self.swap_colors_allowed = QtWidgets.QCheckBox(self.tr('Allow the "Swap Colors" Option to be Enabled with Random Colors'))
        main_layout.addWidget(self.swap_colors_allowed, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        tex = create_MObj_sprite(overlay_FObj_offsets, overlay_FObj, FObj_file, 0x28, 0, 0)
        tex = tex.toImage()
        for i in range(tex.width() * tex.height()):
            x, y = i % tex.width(), i // tex.width()
            replace = { # make the pants red
                "#3c75ff": "#f82808",
                "#1445df": "#d81800",  
                "#0c2cae": "#a80000",
                "#000075": "#600000",
            }
            if tex.pixelColor(x, y).name() in replace.keys():
                tex.setPixelColor(x, y, replace[tex.pixelColor(x, y).name()])
        self.swap_colors_allowed.setIcon(QtGui.QPixmap.fromImage(tex))

        self.use_custom_colors = QtWidgets.QCheckBox(self.tr("Use Personalized Colors"))
        self.use_custom_colors.checkStateChanged.connect(self.enable_custom_colors)
        main_layout.addWidget(self.use_custom_colors, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.use_custom_colors.setIcon(QtGui.QIcon(str(FILES_DIR / 'pal_alt.png')))

        # ------------------------------------------
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line)
        # ------------------------------------------

        self.presets = QtWidgets.QWidget()
        presets_layout = QtWidgets.QGridLayout(self.presets)
        presets_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.presets)
        presets_layout.addWidget(QtWidgets.QLabel(self.tr("Presets")), 0, 0, 1, 2)

        for i in range(len(PRESETS)):
            button = QtWidgets.QPushButton(self.PAL_PRESET_NAMES[i])
            button.clicked.connect(partial(self.change_bros_preset, i))

            presets_layout.addWidget(button, (i // 2) + 1, i % 2)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.VLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        presets_layout.addWidget(line, 1, 2, 4, 1)
        
        for i in range(len(PRESETS_KP)):
            button = QtWidgets.QPushButton(self.PAL_PRESET_KP_NAMES[i])
            button.clicked.connect(partial(self.change_koopa_preset, i))
            presets_layout.addWidget(button, (i // 2) + 1, (i % 2) + 3)

        # ------------------------------------------
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line)
        # ------------------------------------------

        self.bros = QtWidgets.QWidget()
        bros_layout = QtWidgets.QGridLayout(self.bros)
        bros_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.bros)

        self.mario_image = QtWidgets.QLabel()
        bros_layout.addWidget(self.mario_image, 0, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.luigi_image = QtWidgets.QLabel()
        bros_layout.addWidget(self.luigi_image, 0, 0, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.koopa_image = QtWidgets.QLabel()
        bros_layout.addWidget(self.koopa_image, 0, 2, 1, 2, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.mario_color_0 = QtWidgets.QComboBox()
        self.mario_color_0.addItems(self.PAL_0_NAMES)
        string = QtWidgets.QLabel(self.tr("Primary Color") + ":")
        string.setBuddy(self.mario_color_0)
        bros_layout.addWidget(string, 1, 1)
        bros_layout.addWidget(self.mario_color_0, 2, 1)
        self.mario_color_1 = QtWidgets.QComboBox()
        self.mario_color_1.addItems(self.PAL_1_NAMES)
        string = QtWidgets.QLabel(self.tr("Secondary Color") + ":")
        string.setBuddy(self.mario_color_1)
        bros_layout.addWidget(string, 3, 1)
        bros_layout.addWidget(self.mario_color_1, 4, 1)
        self.mario_color_inv = QtWidgets.QCheckBox(self.tr("Swap Colors"))
        bros_layout.addWidget(self.mario_color_inv, 5, 1)

        self.luigi_color_0 = QtWidgets.QComboBox()
        self.luigi_color_0.addItems(self.PAL_0_NAMES)
        string = QtWidgets.QLabel(self.tr("Primary Color") + ":")
        string.setBuddy(self.luigi_color_0)
        bros_layout.addWidget(string, 1, 0)
        bros_layout.addWidget(self.luigi_color_0, 2, 0)
        self.luigi_color_1 = QtWidgets.QComboBox()
        self.luigi_color_1.addItems(self.PAL_1_NAMES)
        string = QtWidgets.QLabel(self.tr("Secondary Color") + ":")
        string.setBuddy(self.luigi_color_1)
        bros_layout.addWidget(string, 3, 0)
        bros_layout.addWidget(self.luigi_color_1, 4, 0)
        self.luigi_color_inv = QtWidgets.QCheckBox(self.tr("Swap Colors"))
        bros_layout.addWidget(self.luigi_color_inv, 5, 0)

        # these are just so these entries show up in Linguist
        _true_text = self.tr("True")
        _false_text = self.tr("False")

        string = QtWidgets.QLabel(self.tr("Skin") + ":")
        bros_layout.addWidget(string, 1, 2)
        self.koopa_color_0 = QtWidgets.QComboBox()
        self.koopa_color_0.addItems(self.PAL_KP_0_NAMES)
        string.setBuddy(self.koopa_color_0)

        string = QtWidgets.QLabel(self.tr("Shell") + ":")
        bros_layout.addWidget(string, 1, 3)
        self.koopa_color_1 = QtWidgets.QComboBox()
        self.koopa_color_1.addItems(self.PAL_KP_1_NAMES)
        string.setBuddy(self.koopa_color_1)

        string = QtWidgets.QLabel(self.tr("Face") + ":")
        bros_layout.addWidget(string, 3, 2)
        self.koopa_color_2 = QtWidgets.QComboBox()
        self.koopa_color_2.addItems(self.PAL_KP_2_NAMES)
        string.setBuddy(self.koopa_color_2)

        string = QtWidgets.QLabel(self.tr("Hair") + ":")
        bros_layout.addWidget(string, 3, 3)
        self.koopa_color_3 = QtWidgets.QComboBox()
        self.koopa_color_3.addItems(self.PAL_KP_3_NAMES)
        string.setBuddy(self.koopa_color_3)

        bros_layout.addWidget(self.koopa_color_0, 2, 2)
        bros_layout.addWidget(self.koopa_color_1, 2, 3)
        bros_layout.addWidget(self.koopa_color_2, 4, 2)
        bros_layout.addWidget(self.koopa_color_3, 4, 3)

        for i in range(len(PAL_0_CHOICES)):
            gradient = QtGui.QLinearGradient(QtCore.QPointF(0, (i + 0.33) * 24), QtCore.QPointF(0, (i + 1) * 24))

            gradient.setColorAt(0, QtGui.QColor(PAL_0_CHOICES[i].split()[0]))
            gradient.setColorAt(1, QtGui.QColor(PAL_0_CHOICES[i].split()[1]))
            self.mario_color_0.setItemData(i, QtGui.QBrush(gradient), QtCore.Qt.BackgroundRole)

            gradient.setColorAt(0, QtGui.QColor(PAL_0_CHOICES[i].split()[0]))
            gradient.setColorAt(1, QtGui.QColor(PAL_0_CHOICES[i].split()[1]))
            self.luigi_color_0.setItemData(i, QtGui.QBrush(gradient), QtCore.Qt.BackgroundRole)

        for i in range(len(PAL_1_CHOICES)):
            gradient = QtGui.QLinearGradient(QtCore.QPointF(0, (i + 0.33) * 24), QtCore.QPointF(0, (i + 1) * 24))

            gradient.setColorAt(0, QtGui.QColor(PAL_1_CHOICES[i].split()[0]))
            gradient.setColorAt(1, QtGui.QColor(PAL_1_CHOICES[i].split()[1]))
            self.mario_color_1.setItemData(i, QtGui.QBrush(gradient), QtCore.Qt.BackgroundRole)

            gradient.setColorAt(0, QtGui.QColor(PAL_1_CHOICES[i].split()[0]))
            gradient.setColorAt(1, QtGui.QColor(PAL_1_CHOICES[i].split()[1]))
            self.luigi_color_1.setItemData(i, QtGui.QBrush(gradient), QtCore.Qt.BackgroundRole)
        
        for i in range(len(PAL_KP_0_CHOICES)):
            gradient = QtGui.QLinearGradient(QtCore.QPointF(0, (i + 0.33) * 24), QtCore.QPointF(0, (i + 1) * 24))
            gradient.setColorAt(0, QtGui.QColor(PAL_KP_0_CHOICES[i].split()[4]))
            gradient.setColorAt(1, QtGui.QColor(PAL_KP_0_CHOICES[i].split()[5]))
            self.koopa_color_0.setItemData(i, QtGui.QBrush(gradient), QtCore.Qt.BackgroundRole)

        for i in range(len(PAL_KP_1_CHOICES)):
            gradient = QtGui.QLinearGradient(QtCore.QPointF(0, (i + 0.33) * 24), QtCore.QPointF(0, (i + 1) * 24))
            gradient.setColorAt(0, QtGui.QColor(PAL_KP_1_CHOICES[i].split()[0]))
            gradient.setColorAt(1, QtGui.QColor(PAL_KP_1_CHOICES[i].split()[1]))
            self.koopa_color_1.setItemData(i, QtGui.QBrush(gradient), QtCore.Qt.BackgroundRole)

        for i in range(len(PAL_KP_2_CHOICES)):
            gradient = QtGui.QLinearGradient(QtCore.QPointF(0, (i + 0.33) * 24), QtCore.QPointF(0, (i + 1) * 24))
            gradient.setColorAt(0, QtGui.QColor(PAL_KP_2_CHOICES[i].split()[0]))
            gradient.setColorAt(1, QtGui.QColor(PAL_KP_2_CHOICES[i].split()[1]))
            self.koopa_color_2.setItemData(i, QtGui.QBrush(gradient), QtCore.Qt.BackgroundRole)

        for i in range(len(PAL_KP_3_CHOICES)):
            gradient = QtGui.QLinearGradient(QtCore.QPointF(0, (i + 0.33) * 24), QtCore.QPointF(0, (i + 1) * 24))
            gradient.setColorAt(0, QtGui.QColor(PAL_KP_3_CHOICES[i].split()[0]))
            gradient.setColorAt(1, QtGui.QColor(PAL_KP_3_CHOICES[i].split()[1]))
            self.koopa_color_3.setItemData(i, QtGui.QBrush(gradient), QtCore.Qt.BackgroundRole)

        self.textbox_image = QtWidgets.QLabel()
        bros_layout.addWidget(self.textbox_image, 6, 0, 1, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.textbox_image_other = QtWidgets.QLabel()
        bros_layout.addWidget(self.textbox_image_other, 7, 0, 1, 3, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.ml_action_icon_image = QtWidgets.QLabel()
        bros_layout.addWidget(self.ml_action_icon_image, 6, 3, 1, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)
        self.kp_action_icon_image = QtWidgets.QLabel()
        bros_layout.addWidget(self.kp_action_icon_image, 7, 3, 1, 1, alignment = QtCore.Qt.AlignmentFlag.AlignCenter)

        self.mario_color_0.currentIndexChanged.connect(self.update_bros_widget_colors)
        self.mario_color_1.currentIndexChanged.connect(self.update_bros_widget_colors)
        self.luigi_color_0.currentIndexChanged.connect(self.update_bros_widget_colors)
        self.luigi_color_1.currentIndexChanged.connect(self.update_bros_widget_colors)
        self.mario_color_inv.checkStateChanged.connect(self.update_bros_images)
        self.luigi_color_inv.checkStateChanged.connect(self.update_bros_images)

        self.mario_color_0.setCurrentIndex(0)
        self.mario_color_1.setCurrentIndex(0)
        self.luigi_color_0.setCurrentIndex(1)
        self.luigi_color_1.setCurrentIndex(1)
        self.mario_color_inv.setChecked(False)
        self.luigi_color_inv.setChecked(False)

        self.koopa_color_0.currentIndexChanged.connect(self.update_bros_widget_colors)
        self.koopa_color_1.currentIndexChanged.connect(self.update_bros_widget_colors)
        self.koopa_color_2.currentIndexChanged.connect(self.update_bros_widget_colors)
        self.koopa_color_3.currentIndexChanged.connect(self.update_bros_widget_colors)

        self.koopa_color_0.setCurrentIndex(0)
        self.koopa_color_1.setCurrentIndex(0)
        self.koopa_color_2.setCurrentIndex(0)
        self.koopa_color_3.setCurrentIndex(0)

        self.default_buttons.checkStateChanged.connect(self.update_bros_images)

        self.swap_colors_allowed.setChecked(False)
        self.use_custom_colors.setChecked(True)
        self.use_custom_colors.setChecked(False)
        self.default_buttons.setChecked(True)
        self.default_buttons.setChecked(False)

        # ------------------------------------------
        padding = QtWidgets.QWidget()
        main_layout.addWidget(padding)
        padding.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.update_bros_images()
    
    def enable_custom_colors(self, check_state):
        self.presets.setEnabled(check_state == QtCore.Qt.Checked)
        self.bros.setEnabled(check_state == QtCore.Qt.Checked)
    
    def change_bros_preset(self, preset):
        self.mario_color_0.blockSignals(True)
        self.mario_color_1.blockSignals(True)
        self.luigi_color_0.blockSignals(True)
        self.luigi_color_1.blockSignals(True)
        self.mario_color_inv.blockSignals(True)
        self.luigi_color_inv.blockSignals(True)

        self.mario_color_0.setCurrentIndex(PRESETS[preset][0])
        self.mario_color_1.setCurrentIndex(PRESETS[preset][1])
        self.luigi_color_0.setCurrentIndex(PRESETS[preset][2])
        self.luigi_color_1.setCurrentIndex(PRESETS[preset][3])
        self.mario_color_inv.setChecked(PRESETS[preset][4])
        self.luigi_color_inv.setChecked(PRESETS[preset][5])

        self.mario_color_0.blockSignals(False)
        self.mario_color_1.blockSignals(False)
        self.luigi_color_0.blockSignals(False)
        self.luigi_color_1.blockSignals(False)
        self.mario_color_inv.blockSignals(False)
        self.luigi_color_inv.blockSignals(False)

        self.update_bros_widget_colors()
    
    def change_koopa_preset(self, preset):
        self.koopa_color_0.blockSignals(True)
        self.koopa_color_1.blockSignals(True)
        self.koopa_color_2.blockSignals(True)
        self.koopa_color_3.blockSignals(True)

        self.koopa_color_0.setCurrentIndex(PRESETS_KP[preset][0])
        self.koopa_color_1.setCurrentIndex(PRESETS_KP[preset][1])
        self.koopa_color_2.setCurrentIndex(PRESETS_KP[preset][2])
        self.koopa_color_3.setCurrentIndex(PRESETS_KP[preset][3])

        self.koopa_color_0.blockSignals(False)
        self.koopa_color_1.blockSignals(False)
        self.koopa_color_2.blockSignals(False)
        self.koopa_color_3.blockSignals(False)

        self.update_bros_widget_colors()
    
    def update_bros_widget_colors(self):
        self.mario_color_0.setStyleSheet(f"color: #000000; background-color: {PAL_0_CHOICES[self.mario_color_0.currentIndex()].split()[1]}; selection-background-color: #50FFFFFF; ")
        self.mario_color_1.setStyleSheet(f"color: #000000; background-color: {PAL_1_CHOICES[self.mario_color_1.currentIndex()].split()[1]}; selection-background-color: #50FFFFFF; ")
        self.luigi_color_0.setStyleSheet(f"color: #000000; background-color: {PAL_0_CHOICES[self.luigi_color_0.currentIndex()].split()[1]}; selection-background-color: #50FFFFFF; ")
        self.luigi_color_1.setStyleSheet(f"color: #000000; background-color: {PAL_1_CHOICES[self.luigi_color_1.currentIndex()].split()[1]}; selection-background-color: #50FFFFFF; ")

        self.koopa_color_0.setStyleSheet(f"color: #000000; background-color: {PAL_KP_0_CHOICES[self.koopa_color_0.currentIndex()].split()[5]}; selection-background-color: #50FFFFFF; ")
        self.koopa_color_1.setStyleSheet(f"color: #000000; background-color: {PAL_KP_1_CHOICES[self.koopa_color_1.currentIndex()].split()[1]}; selection-background-color: #50FFFFFF; ")
        self.koopa_color_2.setStyleSheet(f"color: #000000; background-color: {PAL_KP_2_CHOICES[self.koopa_color_2.currentIndex()].split()[1]}; selection-background-color: #50FFFFFF; ")
        self.koopa_color_3.setStyleSheet(f"color: #000000; background-color: {PAL_KP_3_CHOICES[self.koopa_color_3.currentIndex()].split()[1]}; selection-background-color: #50FFFFFF; ")

        self.update_bros_images()
    
    def update_bros_images(self):
        mario_pal_0 = struct.pack('<4H', *generate_color_lists(PAL_0_CHOICES[self.mario_color_0.currentIndex()]))
        mario_pal_1 = struct.pack('<4H', *generate_color_lists(PAL_1_CHOICES[self.mario_color_1.currentIndex()]))
        if self.mario_color_inv.isChecked():
            mario_pal_0, mario_pal_1 = mario_pal_1, mario_pal_0

        luigi_pal_0 = struct.pack('<4H', *generate_color_lists(PAL_0_CHOICES[self.luigi_color_0.currentIndex()]))
        luigi_pal_1 = struct.pack('<4H', *generate_color_lists(PAL_1_CHOICES[self.luigi_color_1.currentIndex()]))
        if self.luigi_color_inv.isChecked():
            luigi_pal_0, luigi_pal_1 = luigi_pal_1, luigi_pal_0
        
        koopa_pal_0 = struct.pack('<10H', *generate_color_lists(PAL_KP_0_CHOICES[self.koopa_color_0.currentIndex()]))
        koopa_pal_0A = struct.pack('<3H', *generate_color_lists(PAL_KP_0A_CHOICES[self.koopa_color_0.currentIndex()]))
        koopa_pal_1 = struct.pack('<4H', *generate_color_lists(PAL_KP_1_CHOICES[self.koopa_color_1.currentIndex()]))
        koopa_pal_2 = struct.pack('<4H', *generate_color_lists(PAL_KP_2_CHOICES[self.koopa_color_2.currentIndex()]))
        koopa_pal_3 = struct.pack('<3H', *generate_color_lists(PAL_KP_3_CHOICES[self.koopa_color_3.currentIndex()]))

        if not self.default_buttons.isChecked():
            text_pal_0a = struct.pack('<2H', *generate_color_lists(PAL_TEXT_CHOICES[0][self.mario_color_0.currentIndex()][0]))
            text_pal_0b = struct.pack('<2H', *generate_color_lists(PAL_TEXT_CHOICES[0][self.mario_color_0.currentIndex()][1]))
            text_pal_1a = struct.pack('<2H', *generate_color_lists(PAL_TEXT_CHOICES[0][self.luigi_color_0.currentIndex()][0]))
            text_pal_1b = struct.pack('<2H', *generate_color_lists(PAL_TEXT_CHOICES[0][self.luigi_color_0.currentIndex()][1]))
            text_pal_2a = struct.pack('<2H', *generate_color_lists(PAL_TEXT_CHOICES[1][self.koopa_color_0.currentIndex()][0]))
            text_pal_2b = struct.pack('<2H', *generate_color_lists(PAL_TEXT_CHOICES[1][self.koopa_color_0.currentIndex()][1]))
            
            mario_pal_2 = struct.pack('<5H', *generate_color_lists(PAL_2_CHOICES[self.mario_color_0.currentIndex()]))
            luigi_pal_2 = struct.pack('<5H', *generate_color_lists(PAL_2_CHOICES[self.luigi_color_0.currentIndex()]))
            koopa_pal_4 = struct.pack('<5H', *generate_color_lists(PAL_KP_4_CHOICES[self.koopa_color_0.currentIndex()]))

        bobj_file = BytesIO(self.BObj_file)
        overlay_data_group = BytesIO(self.overlay_BObj[1])
        overlay_data_file = BytesIO(self.overlay_BObj[0])

        overlay_data_group.seek(self.overlay_BObj_offsets[2] + (0x5 * 4)) # bros
        overlay_data_file.seek(self.overlay_BObj_offsets[0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

        bobj_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x11 * 2))
        bobj_file.write(mario_pal_1)
        bobj_file.write(mario_pal_0)
        bobj_file.seek(0x38 * 2, 1)
        bobj_file.write(luigi_pal_1)
        bobj_file.write(luigi_pal_0)
        bobj_file.seek(0x29 * 2, 1)
        bobj_file.write(koopa_pal_0)
        bobj_file.write(koopa_pal_2)
        bobj_file.write(koopa_pal_1)
        bobj_file.write(koopa_pal_3)
        bobj_file.seek(0x6 * 2, 1)
        bobj_file.write(koopa_pal_0A)

        bobj_file.seek(0)
        BObj_file = bobj_file.read()

        textbox_pal = self.textbox_pal
        FObj_file = self.FObj_file
        if not self.default_buttons.isChecked():
            textbox_pal_a = BytesIO(textbox_pal[0])
            textbox_pal_a.seek(8 * 2)
            textbox_pal_a.write(text_pal_1a)
            textbox_pal_a.write(text_pal_2a)
            textbox_pal_a.seek(2 * 2, 1)
            textbox_pal_a.write(text_pal_0a)

            textbox_pal_b = BytesIO(textbox_pal[1])
            textbox_pal_b.seek(8 * 2)
            textbox_pal_b.write(text_pal_1b)
            textbox_pal_b.write(text_pal_2b)
            textbox_pal_b.seek(2 * 2, 1)
            textbox_pal_b.write(text_pal_0b)

            textbox_pal_a.seek(0)
            textbox_pal_b.seek(0)
            textbox_pal = (textbox_pal_a.read(), textbox_pal_b.read())

            fobj_file = BytesIO(self.FObj_file)
            overlay_data_group = BytesIO(self.overlay_FObj)
            overlay_data_file = BytesIO(self.overlay_FObj)

            overlay_data_group.seek(self.overlay_FObj_offsets[2] + (0x1 * 4)) # bros
            overlay_data_file.seek(self.overlay_FObj_offsets[0] + (int.from_bytes(overlay_data_group.read(2), 'little') * 4) + 4)

            fobj_file.seek(int.from_bytes(overlay_data_file.read(4), 'little') + 4 + (0x2 * 2))
            fobj_file.write(mario_pal_2)
            fobj_file.seek(0x4 * 2, 1)
            fobj_file.write(koopa_pal_4)
            fobj_file.seek(0x12 * 2, 1)
            fobj_file.write(luigi_pal_2)

            fobj_file.seek(0)
            FObj_file = fobj_file.read()

        tex = create_BObj_sprite(
            self.overlay_BObj_offsets,
            *self.overlay_BObj,
            BObj_file,
            0x45, 4, 13)
        tex = tex.transformed(QtGui.QTransform().scale(2, 2))
        self.mario_image.setPixmap(tex)

        tex = create_BObj_sprite(
            self.overlay_BObj_offsets,
            *self.overlay_BObj,
            BObj_file,
            0x46, 4, 12)
        tex = tex.transformed(QtGui.QTransform().scale(2, 2))
        self.luigi_image.setPixmap(tex)

        tex = create_BObj_sprite(
            self.overlay_BObj_offsets,
            *self.overlay_BObj,
            BObj_file,
            0x52, 6, 18)
        tex = tex.transformed(QtGui.QTransform().scale(-2, 2))
        self.koopa_image.setPixmap(tex)

        tex = create_MObj_sprite(
            self.overlay_FObj_offsets,
            self.overlay_FObj,
            FObj_file,
            0x2E, 2, 0)
        tex = tex.transformed(QtGui.QTransform().scale(2, 2))
        self.ml_action_icon_image.setPixmap(tex)

        tex = create_MObj_sprite(
            self.overlay_FObj_offsets,
            self.overlay_FObj,
            FObj_file,
            0x1E0, 2, 0)
        tex = tex.transformed(QtGui.QTransform().scale(2, 2))
        self.kp_action_icon_image.setPixmap(tex)

        tex = create_textbox(
            textbox_pal,
            self.textbox_graph,
            0, 23, 3,
            self.latin_font_file,
            b"\xFF\x27\xFF\xE8\x1E\x1F\xFF\xEF \xFF\x2D\xFF\xE8\x1C\x1D\xFF\xEF \xFF\x29\xFF\xE8\x05\x06\xFF\xEF \xFF\x29\xFF\xE8\x07\x08\xFF\xEF \xFF\x2B\xFF\xE8\x18\x19\xFF\xEF \xFF\x2B\xFF\xE8\x1A\x1B\xFF\xEF")
        tex = tex.transformed(QtGui.QTransform().scale(2, 2))
        self.textbox_image.setPixmap(tex)

        M_name = b"\xFF\x2D" + self.help_text[0x13].encode('cp1252') + b"\xFF\x20, "
        L_name = b"\xFF\x27" + self.help_text[0x14].encode('cp1252') + b"\xFF\x20, "
        K_name = b"& \xFF\x29" + self.help_text[0x15].encode('cp1252') + b"\xFF\x20."
        text_base = L_name + M_name + K_name
        tex = create_textbox(
            textbox_pal,
            self.textbox_graph,
            1, 23, 3,
            self.font_file,
            text_base)
        tex = tex.transformed(QtGui.QTransform().scale(2, 2))
        self.textbox_image_other.setPixmap(tex)

    def set_constants(self):
        self.PAL_0_NAMES = [ # bros shirts
            self.tr("Red"),
            self.tr("Green"),
            self.tr("Yellow"),
            self.tr("Purple"),
            self.tr("White"),
            self.tr("Light Blue"),
            self.tr("Orange"),
            self.tr("Tan"),
        ]

        self.PAL_1_NAMES = [ # bros pants
            self.tr("Blue"),
            self.tr("Dark Blue"),
            self.tr("Purple"),
            self.tr("Black"),
            self.tr("Dark Red"),
            self.tr("Dark Green"),
            self.tr("Pink"),
            self.tr("Brown"),
        ]

        self.PAL_KP_0_NAMES = [ # koopa skin
            self.tr("Yellow"),
            self.tr("Blue"),
            self.tr("Green"),
            self.tr("White"),
            self.tr("Magenta"),
            self.tr("Red"),
            self.tr("Orange"),
            self.tr("Pink"),
        ]

        self.PAL_KP_1_NAMES = [ # koopa shell
            self.tr("Green"),
            self.tr("Blue"),
            self.tr("Black"),
            self.tr("Yellow"),
            self.tr("Red"),
            self.tr("Light Blue"),
            self.tr("Purple"),
            self.tr("Orange"),
        ]

        self.PAL_KP_2_NAMES = [ # koopa face
            self.tr("Green"),
            self.tr("Blue"),
            self.tr("White"),
            self.tr("Magenta"),
            self.tr("Pink"),
            self.tr("Orange"),
            self.tr("Yellow"),
            self.tr("Black"),
        ]

        self.PAL_KP_3_NAMES = [ # koopa hair
            self.tr("Red"),
            self.tr("Black"),
            self.tr("Yellow"),
            self.tr("Orange"),
            self.tr("White"),
            self.tr("Light Blue"),
            self.tr("Blue"),
            self.tr("Magenta"),
        ]

        self.PAL_PRESET_NAMES = [
            self.tr("Super Mario Bros"),
            self.tr("Super Mario Bros 3"),
            self.tr("Super Mario World"),
            self.tr("Super Mario Maker"),
            self.tr("Elemental Bros"),
            self.tr("Wonder Bros"),
            self.tr("Wario Bros"),
            self.tr("Chocolate Bros"),
        ]

        self.PAL_PRESET_KP_NAMES = [
            self.tr("Super Mario Bros"),
            self.tr("Super Mario World"),
            self.tr("Dark Bowser"),
            self.tr("Midbus"),
            self.tr("Dry Bowser"),
            self.tr("Meowser"),
            self.tr("King Koopa"),
            self.tr("Birdo"),
        ]