from mnllib import *
from mnllib.bis import *

import importlib
import mnlscript.bis.text
import sys

if 'mnlscript.bis.text' in sys.modules:
    del sys.modules['mnlscript.bis.text']
if 'mnlscript.bis' in sys.modules:
    del sys.modules['mnlscript.bis']

import mnlscript.bis.text
mnlscript.bis.text.TT = None

import mnlscript.bis
importlib.reload(mnlscript.bis)

from mnlscript import label, return_, CodeCommandWithOffsets, update_commands_with_offsets, SubroutineExt
from mnlscript.bis import Variables, Actors, StackTopModification, StackPopCondition, Sound
from mnlscript.bis.commands import *

from typing import cast
import mnlscript
import functools
import inspect

# Workaround for dynamic scope in Nuitka
def subroutine(*args, **kwargs):
    def decorator(function):
        @mnlscript.subroutine(*args, **kwargs)
        @functools.wraps(function)
        def subroutine(sub: Subroutine):
            if '__compiled__' in globals():
                inspect.currentframe().f_locals['sub'] = sub
            function(sub=sub)
        return subroutine
    return decorator


##################################################################################
##################################################################################
##################################################################################


def bowser_map_mods(fevent_manager):
    room_id = 0x1B
    script = fevent_manager.fevent_chunks[room_id][0]
    subroutine_num = len(script.subroutines)
    
    cast(SubroutineExt, script.subroutines[0x06]).name = 'sub_0x6'
    cast(SubroutineExt, script.subroutines[0x0A]).name = 'sub_0xa'
    cast(SubroutineExt, script.subroutines[0x0E]).name = 'sub_0xe'
    cast(SubroutineExt, script.subroutines[0x42]).name = 'sub_0x42'

    script.subroutines[0x17].commands[2].arguments[0] = Variables[0x605C]
    script.subroutines[0x17].commands[4] = CodeCommandWithOffsets(0x0003, [0x00, PLACEHOLDER_OFFSET], offset_arguments = {1: 'sub_0x42'})
    
    @subroutine(subs = script.subroutines, hdr = script.header)
    def flame_pipe_enter(sub: Subroutine):
        branch_if(Variables[0xEB5E], '==', 0x1, 'flame_pipe_disallow', invert=True) # flame pipe is allowed to be entered

        Variables[0x1000] = 0xFFF
        branch_if(Variables[0x3008], '==', 0x1, 'flame_pipe_enter_0', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('flame_pipe_enter_0', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
        emit_command(0x01A1)
        branch_if(Variables[0xA000], '==', 0x0, 'flame_pipe_enter_1', invert=True)
        emit_command(0x005B, [0x00])
        branch('flame_pipe_enter_2')

        label('flame_pipe_enter_1', manager = fevent_manager)
        emit_command(0x005B, [0x02])

        label('flame_pipe_enter_2', manager = fevent_manager)
        emit_command(0x01CE, [0x0002021C, 0x06, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x014B, [0x7F, -0x10, 0x0010])
        emit_command(0x014C)
        call('sub_0xe')
        emit_command(0x0058, [0x02, 0x00])
        branch_if(Variables[0x901E], '!=', 0x63, 'flame_pipe_enter_3', invert=True)
        emit_command(0x0063, [0x09, 0x00])
        emit_command(0x0064, [0x09, 0x00])
        wait(1)

        label('flame_pipe_enter_3', manager = fevent_manager)
        emit_command(0x00F5, [0x00, 0x01, 0x01])
        emit_command(0x00F6, [0x00, 0x03])
        emit_command(0x00F6, [0x01, 0x03])
        emit_command(0x00F0, [0x00])
        set_animation(Actors.MARIO, 0x03, unk3=0x00)
        emit_command(0x00F0, [0x01])
        set_animation(Actors.LUIGI, 0x03, unk3=0x00)
        branch_if(0x0, '==', 0x0, 'flame_pipe_enter_4', invert=True)
        emit_command(0x00F0, [0x00])
        set_animation(Actors.MARIO, 0x03, unk3=0x00)
        emit_command(0x00F0, [0x01])
        set_animation(Actors.LUIGI, 0x03, unk3=0x00)
        emit_command(0x011D, [0x00])
        branch('flame_pipe_enter_5')

        label('flame_pipe_enter_4', manager = fevent_manager)
        emit_command(0x00F0, [0x02])
        set_animation(Actors.BOWSER, 0x03, unk3=0x00)
        emit_command(0x011D, [0x01])

        label('flame_pipe_enter_5', manager = fevent_manager)
        emit_command(0x01A9)
        emit_command(0x007A, [0x00, -0x01, -0x01, -0x01, -0x01, -0x01])
        emit_command(0x007A, [0x01, -0x01, -0x01, -0x01, -0x01, -0x01])
        emit_command(0x0063, [0x00, 0x01])
        emit_command(0x0063, [0x01, 0x01])
        emit_command(0x00E7, [0x01])
        emit_command(0x0192, [0x01, Variables[0x3000]])
        Variables[0x1000] = 0x0
        branch_if(Variables[0x3008], '==', 0x1, 'flame_pipe_enter_6', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('flame_pipe_enter_6', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
        emit_command(0x011E, [0x0038, 0x001E, 0x0230, 0x0000, 0x02, 0x00, -0x0001, -0x00000003, 0x01])
        branch_if(Variables[0xA000], '==', 0x0, 'sub_0x6')

        label('flame_pipe_disallow', manager = fevent_manager)
        emit_command(0x01CD, [0x2002007E, 0x0080, 0x0060, 0x0000, 0x0000, 0x0001, 0x00])

        set_animation(0x0A, 0x01)
        emit_command(0x0098, [0x0A, 0x04, 0x03, 0x0000, 0x0001, 0x01, 0x01])
        emit_command(0x0094, [0x0A, 0x0000, 0x00])

        load_data_from_array('sub_0xa', 8, res=Variables[0xA000])
        load_data_from_array('sub_0xa', 9, res=Variables[0xA001])
        Variables[0xA000] -= 0x6
        Variables[0xA001] -= 0x8
        emit_command(0x00BD, [0x0A, 0x00, Variables[0xA000], Variables[0xA001], 0x0000])
        emit_command(0x0063, [0x0A, 0x01])
        emit_command(0x0064, [0x0A, 0x01])

        emit_command(0x0093, [0x0A])
        set_animation(0x0A, 0x00)
        emit_command(0x0063, [0x0A, 0x00])
        emit_command(0x0064, [0x0A, 0x00])

    @subroutine(subs = script.subroutines, hdr = script.header)
    def joint_tower_enter(sub: Subroutine):
        branch_if(Variables[0xEB63], '==', 0x1, 'joint_tower_disallow', invert=True) # joint tower is allowed to be entered

        Variables[0x1000] = 0xFFF
        branch_if(Variables[0x3008], '==', 0x1, 'joint_tower_enter_0', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('joint_tower_enter_0', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
        emit_command(0x01A1)
        branch_if(Variables[0xA000], '==', 0x0, 'joint_tower_enter_1', invert=True)
        emit_command(0x005B, [0x00])
        branch('joint_tower_enter_2')

        label('joint_tower_enter_1', manager = fevent_manager)
        emit_command(0x005B, [0x02])

        label('joint_tower_enter_2', manager = fevent_manager)
        emit_command(0x01CE, [0x0002021C, 0x06, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x014B, [0x7F, -0x10, 0x0010])
        emit_command(0x014C)
        call('sub_0xe')
        emit_command(0x0058, [0x02, 0x00])
        branch_if(Variables[0x901E], '!=', 0x63, 'joint_tower_enter_3', invert=True)
        emit_command(0x0063, [0x09, 0x00])
        emit_command(0x0064, [0x09, 0x00])
        wait(1)

        label('joint_tower_enter_3', manager = fevent_manager)
        emit_command(0x00F5, [0x00, 0x01, 0x01])
        emit_command(0x00F6, [0x00, 0x03])
        emit_command(0x00F6, [0x01, 0x03])
        emit_command(0x00F0, [0x00])
        set_animation(Actors.MARIO, 0x03, unk3=0x00)
        emit_command(0x00F0, [0x01])
        set_animation(Actors.LUIGI, 0x03, unk3=0x00)
        branch_if(0x0, '==', 0x0, 'joint_tower_enter_4', invert=True)
        emit_command(0x00F0, [0x00])
        set_animation(Actors.MARIO, 0x03, unk3=0x00)
        emit_command(0x00F0, [0x01])
        set_animation(Actors.LUIGI, 0x03, unk3=0x00)
        emit_command(0x011D, [0x00])
        branch('joint_tower_enter_5')

        label('joint_tower_enter_4', manager = fevent_manager)
        emit_command(0x00F0, [0x02])
        set_animation(Actors.BOWSER, 0x03, unk3=0x00)
        emit_command(0x011D, [0x01])

        label('joint_tower_enter_5', manager = fevent_manager)
        emit_command(0x01A9)
        emit_command(0x007A, [0x00, -0x01, -0x01, -0x01, -0x01, -0x01])
        emit_command(0x007A, [0x01, -0x01, -0x01, -0x01, -0x01, -0x01])
        emit_command(0x0063, [0x00, 0x01])
        emit_command(0x0063, [0x01, 0x01])
        emit_command(0x00E7, [0x01])
        emit_command(0x0192, [0x01, Variables[0x3000]])
        Variables[0x1000] = 0x0
        branch_if(Variables[0x3008], '==', 0x1, 'joint_tower_enter_6', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('joint_tower_enter_6', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
        emit_command(0x011E, [0x013A, 0x001E, 0x02E8, 0x0098, 0x02, 0x01, -0x0001, -0x00000003, 0x01])
        branch_if(Variables[0xA000], '==', 0x0, 'sub_0x6')
        return_()

        label('joint_tower_disallow', manager = fevent_manager)
        emit_command(0x01CD, [0x2002007E, 0x0080, 0x0060, 0x0000, 0x0000, 0x0001, 0x00])

        set_animation(0x0A, 0x01)
        emit_command(0x0098, [0x0A, 0x04, 0x03, 0x0000, 0x0001, 0x01, 0x01])
        emit_command(0x0094, [0x0A, 0x0000, 0x00])

        load_data_from_array('sub_0xa', 26, res=Variables[0xA000])
        load_data_from_array('sub_0xa', 27, res=Variables[0xA001])
        Variables[0xA000] -= 0x6
        Variables[0xA001] -= 0x8
        emit_command(0x00BD, [0x0A, 0x00, Variables[0xA000], Variables[0xA001], 0x0000])
        emit_command(0x0063, [0x0A, 0x01])
        emit_command(0x0064, [0x0A, 0x01])

        emit_command(0x0093, [0x0A])
        set_animation(0x0A, 0x00)
        emit_command(0x0063, [0x0A, 0x00])
        emit_command(0x0064, [0x0A, 0x00])

    script.subroutines[4].commands[268] = CodeCommandWithOffsets(0x0003, [0x01, PLACEHOLDER_OFFSET], offset_arguments = {1: 'flame_pipe_enter'})
    script.subroutines[4].commands[317] = CodeCommandWithOffsets(0x0003, [0x01, PLACEHOLDER_OFFSET], offset_arguments = {1: 'joint_tower_enter'})
    script.header.subroutine_table = [0] * len(script.subroutines)
    for i in range(len(script.header.array5)): # update offsets in array5
        script.header.array5[i] += (len(script.subroutines) - subroutine_num) * 2
    update_commands_with_offsets(fevent_manager, [script.header.post_table_subroutine, *script.subroutines], len(script.header.to_bytes(fevent_manager)))
    
    script.subroutines[4].commands = [
        *script.subroutines[4].commands[:269],
        CodeCommand(0x0003, [0x00, 0x0000]),
        CodeCommand(0x00BB, [0x00]),
        CodeCommand(0x00BB, [0x00]),
        *script.subroutines[4].commands[270:318],
        CodeCommand(0x0003, [0x00, 0x0000]),
        CodeCommand(0x00BB, [0x00]),
        CodeCommand(0x00BB, [0x00]),
        *script.subroutines[4].commands[319:],
    ]

    script.header.actors.append((
        script.header.actors[9][0],
        script.header.actors[9][1],
        script.header.actors[9][2],
        script.header.actors[9][3],
        script.header.actors[9][4],
    ))

    # print(hex(len(script.subroutines)))
    # for i, command in enumerate(script.subroutines[4].commands):
    #     if command.command_id == 0x011E:
    #         print(i)


##################################################################################
##################################################################################
##################################################################################


def trash_pit_skips(fevent_manager):
    room_id = 0x210
    script = fevent_manager.fevent_chunks[room_id][0]
    subroutine_num = len(script.subroutines)

    script.subroutines.pop() # fsr this room doesn't like when i add subroutines, and the last one is never used so ¯\_(ツ)_/¯
    @subroutine(subs = script.subroutines, hdr = script.header)
    def starlow_rescue_end(sub: Subroutine):
        emit_command(0x01CE, [0x20020076, 0x05, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x00B5, [0x05, 0x00, 0x0000, 0x0000, 0x0008, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x05])
        emit_command(0x0063, [0x05, 0x00])
        emit_command(0x0064, [0x05, 0x00])
        emit_command(0x0192, [0x01, 0x00])
        emit_command(0x00F5, [0x00, 0x01, 0x00])

        label('starlow_rescue_end_loop_start', manager = fevent_manager)
        wait(1)
        branch_if(Variables[0x3017], '==', 0x1, 'starlow_rescue_end_loop_start')
        Variables[0x1000] = 0xF0E
        branch_if(Variables[0x3008], '==', 0x1, 'starlow_rescue_end_loop_end', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('starlow_rescue_end_loop_end', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])

    script.subroutines[2].commands[177].arguments[1] = 0 # make the camera pan directly to mario instead of framing it like starlow's gonna talk
    script.subroutines[2].commands[180] = CodeCommandWithOffsets(0x0003, [0x00, PLACEHOLDER_OFFSET], offset_arguments = {1: 'starlow_rescue_end'})
    script.header.subroutine_table = [0] * len(script.subroutines)
    for i in range(len(script.header.array5)): # update offsets in array5
        script.header.array5[i] += (len(script.subroutines) - subroutine_num) * 2
    update_commands_with_offsets(fevent_manager, [script.header.post_table_subroutine, *script.subroutines], len(script.header.to_bytes(fevent_manager)))

    # -------------------------

    room_id = 0x207
    script = fevent_manager.fevent_chunks[room_id][0]

    cast(SubroutineExt, script.subroutines[0x0D]).name = 'sub_0xd'
    cast(SubroutineExt, script.subroutines[0x0E]).name = 'sub_0xe'
    cast(SubroutineExt, script.subroutines[0x1A]).name = 'sub_0x1a'
    cast(SubroutineExt, script.subroutines[0x1C]).name = 'sub_0x1c'

    script.subroutines.pop() # fsr this room doesn't like when i add subroutines, and the last one is never used so ¯\_(ツ)_/¯
    @subroutine(subs = script.subroutines, hdr = script.header)
    def luigi_rescue_end(sub: Subroutine):
        emit_command(0x00D1, [0x01, 0x00, 0x06])
        wait(30)
        emit_command(0x01CD, [0x00020037, 0x0080, 0x0060, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x0129, [0x00])
        emit_command(0x012A, [0x00])
        emit_command(0x012B, [0x00])
        wait(60)
        emit_command(0x0134, [0x00, 0x0098, 0x00C8, 0x0028, 0x01, 0x01])
        emit_command(0x0137)
        wait(20)
        emit_command(0x00D1, [0x01, 0x00, 0x02])
        set_animation(Actors.MARIO, 0x01)
        emit_command(0x0091, [0x00, 0x0C, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x00, 0x0000, 0x00])
        set_animation(Actors.MARIO, 0x03)
        emit_command(0x00D1, [0x00, 0x00, 0x06])
        set_animation(Actors.LUIGI, 0x01)
        emit_command(0x0091, [0x01, 0x07, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x01, 0x0000, 0x00])
        set_animation(Actors.LUIGI, 0x03)
        emit_command(0x00D1, [0x01, 0x00, 0x02])
        wait(30)
        emit_command(0x01CE, [0x4000006C, 0x00, 0x0000, 0x0000, 0x0001, 0x00])
        branch_in_thread(0x00, 'sub_0x1a')
        join_thread(0x00)
        wait(60)
        emit_command(0x01CE, [0x40000041, 0x01, 0x0000, 0x0000, 0x0001, 0x00])
        branch_in_thread(0x01, 'sub_0x1c')
        join_thread(0x01)
        wait(60)
        emit_command(0x00B2, [0x00, 0x00, 0x0118, 0x0170, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x00, 0x00, 0x01, 0x01])
        unk_thread_branch_0x004a(0x01, 'luigi_rescue_0')
        emit_command(0x00B2, [-0x01, 0x00, 0x012C, 0x0170, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        emit_command(0x00D1, [-0x01, 0x00, 0x06])
        return_()

        label('luigi_rescue_0', manager = fevent_manager)
        emit_command(0x00BB, [0x00])
        branch_if(0x1, '==', 0x0, 'luigi_rescue_1', invert=True)
        get_actor_attribute(Actors.MARIO, 0x0E, res=Variables[0x1000])
        Variables[0x1000] = Variables[0x1000] + 0x4
        Variables[0x1000] = Variables[0x1000] & 0x7
        load_data_from_array('sub_0xd', Variables[0x1000], res=Variables[0x1001])
        load_data_from_array('sub_0xe', Variables[0x1000], res=Variables[0x1002])
        Variables[0x1000] = Variables[0x1000] & 0x1
        branch_if(Variables[0x1000], '==', 0x0, 'luigi_rescue_2', invert=True)
        Variables[0x1001] = Variables[0x1001] * 0x14
        Variables[0x1002] = Variables[0x1002] * 0x14
        branch('luigi_rescue_3')

        label('luigi_rescue_2', manager = fevent_manager)
        Variables[0x1001] = Variables[0x1001] * 0xF
        Variables[0x1002] = Variables[0x1002] * 0xF

        label('luigi_rescue_3', manager = fevent_manager)
        get_actor_attribute(Actors.MARIO, ActorAttribute.X_POSITION, res=Variables[0x1003])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Y_POSITION, res=Variables[0x1004])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Z_POSITION, res=Variables[0x1005])
        Variables[0x1001] = Variables[0x1001] + Variables[0x1003]
        Variables[0x1002] = Variables[0x1002] + Variables[0x1004]
        emit_command(0x00B2, [0x01, 0x00, Variables[0x1001], Variables[0x1002], Variables[0x1005], 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x01])
        emit_command(0x00D2, [0x01, 0x00])

        label('luigi_rescue_1', manager = fevent_manager)
        emit_command(0x00E9, [0x01, 0x00])
        branch_if(0x0, '==', 0xFF, 'luigi_rescue_4', invert=True)
        emit_command(0x0192, [0x00, -0x01])
        branch('luigi_rescue_5')

        label('luigi_rescue_4', manager = fevent_manager)
        emit_command(0x0192, [0x01, 0x00])

        label('luigi_rescue_5', manager = fevent_manager)
        Variables[0xE89A] = 0x0
        branch_if(0x3, '>=', Variables[0x3029], 'luigi_rescue_6', invert=True)
        emit_command(0x01AF, [0x03])

        label('luigi_rescue_6', manager = fevent_manager)
        emit_command(0x0189, [0x00])
        branch_if(Variables[0x3019], '==', 0x0, 'luigi_rescue_7', invert=True)
        emit_command(0x00F5, [0x00, 0x01, 0x00])
        branch_if(0x0, '==', 0x0, 'luigi_rescue_9', invert=True)

        label('luigi_rescue_8', manager = fevent_manager)
        wait(1)
        branch_if(Variables[0x3017], '==', 0x1, 'luigi_rescue_8')

        label('luigi_rescue_7', manager = fevent_manager)
        branch_if(Variables[0x3008], '==', 0x0, 'luigi_rescue_10', invert=True)
        emit_command(0x00F5, [0x01, 0x01, 0x00])
        branch_if(0x0, '==', 0x0, 'luigi_rescue_9', invert=True)

        label('luigi_rescue_11', manager = fevent_manager)
        wait(1)
        branch_if(Variables[0x3018], '==', 0x1, 'luigi_rescue_11')

        label('luigi_rescue_10', manager = fevent_manager)
        emit_command(0x00F5, [0x00, 0x01, 0x00])
        branch_if(0x0, '==', 0x0, 'luigi_rescue_9', invert=True)

        label('luigi_rescue_12', manager = fevent_manager)
        wait(1)
        branch_if(Variables[0x3017], '==', 0x1, 'luigi_rescue_12')

        label('luigi_rescue_9', manager = fevent_manager)
        branch_if(Variables[0x3008], '==', 0x0, 'luigi_rescue_13', invert=True)
        emit_command(0x018C, [Variables[0x3008], 0x0000], Variables[0x1007])
        branch('luigi_rescue_14')

        label('luigi_rescue_13', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], 0x00C0], Variables[0x1007])

        label('luigi_rescue_14', manager = fevent_manager)

    script.subroutines[2].commands[416] = CodeCommandWithOffsets(0x0003, [0x00, PLACEHOLDER_OFFSET], offset_arguments = {1: 'luigi_rescue_end'})
    script.header.subroutine_table = [0] * len(script.subroutines)
    update_commands_with_offsets(fevent_manager, [script.header.post_table_subroutine, *script.subroutines], len(script.header.to_bytes(fevent_manager)))
    
    # -------------------------

    room_id = 0x213
    script = fevent_manager.fevent_chunks[room_id][0]

    for i in range(9):
        script.subroutines.pop()

    @subroutine(subs = script.subroutines, hdr = script.header)
    def door_check(sub: Subroutine):
        branch_if(Variables[0xE701], '==', 0x0, 'door_abort')
        branch_if(Variables[0xE702], '==', 0x0, 'door_abort')
        branch_if(Variables[0xE703], '==', 0x0, 'door_abort')
        branch_if(Variables[0xE704], '==', 0x0, 'door_abort')
        branch_if(Variables[0xE705], '==', 0x0, 'door_abort')
        branch_if(Variables[0xE706], '==', 0x0, 'door_abort')
        branch_if(Variables[0xE707], '==', 0x0, 'door_abort')
        branch_if(Variables[0xE708], '==', 0x0, 'door_abort')

        emit_command(0x0127, [0x01])
        emit_command(0x018C, [Variables[0x3008], 0x0FFF], Variables[0x1007])
        emit_command(0x00F5, [0x00, 0x00, 0x00])
        wait(30)

        emit_command(0x0134, [0x00, 0x0000, 0x0000, 0x0028, 0x01, 0x01])
        emit_command(0x0137)
        wait(20)
        emit_command(0x01CD, [0x00020092, 0x0080, 0x0060, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x0129, [0x00])
        emit_command(0x012A, [0x00])
        emit_command(0x012B, [0x00])
        wait(60)
        emit_command(0x0136, [0x00, 0x0000, 0x0000, 0x001E, 0x01, 0x01])
        emit_command(0x0137)

        emit_command(0x00F5, [0x00, 0x01, 0x00])
        branch_if(Variables[0x3008], '==', 0x0, 'door_something_check', invert=True)
        emit_command(0x018C, [Variables[0x3008], 0x0000], Variables[0x1007])
        emit_command(0x0127, [0x00])
        branch('door_abort')

        label('door_something_check', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], 0x00C0], Variables[0x1007])
        emit_command(0x0127, [0x00])

        label('door_abort', manager = fevent_manager)

    for i in range(8):
        block_var = 0xE701 + i
        @subroutine(subs = script.subroutines, hdr = script.header)
        def block_sub(sub: Subroutine):
            branch_if(Variables[block_var], '==', 0x1, 'block_sub_abort')
            Variables[block_var] = 1
            match i:
                case 0: Variables[0x601B] |= 0x2
                case 1: Variables[0x601B] |= 0x4
                case 2: Variables[0x601B] |= 0x8
                case 3: Variables[0x601B] |= 0x10
                case 4: Variables[0x601C] |= 0x1
                case 5: Variables[0x601C] |= 0x2
                case 6: Variables[0x601C] |= 0x4
                case 7: Variables[0x601C] |= 0x8
            Variables[0x601D] += 1
            Variables[0x900F] = i + 2

            unk_thread_branch_0x004a(Variables[0x900F], 'piece_anim')
            emit_command(0x01CE, [0x02000094, Variables[0x900F], 0x0000, 0x0000, 0x0001, 0x00])
            emit_command(0x00D9, [Variables[0x900F]])
            set_animation(Variables[0x900F], 0x01)
            emit_command(0x0091, [Variables[0x900F], -0x01, 0x0000, -0x0001, 0x01])
            emit_command(0x0094, [Variables[0x900F], 0x0000, 0x00])
            set_animation(Variables[0x900F], 0x00)
            emit_command(0x00D7, [Variables[0x900F], 0x00])
            emit_command(0x00D8, [Variables[0x900F], 0x00])
            return_()

            label('piece_anim', manager = fevent_manager)
            start_thread_here_and_branch(0x0A, 'block_sub_end')
            get_actor_attribute(Variables[0x900F], ActorAttribute.X_POSITION, res=Variables[0x1000])
            get_actor_attribute(Variables[0x900F], ActorAttribute.Y_POSITION, res=Variables[0x1001])
            get_actor_attribute(Variables[0x900F], ActorAttribute.Z_POSITION, res=Variables[0x1002])
            Variables[0x1000] = Variables[0x1000] + 0x0
            Variables[0x1001] = Variables[0x1001] + 0x0
            Variables[0x1002] = Variables[0x1002] + 0x26
            emit_command(0x00BD, [-0x01, 0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002]])
            wait(5)
            emit_command(0x0063, [-0x01, 0x01])
            emit_command(0x0078, [-0x01, 0x00000000])
            emit_command(0x00B2, [-0x01, 0x01, 0x0000, 0x0000, 0x0010, 0x0200, 0x0000, 0x0200, 0x0080, 0x00, 0x00, 0x01, 0x01])
            emit_command(0x00BB, [-0x01])
            wait(20)
            emit_command(0x0063, [-0x01, 0x00])
            return_()

            label('block_sub_end', manager = fevent_manager)
            call('door_check')

            label('block_sub_abort', manager = fevent_manager)
        
        script.header.actors[i + 2] = (
            script.header.actors[i + 2][0],
            script.header.actors[i + 2][1],
            script.header.actors[i + 2][2],
            (block_var << 16) + (len(script.subroutines) - 1),
            script.header.actors[i + 2][4],
        )
    
    script.header.subroutine_table = [0] * len(script.subroutines)
    update_commands_with_offsets(fevent_manager, [script.header.post_table_subroutine, *script.subroutines], len(script.header.to_bytes(fevent_manager)))


##################################################################################
##################################################################################
##################################################################################


def funny_bone_skips(fevent_manager):
    room_id = 0x1FC
    script = fevent_manager.fevent_chunks[room_id][0]
    script.subroutines.pop()

    cast(SubroutineExt, script.subroutines[0x06]).name = 'sub_0x6'
    cast(SubroutineExt, script.subroutines[0x07]).name = 'sub_0x7'
    cast(SubroutineExt, script.subroutines[0x17]).name = 'sub_0x17'

    @subroutine(subs = script.subroutines, hdr = script.header)
    def awaken_bowser(sub: Subroutine):
        emit_command(0x00F4, [0x00, 0x01], Variables[0xA000])
        branch_if(Variables[0xA000], '!=', 0x2, 'sub_0x17')

        branch_if(Variables[0xE852], '==', 0x1, 'sub_0x17')
        Variables[0xE852] = 0x1
        Variables[0xE88A] = 0
        Variables[0x6020] = 0
        branch_in_thread(0x04, 'sub_0x7')
        emit_command(0x01D7, [0x00, 0x001E])
        emit_command(0x01D7, [0x01, 0x001E])
        branch_in_thread(0x05, 'sub_0x6')
        emit_command(0x018C, [Variables[0x3008], 0x0FFF], Variables[0x1007])
        branch_if(Variables[0x3019], '==', 0x0, 'awaken_bowser_0', invert=True)
        emit_command(0x00F5, [0x00, 0x00, 0x00])
        branch('awaken_bowser_1')

        label('awaken_bowser_0', manager = fevent_manager)
        branch_if(Variables[0x3008], '==', 0x0, 'awaken_bowser_2', invert=True)
        emit_command(0x00F5, [0x01, 0x00, 0x00])
        branch('awaken_bowser_1')

        label('awaken_bowser_2', manager = fevent_manager)
        emit_command(0x00F5, [0x00, 0x00, 0x00])

        label('awaken_bowser_1', manager = fevent_manager)
        emit_command(0x01CE, [0x00020056, 0x04, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x0192, [0x00, Variables[0x3000]])
        emit_command(0x0133, [0x00, 0x0200, 0x0078, 0x0400, 0x0000, 0x0400, 0x0400, 0x01, 0x01])
        join_thread(0x05)
        emit_command(0x01CD, [0x00024080, 0x0080, 0x0060, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x013F, [0x00000007, 0x0001, 0x0200, 0x00, 0x06, 0x00])
        
        Variables[0xE853] = 0x1
        Variables[0xD0BA] = 0x1
        Variables[0x1000] = 0xFFF
        branch_if(Variables[0x3008], '==', 0x1, 'awaken_bowser_3', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('awaken_bowser_3', manager = fevent_manager)
        execute_on_secondary_screen('awaken_bowser_other_screen', unk1=0x00)
        return_()


        label('awaken_bowser_other_screen', manager = fevent_manager)
        emit_command(0x014B, [0x7F, 0x00, 0x0010])
        emit_command(0x014C)
        wait(20)
        emit_command(0x009A, [0x00, 0x00000127])
        emit_command(0x01A9)
        set_animation(Actors.BOWSER, 0x01)
        emit_command(0x009B, [0x02, 0x00, 0x0001, -0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        emit_command(0x00BF, [0x02, 0x0028, -0x00001000])
        emit_command(0x01CE, [0x4000000D, 0x02, 0x0000, 0x0000, 0x0001, 0x00])
        say((-32768, 120), Sound.NONE, 0x00, bubble=BubbleType.SHOUTING, tail=TailType.NONE, tail_hoffset=0xFF, force_wait_command=False)
        emit_command(0x00C1, [0x02])
        set_animation(Actors.BOWSER, 0x00)
        emit_command(0x0091, [0x02, 0x03, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x01])
        wait(30)
        emit_command(0x01CE, [0x4000001B, 0x02, 0x0096, 0x0000, 0x0001, 0x00])
        execute_on_secondary_screen('awaken_bowser_bros_react', unk1=0x00)
        set_animation(Actors.BOWSER, 0x00)
        emit_command(0x0091, [0x02, -0x01, 0x0000, 0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        emit_command(0x0093, [0x02])
        set_animation(Actors.BOWSER, 0x01)
        emit_command(0x0091, [0x02, 0x01, 0x0001, -0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        set_animation(Actors.BOWSER, 0x00)
        wait_for_textbox()
        wait(8)
        emit_command(0x01CE, [0x0002404E, 0x02, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x00D4, [0x02, 0x01, 0x01, 0x0000, -0x0008, 0x0028, 0x00])
        emit_command(0x00D6, [0x02])
        wait(40)
        emit_command(0x009A, [0x00, 0x00000138])
        emit_command(0x01A9)
        set_animation(Actors.BOWSER, 0x01)
        emit_command(0x009B, [0x02, 0x00, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        emit_command(0x0165)
        get_actor_attribute(Actors.BOWSER, ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Z_POSITION, res=Variables[0x1002])
        Variables[0x1000] = Variables[0x1000] + 0x0
        Variables[0x1001] = Variables[0x1001] + 0x0
        Variables[0x1002] = Variables[0x1002] + 0x0
        emit_command(0x0161, [0x01, Variables[0x1000], Variables[0x1001], Variables[0x1002], 0x0100], Variables[0xA009])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Z_POSITION, res=Variables[0x1002])
        Variables[0x1000] = Variables[0x1000] + 0x0
        Variables[0x1001] = Variables[0x1001] + 0x0
        Variables[0x1002] = Variables[0x1002] + 0x0
        emit_command(0x00BD, [0x04, 0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002]])
        wait(1)
        start_thread_here_and_branch(0x04, 'camera_pan_0')
        emit_command(0x0192, [0x00, -0x01])
        emit_command(0x0063, [-0x01, 0x01])
        emit_command(0x0064, [-0x01, 0x01])
        emit_command(0x00B2, [-0x01, 0x01, 0x0040, 0x0000, 0x0000, 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        emit_command(0x00B9, [-0x01, 0x02, 0x0000, 0x0000, 0x0000, 0x06, 0x00168000, 0x0180, -0x01, 0x0100, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        emit_command(0x00B2, [-0x01, 0x01, -0x0040, 0x0000, 0x0000, 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        return_()

        label('camera_pan_0', manager = fevent_manager)
        start_thread_here_and_branch(0x02, 'camera_pan_1')
        wait(1)

        label('camera_pan_2', manager = fevent_manager)
        emit_command(0x0136, [0x04, 0x0000, 0x0000, 0x0001, 0x01, 0x01])
        emit_command(0x0137)
        branch('camera_pan_2', type=0x00)
        return_()

        label('camera_pan_1', manager = fevent_manager)
        wait(10)
        emit_command(0x01D3, [0x00, 0x0042])
        emit_command(0x01D5)
        emit_command(0x01D3, [0x01, 0x0043])
        emit_command(0x01D5)
        join_thread(0x04)
        emit_command(0x00BB, [0x04])
        emit_command(0x004E, [0x02])
        wait(20)
        set_animation(Actors.BOWSER, 0x01)
        emit_command(0x0091, [0x02, 0x00, 0x0004, -0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        set_animation(Actors.BOWSER, 0x03)
        emit_command(0x00D1, [0x02, 0x00, 0x04])
        emit_command(0x0151, [0x00])
        wait(10)
        emit_command(0x00D1, [0x02, 0x00, 0x04])
        emit_command(0x009A, [0x00, 0x00000024])
        emit_command(0x01A9)
        set_animation(Actors.BOWSER, 0x01)
        emit_command(0x009B, [0x02, 0x00, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        emit_command(0x0092, [0x02])
        emit_command(0x0097, [0x02])

        emit_command(0x018D, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
        emit_command(0x00F7, [0x01, 0x00, 0x00])
        wait(1)
        emit_command(0x01D6, [0x00, 0x00, 0x00])
        emit_command(0x01D6, [0x01, 0x00, 0x01])
        branch_if(0x4, '>=', Variables[0x3029], 'awaken_bowser_other_screen_0', invert=True)
        emit_command(0x01AF, [0x04])

        label('awaken_bowser_other_screen_0', manager = fevent_manager)
        Variables[0x202E] = 0x1
        Variables[0xEA6C] = 0x1
        Variables[0x2030] = 0x0
        Variables[0xEB00] = 0x0
        Variables[0xEB40] = 0x0
        Variables[0xEAEE] = 0x1
        Variables[0xEAEF] = 0x1
        Variables[0xEAF0] = 0x1
        Variables[0xEAF1] = 0x1
        Variables[0xEAF3] = 0x1
        Variables[0xEAF4] = 0x1
        Variables[0xEAF5] = 0x1
        Variables[0xEAF7] = 0x1
        Variables[0xEAF8] = 0x1
        emit_command(0x0119, [0x00])
        emit_command(0x00ED, [0x01, 0x00])
        emit_command(0x0192, [0x01, 0x02])
        emit_command(0x006E, [0x02, 0x01, 0x01])
        branch_if(Variables[0x3019], '==', 0x0, 'awaken_bowser_other_screen_1', invert=True)
        emit_command(0x00F5, [0x00, 0x01, 0x00])

        label('awaken_bowser_other_screen_1', manager = fevent_manager)
        branch_if(Variables[0x3008], '==', 0x0, 'awaken_bowser_other_screen_2', invert=True)
        emit_command(0x00F5, [0x01, 0x01, 0x00])

        label('awaken_bowser_other_screen_2', manager = fevent_manager)
        emit_command(0x00F5, [0x00, 0x01, 0x00])

        branch_if(Variables[0x3008], '==', 0x0, 'awaken_bowser_other_screen_3', invert=True)
        emit_command(0x018C, [Variables[0x3008], 0x0000], Variables[0x1007])
        branch('awaken_bowser_other_screen_4')

        label('awaken_bowser_other_screen_3', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], 0x00C0], Variables[0x1007])

        label('awaken_bowser_other_screen_4', manager = fevent_manager)
        Variables[0x1000] = 0x3
        branch_if(Variables[0x3008], '==', 0x1, 'awaken_bowser_other_screen_5', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('awaken_bowser_other_screen_5', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
        emit_command(0x01D0, [0x00])
        emit_command(0x01A1)
        Variables[0xEB3F] = 0x1
        return_()

        label('awaken_bowser_bros_react', manager = fevent_manager)
        wait(270)
        unk_thread_branch_0x004a(0x02, 'awaken_bowser_bros_react_0')
        emit_command(0x0064, [-0x01, 0x01])
        get_actor_attribute(Actors.MARIO, ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Z_POSITION, res=Variables[0x1002])
        Variables[0x1000] = Variables[0x1000] + 0x0
        Variables[0x1001] = Variables[0x1001] + 0x0
        Variables[0x1002] = Variables[0x1002] + 0xC
        emit_command(0x00BD, [-0x01, 0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002]])
        emit_command(0x01CE, [0x20020076, 0x02, 0x0000, 0x0000, 0x0001, 0x00])
        set_animation(Self, 0x01)
        emit_command(0x0091, [-0x01, 0x02, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        emit_command(0x0063, [-0x01, 0x01])
        emit_command(0x00B2, [-0x01, 0x01, 0x0000, 0x0000, 0x0040, 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        emit_command(0x0078, [-0x01, 0x00000000])
        return_()

        label('awaken_bowser_bros_react_0', manager = fevent_manager)
        emit_command(0x00E7, [0x00])
        start_thread_here_and_branch(0x00, 'awaken_bowser_bros_react_1')
        get_actor_attribute(-0x01, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        emit_command(0x00B2, [-0x01, 0x00, 0x0250, Variables[0x1001], 0x0160, 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        set_animation(Self, 0x00)
        emit_command(0x0091, [-0x01, 0x09, 0x0001, 0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        emit_command(0x0093, [-0x01])
        return_()

        label('awaken_bowser_bros_react_1', manager = fevent_manager)
        start_thread_here_and_branch(0x01, 'awaken_bowser_bros_react_2')
        get_actor_attribute(-0x01, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        emit_command(0x00B2, [-0x01, 0x00, 0x0238, Variables[0x1001], 0x0160, 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        emit_command(0x00D1, [-0x01, 0x00, 0x02])
        set_animation(Self, 0x00)
        emit_command(0x0091, [-0x01, 0x0A, 0x0000, 0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        emit_command(0x0093, [-0x01])
        return_()
        
        label('awaken_bowser_bros_react_2', manager = fevent_manager)
        return_()

    script.subroutines[5].commands[0] = CodeCommandWithOffsets(0x0002, [0x00, Variables[0xE850], 0x00000001, 0x00000001, PLACEHOLDER_OFFSET], offset_arguments = {4: 'awaken_bowser'})
    script.header.subroutine_table = [0] * len(script.subroutines)
    update_commands_with_offsets(fevent_manager, [script.header.post_table_subroutine, *script.subroutines], len(script.header.to_bytes(fevent_manager)))


##################################################################################
##################################################################################
##################################################################################


def cavi_cape_skips(fevent_manager):
    room_id = 0x15D
    script = fevent_manager.fevent_chunks[room_id][0]
    subroutine_num = len(script.subroutines)

    @subroutine(subs = script.subroutines, hdr = script.header)
    def fawful_fly(sub: Subroutine):
        branch_if(Variables[0xEA8F], '==', 0x1, 'fawful_dont_fly')
        Variables[0xEA8F] = 0x1
        emit_command(0x0063, [0x07, 0x01])
        emit_command(0x0064, [0x07, 0x01])
        emit_command(0x00BD, [0x07, 0x00, 0x0062, 0x0058, -0x0020])
        emit_command(0x00B2, [0x07, 0x01, 0x0258, 0x0000, 0x0000, 0x0400, 0x0000, 0x0400, 0x0400, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x07])
        emit_command(0x0063, [0x07, 0x00])
        emit_command(0x0064, [0x07, 0x00])

        label('fawful_dont_fly', manager = fevent_manager)
    
    script.header.subroutine_table = [0] * len(script.subroutines)
    for i in range(len(script.header.array5)): # update offsets in array5
        script.header.array5[i] += (len(script.subroutines) - subroutine_num) * 2
    update_commands_with_offsets(fevent_manager, [script.header.post_table_subroutine, *script.subroutines], len(script.header.to_bytes(fevent_manager)))
    
    script.header.triggers[0] = (
        script.header.triggers[0][0],
        script.header.triggers[0][1],
        script.header.triggers[0][2],
        script.header.triggers[0][3],
        script.header.triggers[0][4],
        len(script.subroutines) - 1,
        script.header.triggers[0][6],
    )
    

##################################################################################
##################################################################################
##################################################################################


def plack_beach_skips(fevent_manager):
    room_id = 0x11
    script = fevent_manager.fevent_chunks[room_id][0]
    script.subroutines[1].commands[-2].arguments = [0x003E, 0x012C, 0x01BE, 0x0000, 0x00, 0x01, 0x0050, -0x00000003, 0x01]

    # -------------------------

    room_id = 0x3d
    script = fevent_manager.fevent_chunks[room_id][0]
    subroutine_num = len(script.subroutines)
    script.subroutines.pop()
    script.header.init_subroutine = None

    cast(SubroutineExt, script.subroutines[0x05]).name = 'sub_0x5'

    @subroutine(subs = script.subroutines, hdr = script.header, init = True)
    def broque_encounter_check(sub: Subroutine): # TODO: i can get rid of this gear shit once the vacuum block cutscene is redone
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Y_POSITION, res=Variables[0x1000])
        branch_if(Variables[0x1000], '<', 150, 'bowser_is_entering') # go to normal init
        set_player_stat(Actors.BOWSER, PlayerStat.GEAR_PIECE_1, Variables[0x5000])
        set_player_stat(Actors.BOWSER, PlayerStat.GEAR_PIECE_2, Variables[0x5001])
        set_player_stat(Actors.BOWSER, PlayerStat.GEAR_PIECE_3, Variables[0x5002])
        get_player_stat(Actors.BOWSER, PlayerStat.MAX_HP, res=Variables[0x1000])
        set_player_stat(Actors.BOWSER, PlayerStat.CURRENT_HP, Variables[0x1000])
        get_player_stat(Actors.BOWSER, PlayerStat.MAX_SP, res=Variables[0x1000])
        set_player_stat(Actors.BOWSER, PlayerStat.CURRENT_SP, Variables[0x1000])
        return_()

        label('bowser_is_entering', manager = fevent_manager)
        branch_if(Variables[0xE943], '==', 0x1, 'sub_0x5') # go to normal init
        emit_command(0x011E, [0x003E, 300, 92, 0, 0x04, 0x01, 0x0050, -0x00000003, 0x01])
    
    script.header.subroutine_table = [0] * len(script.subroutines)
    for i in range(len(script.header.array5)): # update offsets in array5
        script.header.array5[i] += (len(script.subroutines) - subroutine_num) * 2
    update_commands_with_offsets(fevent_manager, [script.header.post_table_subroutine, *script.subroutines], len(script.header.to_bytes(fevent_manager)))

    # -------------------------

    room_id = 0x3e
    script = fevent_manager.fevent_chunks[room_id][0]

    cast(SubroutineExt, script.subroutines[0x05]).name = 'sub_0x5'
    cast(SubroutineExt, script.subroutines[0x0C]).name = 'sub_0xc'
    cast(SubroutineExt, script.subroutines[0x27]).name = 'sub_0x27'

    @subroutine(subs = script.subroutines, hdr = script.header)
    def broque_encounter(sub: Subroutine):
        Variables[0x1000] = 0xFFF
        branch_if(Variables[0x3008], '==', 0x1, 'broque_beach_island_0', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('broque_beach_island_0', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
        emit_command(0x0188)
        emit_command(0x01A1)
        Variables[0xEB3F] = 0x1
        emit_command(0x00F5, [0x01, 0x00, 0x01])
        emit_command(0x009A, [0x00, 0x00000047])
        emit_command(0x01A9)
        emit_command(0x0136, [0x02, 0x0000, 0x0000, 0x0001, 0x01, 0x01])
        emit_command(0x0137)
        emit_command(0x014B, [-0x10, 0x00, 0x0010])
        emit_command(0x014C)
        wait(40)
        say(0x04, 0x24147, 0x00, anim=None, post_anim=None, tail_hoffset=0xFF)
        emit_command(0x01D7, [0x00, 0x003C])
        emit_command(0x01D7, [0x01, 0x003C])
        emit_command(0x01CE, [0x0002404D, 0x02, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x00D4, [0x02, 0x00, 0x01, 0x0000, -0x0012, 0x0028, 0x00])
        wait(40)
        emit_command(0x00B5, [0x02, 0x0C, 0x0000, -0x0010, 0x0000, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x02])
        get_actor_attribute(Actors.BOWSER, 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x2 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'broque_beach_island_1', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'broque_beach_island_2', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('broque_beach_island_3')

        label('broque_beach_island_2', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('broque_beach_island_3', manager = fevent_manager)
        push(Variables[0x1001])

        label('broque_beach_island_4', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'broque_beach_island_5', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [0x02, 0x01, Variables[0x1002]])
        wait(3)
        branch('broque_beach_island_4')

        label('broque_beach_island_1', manager = fevent_manager)
        wait(3)

        label('broque_beach_island_5', manager = fevent_manager)
        wait(10)
        emit_command(0x0192, [0x00, -0x01])
        emit_command(0x0135, [0x04, 0x0000, 0x0000, 0x0800, 0x01, 0x01])
        emit_command(0x0137)
        wait(10)
        branch_in_thread(0x04, 'sub_0x27')
        wait(70)
        emit_command(0x0135, [0x02, 0x0000, 0x0000, 0x0800, 0x01, 0x01])
        emit_command(0x0137)
        emit_command(0x0192, [0x01, 0x02])
        emit_command(0x009A, [0x00, 0x00000030])
        emit_command(0x01A9)
        emit_command(0x009A, [0x01, 0x00000055])
        emit_command(0x01A9)
        wait(20)
        emit_command(0x00B5, [0x02, 0x0C, 0x0000, 0x0000, 0x0000, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x02])
        emit_command(0x01CE, [0x02000041, 0x02, 0x0000, 0x0000, 0x0001, 0x00])
        start_thread_here_and_branch(0x02, 'broque_beach_island_6')
        set_animation(Self, 0x00)
        emit_command(0x009B, [-0x01, 0x00, 0x0000, 0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        emit_command(0x0093, [-0x01])
        set_animation(Self, 0x01)
        emit_command(0x009B, [-0x01, 0x01, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        return_()

        label('broque_beach_island_6', manager = fevent_manager)
        get_actor_attribute(Actors.BOWSER, 0x0A, res=Variables[0x1000])
        Variables[0x1000] = Variables[0x1000] - 0x1
        Variables[0x1001] = Variables[0x1000] & 0xF
        Variables[0x1002] = Variables[0x1000] & 0xF0
        Variables[0x1002] = Variables[0x1002] >> 0x4
        Variables[0x1003] = Variables[0x1001] - Variables[0x1002]
        emit_command(0x0078, [0x0C, Variables[0x1003]])
        emit_command(0x00BD, [0x0C, 0x01, 0x0000, 0x0028, 0x0028])
        set_animation(0x0C, 0x00)
        emit_command(0x0091, [0x0C, -0x01, 0x0001, 0x0001, 0x01])
        emit_command(0x0094, [0x0C, 0x0000, 0x00])
        emit_command(0x0093, [0x0C])
        set_animation(0x0C, 0x01)
        emit_command(0x0091, [0x0C, -0x01, 0x0003, -0x0001, 0x01])
        emit_command(0x0094, [0x0C, 0x0000, 0x00])
        join_thread(0x02)
        wait(20)
        emit_command(0x009A, [0x00, 0x00000056])
        emit_command(0x01A9)
        say(Actors.BOWSER, Sound.SPEECH_BOWSER, 0x19, anim=None, post_anim=None, tail_hoffset=0xFF)
        wait(20)
        emit_command(0x01D4, [0x00])
        emit_command(0x01D5)
        emit_command(0x01D6, [0x00, 0x00, 0x00])
        emit_command(0x01D6, [0x01, 0x00, 0x01])
        execute_on_secondary_screen('sub_0x5', unk1=0x00)
        branch_if(Variables[0x3008], '==', 0x0, 'broque_beach_island_7', invert=True)
        Variables[0xEB0E] = 0x1

        label('broque_beach_island_8', manager = fevent_manager)
        wait(1)
        branch_if(Variables[0xEB0F], '==', 0x0, 'broque_beach_island_8')
        Variables[0xEB0F] = 0x0
        branch('broque_beach_island_9')

        label('broque_beach_island_7', manager = fevent_manager)
        wait(1)
        branch_if(Variables[0xEB0E], '==', 0x0, 'broque_beach_island_7')
        Variables[0xEB0E] = 0x0
        Variables[0xEB0F] = 0x1
        wait(1)

        label('broque_beach_island_9', manager = fevent_manager)
        wait(1)
        emit_command(0x01CD, [0x0200400E, 0x0080, 0x0060, 0x0000, 0x0000, 0x0001, 0x00])
        branch_if(Variables[0x3008], '==', 0x0, 'broque_beach_island_10', invert=True)
        Variables[0x6051] = 0xA8
        branch('broque_beach_island_11')

        label('broque_beach_island_10', manager = fevent_manager)
        Variables[0x6051] = 0x20

        label('broque_beach_island_11', manager = fevent_manager)
        start_thread_here_and_branch(0x11, 'broque_beach_island_12')
        emit_command(0x0064, [-0x01, 0x01])
        emit_command(0x00BD, [-0x01, 0x00, 0x0080, Variables[0x6051], 0x0000])
        emit_command(0x0063, [-0x01, 0x01])
        set_animation(Self, 0x01)
        emit_command(0x0091, [-0x01, -0x01, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        wait(90)
        set_animation(Self, 0x00)
        emit_command(0x0091, [-0x01, -0x01, 0x0001, 0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        emit_command(0x0093, [-0x01])
        emit_command(0x0063, [-0x01, 0x00])
        emit_command(0x0064, [-0x01, 0x00])
        return_()

        label('broque_beach_island_12', manager = fevent_manager)
        wait(45)
        Variables[0x500E] = 0x3

        # automatically determine the arm center level
        Variables[0x500D] = 0x0
        Variables[0x500D] += Variables[0xE943] # broque
        Variables[0x500D] += Variables[0xE95D] # wiggler statue
        Variables[0x500D] += Variables[0xE950] # carrot
        Variables[0x500D] += Variables[0xEBB4] # midbus

        branch_if(Variables[0x500D], '==', 0x0, 'skip_lives_feature_arm_center', invert=True)
        Variables[0xE97F] = 0x1

        label('skip_lives_feature_arm_center', manager = fevent_manager)
        Variables[0xE937] = 0x1
        Variables[0x6020] = 0x3
        wait(120)
        execute_on_secondary_screen('beach_arm_bros_alert', unk1=0x00)
        emit_command(0x0119, [0x01])
        emit_command(0x00ED, [0x00, 0x01])
        Variables[0x1000] = 0xFF0
        branch_if(Variables[0x3008], '==', 0x1, 'broque_beach_island_13', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('broque_beach_island_13', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
        Variables[0x1000] = 0xC00
        branch_if(0x1, '==', 0x1, 'broque_beach_island_14', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('broque_beach_island_14', manager = fevent_manager)
        emit_command(0x018D, [0x01, Variables[0x1000]], Variables[0x1007])
        branch_if(0x1, '==', 0x1, 'broque_beach_island_15', invert=True)
        emit_command(0x01A0)
        branch('broque_beach_island_16')

        label('broque_beach_island_15', manager = fevent_manager)
        emit_command(0x01A1)

        label('broque_beach_island_16', manager = fevent_manager)
        Variables[0xEB3F] = 0x0
        branch_in_thread(0x10, 'beach_arm_bowser_react')
        return_()

        label('beach_arm_bros_alert', manager = fevent_manager)
        emit_command(0x0135, [0x00, 0x0000, 0x0000, 0x0300, 0x01, 0x01])
        emit_command(0x0137)
    
    @subroutine(subs = script.subroutines, hdr = script.header)
    def beach_arm_bowser_react(sub: Subroutine):
        label('beach_bowser_react_loop_start', manager = fevent_manager)
        wait(1)
        branch_if(Variables[0xEB02], '==', 0x0, 'beach_bowser_react_down', invert=True)
        branch_if(Variables[0x6055], '==', Variables[0x500E], 'beach_bowser_react_up_2')
        branch_if(Variables[0x6055], '==', 0x2, 'beach_bowser_react_up_1')
        branch_if(Variables[0x6055], '==', 0x1, 'beach_bowser_react_up_0')
        branch('beach_bowser_react_loop_start', type=0x00)
        return_()


        label('beach_bowser_react_down', manager = fevent_manager)
        wait(30)
        set_animation(Actors.BOWSER, 0x01)
        emit_command(0x009B, [0x02, 0x01, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        set_animation(0x0C, 0x01)
        emit_command(0x0091, [0x0C, -0x01, 0x0003, -0x0001, 0x01])
        emit_command(0x0094, [0x0C, 0x0000, 0x00])
        wait(90)
        Variables[0xEB02] = 0x0
        branch('beach_bowser_react_loop_start', type=0x00)


        label('beach_bowser_react_up_0', manager = fevent_manager)
        branch_if(Variables[0xEB37], '==', 0x0, 'beach_bowser_react_loop_start')
        Variables[0xEB37] = 0x0
        wait(60)
        get_actor_attribute(Actors.BOWSER, ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Z_POSITION, res=Variables[0x1002])
        Variables[0x1000] = Variables[0x1000] + -0x6
        Variables[0x1001] = Variables[0x1001] + 0x0
        Variables[0x1002] = Variables[0x1002] + 0x0
        emit_command(0x0161, [0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002], 0x0100], Variables[0xA009])
        emit_command(0x01CE, [0x4000000E, 0x02, 0x0000, 0x0000, 0x0001, 0x00])
        wait(60)
        Variables[0xE93A] = 0x0
        branch('beach_bowser_react_loop_start', type=0x00)


        label('beach_bowser_react_up_1', manager = fevent_manager)
        branch_if(Variables[0xEB37], '==', 0x0, 'beach_bowser_react_loop_start')
        Variables[0xEB37] = 0x0
        wait(60)
        get_actor_attribute(Actors.BOWSER, ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Z_POSITION, res=Variables[0x1002])
        Variables[0x1000] = Variables[0x1000] + -0x6
        Variables[0x1001] = Variables[0x1001] + 0x0
        Variables[0x1002] = Variables[0x1002] + 0x0
        emit_command(0x0161, [0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002], 0x0100], Variables[0xA009])
        set_animation(Actors.BOWSER, 0x01)
        emit_command(0x009B, [0x02, 0x00, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        set_animation(0x0C, 0x01)
        emit_command(0x0091, [0x0C, -0x01, 0x0003, -0x0001, 0x01])
        emit_command(0x0094, [0x0C, 0x0000, 0x00])
        emit_command(0x01CE, [0x40000011, 0x02, 0x0000, 0x0000, 0x0001, 0x00])
        wait(60)
        Variables[0xE93A] = 0x0
        branch('beach_bowser_react_loop_start', type=0x00)

        
        label('beach_bowser_react_up_2', manager = fevent_manager)
        emit_command(0x009A, [0x01, 0x00000057])
        emit_command(0x01A9)
        branch('sub_0xc', type=0x00)

    script.header.subroutine_table = [0] * len(script.subroutines)
    update_commands_with_offsets(fevent_manager, [script.header.post_table_subroutine, *script.subroutines], len(script.header.to_bytes(fevent_manager)))

    # -------------------------

    room_id = 0x28B
    script = fevent_manager.fevent_chunks[room_id][0]
    script.subroutines.pop()
    script.subroutines.pop()
    script.subroutines.pop()
    script.header.init_subroutine = None

    script.header.triggers = [
        (0x017C00BC, 0x01800144, 0x00000000, 0x00000000, 0x00000000, 0x0000003D, 0x00020022),
        (0x008801FC, 0x00C80200, 0x00000000, 0x00000000, 0x00000000, 0x0000003E, 0x00010022),
    ]

    if fevent_manager.fevent_chunks[room_id][2].text_tables[0x44] is not None:
        fevent_manager.fevent_chunks[room_id][2].text_tables[0x44].entries[0x12] = b'\xff\x0b\x01It is I who\xff\x00nuts to that\xff\x11\x01\xff\n\x00'

    cast(SubroutineExt, script.subroutines[0x03]).name = 'sub_0x3'
    cast(SubroutineExt, script.subroutines[0x04]).name = 'sub_0x4'
    
    @subroutine(subs = script.subroutines, hdr = script.header)
    def sea_pipe_south_exit(sub: Subroutine):
        branch_if(Variables[0x3019], '==', 0x0, 'sea_pipe_south_exit_0', invert=True)
        emit_command(0x0114, [0x00])
        branch('sea_pipe_south_exit_0')

        label('sea_pipe_south_exit_0', manager = fevent_manager)
        Variables[0xEB00] = 0x0
        Variables[0xEB39] = 0x0
        Variables[0x1000] = 0xFFF
        branch_if(Variables[0x3008], '==', 0x1, 'sea_pipe_south_exit_1', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('sea_pipe_south_exit_1', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
        branch_if(0x0, '==', 0x1, 'sea_pipe_south_exit_2', invert=True)
        emit_command(0x01A0)
        branch('sea_pipe_south_exit_3')

        label('sea_pipe_south_exit_2', manager = fevent_manager)
        emit_command(0x01A1)

        label('sea_pipe_south_exit_3', manager = fevent_manager)
        emit_command(0x014B, [0x7F, -0x10, 0x0010])
        branch_if(Variables[0x3000], '==', 0x2, 'sea_pipe_south_exit_4', invert=True)
        branch_if(Variables[0x300A], '!=', 0x1B, 'sea_pipe_south_exit_4', invert=True)
        Variables[0xEB6D] = 0x1
        emit_command(0x0119, [0x01])

        label('sea_pipe_south_exit_5', manager = fevent_manager)
        wait(1)
        branch_if(Variables[0xE8EF], '==', 0x1, 'sea_pipe_south_exit_5')
        emit_command(0x0119, [0x00])

        label('sea_pipe_south_exit_4', manager = fevent_manager)
        Variables[0x1000] = 0x0
        branch_if(Variables[0x3008], '==', 0x1, 'sea_pipe_south_exit_6', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('sea_pipe_south_exit_6', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
        emit_command(0x011E, [0x0154, 0x0100, 0x003C, 0x0000, 0x04, 0x01, -0x0001, -0x00000003, 0x01])

    @subroutine(subs = script.subroutines, hdr = script.header)
    def sea_pipe_east_exit(sub: Subroutine):
        branch_if(Variables[0x3019], '==', 0x0, 'sea_pipe_east_exit_0', invert=True)
        emit_command(0x0114, [0x00])
        branch('sea_pipe_east_exit_0')

        label('sea_pipe_east_exit_0', manager = fevent_manager)
        Variables[0xEB00] = 0x0
        Variables[0xEB39] = 0x0
        Variables[0x1000] = 0xFFF
        branch_if(Variables[0x3008], '==', 0x1, 'sea_pipe_east_exit_1', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('sea_pipe_east_exit_1', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
        branch_if(0x0, '==', 0x1, 'sea_pipe_east_exit_2', invert=True)
        emit_command(0x01A0)
        branch('sea_pipe_east_exit_3')

        label('sea_pipe_east_exit_2', manager = fevent_manager)
        emit_command(0x01A1)

        label('sea_pipe_east_exit_3', manager = fevent_manager)
        emit_command(0x014B, [0x7F, -0x10, 0x0010])
        branch_if(Variables[0x3000], '==', 0x2, 'sea_pipe_east_exit_4', invert=True)
        branch_if(Variables[0x300A], '!=', 0x1B, 'sea_pipe_east_exit_4', invert=True)
        Variables[0xEB6D] = 0x1
        emit_command(0x0119, [0x01])

        label('sea_pipe_east_exit_5', manager = fevent_manager)
        wait(1)
        branch_if(Variables[0xE8EF], '==', 0x1, 'sea_pipe_east_exit_5')
        emit_command(0x0119, [0x00])

        label('sea_pipe_east_exit_4', manager = fevent_manager)
        Variables[0x1000] = 0x0
        branch_if(Variables[0x3008], '==', 0x1, 'sea_pipe_east_exit_6', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('sea_pipe_east_exit_6', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
        emit_command(0x011E, [0x0035, 0x001E, 0x0180, 0x0000, 0x02, 0x01, -0x0001, -0x00000003, 0x01])

    @subroutine(subs = script.subroutines, hdr = script.header, init = True)
    def sea_pipe_encounter(sub: Subroutine):
        branch_if(Variables[0x200E], '==', 0x0, 'sea_pipe_encounter', invert=True)
        Variables[0x1000] = 0xFFF
        branch_if(Variables[0x3008], '==', 0x1, 'sea_pipe_no_encounter_0', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('sea_pipe_no_encounter_0', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0xA000])
        emit_command(0x0188)
        emit_command(0x014B, [-0x10, 0x00, 0x0010])
        emit_command(0x014C)
        Variables[0x1000] = 0
        branch_if(Variables[0x3008], '==', 0x1, 'sea_pipe_no_encounter_1', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('sea_pipe_no_encounter_1', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
        return_()

        label('sea_pipe_encounter', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], 0x0FFF], Variables[0x1007])
        branch_if(Variables[0x3019], '==', 0x0, 'sea_pipe_encounter_0', invert=True)
        emit_command(0x00F5, [0x00, 0x00, 0x01])
        branch('sea_pipe_encounter_1')

        label('sea_pipe_encounter_0', manager = fevent_manager)
        branch_if(Variables[0x3008], '==', 0x0, 'sea_pipe_encounter_2', invert=True)
        emit_command(0x00F5, [0x01, 0x00, 0x01])
        branch('sea_pipe_encounter_1')

        label('sea_pipe_encounter_2', manager = fevent_manager)
        emit_command(0x00F5, [0x00, 0x00, 0x01])

        label('sea_pipe_encounter_1', manager = fevent_manager)
        emit_command(0x0188)
        branch_if(0x0, '==', 0x1, 'sea_pipe_encounter_3', invert=True)
        emit_command(0x01A0)
        branch('sea_pipe_encounter_4')

        label('sea_pipe_encounter_3', manager = fevent_manager)
        emit_command(0x01A1)

        label('sea_pipe_encounter_4', manager = fevent_manager)
        Variables[0xEB00] = 0x1
        emit_command(0x014B, [-0x10, 0x00, 0x0010])
        emit_command(0x01D7, [0x00, 0x003C])
        emit_command(0x01D7, [0x01, 0x003C])
        get_actor_attribute(0x04, ActorAttribute.X_POSITION, res=Variables[0xA00A])
        get_actor_attribute(0x04, ActorAttribute.Y_POSITION, res=Variables[0xA00B])
        get_actor_attribute(0x04, ActorAttribute.Z_POSITION, res=Variables[0xA00C])
        emit_command(0x01CE, [0x000200B9, 0x04, 0x0000, 0x0000, 0x0001, 0x00])
        branch_in_thread(0x04, 'sub_0x4')
        emit_command(0x014C)
        wait(40)
        emit_command(0x01CE, [0x0002404E, 0x02, 0x0000, 0x0000, 0x0001, 0x00])
        
        get_actor_attribute(Actors.BOWSER, 0x0E, res=Variables[0x1000])
        branch_if(Variables[0x1000], '==', 0x0, 'sea_pipe_question_bubble_0', invert=True)
        Variables[0x1001] = 0x0
        Variables[0x1002] = -0x12
        branch('sea_pipe_question_bubble_1', type=0x00)

        label('sea_pipe_question_bubble_0', manager = fevent_manager)
        Variables[0x1001] = -0x10
        Variables[0x1002] = -0xE

        label('sea_pipe_question_bubble_1', manager = fevent_manager)
        emit_command(0x00D4, [0x02, 0x01, 0x01, Variables[0x1001], Variables[0x1002], 0x002D, 0x00])
        emit_command(0x00D6, [0x02])
        emit_command(0x0192, [0x00, Variables[0x3000]])
        emit_command(0x0133, [0x00, 0x0080, 0x0040, 0x0300, 0x0000, 0x0300, 0x0300, 0x01, 0x01])
        emit_command(0x00B2, [0x02, 0x00, 0x0100, 0x00D4, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x02])

        get_actor_attribute(Actors.BOWSER, 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x0 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'sea_pipe_bowser_turn_0', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'sea_pipe_bowser_turn_1', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('sea_pipe_bowser_turn_2')

        label('sea_pipe_bowser_turn_1', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('sea_pipe_bowser_turn_2', manager = fevent_manager)
        push(Variables[0x1001])

        label('sea_pipe_bowser_turn_4', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'sea_pipe_bowser_turn_3', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [0x02, 0x01, Variables[0x1002]])
        wait(3)
        branch('sea_pipe_bowser_turn_4')

        label('sea_pipe_bowser_turn_3', manager = fevent_manager)
        branch('sea_pipe_bowser_turn_5')

        label('sea_pipe_bowser_turn_0', manager = fevent_manager)
        wait(3)

        label('sea_pipe_bowser_turn_5', manager = fevent_manager)

        wait(20)
        emit_command(0x00D4, [0x02, 0x03, 0x01, 0x0000, -0x0012, 0x005A, 0x00])
        wait(90)
        emit_command(0x0133, [0x00, 0x0080, 0x0028, 0x0100, 0x0000, 0x0100, 0x0100, 0x01, 0x01])
        emit_command(0x0137)
        wait(30)
        emit_command(0x01CD, [0x00020039, 0x0080, 0x0060, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x0161, [0x01, 0x0100, 0x00A4, 0x0000, 0x0100], Variables[0xA000])
        emit_command(0x016A, [Variables[0xA000]])
        emit_command(0x01CE, [0x0002404D, 0x02, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x00D4, [0x02, 0x00, 0x01, 0x0000, -0x0012, 0x0028, 0x00])
        wait(40)
        set_animation(Actors.BOWSER, 0x02)
        emit_command(0x00B2, [0x02, 0x01, 0x0000, 0x0018, 0x0000, 0x0100, 0x0000, 0x0100, 0x0100, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x02])
        set_animation(Actors.BOWSER, 0x01)
        emit_command(0x0091, [0x02, 0x01, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        set_animation(Actors.BOWSER, 0x03)
        wait(20)
        emit_command(0x004E, [0x04])
        emit_command(0x00BD, [0x04, 0x00, Variables[0xA00A], Variables[0xA00B], Variables[0xA00C]])
        emit_command(0x01CF, [0x000200B9])
        wait(50)


        # nuts to that
        branch_if(Variables[0x302B], '==', 0x1, 'doesnt_nut', invert=True)
        random_below(1000, Variables[0x1000])
        branch_if(Variables[0x1000], '==', 0x0, 'doesnt_nut', invert=True)
        branch_in_thread(0x02, 'sub_0x3')
        emit_command(0x00BD, [0x05, 0x00, 0x0028, 0x0008, 0x0030])
        emit_command(0x0063, [0x05, 0x01])
        emit_command(0x0064, [0x05, 0x01])
        emit_command(0x00D7, [0x05, 0x00])
        branch_if(0x5, '==', 0xFF, 'nuts_to_that_0', invert=True)
        emit_command(0x0192, [0x00, -0x01])
        branch('nuts_to_that_1')

        label('nuts_to_that_0', manager = fevent_manager)
        emit_command(0x0192, [0x01, 0x05])

        label('nuts_to_that_1', manager = fevent_manager)
        emit_command(0x01CE, [0x000200B1, 0x05, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x00B2, [0x05, 0x00, 0x00D0, 0x0060, 0x0030, 0x0300, 0x0000, 0x0300, 0x0300, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x05])
        emit_command(0x00B2, [0x05, 0x00, 0x0128, 0x0078, 0x0030, 0x0300, 0x0000, 0x0300, 0x0300, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x05])
        emit_command(0x0192, [0x00, Variables[0x3000]])
        emit_command(0x0133, [0x00, 0x00C0, 0x0060, 0x0300, 0x0000, 0x0300, 0x0300, 0x01, 0x01])
        emit_command(0x00B2, [0x05, 0x00, 0x0168, 0x00B0, 0x0030, 0x0300, 0x0000, 0x0300, 0x0300, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x05])
        emit_command(0x00B2, [0x05, 0x00, 0x0180, 0x00D8, 0x0030, 0x0300, 0x0000, 0x0300, 0x0300, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x05])
        emit_command(0x01CF, [0x000200B1])
        emit_command(0x00D1, [0x05, 0x00, 0x05])
        wait(30)
        emit_command(0x004E, [0x02])
        emit_command(0x00D7, [0x05, 0x01])
        emit_command(0x01CE, [0x000240B2, 0x05, 0x0000, 0x0000, 0x0001, 0x00])
        set_animation(0x05, 0x00)
        emit_command(0x0091, [0x05, -0x01, 0x0009, 0x0001, 0x01])
        emit_command(0x0094, [0x05, 0x0000, 0x00])
        emit_command(0x0093, [0x05])
        set_animation(0x05, 0x01)
        emit_command(0x0091, [0x05, -0x01, 0x000B, -0x0001, 0x01])
        emit_command(0x0094, [0x05, 0x0000, 0x00])
        get_actor_attribute(0x05, 0x11, res=Variables[0x1000])
        get_actor_attribute(0x05, 0x12, res=Variables[0x1001])
        branch_if(-0xA8, '<', -0x10, 'nuts_to_that_2', invert=True)
        Variables[0x1002] = 0xA8
        branch('nuts_to_that_3')

        label('nuts_to_that_2', manager = fevent_manager)
        Variables[0x1002] = 0x10

        label('nuts_to_that_3', manager = fevent_manager)
        Variables[0x1000] = Variables[0x1000] + -0xA8
        emit_command(0x01C6, [0x12, 0x00], Variables[0x1007])
        Variables[0x1007] = Variables[0x1007] * 0x8
        Variables[0x1003] = Variables[0x1000] + Variables[0x1007]
        branch_if(Variables[0x1003], '>', 0xFE, 'nuts_to_that_4', invert=True)
        Variables[0x1006] = Variables[0x1003] - 0xFE
        Variables[0x1000] = Variables[0x1000] - Variables[0x1006]
        Variables[0x1002] = Variables[0x1002] + Variables[0x1006]

        label('nuts_to_that_4', manager = fevent_manager)
        Variables[0x1007] = Variables[0x1007] - 0x14
        Variables[0x1006] = Variables[0x1002] - Variables[0x1007]
        branch_if(Variables[0x1006], '>', 0x0, 'nuts_to_that_5', invert=True)
        Variables[0x1000] = Variables[0x1000] + Variables[0x1006]
        Variables[0x1002] = Variables[0x1002] - Variables[0x1006]

        label('nuts_to_that_5', manager = fevent_manager)
        Variables[0x1001] = Variables[0x1001] + 0x2A
        say((Variables[0x1000], Variables[0x1001]), 0x2014D, 0x12, hoffsets_arg=Variables[0x1002])
        branch_in_thread(0x02, 'sub_0x3')
        set_animation(0x05, 0x01)
        emit_command(0x0091, [0x05, -0x01, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x05, 0x0000, 0x00])
        set_animation(0x05, 0x03)
        emit_command(0x01CE, [0x000200B1, 0x05, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x00B2, [0x05, 0x00, 0x0168, 0x00B0, 0x0030, 0x0002, 0x000C, 0x0300, 0x0300, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x05])
        emit_command(0x00B2, [0x05, 0x00, 0x0040, 0x0000, 0x0030, 0x0300, 0x0000, 0x0300, 0x0300, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x05])
        emit_command(0x01CF, [0x000200B1])
        emit_command(0x0063, [0x05, 0x00])
        emit_command(0x0064, [0x05, 0x00])
        emit_command(0x004E, [0x02])
        emit_command(0x0133, [0x00, 0x0080, 0x0028, 0x0100, 0x0000, 0x0300, 0x0300, 0x01, 0x01])
        emit_command(0x0137)
        wait(10)


        label('doesnt_nut', manager = fevent_manager)
        emit_command(0x00D1, [0x02, 0x00, 0x00])
        set_animation(0x04, 0x00)
        emit_command(0x0091, [0x04, -0x01, 0x0005, 0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        emit_command(0x0093, [0x04])
        emit_command(0x01CE, [0x00020038, 0x04, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x01CE, [0x00020038, 0x04, 0x0028, 0x0000, 0x0001, 0x00])
        set_animation(0x04, 0x00)
        emit_command(0x0091, [0x04, -0x01, 0x0001, 0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        wait(62)
        emit_command(0x01CE, [0x000200B9, 0x04, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x013F, [0x00000016, 0x0052, 0x0300, 0x00, 0x03, 0x00])
        emit_command(0x0140)
        emit_command(0x01CF, [0x000200B9])
        wait(10)
        emit_command(0x01CE, [0x000200B7, 0x04, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x013F, [0x00000016, 0x001D, 0x0400, 0x00, 0x03, 0x00])
        emit_command(0x0140)
        emit_command(0x0093, [0x04])
        set_animation(0x04, 0x01)
        emit_command(0x0091, [0x04, -0x01, 0x0002, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        wait(30)
        emit_command(0x01CE, [0x000200B8, 0x04, 0x0000, 0x0000, 0x0001, 0x00])
        set_animation(0x04, 0x01)
        emit_command(0x0091, [0x04, -0x01, 0x0003, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        wait(40)
        emit_command(0x009A, [0x00, 0x00000049])
        emit_command(0x01A9)
        emit_command(0x00B2, [0x02, 0x01, 0x0000, -0x0028, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x02])
        set_animation(Actors.BOWSER, 0x00)
        emit_command(0x009B, [0x02, 0x00, 0x0000, 0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        emit_command(0x0093, [0x02])
        emit_command(0x01CF, [0x000200B8])
        emit_command(0x01CF, [0x000200B9])
        emit_command(0x004E, [0x04])
        emit_command(0x0195, [0x1018, 0x00, 0x0001, 0x04, 0x01, 0x00, 0x06, 0x00])
        emit_command(0x01D7, [0x00, 0x0000])
        emit_command(0x01D7, [0x01, 0x0000])
        emit_command(0x011E, [0x001A, 0x0000, 0x0000, 0x0000, 0x00, 0x00, 0x0068, 0x00000000, 0x01])

    script.header.subroutine_table = [0] * len(script.subroutines)
    update_commands_with_offsets(fevent_manager, [script.header.post_table_subroutine, *script.subroutines], len(script.header.to_bytes(fevent_manager)))

    # -------------------------

    fevent_manager.fevent_chunks[0x154][0].subroutines[0].commands[10].arguments[0] = 0x1A

    # -------------------------

    room_id = 0x1A
    script = fevent_manager.fevent_chunks[room_id][0]
    script.subroutines.pop()
    script.header.init_subroutine = None

    cast(SubroutineExt, script.subroutines[0x00]).name = 'sub_0x0'
    cast(SubroutineExt, script.subroutines[0x05]).name = 'sub_0x5'

    @subroutine(subs = script.subroutines, hdr = script.header, init = True)
    def sea_pipe_encounter_cont(sub: Subroutine):
        branch_if(Variables[0x200E], '==', 0x0, 'send_to_inactive') # if player doesn't have the vacuum block: the room should be vacant
        branch_if(Variables[0x901F], '!=', 0x0, 'normal_behavior') # if player is already in the room: do normal shit
        Variables[0x1000] = 1 - Variables[0xEB8C]
        Variables[0x1000] = Variables[0x1000] + Variables[0xEB00] # if player hasn't finished sea pipe cutscene AND has already been in the room: finish sea pipe
        branch_if(Variables[0x1000], '==', 0x2, 'sea_pipe_encounter_cont')
        branch_if(Variables[0xEB8C], '==', 0x1, 'sub_0x0') # if the player has already defeated the sea pipe statue: the room should be initialized normally

        # otherwise, send the player to the inactive sea pipe room
        label('send_to_inactive', manager = fevent_manager)
        get_actor_attribute(Actors.BOWSER, ActorAttribute.X_POSITION, res=Variables[0x1000])
        branch_if(Variables[0x1000], '>', 400, 'other_entrance', invert=True)
        emit_command(0x011E, [0x028B, 482, 168, 0, 0x06, 0x01, -0x0001, -0x00000003, 0x01])
        return_()
        label('other_entrance', manager = fevent_manager)
        emit_command(0x011E, [0x028B, 256, 364, 0, 0x00, 0x01, -0x0001, -0x00000003, 0x01])
        return_()


        label('normal_behavior', manager = fevent_manager)
        branch_if(Variables[0xEB00], '==', 0x0, 'sub_0x0') # if player is entering the room with a stale 901F: the room should be initialized normally
        emit_command(0x0063, [0x1B, 0x00])
        emit_command(0x0064, [0x1B, 0x00])
        emit_command(0x0063, [0x1C, 0x00])
        emit_command(0x0064, [0x1C, 0x00])
        return_()


        label('sea_pipe_encounter_cont', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], 0x0FFF], Variables[0x1007])
        branch_if(Variables[0x3019], '==', 0x0, 'sea_pipe_encounter_cont_0', invert=True)
        emit_command(0x00F5, [0x00, 0x00, 0x01])
        branch('sea_pipe_encounter_cont_1')

        label('sea_pipe_encounter_cont_0', manager = fevent_manager)
        branch_if(Variables[0x3008], '==', 0x0, 'sea_pipe_encounter_cont_2', invert=True)
        emit_command(0x00F5, [0x01, 0x00, 0x01])
        branch('sea_pipe_encounter_cont_1')

        label('sea_pipe_encounter_cont_2', manager = fevent_manager)
        emit_command(0x00F5, [0x00, 0x00, 0x01])

        label('sea_pipe_encounter_cont_1', manager = fevent_manager)
        emit_command(0x0188)
        branch_if(0x0, '==', 0x1, 'sea_pipe_encounter_cont_3', invert=True)
        emit_command(0x01A0)
        branch('sea_pipe_encounter_cont_4')

        label('sea_pipe_encounter_cont_3', manager = fevent_manager)
        emit_command(0x01A1)

        label('sea_pipe_encounter_cont_4', manager = fevent_manager)
        emit_command(0x0063, [0x0B, 0x00])
        emit_command(0x0064, [0x0B, 0x00])
        emit_command(0x0063, [0x0D, 0x00])
        emit_command(0x0064, [0x0D, 0x00])
        emit_command(0x0063, [0x0F, 0x00])
        emit_command(0x0064, [0x0F, 0x00])
        emit_command(0x0063, [0x11, 0x00])
        emit_command(0x0064, [0x11, 0x00])
        emit_command(0x0063, [0x0C, 0x00])
        emit_command(0x0064, [0x0C, 0x00])
        emit_command(0x0063, [0x0E, 0x00])
        emit_command(0x0064, [0x0E, 0x00])
        emit_command(0x0063, [0x10, 0x00])
        emit_command(0x0064, [0x10, 0x00])
        emit_command(0x0063, [0x12, 0x00])
        emit_command(0x0064, [0x12, 0x00])
        emit_command(0x0063, [0x06, 0x00])
        emit_command(0x0064, [0x06, 0x00])
        emit_command(0x0063, [0x07, 0x00])
        emit_command(0x0064, [0x07, 0x00])
        emit_command(0x0134, [0x00, 0x0080, 0x0040, 0x0001, 0x01, 0x01])
        emit_command(0x0137)
        emit_command(0x00BD, [0x02, 0x00, 0x0100, 0x00E0, 0x0000])
        set_animation(Actors.BOWSER, 0x01)
        emit_command(0x0091, [0x02, 0x06, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        set_animation(Actors.BOWSER, 0x03)
        emit_command(0x00D1, [0x02, 0x00, 0x00])
        set_animation(0x05, 0x01)
        emit_command(0x0091, [0x05, -0x01, 0x0002, -0x0001, 0x01])
        emit_command(0x0094, [0x05, 0x0000, 0x00])
        emit_command(0x005F, [0x00, 0x001B0034])
        emit_command(0x014B, [-0x10, 0x00, 0x0010])
        emit_command(0x014C)
        wait(40)
        emit_command(0x007E, [0x05, 0x0100])
        emit_command(0x01CE, [0x000200B7, 0x05, 0x0000, 0x0000, 0x0001, 0x00])
        set_animation(0x05, 0x00)
        emit_command(0x0091, [0x05, -0x01, 0x0004, 0x0001, 0x01])
        emit_command(0x0094, [0x05, 0x0000, 0x00])
        emit_command(0x0093, [0x05])
        set_animation(0x05, 0x00)
        emit_command(0x0091, [0x05, -0x01, 0x0006, 0x0001, 0x01])
        emit_command(0x0094, [0x05, 0x0000, 0x00])
        emit_command(0x0093, [0x05])
        set_animation(0x05, 0x01)
        emit_command(0x0091, [0x05, -0x01, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x05, 0x0000, 0x00])
        wait(60)
        emit_command(0x01CE, [0x00020039, 0x05, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x0161, [0x00, 0x0100, 0x00A4, 0x0000, 0x0100], Variables[0xA000])
        emit_command(0x016A, [Variables[0xA000]])
        wait(60)
        emit_command(0x01CE, [0x00020079, 0x05, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x0161, [0x01, 0x0100, 0x00A0, 0x0000, 0x0100], Variables[0xA000])
        emit_command(0x016A, [Variables[0xA000]])
        wait(30)
        emit_command(0x01CE, [0x04024009, 0x05, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x0063, [0x07, 0x01])
        emit_command(0x0064, [0x07, 0x01])
        emit_command(0x0063, [0x06, 0x01])
        emit_command(0x0064, [0x06, 0x01])
        set_animation(0x07, 0x00)
        emit_command(0x0091, [0x07, -0x01, 0x0002, 0x0001, 0x01])
        emit_command(0x0094, [0x07, 0x0000, 0x00])
        set_animation(0x06, 0x00)
        emit_command(0x0091, [0x06, -0x01, 0x0003, 0x0001, 0x01])
        emit_command(0x0094, [0x06, 0x0000, 0x00])
        emit_command(0x0093, [0x06])
        set_animation(0x07, 0x01)
        emit_command(0x0091, [0x07, -0x01, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x07, 0x0000, 0x00])
        set_animation(0x06, 0x01)
        emit_command(0x0091, [0x06, -0x01, 0x0001, -0x0001, 0x01])
        emit_command(0x0094, [0x06, 0x0000, 0x00])
        wait(60)
        emit_command(0x01D4, [0x00])
        emit_command(0x01D5)
        emit_command(0x01D6, [0x00, 0x00, 0x00])
        emit_command(0x01D6, [0x01, 0x00, 0x01])

        emit_command(0x01A0)
        Variables[0x1000] = 0x0
        branch_if(Variables[0x3008], '==', 0x1, 'sea_pipe_encounter_cont_5', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('sea_pipe_encounter_cont_5', manager = fevent_manager)
        emit_command(0x0135, [0x02, 0x0000, 0x0000, 0x0300, 0x01, 0x01])
        emit_command(0x0137)
        emit_command(0x0192, [0x01, Variables[0x3000]])
        emit_command(0x00F5, [0x01, 0x01, 0x00])
        Variables[0xEB8C] = 1
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])

    script.header.subroutine_table = [0] * len(script.subroutines)
    update_commands_with_offsets(fevent_manager, [script.header.post_table_subroutine, *script.subroutines], len(script.header.to_bytes(fevent_manager)))

    # -------------------------

    room_id = 0x35
    script = fevent_manager.fevent_chunks[room_id][0]

    # this literally just hides the trees in the post-sea-pipe room bc the game already does that but only when you're playing as the bros
    for command in [5, 12, 15, 19, 23]:
        script.subroutines[0x35].commands[command].arguments[4] = 0


##################################################################################
##################################################################################
##################################################################################


def pump_works_skips(fevent_manager):
    pass
    

##################################################################################
##################################################################################
##################################################################################


def flame_pipe_skips(fevent_manager):
    pass
    

##################################################################################
##################################################################################
##################################################################################


def dimble_wood_skips(fevent_manager):
    room_id = 0x33
    script = fevent_manager.fevent_chunks[room_id][0]

    # prevent the game from overwriting your ability state
    script.subroutines[0].commands[3].arguments[0] = Variables[0x2000]
    script.subroutines[0].commands[4].arguments[0] = Variables[0x2001]

    # -------------------------

    room_id = 0x49
    script = fevent_manager.fevent_chunks[room_id][0]

    # prevent the game from overwriting your ability state
    script.subroutines[0].commands[0].arguments[0] = Variables[0x2000]
    script.subroutines[0].commands[1].arguments[0] = Variables[0x2001]