import struct
from io import BytesIO
from math import ceil

import mnlscript.bis.text
mnlscript.bis.text.TT = None

from mnlscript.bis import add_coins, add_items

class Treasure:
    def __init__(self):
        # i realized after making this dict that this actually won't work for what i'm trying to do
        # however, it's still a good resource for future reference so i'm keeping it for now
        self.requirements = {
            "ml_has_access":       True,
            "ml_req_hammer":       False,
            "ml_req_mini_mario":   False,
            "ml_req_spin_jump":    False,
            "ml_req_drill":        False,
            "ml_req_blue_shell":   False,
            "ml_req_balloon":      False,
            "ml_req_snack_basket": False,

            "kp_has_access":       True,
            "kp_req_flame":        False,
            "kp_req_slide_punch":  False,
            "kp_req_body_slam":    False,
            "kp_req_spike_ball":   False,
            "kp_req_vacuum":       False,

            "req_stingler":        False,
            "req_banzai_bill":     False,
            "req_key_r":           False,
            "req_key_g":           False,
            "req_key_b":           False,
            "req_cure_r":          False,
            "req_cure_y":          False,
            "req_cure_g":          False,
        }

    def from_treasure_info(self, data):
        bitfield, self.item = struct.unpack('<HH', data)
        self.is_last_entry_in_room = bitfield & 0b1
        self.treasure_type = (bitfield >> 1) & 0b1111
        self.max_hits = (bitfield >> 5) & 0b11111
        self.quantity = (bitfield >> 10) & 0b11111
    def from_item_id(self, data):
        self.item = data
        self.is_last_entry_in_room = 0
        self.treasure_type = 0
        self.max_hits = 1
        self.quantity = 0
    def from_script_command(self, data):
        self.is_last_entry_in_room = 0
        self.treasure_type = 0
        if data.command_id == 0x0041:
            coin_amt = data.arguments[0]
            if coin_amt == 5: # spawn one 5 coin
                self.quantity = 1
                self.max_hits = 1
            if coin_amt == 50: # spawn one 50 coin
                self.quantity = 3
                self.max_hits = 1
            elif coin_amt < 10: # spawn several 1 coins
                self.quantity = 0
                self.max_hits = coin_amt
            elif coin_amt < 100: # spawn several 10 coins
                self.quantity = 2
                self.max_hits = coin_amt // 10
            else: # spawn several 100 coins
                self.quantity = 4
                self.max_hits = coin_amt // 100
            self.item = 0xFFFF - self.quantity
            # if ([1, 5, 10, 50, 100][self.quantity] * self.max_hits) != coin_amt or self.max_hits > 31:
            #     print("COIN ROUTINE FAILED")
        elif data.command_id == 0x0044:
            self.item = data.arguments[0]
            self.quantity = data.arguments[1] - 1
            self.max_hits = 1
    
    def to_treasure_info(self):
        bitfield = self.is_last_entry_in_room + (self.treasure_type << 1) + (self.max_hits << 5) + (self.quantity << 10)
        return struct.pack('<HH', bitfield, self.item)
    def to_item_id(self):
        return self.item
    def to_script_command(self):
        if self.item > 0xEFFF:
            return add_coins([1, 5, 10, 50, 100][self.quantity] * self.max_hits)
        else:
            return add_items(self.item, (self.quantity + 1) * self.max_hits)

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

class EnemyData: # i stole this from dataglobin (me)
    def __init__(self, input_data):
        data = struct.unpack('<2HIxBh3HI6H2x', input_data)

        self.name      = data[0x0]
        self.script    = data[0x1]
        self.obj_id    = data[0x2]

        self.level     = data[0x3] # cap at 99
        self.HP        = data[0x4] # seemingly no cap
        self.POW       = data[0x5] # cap at 999
        self.DEF       = data[0x6] # cap at 999
        self.SPEED     = data[0x7] # cap at 999

        self.is_spiked = data[0x8] & 0x00000001 != 0
        self.is_flying = data[0x8] & 0x00000004 != 0

        self.fire_damage  = (data[0x8] >>  3) & 0b11
        self.burn_chance  = (data[0x8] >>  8) & 0b11
        self.dizzy_chance = (data[0x8] >> 10) & 0b11
        self.stat_chance  = (data[0x8] >> 12) & 0b11
        self.insta_chance = (data[0x8] >> 14) & 0b11

        self.unk0      = data[0x8] & 0x00010000 != 0
        self.unk1      = data[0x8] & 0x00020000 != 0

        self.EXP       = data[0x9] # cap at 9999
        self.coins     = data[0xA] # cap at 9999
        self.item_1    = data[0xB]
        self.rare_1    = data[0xC]
        self.item_2    = data[0xD]
        self.rare_2    = data[0xE]
    
    def pack(self):
        bitfield = sum([
            int(self.is_spiked) << 0,
            int(self.is_flying) << 2,
            self.fire_damage  <<  3,
            self.burn_chance  <<  8,
            self.dizzy_chance << 10,
            self.stat_chance  << 12,
            self.insta_chance << 14,
            int(self.unk0) << 16,
            int(self.unk1) << 17,
        ])

        return struct.pack(
            '<2HIxBh3HI6H2x',
            self.name,
            self.script,
            self.obj_id,
            self.level,
            self.HP,
            self.POW,
            self.DEF,
            self.SPEED,
            bitfield,
            self.EXP,
            self.coins,
            self.item_1,
            self.rare_1,
            self.item_2,
            self.rare_2,
        )