from io import BytesIO
from mnllib import CodeCommand, Variable
from mnllib.bis import Subroutine

from randoglobin.data_classes import LevelUpStats

def skip_intro(fevent_manager, skip_peach_castle):
    if skip_peach_castle: # TO DO: fix this eventually
        fevent_manager.fevent_chunks[0x021D][0].subroutines[6] = skip_intro_1a
        fevent_manager.fevent_chunks[0x0208][0].subroutines[2] = skip_intro_1b
    else:
        fevent_manager.fevent_chunks[0x021D][0].subroutines[6] = skip_intro_0a
        fevent_manager.fevent_chunks[0x0208][0].subroutines[2] = skip_intro_0b
        if fevent_manager.fevent_chunks[0x021A][2].text_tables[0x44] != None:
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
    CodeCommand(0x01AE),
    CodeCommand(0x011E, [0x0296, 0x0000, 0x0000, 0x0000, 0x00, 0x00, 0x0001, -0x00000003, 0x00]),
    CodeCommand(0x0001),
])

skip_intro_1b = Subroutine([
    CodeCommand(0x0120, [0x0295, 0x0002, -0x00000003]),
    CodeCommand(0x0001),
])

def remove_enemies(fevent_manager):
    for i in range(len(fevent_manager.fevent_chunks)):
        chunk_triple = fevent_manager.fevent_chunks[i]
        fevent_manager.fevent_chunks[i] = (chunk_triple[0], None, chunk_triple[2])
    return fevent_manager

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

def change_start_level(fevent_manager, target_level, arm9_data, table_offsets):
    arm9 = BytesIO(arm9_data)

    level_up = []
    for i in range(3):
        arm9.seek(table_offsets[i])

        exp = 0
        for j in range(target_level - 1):
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
    
    fevent_manager.fevent_chunks[0x01FD][0].subroutines[1].commands[:0] = level_up
    
    return fevent_manager

# TO DO: add a patch to shorten the attack piece cutscene

def open_worldify(fevent_manager):
    if False: # this ain't ready
        # TO DO: remove starlow's first yapfest in the bowser map
        # TO DO: unlock chakroads
        # TO DO: un-break joint tower
        # TO DO: lock stingler areas behind the stingler
        # TO DO: lock bumpsy 1's side entrance behind the banzai bill
        # TO DO: remove cutscenes where bowser gets downed

        # unlock all bowser maps
        for command in fevent_manager.fevent_chunks[0x01FB][0].subroutines[1].commands:
            if command.result_variable is not None:
                if command.result_variable.number == 0x605C:
                    command.arguments[0] = 0xA

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
        fevent_manager.fevent_chunks[0x0215][0].subroutines[0].commands[:0] = fast_travel

    fevent_manager = skip_tutorials(fevent_manager)

    return fevent_manager


def skip_tutorials(fevent_manager):
    field_tutorial_skips = [
        # trash pit to do:
        # - post-luigi menu tut
        # - post-first-atk-piece starlow interjection
        # - post-hammer starlow interjection
        CodeCommand(0x0008, [0x0001], Variable(0xE89D)), # trash pit: starlow discovery
        CodeCommand(0x0008, [0x0001], Variable(0xE8A0)), # trash pit: luigi discovery
        CodeCommand(0x0008, [0x0001], Variable(0xE8A7)), # trash pit: hammer discovery

        CodeCommand(0x0008, [0x0001], Variable(0xE850)), # funny bone: first visit

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
    ]

    fevent_manager.fevent_chunks[0x01FD][0].subroutines[1].commands[:0] = field_tutorial_skips
    fevent_manager.fevent_chunks[0x0215][0].subroutines[0].commands[:0] = field_tutorial_skips

    # -----------------------------------------------------------------------------------------------
    # cutscene skips
    # TO DO: do these eventually

    # # remove starlow's yap after getting saved
    # fevent_manager.fevent_chunks[0x0210][0].subroutines[2].commands = [
    #     *fevent_manager.fevent_chunks[0x0210][0].subroutines[2].commands[:143],
    #     *fevent_manager.fevent_chunks[0x0210][0].subroutines[2].commands[-17:],
    # ]
    # # disable starlow's yapfest after escaping trash pit
    # fevent_manager.fevent_chunks[0x01FB][0].subroutines[3] = Subroutine([
    #     Command(0x0001),
    # ])

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

    return fevent_manager