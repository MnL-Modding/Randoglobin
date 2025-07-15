import struct
from io import BytesIO
from math import ceil

class Treasure:
    def from_treasure_info(self, data):
        bitfield, self.item = struct.unpack('<HH', data)
        self.treasure_type = bitfield & 0b111111
        self.max_hits = (bitfield >> 6) & 0b1111
        self.quantity = (bitfield >> 10) & 0b11111
    def from_item_id(self, data):
        self.item = data
        self.treasure_type = 0
        self.max_hits = 0
        self.quantity = 0
    
    def to_treasure_info(self):
        bitfield = self.treasure_type + (self.quantity << 10)
        return struct.pack('<HH', bitfield, self.item)
    def to_item_id(self):
        return self.item

class MapMetadata:
    def __init__(self, data):
        self.base = list(struct.unpack('<III', data))
        self.select_map = (self.base[0] >> 2) & 0x3FF
        self.music = self.base[2] >> 12
    def pack(self):
        self.base[0] = (self.base[0] & 0xFFFFF003) + (self.select_map << 2)
        self.base[2] = (self.base[2] & 0x00000FFF) + (self.music << 12)
        return struct.pack('<III', *self.base)

class ShopList:
    def __init__(self, _data):
        data = BytesIO(_data)
        table_length = int.from_bytes(data.read(4), 'little') - 4

        shop_offset_list = struct.unpack(f'<{table_length // 4}I', data.read(table_length))
        shop_list = []
        for i in range(len(shop_offset_list) - 1):
            shop_list.append(data.read(shop_offset_list[i + 1] - shop_offset_list[i]))
        
        self.shops = []
        for _shop in shop_list:
            shop = BytesIO(_shop)
            shop_states = [struct.unpack(f'<2H', shop.read(4)) for i in range(8)]
            item_lists = [struct.unpack(f'<{shop_data[1]}H', shop.read(shop_data[1] * 2)) for shop_data in shop_states]
            full_shop = []
            index = 7
            for item_list in reversed(item_lists):
                if index == 7:
                    for item in item_list:
                        full_shop.append([item, 7])
                
                for i, item in enumerate(full_shop):
                    if item[0] in item_list:
                        full_shop[i][1] = index
                index -= 1
            
            self.shops.append(full_shop)
    
    def pack(self):
        shop_list = BytesIO()
        shop_offsets = []
        for shop in self.shops:
            shop_offsets.append(shop_list.tell())
            shop_header = BytesIO()
            shop_items = BytesIO()
            anchor = 0
            for i in range(8):
                amt = 0
                for item in shop:
                    if i >= item[1]:
                        shop_items.write(item[0].to_bytes(2, 'little'))
                        amt += 1
                shop_header.write(anchor.to_bytes(2, 'little'))
                shop_header.write(amt.to_bytes(2, 'little'))
                anchor += amt
            shop_header.seek(0)
            shop_list.write(shop_header.read())
            shop_items.seek(0)
            shop_list.write(shop_items.read().ljust(ceil(shop_items.getbuffer().nbytes / 0x4) * 0x4, b'\0'))
        shop_offsets.append(shop_list.tell())
        shop_list.seek(0)

        offsets = [(len(shop_offsets) + 1) * 4]
        offsets.extend([offset + ((len(shop_offsets) + 1) * 4) for offset in shop_offsets])

        return_file = struct.pack(f'<{len(shop_offsets) + 1}I', *offsets) + shop_list.read()
        return(bytearray(return_file.ljust(ceil(len(return_file) / 0x200) * 0x200, b'\0')))
    
    def print_data(self):
        for shop in self.shops:
            for item in shop:
                print(f"{hex(item[0])}, {item[1]}")
            print()

class LevelUpStats:
    def __init__(self, _data):
        data = struct.unpack(f'<3I', _data)
        
        self.HP     = (data[0] >>  0) & 0x3FF
        self.SP     = (data[0] >> 10) & 0x3FF
        self.POW    = (data[0] >> 20) & 0x3FF
        self.DEF    = (data[1] >>  0) & 0x3FF
        self.SPEED  = (data[1] >> 10) & 0x3FF
        self.STACHE = (data[1] >> 20) & 0x3FF
        self.EXP = data[2]