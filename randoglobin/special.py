from io import BytesIO
import struct
import random

import mnllib


# =========================================================================================================================
# special attacks

BRAWL_ATTACK_ACTOR_OBJ = [
    0x0E5, # goombas
    0x13C, # koopas
    0x13D, # shy guys
    0x219, # bob-bombs
    0x27C, # magikoopas
    0x0B7, # broggy
]

def randomize_special_attacks(seed, bros_attack_string, fevent_manager, overlay_data, bros_attacks_table_offset, bros_attacks_item_table_offset, arm9_data, spoiler_file, string_lists, parent):
    random.seed(seed)
    # TO DO: remove tutorials for special attacks
    # TO DO: figure out why these are borked
    overlay_data = BytesIO(overlay_data)
    overlay_data.seek(bros_attacks_table_offset)
    special_attack_data = [struct.unpack('<H2x3H4xH2x', overlay_data.read(18)) for i in range(10)] # [area name, area name, pieces variable, attack variable, attack item ID]
    arm9_data = BytesIO(arm9_data)

    special_attack_names = []
    expensive_attacks = []
    bros_attack_list = []
    bros_pieces_list = []
    for i in range(10):
        arm9_data.seek(bros_attacks_item_table_offset + ((special_attack_data[i][4] - 0x1000) * 24))
        special_attack_names.append(int.from_bytes(arm9_data.read(2), 'little'))
        arm9_data.seek(bros_attacks_item_table_offset + ((special_attack_data[i][4] - 0x1000) * 24) + 20)
        if int.from_bytes(arm9_data.read(2), 'little') > 9: # luigi's starting SP stat
            expensive_attacks.append(i)
        bros_attack_list.append(special_attack_data[i][3])
        bros_pieces_list.append(special_attack_data[i][2])

    random.shuffle(special_attack_data)
    # make sure snack basket isn't in peach's castle or toadley's clinic
    # make sure trash pit's attack isn't too expensive
    while (special_attack_data[7][2] == 0x6015 or special_attack_data[7][2] == 0x600D) or any(special_attack_data[i][2] == 0x601B for i in range(7, 9)):
        # TO DO: add an additional check if chakron still owns any items the player needs. if he doesn't, this step is unnecessary
        if (special_attack_data[7][2] == 0x6015 or special_attack_data[7][2] == 0x600D):
            parent.log.appendPlainText("- Snack Basket was placed beyond Chakron. Reshuffling...")
        elif any(special_attack_data[i][2] == 0x601B for i in expensive_attacks):
            parent.log.appendPlainText("- Trash Pit's Special Attack is too costly. Reshuffling...")
        random.shuffle(special_attack_data)

    # TO DO: randomize bowser's special attacks too
    # TO DO: actually refine the cutscenes with bowser's attacks

    bros_attack_rando = []
    bros_pieces_rando = []
    spoiler_file += "\n\n----" + bros_attack_string + "----"
    for i in range(10):
        overlay_data.seek(bros_attacks_table_offset + (i * 18))
        overlay_data.write(special_attack_data[i][0].to_bytes(2, 'little'))
        overlay_data.seek(2, 1)
        overlay_data.write(special_attack_data[i][1].to_bytes(2, 'little'))
        overlay_data.write(special_attack_data[i][2].to_bytes(2, 'little'))
        bros_attack_rando.append(special_attack_data[i][3])
        bros_pieces_rando.append(special_attack_data[i][2])
    
    for i in range(10):
        j = bros_pieces_rando.index(bros_pieces_list[i])
        spoiler_file += f"\n{string_lists[0][special_attack_data[j][0]]}: {string_lists[1][special_attack_names[j]]}"

    for i in range(len(fevent_manager.fevent_chunks)):
        if i == 0x28A: # don't mess with challenge node
            # TO DO: don't mess with broque madame
            continue
        script = fevent_manager.fevent_chunks[i][0]
        for subroutine in script.subroutines:
            for command in subroutine.commands:
                if not isinstance(command, mnllib.CodeCommand):
                    continue
                if command.result_variable is not None:
                    if command.result_variable.number in bros_attack_rando:
                        command.result_variable = mnllib.Variable(bros_attack_list[bros_attack_rando.index(command.result_variable.number)])
                for argument in command.arguments:
                    if isinstance(argument, mnllib.Variable):
                        if argument.number in bros_attack_rando:
                            argument = mnllib.Variable(bros_attack_list[bros_attack_rando.index(argument.number)])

    fevent_manager.fevent_chunks[0x01FD][0].subroutines[1].commands = [ # let the bros use any special attacks they have at any time just in case
        mnllib.CodeCommand(0x0008, [0x0001], mnllib.Variable(0x200B)),
        mnllib.CodeCommand(0x0008, [0x0001], mnllib.Variable(0x200D)),
        ] + fevent_manager.fevent_chunks[0x01FD][0].subroutines[1].commands

    overlay_data.seek(0)
    return overlay_data.read(), fevent_manager, spoiler_file