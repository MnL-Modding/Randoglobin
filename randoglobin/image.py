import struct
from io import BytesIO
from math import prod

from PySide6 import QtCore, QtGui, QtWidgets
from PIL import Image, ImageOps
from PIL.ImageQt import ImageQt
from mnllib.bis import decompress

SIZING_TABLE = [[(8, 8), (16, 16), (32, 32), (64, 64)], [(16, 8), (32, 8), (32, 16), (64, 32)], [(8, 16), (8, 32), (16, 32), (32, 64)]]

def create_MObj_sprite(table_offsets, overlay, XObj_file, group_num, anim_num, frame_num, lang = 0):
    overlay = BytesIO(overlay)
    XObj_file = BytesIO(XObj_file)

    # ==================================================================
    # start reading the data

    overlay.seek(table_offsets[1] + (group_num * 10)) # get sprite group data
    anim_id, graph_id, pal_gid, use_lang = struct.unpack('<3H2xH', overlay.read(10))

    if use_lang & 1 != 0: # check if current sprite group uses languages
        overlay.seek(table_offsets[1] + ((group_num + lang) * 10)) # get sprite group data again
        anim_id, graph_id, pal_gid = struct.unpack('<3H', overlay.read(6))
    
    overlay.seek(table_offsets[2] + (pal_gid * 4))
    pal_id = int.from_bytes(overlay.read(2), "little")

    overlay.seek(table_offsets[0] + (anim_id * 4) + 4)
    XObj_file.seek(int.from_bytes(overlay.read(4), "little"))
    animation_file = BytesIO(decompress(XObj_file))

    overlay.seek(table_offsets[0] + (graph_id * 4) + 4)
    XObj_file.seek(int.from_bytes(overlay.read(4), "little"))
    graphics_buffer = BytesIO(decompress(XObj_file))

    overlay.seek(table_offsets[0] + (pal_id * 4) + 4)
    XObj_file.seek(int.from_bytes(overlay.read(4), "little"))
    palette_file_size = int.from_bytes(XObj_file.read(4), "little")
    palette_file = define_palette(struct.unpack(f'<{palette_file_size // 2}H', XObj_file.read(palette_file_size)))

    # ==================================================================
    # start interpreting the data

    _settings_byte, anims_table, parts_table, tex_shift, graph_offset_table = struct.unpack('<2xBx2I9xB2xI', animation_file.read(0x1C))
    sprite_mode = _settings_byte & 3
    swizzle_flag = (_settings_byte >> 3) & 1 == 0

    img = Image.new("RGBA", (256, 256))

    animation_file.seek(anims_table + (anim_num * 8))
    frame_offset = int.from_bytes(animation_file.read(2), "little")

    animation_file.seek(frame_offset + (frame_num * 8))
    part_list_offset, part_amt = struct.unpack('<HxB', animation_file.read(4))

    # ==================================================================
    # start assembling the sprite

    if part_amt == 0 and len(anim_list) == 1:
        return QtGui.QPixmap(QtGui.QImage(ImageQt(Image.new("RGBA", (16, 16)))))

    for i in reversed(range(part_amt)):
        animation_file.seek(parts_table + ((part_list_offset + i) * 8))
        oam_settings, part_x, part_y = struct.unpack('<I2h', animation_file.read(8))

        part_xy = SIZING_TABLE[(oam_settings >> 6) & 0b11][(oam_settings >> 10) & 0b11]

        pal_shift = (oam_settings >> 14) & 0b1111

        animation_file.seek(graph_offset_table + ((part_list_offset + i) * 2))
        graphics_buffer.seek((int.from_bytes(animation_file.read(2), "little") << tex_shift) + 4)
        buffer_in = graphics_buffer.read(prod(part_xy))

        img_part = create_sprite_part(
            buffer_in,
            palette_file,
            part_xy,
            sprite_mode,
            pal_shift,
            swizzle_flag
        )

        x_flip = (oam_settings >> 8) & 1 != 0
        y_flip = (oam_settings >> 9) & 1 != 0

        if x_flip:
            img_part = ImageOps.mirror(img_part)
        if y_flip:
            img_part = ImageOps.flip(img_part)

        img.paste(img_part, (part_x - (part_xy[0] // 2) + 128, part_y - (part_xy[1] // 2) + 128), img_part)
    
    img = img.crop(img.getbbox())

    return QtGui.QPixmap(QtGui.QImage(ImageQt(img)))

def create_BObj_sprite(table_offsets, file_data_overlay, group_data_overlay, XObj_file, group_num, anim_num, frame_num):
    file_data_overlay = BytesIO(file_data_overlay)
    group_data_overlay = BytesIO(group_data_overlay)
    XObj_file = BytesIO(XObj_file)

    # ==================================================================
    # start reading the data

    group_data_overlay.seek(table_offsets[1] + (group_num * 24)) # get sprite group data
    anim_id, graph_id, pal_gid = struct.unpack('<3H', group_data_overlay.read(6))
    
    group_data_overlay.seek(table_offsets[2] + (pal_gid * 4))
    pal_id = int.from_bytes(group_data_overlay.read(2), "little")

    file_data_overlay.seek(table_offsets[0] + (anim_id * 4) + 4)
    XObj_file.seek(int.from_bytes(file_data_overlay.read(4), "little"))
    animation_file = BytesIO(decompress(XObj_file))

    file_data_overlay.seek(table_offsets[0] + (graph_id * 4) + 4)
    XObj_file.seek(int.from_bytes(file_data_overlay.read(4), "little"))
    graphics_buffer = BytesIO(decompress(XObj_file))

    file_data_overlay.seek(table_offsets[0] + (pal_id * 4) + 4)
    XObj_file.seek(int.from_bytes(file_data_overlay.read(4), "little"))
    palette_file_size = int.from_bytes(XObj_file.read(4), "little")
    palette_file = define_palette(struct.unpack(f'<{palette_file_size // 2}H', XObj_file.read(palette_file_size)))

    # ==================================================================
    # start interpreting the data

    _settings_byte, anims_table, parts_table, tex_shift, graph_offset_table = struct.unpack('<2xBx2I9xB2xI', animation_file.read(0x1C))
    sprite_mode = _settings_byte & 3
    swizzle_flag = (_settings_byte >> 3) & 1 == 0

    img = Image.new("RGBA", (256, 256))

    animation_file.seek(anims_table + (anim_num * 8))
    frame_offset = int.from_bytes(animation_file.read(2), "little")

    animation_file.seek(frame_offset + (frame_num * 8))
    part_list_offset, part_amt = struct.unpack('<HxB', animation_file.read(4))

    # ==================================================================
    # start assembling the sprite

    for i in reversed(range(part_amt)):
        animation_file.seek(parts_table + ((part_list_offset + i) * 8))
        oam_settings, part_x, part_y = struct.unpack('<I2h', animation_file.read(8))

        part_xy = SIZING_TABLE[(oam_settings >> 6) & 0b11][(oam_settings >> 10) & 0b11]

        pal_shift = (oam_settings >> 14) & 0b1111

        animation_file.seek(graph_offset_table + ((part_list_offset + i) * 2))
        graphics_buffer.seek((int.from_bytes(animation_file.read(2), "little") << tex_shift) + 4)
        buffer_in = graphics_buffer.read(prod(part_xy))

        img_part = create_sprite_part(
            buffer_in,
            palette_file,
            part_xy,
            sprite_mode,
            pal_shift,
            swizzle_flag
        )

        x_flip = (oam_settings >> 8) & 1 != 0
        y_flip = (oam_settings >> 9) & 1 != 0

        if x_flip:
            img_part = ImageOps.mirror(img_part)
        if y_flip:
            img_part = ImageOps.flip(img_part)

        img.paste(img_part, (part_x - (part_xy[0] // 2) + 128, part_y - (part_xy[1] // 2) + 128), img_part)
    
    img = img.crop(img.getbbox())

    return QtGui.QPixmap(QtGui.QImage(ImageQt(img)))

# mode 0 is 2D, mode 1 is 3D
def define_palette(current_pal, mode = 1):
    out_pal = []
    for color_raw in current_pal:
        return_color = []
        for i in range(3):
            x = color_raw >> (i * 5) & 0x1F               # 15 bit color
            x = (x << 1) + min(x, mode)                   # 18 bit color
            return_color.append((x << 2) | (x >> 4))      # 24 bit color
        out_pal.append(return_color)
    return out_pal

def create_sprite_part(buffer_in, current_pal, part_xy, sprite_mode, pal_shift, swizzle, transparent_flag = True):
    pal_shift *= 16
    if (swizzle):
        part_size = 8 * 8
        tiles = (part_xy[0] * part_xy[1]) // 64
        tile_x, tile_y = 8, 8
    else:
        part_size = part_xy[0] * part_xy[1]
        tile_x, tile_y = part_xy[0], part_xy[1]
        tiles = 1
    img_out = Image.new("RGBA", (part_xy[0], part_xy[1]))
    for t in range(tiles):
        buffer_out = bytearray()
        match (sprite_mode):
            case 0:
                # 8bpp bitmap
                for i in range(part_size):
                    current_pixel = buffer_in[(t * 64) + i]
                    if current_pixel + pal_shift < len(current_pal):
                        buffer_out.extend(current_pal[current_pixel + pal_shift])
                    else:
                        buffer_out.extend([0, 0, 0])
                    # transparency
                    if transparent_flag:
                        if (current_pixel == 0): buffer_out.append(0x00)
                        else: buffer_out.append(0xFF)
                    else:
                        buffer_out.append(0xFF)
            case 1:
                # AI35
                for i in range(part_size):
                    current_pixel = buffer_in[(t * 64) + i] & 0b11111
                    if current_pixel + pal_shift < len(current_pal):
                        buffer_out.extend(current_pal[current_pixel + pal_shift])
                    else:
                        buffer_out.extend([0, 0, 0])
                    # transparency
                    if transparent_flag:
                        alpha = ceil(0xFF * ((buffer_in[(t * 64) + i] >> 5) / 7))
                        buffer_out.append(alpha)
                    else:
                        buffer_out.append(0xFF)
            case 2:
                # AI53
                for i in range(part_size):
                    current_pixel = buffer_in[(t * 64) + i] & 0b111
                    if current_pixel + pal_shift < len(current_pal):
                        buffer_out.extend(current_pal[current_pixel + pal_shift])
                    else:
                        buffer_out.extend([0, 0, 0])
                    # transparency
                    if transparent_flag:
                        alpha = buffer_in[(t * 64) + i] >> 3
                        alpha = (alpha << 3) | (alpha >> 2)
                        buffer_out.append(alpha)
                    else:
                        buffer_out.append(0xFF)
            case 3:
                # 4bpp bitmap
                for i in range(part_size):
                    current_pixel = (buffer_in[((t * 64) + i) // 2] >> ((i % 2) * 4)) & 0b1111
                    if current_pixel + pal_shift < len(current_pal):
                        buffer_out.extend(current_pal[current_pixel + pal_shift])
                    else:
                        buffer_out.extend([0, 0, 0])
                    # transparency
                    if transparent_flag:
                        if (current_pixel == 0): buffer_out.append(0x00)
                        else: buffer_out.append(0xFF)
                    else:
                        buffer_out.append(0xFF)
        # swizzle (if swizzle is disabled, x and y offset will always just be 0 and the image will display normally)
        x = (t % (part_xy[0] // tile_x)) * 8
        y = (t // (part_xy[0] // tile_x)) * 8
        img_out.paste(Image.frombytes("RGBA", (tile_x, tile_y), buffer_out), (x, y))
    return img_out

def create_textbox(_palette, _box_graph, _box_type, _width, _height, _font_file, input_string):
    width = max(_width - 3, 0)
    height = max(_height - 3, 0)
    box_graph = BytesIO(_box_graph)
    img = Image.new("RGBA", ((width + 4) * 8, (height + 4) * 8))

    box_design = _box_type
    palette = define_palette(struct.unpack(f'<16H', _palette[_box_type]))

    match box_design:
        case 0:
            corners = [
                [0x07, 0x08, 0x06, 0x01],
                [0x09, 0x0A, 0x01, 0x0B],
                [0x0C, 0x01, 0x0D, 0x0E],
                [0x01, 0x11, 0x0F, 0x10],
            ]
        case 1:
            corners = [
                [[0x44, 0x45, 0x50, 0x01], [0x44, 0x45, 0x5A, 0x3A], [0x48, 0x49, 0x5C, 0x3B], [0x4C, 0x4D, 0x5E, 0x3C]][max(-height + 3, 0)],
                [[0x46, 0x47, 0x01, 0x55], [0x46, 0x47, 0x3A, 0x5B], [0x4A, 0x4B, 0x3B, 0x5D], [0x4E, 0x4F, 0x3C, 0x5F]][max(-height + 3, 0)],
                [0x54, 0x3D, 0x60, 0x61],
                [0x3D, 0x59, 0x62, 0x63],
            ]

    current_corner = 0
    for full_corner in corners:
        corner_buffer = bytearray()
        for sub_corner in full_corner:
            box_graph.seek(sub_corner * 0x20)
            corner_buffer += box_graph.read(32)
        match current_corner:
            case 0: img.paste(create_sprite_part(corner_buffer, palette, (16, 16), 3, 0, True), (             0,               0))
            case 1: img.paste(create_sprite_part(corner_buffer, palette, (16, 16), 3, 0, True), (img.width - 16,               0))
            case 2: img.paste(create_sprite_part(corner_buffer, palette, (16, 16), 3, 0, True), (             0, img.height - 16))
            case 3: img.paste(create_sprite_part(corner_buffer, palette, (16, 16), 3, 0, True), (img.width - 16, img.height - 16))
        current_corner += 1
    
    for i in range(width):
        box_graph.seek([2, [0x3E, 0x3F, 0x40][max(-height + 2, 0)]][box_design] * 0x20)
        img.paste(create_sprite_part(box_graph.read(32), palette, (8, 8), 3, 0, True), (16 + (i * 8), 0))
        box_graph.seek([1, [1, 0x3A, 0x3B, 0x3C][max(-height + 3, 0)]][box_design] * 0x20)
        img.paste(create_sprite_part(box_graph.read(32), palette, (8, 8), 3, 0, True), (16 + (i * 8), 8))
        box_graph.seek([1, 0x3D][box_design] * 0x20)
        img.paste(create_sprite_part(box_graph.read(32), palette, (8, 8), 3, 0, True), (16 + (i * 8), img.height - 16))
        box_graph.seek([3, 0x41][box_design] * 0x20)
        img.paste(create_sprite_part(box_graph.read(32), palette, (8, 8), 3, 0, True), (16 + (i * 8), img.height - 8))
    
    for i in range(height):
        box_graph.seek([4, [0x42, 0x51, 0x52, 0x53][max(i - (height - 4), 0)]][box_design] * 0x20)
        img.paste(create_sprite_part(box_graph.read(32), palette, (8, 8), 3, 0, True), (             0, 16 + (i * 8)))
        box_graph.seek([1, [1, 0x3A, 0x3B, 0x3C][max(i - (height - 4), 0)]][box_design] * 0x20)
        img.paste(create_sprite_part(box_graph.read(32), palette, (8, 8), 3, 0, True), (             8, 16 + (i * 8)))
        box_graph.seek([1, [1, 0x3A, 0x3B, 0x3C][max(i - (height - 4), 0)]][box_design] * 0x20)
        img.paste(create_sprite_part(box_graph.read(32), palette, (8, 8), 3, 0, True), (img.width - 16, 16 + (i * 8)))
        box_graph.seek([5, [0x43, 0x56, 0x57, 0x58][max(i - (height - 4), 0)]][box_design] * 0x20)
        img.paste(create_sprite_part(box_graph.read(32), palette, (8, 8), 3, 0, True), (img.width -  8, 16 + (i * 8)))

        for j in range(width):
            box_graph.seek([1, [1, 0x3A, 0x3B, 0x3C][max(i - (height - 4), 0)]][box_design] * 0x20)
            img.paste(create_sprite_part(box_graph.read(32), palette, (8, 8), 3, 0, True), (16 + (j * 8), 16 + (i * 8)))
    
    text_origin = (12, 8)
    text_x, text_y = text_origin
    text_spacing = 1
    read_flag = False
    color = 0
    text_img = Image.new("RGBA", ((width + 4) * 8, (height + 4) * 8))
    for char in input_string:
        if read_flag:
            if char & 0xF0 == 0x20:
                color = char & 0xF
            elif char == 0xE8:
                text_spacing = 0
            elif char == 0xEF:
                text_spacing = 1
            read_flag = False
            continue

        if char == 0x20:
            text_x += 8
            continue
        if char == 0xFF:
            read_flag = True
            continue
        
        current_char = interpret_character(BytesIO(_font_file), palette, char, color)
        text_img.paste(current_char[0], (text_x, text_y), current_char[0])
        text_x += current_char[1] + text_spacing

    img_test = text_img.getbbox()
    if img_test != None:
        text_img = text_img.crop((img_test[0], 0, img_test[2], img.height))
        img.paste(text_img, ((img.width // 2) - (text_img.width // 2), 0), text_img)
    return QtGui.QPixmap(QtGui.QImage(ImageQt(img)))

def interpret_character(font_file, palette, char_id, color):
    char_map_size, char_map_offset, glyph_table_offset = struct.unpack('<III', font_file.read(0xC))

    font_file.seek(char_map_offset + (char_id * 2))

    char = int.from_bytes(font_file.read(2), 'little') // 0x100

    font_file.seek(glyph_table_offset)
    _glyph_size, unk0, char_width_table_length = struct.unpack('<BHB', font_file.read(0x4))
    glyph_height = (_glyph_size & 0b1111) * 4
    glyph_width = (_glyph_size >> 4) * 4
    
    font_file.seek(char // 2, 1)
    char_width = 1 + ((int.from_bytes(font_file.read(1)) >> (4 * ((char) % 2))) & 0b1111)

    glyph = Image.new("RGBA", (glyph_width, glyph_height))
    glyph_size = (glyph_height * glyph_width) // 4
    font_file.seek(glyph_table_offset + 4 + (char_width_table_length * 4) + (char * ((glyph_height * glyph_width) // 4)))

    for x in range(0, glyph_width, 8):
        buffer_len = min(4, (glyph_width - x) // 2)
        for y in range(0, glyph_height, 4):
            alpha_buffer = font_file.read(buffer_len)
            color_buffer = font_file.read(buffer_len)

            glyph_section = Image.new("RGBA", (8, 4))
            for z in range(buffer_len * 8):
                pixel_alpha = (alpha_buffer[z // 8] >> (z % 8)) & 1
                pixel_color = (color_buffer[z // 8] >> (z % 8)) & 1
                if pixel_alpha == 0: continue
                
                glyph_section.putpixel((z // 4, z % 4), tuple(palette[(1 + color + pixel_color) % 16]))
            glyph.paste(glyph_section, (x, y), glyph_section)

    return [glyph, char_width]