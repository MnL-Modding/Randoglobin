from mnllib import *
from mnllib.bis import *
from mnlscript import label, return_, CodeCommandWithOffsets, update_commands_with_offsets, SubroutineExt

import importlib
import mnlscript.bis.text
mnlscript.bis.text.TT = None

import mnlscript.bis
importlib.reload(mnlscript.bis)

from mnlscript.bis import Variables, Actors, StackTopModification, StackPopCondition, Sound
from mnlscript.bis.commands import *

from typing import cast
from copy import deepcopy
import mnlscript
import functools
import inspect

from randoglobin.treasure import get_meswin_size

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


def create_blitty_hiding_spot(fevent_manager, room_id, coords, blitty_flag, key_menu_flag, blitty_object, init_sub_id, text_entries, text_sizes):
    script = fevent_manager.fevent_chunks[room_id][1]

    if fevent_manager.fevent_chunks[room_id][2] is None:
        fevent_manager.fevent_chunks[room_id] = ( # nab a working text table from a different room
            fevent_manager.fevent_chunks[room_id][0],
            fevent_manager.fevent_chunks[room_id][1],
            deepcopy(fevent_manager.fevent_chunks[0x21D][2]),
        )

        for j in range(6):
            if not fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + j]:
                continue
            
            fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + j].entries[0] = text_entries[j]
            fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + j].textbox_sizes[0] = text_sizes[j]
    else:
        for j in range(6):
            if not fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + j]:
                continue
            
            fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + j].entries.append(text_entries[j])
            fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + j].textbox_sizes.append(text_sizes[j])

    fevent_manager.fevent_chunks[room_id][2].text_tables[FEVENT_PADDING_TEXT_TABLE_ID] = b""
    language_table_size = len(fevent_manager.fevent_chunks[room_id][2].to_bytes())
    fevent_manager.fevent_chunks[room_id][2].text_tables[FEVENT_PADDING_TEXT_TABLE_ID] = (
        b"\x00"
        * (
            (-(language_table_size + 1) % LANGUAGE_TABLE_ALIGNMENT)
            + 1
        )
    )
    
    blitty_actor = ( # this isn't readable but fuck it, actors are tough rn
        coords[0] + (coords[1] << 16),
        coords[2],
        0x00000000,
        0x0001 + (blitty_flag << 16),
        0x014821C3 # these properties are a bit fucked, once these are understood they probably need to be fixed
    )

    bowser_actor = (0x00000000, 0x00000000, 0xFFFF0104, 0xFFFFFFFF, 0x003AB000) # stolen from the conference scene

    bounding_box = [None, None, None, None]
    for command in script.subroutines[init_sub_id].commands:
        if command.command_id == 0x0008:
            coord = command.arguments[0]
            if coord < 0: coord &= 0x7fff # this is what the game does so whatever lol
            bounding_box[command.result_variable.number - 0xA00C] = coord

    script.header.sprite_groups = [blitty_object, 0x01000318, 0x0000003D]
    script.header.palettes = [0x0100019F, 0x00000000]
    script.header.actors = [blitty_actor, bowser_actor]
    script.subroutines = []

    @subroutine(subs = script.subroutines, hdr = script.header)
    def blitty_init(sub: Subroutine):
        if bounding_box != [None, None, None, None]:
            branch_if(Variables[0x200E], '==', 0x0, 'hide_blitty') # if vacuum block isn't acquired, hide the blitty and abort
            set_animation(Self, 0x01)
            wait(3)
            emit_command(0x01CE, [0x20020210, Variables[0x3000], 0x0000, 0x0000, 0x0001, 0x00])
            Variables[0xA00C] = bounding_box[0]
            Variables[0xA00D] = bounding_box[1]
            Variables[0xA00E] = bounding_box[2]
            Variables[0xA00F] = bounding_box[3]

            emit_command(0x00DB, [-0x01, 0x01])
            get_actor_attribute(Variables[0x3006], ActorAttribute.X_POSITION, res=Variables[0xA00A])
            get_actor_attribute(Variables[0x3006], ActorAttribute.Y_POSITION, res=Variables[0xA00B])
            Variables[0xA009] = -0x2
            set_animation(Self, 0x04)

            label('blitty_pathfind_start', manager = fevent_manager)
            branch_if(Variables[blitty_flag], '==', 0x1, 'kill_blitty')
            wait(1)
            get_actor_attribute(Variables[0x3000], ActorAttribute.X_POSITION, res=Variables[0x1000])
            get_actor_attribute(Variables[0x3006], ActorAttribute.X_POSITION, res=Variables[0x1001])
            Variables[0xA001] = Variables[0x1000] - Variables[0x1001]
            get_actor_attribute(Variables[0x3000], ActorAttribute.Y_POSITION, res=Variables[0x1001])
            get_actor_attribute(Variables[0x3006], ActorAttribute.Y_POSITION, res=Variables[0x1002])
            Variables[0xA002] = Variables[0x1001] - Variables[0x1002]
            Variables[0x1000] = Variables[0xA001] * Variables[0xA001]
            Variables[0x1001] = Variables[0xA002] * Variables[0xA002]
            Variables[0x1002] = Variables[0x1000] + Variables[0x1001]
            fx_sqrt(Variables[0x1002], Variables[0x1000])
            Variables[0xA000] = Variables[0x1000] >> 0x6
            branch_if(Variables[0xA000], '<=', 0x60, 'blitty_pathfind_within_range')
            branch_if(Variables[0xB000], '==', 0x1, 'blitty_pathfind_start', invert=True)

            Variables[0xB000] = 0x0
            emit_command(0x007E, [-0x01, 0x0100])
            set_animation(Self, 0x04)
            wait(60)
            Variables[0xA009] = -0x2
            emit_command(0x01CE, [0x20020210, Variables[0x3006], 0x0000, 0x0000, 0x0001, 0x00])
            set_animation(-0x01, 0x01)
            emit_command(0x0091, [-0x01, 0x00, 0x0000, -0x0001, 0x01])
            emit_command(0x0094, [-0x01, 0x0000, 0x00])
            branch('blitty_pathfind_start', type=0x00)

            label('blitty_pathfind_within_range', manager = fevent_manager)
            branch_if(Variables[0xB000], '==', 0x0, 'blitty_pathfind_try_move', invert=True)
            emit_command(0x007E, [-0x01, 0x0200])
            emit_command(0x01CE, [0x20020210, Variables[0x3006], 0x0000, 0x0000, 0x0001, 0x00])
            set_animation(-0x01, 0x01)
            emit_command(0x0091, [-0x01, 0x01, -0x0001, -0x0001, 0x01])
            emit_command(0x0094, [-0x01, 0x0000, 0x00])
            Variables[0xB000] = 0x1

            label('blitty_pathfind_try_move', manager = fevent_manager)
            Variables[0xA001] = Variables[0xA001] * Variables[0xA009]
            Variables[0xA002] = Variables[0xA002] * Variables[0xA009]
            get_actor_attribute(Variables[0x3006], ActorAttribute.X_POSITION, res=Variables[0xA00A])
            get_actor_attribute(Variables[0x3006], ActorAttribute.Y_POSITION, res=Variables[0xA00B])
            Variables[0xA001] = Variables[0xA001] + Variables[0xA00A]
            Variables[0xA002] = Variables[0xA002] + Variables[0xA00B]
            branch_if(Variables[0xA001], '<', Variables[0xA00C], 'blitty_pathfind_bound_check_1', invert=True)
            Variables[0xA001] = Variables[0xA00C]
            branch('blitty_pathfind_bound_check_2')

            label('blitty_pathfind_bound_check_1', manager = fevent_manager)
            branch_if(Variables[0xA001], '>', Variables[0xA00E], 'blitty_pathfind_bound_check_2', invert=True)
            Variables[0xA001] = Variables[0xA00E]

            label('blitty_pathfind_bound_check_2', manager = fevent_manager)
            branch_if(Variables[0xA002], '<', Variables[0xA00D], 'blitty_pathfind_bound_check_3', invert=True)
            Variables[0xA002] = Variables[0xA00D]
            branch('blitty_pathfind_move')

            label('blitty_pathfind_bound_check_3', manager = fevent_manager)
            branch_if(Variables[0xA002], '>', Variables[0xA00F], 'blitty_pathfind_move', invert=True)
            Variables[0xA002] = Variables[0xA00F]

            label('blitty_pathfind_move', manager = fevent_manager)
            get_actor_attribute(Variables[0x3000], ActorAttribute.X_POSITION, res=Variables[0x1000])
            get_actor_attribute(Variables[0x3006], ActorAttribute.X_POSITION, res=Variables[0x1001])
            Variables[0xA006] = Variables[0x1000] - Variables[0x1001]
            get_actor_attribute(Variables[0x3000], ActorAttribute.Y_POSITION, res=Variables[0x1001])
            get_actor_attribute(Variables[0x3006], ActorAttribute.Y_POSITION, res=Variables[0x1002])
            Variables[0xA007] = Variables[0x1001] - Variables[0x1002]

            atan2(Variables[0xA007], Variables[0xA006], Variables[0x1002])
            Variables[0x1002] = Variables[0x1002] + 0x1D9
            Variables[0x1002] = Variables[0x1002] // 0x2D
            Variables[0x1002] = Variables[0x1002] & 0x7

            set_animation(-0x01, 0x01)
            emit_command(0x0091, [-0x01, -0x01, Variables[0x1002], -0x0001, 0x01])

            get_actor_attribute(-0x01, ActorAttribute.Z_POSITION, res=Variables[0x1001])
            emit_command(0x00B2, [-0x01, 0x00, Variables[0xA001], Variables[0xA002], Variables[0x1001], 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
            emit_command(0x00BB, [-0x01])
            branch('blitty_pathfind_start', type=0x00)
        
        else:
            branch_if(Variables[0x200E], '==', 0x0, 'hide_blitty') # if vacuum block isn't acquired, hide the blitty and abort
            set_animation(Self, 0x01)
            wait(3)
            emit_command(0x01CE, [0x20020210, Variables[0x3000], 0x0000, 0x0000, 0x0001, 0x00])

            label('meow_loop', manager = fevent_manager)
            Variables[0x1000] = 60
            Variables[0x1000] = Variables[0x1000] + 0x1
            random_below(Variables[0x1000], Variables[0x1001])
            Variables[0xA001] = Variables[0x1001] + 120
            wait(Variables[0xA001])
            branch_if(Variables[blitty_flag], '==', 0x1, 'kill_blitty')
            if blitty_object != 0x01000325: # this object has a longer animation, so it shouldn't stop or start
                set_animation(Self, 0x00)
            Variables[0x1000] = 150
            Variables[0x1000] = Variables[0x1000] + 0x1
            random_below(Variables[0x1000], Variables[0x1001])
            Variables[0xA002] = Variables[0x1001] + 30
            wait(Variables[0xA002])
            branch_if(Variables[blitty_flag], '==', 0x1, 'kill_blitty')
            if blitty_object != 0x01000325: # this object has a longer animation, so it shouldn't stop or start
                set_animation(Self, 0x01)
            emit_command(0x01CE, [0x20020210, Variables[0x3006], 0x0000, 0x0000, 0x0001, 0x00])
            branch('meow_loop', type=0x00)

        label('hide_blitty', manager = fevent_manager)
        emit_command(0x0063, [-0x01, 0x00])
        emit_command(0x0064, [-0x01, 0x00])

        label('kill_blitty', manager = fevent_manager)

    @subroutine(subs = script.subroutines, hdr = script.header)
    def blitty_interact(sub: Subroutine):
        branch_if(Variables[0x3019], '==', 0x1, 'bowser_collect') # if playing as the bros, just meow and do nothing else

        label('mario_meow_2_the_meowening', manager = fevent_manager)
        emit_command(0x01CE, [0x20020210, Variables[0x3002], 0x0000, 0x0000, 0x0001, 0x00])
        return_()

        label('bowser_collect', manager = fevent_manager)
        emit_command(0x00F1)
        emit_command(0x00F4, [0x01, 0x01], Variables[0xA000])
        # if you flame the blitty it'll still be collected unless you run out of breath
        # idk how to make it not get collected but at least i made the blitty scream while it's being burned
        branch_if(Variables[0xA000], '==', 0x1A, 'mario_meow_2_the_meowening')
        branch_if(Variables[0xA000], '==', 0x1D, 'action_manager_0')
        branch_if(Variables[0xA000], '==', 0x1E, 'action_manager_0')
        branch_if(Variables[0xA000], '==', 0x1F, 'action_manager_0')
        branch_if(Variables[0xA000], '==', 0x27, 'action_manager_0')
        emit_command(0x0112, [0x01, 0x0F])
        branch('action_manager_1', type=0x00)

        label('action_manager_0', manager = fevent_manager)
        emit_command(0x0113, [0x01, 0x0100])
        emit_command(0x0114, [0x01])

        label('action_manager_1', manager = fevent_manager)
        emit_command(0x01A1) # no clue
        emit_command(0x018C, [Variables[0x3008], 0x0FFF], Variables[0x1007]) # take control from bowser
        branch_if(Variables[0x3008], '==', 0x0, 'hud_hide_1', invert=True) # idk but it's responsible for hiding the HUD
        emit_command(0x00F5, [0x01, 0x00, 0x00])
        branch('hud_hide_0')

        label('hud_hide_1', manager = fevent_manager)
        emit_command(0x00F5, [0x00, 0x00, 0x00])

        label('hud_hide_0', manager = fevent_manager)

        emit_command(0x0063, [Actors.BOWSER, 0x00])
        emit_command(0x0064, [Actors.BOWSER, 0x00])
        emit_command(0x0063, [Variables[0x3002], 0x00])
        emit_command(0x0064, [Variables[0x3002], 0x00])

        Variables[0xA003] = Variables[0x3002]
        Variables[0xA003] += 1

        get_actor_attribute(Actors.BOWSER, ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Z_POSITION, res=Variables[0x1002])
        emit_command(0x0063, [Variables[0xA003], 0x01])
        emit_command(0x0064, [Variables[0xA003], 0x01])
        emit_command(0x00BD, [Variables[0xA003], 0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002]])
        set_animation(Variables[0xA003], 0x00)
        emit_command(0x0091, [Variables[0xA003], -0x01, 0x0000, 0x0001, 0x01])
        emit_command(0x0094, [Variables[0xA003], 0x0000, 0x00])
        emit_command(0x0093, [Variables[0xA003]])

        emit_command(0x0063, [Variables[0x3002], 0x01])
        emit_command(0x0064, [Variables[0x3002], 0x01])
        emit_command(0x01CE, [0x20020210, Variables[0x3002], 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x007E, [Variables[0x3002], 0x0200])
        set_animation(Variables[0x3002], 0x01)
        emit_command(0x0091, [Variables[0x3002], 0x01, 0x0004, -0x0001, 0x01])
        emit_command(0x0094, [Variables[0x3002], 0x0000, 0x00])
        Variables[0x1000] = Variables[0x1000] + -0xE
        Variables[0x1001] = Variables[0x1001] + 0x10
        Variables[0x1002] = Variables[0x1002] + 0x48
        emit_command(0x00BD, [Variables[0x3002], 0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002]])
        start_thread_here_and_branch(0x00, 'cutscene_continue')
        emit_command(0x01DA, [0x00, 0x01, 0x001E])
        wait(40)
        emit_command(0x01CE, [0x02000089, Actors.BOWSER, 0x0000, 0x0000, 0x0001, 0x00])
        wait(150)
        emit_command(0x01DA, [0x00, 0x00, 0x001E])
        return_()

        label('cutscene_continue', manager = fevent_manager)
        Variables[blitty_flag] = 1
        Variables[key_menu_flag] = 1
        emit_command(0x01BB, [-0x8000, 0x0010, 0x00, 0x00, 0x03, 0x00, -0x01, -0x01, -0x0001, 0x01, 0x00, 0x00000000, len(fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + j].entries) - 1, 0x00, 0x08, 0x00, 0x0000, -0x01], Variables[0x1000])
        wait_for_textbox()

        emit_command(0x0063, [Variables[0xA003], 0x00])
        emit_command(0x0064, [Variables[0xA003], 0x00])
        emit_command(0x0063, [Actors.BOWSER, 0x01])
        emit_command(0x0064, [Actors.BOWSER, 0x01])
        emit_command(0x0063, [Variables[0x3002], 0x00])
        emit_command(0x0064, [Variables[0x3002], 0x00])
        set_animation(Actors.BOWSER, 0x03)
        emit_command(0x00D1, [Actors.BOWSER, 0x00, 0x04])

        emit_command(0x01A0)
        Variables[0x1000] = 0x0
        branch_if(Variables[0x3008], '==', 0x1, 'sub_end', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('sub_end', manager = fevent_manager)
        emit_command(0x00F5, [0x01, 0x01, 0x00])
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
    
    script.header.subroutine_table = [0] * len(script.subroutines)
    update_commands_with_offsets(fevent_manager, [script.header.post_table_subroutine, *script.subroutines], len(script.header.to_bytes(fevent_manager)))


##################################################################################
##################################################################################
##################################################################################


def arm_center_endless(fevent_manager, font_file):
    room_id = 0x1C
    script = fevent_manager.fevent_chunks[room_id][0]
    subroutine_num = len(script.subroutines)
    # i can have up to 7 subroutines for free basically
    script.subroutines.pop()
    script.subroutines.pop()
    script.subroutines.pop()
    script.subroutines.pop()
    script.subroutines.pop()
    script.subroutines.pop()
    script.subroutines.pop()

    cast(SubroutineExt, script.subroutines[0x06]).name = 'sub_0x6'
    cast(SubroutineExt, script.subroutines[0x07]).name = 'sub_0x7'
    cast(SubroutineExt, script.subroutines[0x08]).name = 'sub_0x8'
    cast(SubroutineExt, script.subroutines[0x09]).name = 'sub_0x9'
    cast(SubroutineExt, script.subroutines[0x0C]).name = 'sub_0xc'
    cast(SubroutineExt, script.subroutines[0x0D]).name = 'sub_0xd'
    cast(SubroutineExt, script.subroutines[0x14]).name = 'sub_0x14'
    cast(SubroutineExt, script.subroutines[0x15]).name = 'sub_0x15'
    cast(SubroutineExt, script.subroutines[0x1A]).name = 'sub_0x1a'
    cast(SubroutineExt, script.subroutines[0x1C]).name = 'sub_0x1c'

    arm_center_score_level_threshold = 15

    script.subroutines[2].commands[0].arguments[4] = 0
    script.header.actors.append((0x00000000, 0x00000000, 0xFFFF0001, 0xFFFFFFFF, 0x01980000))
    script.header.actors.append((0x00000000, 0x00010000, 0xFFFF0001, 0xFFFFFFFF, 0x01980000))
    script.header.actors.append((0x00000000, 0x00020000, 0xFFFF0001, 0xFFFFFFFF, 0x01980000))
    script.header.actors.append((0x00000000, 0x00010000, 0xFFFF0001, 0xFFFFFFFF, 0x01980000))
    script.header.actors.append((0x00000000, 0x00020000, 0xFFFF0001, 0xFFFFFFFF, 0x01980000))
    script.header.actors.append((0x00000000, 0x00030000, 0xFFFF0001, 0xFFFFFFFF, 0x01980000))

    coin_mes_box_id = 0
    
    for i in range(6):
        if fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + i] is None:
            continue
            
        coin_mes_box_id = len(fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + i].entries)
        
        string = fevent_manager.fevent_chunks[0x0128][2].text_tables[0x43 + i].entries[0x2D].replace(b"10", b"99990") # "You got 10 coins!"
        fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + i].textbox_sizes.append(get_meswin_size(string, font_file))

        string = string.replace(b"99990", b"\xff\x0f\x00\x05")
        fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + i].entries.append(b"\xff\x35" + string)
    
    fevent_manager.fevent_chunks[room_id][2].text_tables[FEVENT_PADDING_TEXT_TABLE_ID] = b""
    language_table_size = len(fevent_manager.fevent_chunks[room_id][2].to_bytes())
    fevent_manager.fevent_chunks[room_id][2].text_tables[FEVENT_PADDING_TEXT_TABLE_ID] = (
        b"\x00"
        * (
            (-(language_table_size + 1) % LANGUAGE_TABLE_ALIGNMENT)
            + 1
        )
    )

    script.subroutines[0x19].commands[0] = ArrayCommand( # make the endless mode have a length of -1, rather than 255 (also take advantage of the stage 5 data for space)
        MnLDataTypes.S_BYTE, 
        [0x01, 0x02, 0x08, 0x04, 0x05, 0x06, 0x06, 0x04, 0x07, 0x06, 0x05, 0x06, -0x01, -0x01, -0x01, -0x01]
    )

    script.subroutines[0x00].commands[7] = CodeCommandWithOffsets(0x0002, [0x00, Variables[0xE937], 0x01, 0x00, PLACEHOLDER_OFFSET], offset_arguments = {4: 'arm_center_endless_init'})
    
    @subroutine(subs = script.subroutines, hdr = script.header)
    def arm_center_endless_init(sub: Subroutine):
        # automatically determine the arm center level
        Variables[0x1000] = 0x0
        Variables[0x1000] += Variables[0xE943] # broque
        Variables[0x1000] += Variables[0xE95D] # wiggler statue
        Variables[0x1000] += Variables[0xE950] # carrot
        Variables[0x1000] += Variables[0xEBB4] # midbus
        branch_if(Variables[0x1000], '==', 0x0, 'arm_regular_init') # prevent the player from playing before finishing one arm minigame
        
        emit_command(0x007E, [0x06, 0xA0])
        set_animation(0x06, 0x01)
        emit_command(0x0091, [0x06, -0x01, 0x0002, -0x0001, 0x01])
        emit_command(0x0094, [0x06, 0x0000, 0x00])
        
        label('arm_regular_init', manager = fevent_manager)
        emit_command(0x014B, [-0x10, 0x00, 0x0010])
        emit_command(0x014C)
        branch_if(Variables[0xEB7F], '==', 0x1, 'arm_regular_init_0', invert=True)
        Variables[0xEB0D] = 0x1
        branch('arm_regular_init_1')

        label('arm_regular_init_0', manager = fevent_manager)
        Variables[0xEB0D] = 0x0

        label('arm_regular_init_1', manager = fevent_manager)
        branch_if(Variables[0xE937], '==', 0x1, 'arm_regular_init_2', invert=True)
        Variables[0x1000] = 0xC00
        branch_if(Variables[0x3008], '==', 0x1, 'arm_regular_init_3', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('arm_regular_init_3', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
        branch('arm_regular_init_4')

        label('arm_regular_init_2', manager = fevent_manager)
        Variables[0x1000] = 0x0
        branch_if(Variables[0x3008], '==', 0x1, 'arm_regular_init_5', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('arm_regular_init_5', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])

        label('arm_regular_init_4', manager = fevent_manager)

    @subroutine(subs = script.subroutines, hdr = script.header)
    def arm_center_prepare(sub: Subroutine):
        emit_command(0x00F4, [0x00, 0x01], Variables[0xA000])
        branch_if(Variables[0xA000], '!=', 0x2, 'arm_center_continue', invert=True)
        return_()

        label('arm_center_continue', manager = fevent_manager)
        Variables[0x1000] = 0xFFF
        branch_if(Variables[0x3008], '==', 0x1, 'arm_thingy', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('arm_thingy', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
        get_actor_attribute(Actors.LUIGI, ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(Actors.LUIGI, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(Actors.LUIGI, ActorAttribute.Z_POSITION, res=Variables[0x1002])
        branch_if(Variables[0xE937], '==', 0x0, 'arm_is_normal', invert=True)

        # automatically determine the arm center level
        Variables[0x1000] = 0x0
        Variables[0x1000] += Variables[0xE943] # broque
        Variables[0x1000] += Variables[0xE95D] # wiggler statue
        Variables[0x1000] += Variables[0xE950] # carrot
        Variables[0x1000] += Variables[0xEBB4] # midbus
        branch_if(Variables[0x1000], '==', 0x0, 'arm_abort') # prevent the player from playing before finishing one arm minigame

        start_thread_here_and_branch(Variables[0x3002], 'endless_arm_start')
        emit_command(0x007E, [Variables[0x3002], 0x100])
        emit_command(0x0071, [-0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
        set_animation(Self, 0x01)
        emit_command(0x0091, [-0x01, -0x01, 0x0001, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        wait(30)
        set_animation(Self, 0x01)
        emit_command(0x0091, [-0x01, -0x01, 0x0002, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        return_()

        label('endless_arm_start', manager = fevent_manager)
        emit_command(0x00F5, [0x00, 0x00, 0x00])
        Variables[0xEB14] = 0x0
        Variables[0xEB15] = 0x0
        Variables[0x500E] = 0x3
        Variables[0x500D] = 0x4
        Variables[0xE97F] = 0x1
        branch('arm_center_endless_game_start', type=0x00)
        return_()

        label('arm_is_normal', manager = fevent_manager)
        start_thread_here_and_branch(Variables[0x3002], 'normal_arm_start')
        emit_command(0x0071, [-0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
        set_animation(Self, 0x01)
        emit_command(0x0091, [-0x01, -0x01, 0x0001, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        wait(30)
        set_animation(Self, 0x01)
        emit_command(0x0091, [-0x01, -0x01, 0x0002, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        return_()

        label('normal_arm_start', manager = fevent_manager)
        emit_command(0x00F5, [0x00, 0x00, 0x00])
        Variables[0xEB14] = 0x0
        Variables[0xEB15] = 0x0
        branch('sub_0x6', type=0x00)
        return_()

        label('arm_abort', manager = fevent_manager)
        unk_thread_branch_0x004a(Variables[0x3002], 'arm_abort_continue')
        wait(1)
        set_animation(Self, 0x01)
        emit_command(0x0091, [-0x01, -0x01, 0x0001, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        wait(30)
        set_animation(Self, 0x01)
        emit_command(0x0091, [-0x01, -0x01, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        return_()

        label('arm_abort_continue', manager = fevent_manager)
        Variables[0x1000] = 0x0
        branch_if(Variables[0x3008], '==', 0x1, 'arm_abort_thingy', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('arm_abort_thingy', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])
        return_()


        label('arm_center_endless_game_start', manager = fevent_manager)
        emit_command(0x01D7, [0x01, 0x0028])
        wait(40)
        emit_command(0x01D3, [0x01, 0x004E])
        emit_command(0x01D5)
        emit_command(0x01D6, [0x01, 0x00, 0x00])
        Variables[0x9000] = 0x0
        Variables[0x9001] = 0x0
        Variables[0x9002] = 0x0
        Variables[0x9003] = 0x0
        Variables[0x9004] = 0x0
        Variables[0x9006] = 0x0
        Variables[0x9009] = 0x3
        Variables[0x900A] = 0x0
        Variables[0x900B] = 0x0
        Variables[0xA000] = 0x3 - Variables[0x500E]
        Variables[0x500E] = 0x3
        Variables[0x6055] = Variables[0xA000]
        branch_if(Variables[0xEB31], '==', 0x0, 'endless_arm_game_start_0', invert=True)
        Variables[0x9014] = Variables[0xA000]
        branch('endless_arm_game_start_1')

        label('endless_arm_game_start_0', manager = fevent_manager)
        Variables[0x9014] = 0x0

        label('endless_arm_game_start_1', manager = fevent_manager)
        Variables[0x9016] = 0x0
        Variables[0x9018] = 0x0
        Variables[0x9017] = 0x42
        random_below(Variables[0x9017], Variables[0x9017])
        Variables[0x900C] = 0x0
        Variables[0x900D] = 0x0
        Variables[0x900E] = 0x0
        Variables[0xEB3E] = 0x0
        Variables[0xEB37] = 0x0
        Variables[0xE93A] = 0x0
        Variables[0xEB03] = 0x0
        Variables[0xEB5D] = 0x0
        Variables[0xC000] = 0x0
        emit_command(0x01BB, [0x0098, 0x0096, 0x00, 0x05, 0x03, 0x00, -0x01, -0x01, -0x0001, 0x00, 0x01, 0x00000000, 0x0C, 0x10, 0x00, 0x00, 0x0000, -0x01], Variables[0x1000])
        emit_command(0x01C5, [0x01, 0x03], Variables[0x1002])
        Variables[0x1003] = 0x1C
        Variables[0x1003] = Variables[0x1003] // 0x2
        Variables[0x1000] = 0x98 + Variables[0x1003]
        Variables[0x1002] = Variables[0x1002] // 0x2
        Variables[0x1001] = 0x96 + Variables[0x1002]
        
        Variables[0x1000] += 4
        Variables[0x1001] += 12

        emit_command(0x00BD, [0x13, 0x00, Variables[0x1000], Variables[0x1001], 0x0000])
        emit_command(0x0063, [0x13, 0x01])
        branch_if(Variables[0xE945], '==', 0x0, 'endless_arm_game_start_2', invert=True)
        wait(1)
        emit_command(0x0114, [0x00])
        emit_command(0x0113, [0x00, 0xFFFF])
        emit_command(0x0114, [0x00])
        emit_command(0x0192, [0x00, Variables[0x3000]])
        emit_command(0x0134, [0x00, 0x0022, 0x0000, 0x0014, 0x01, 0x01])
        emit_command(0x0137)

        label('endless_arm_game_start_2', manager = fevent_manager)
        emit_command(0x00BD, [0x14, 0x00, 0x14, 0xB8, 0x00])
        emit_command(0x00BD, [0x15, 0x00, 0x2A, 0xB8, 0x00])
        emit_command(0x00BD, [0x16, 0x00, 0x40, 0xB8, 0x00])
        emit_command(0x00BD, [0x17, 0x00, 0x56, 0xB8, 0x00])
        emit_command(0x00BD, [0x18, 0x00, 0x78, 0xB8 - 0xA, 0x00])
        start_thread_here_and_branch(0x13, 'arm_game_start_cont')
        emit_command(0x0063, [0x14, 0x01])
        emit_command(0x01CE, [0x000200EC, 0x14, 0x0000, 0x0000, 0x0001, 0x00])
        wait(15)
        emit_command(0x0063, [0x15, 0x01])
        emit_command(0x01CE, [0x000200EC, 0x15, 0x0000, 0x0000, 0x0001, 0x00])
        wait(15)
        emit_command(0x0063, [0x16, 0x01])
        emit_command(0x01CE, [0x000200EC, 0x16, 0x0000, 0x0000, 0x0001, 0x00])
        return_()

        label('arm_game_start_cont', manager = fevent_manager)
        branch_in_thread(0x08, 'sub_0x9')
        branch_if(Variables[0xE945], '==', 0x0, 'endless_arm_game_start_3', invert=True)
        emit_command(0x00E7, [0x00])
        emit_command(0x0134, [0x00, 0x0056, 0x0000, 0x0014, 0x01, 0x01])
        emit_command(0x00B2, [0x00, 0x00, 0x0116, 0x00C0, 0x0030, 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x00])
        start_thread_here_and_branch(0x01, 'endless_arm_game_start_4')
        emit_command(0x00B2, [-0x01, 0x00, 0x0116, 0x00C0, 0x0030, 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        emit_command(0x00D1, [-0x01, 0x00, 0x03])
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x6 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'endless_arm_game_start_5', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'endless_arm_game_start_6', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('endless_arm_game_start_7')

        label('endless_arm_game_start_6', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('endless_arm_game_start_7', manager = fevent_manager)
        push(Variables[0x1001])

        label('endless_arm_game_start_9', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'endless_arm_game_start_8', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(2)
        branch('endless_arm_game_start_9')

        label('endless_arm_game_start_8', manager = fevent_manager)
        branch('endless_arm_game_start_10')

        label('endless_arm_game_start_5', manager = fevent_manager)
        wait(2)

        label('endless_arm_game_start_10', manager = fevent_manager)
        return_()

        label('endless_arm_game_start_4', manager = fevent_manager)
        unk_thread_branch_0x004a(0x00, 'endless_arm_game_start_11')
        emit_command(0x01CE, [0x20020006, 0x00, 0x0000, 0x0000, 0x0001, 0x00])
        get_actor_attribute(-0x01, ActorAttribute.Z_POSITION, res=Variables[0x1000])
        Variables[0x1000] = 0x50 - Variables[0x1000]
        emit_command(0x00C0, [-0x01, Variables[0x1000], 0x0040, 0x0014])
        emit_command(0x00B3, [-0x01, 0x00, 0x013E, 0x00C0, 0x0050, 0x0014, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        emit_command(0x00D1, [-0x01, 0x00, 0x03])
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x6 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'endless_arm_game_start_12', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'endless_arm_game_start_13', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('endless_arm_game_start_14')

        label('endless_arm_game_start_13', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('endless_arm_game_start_14', manager = fevent_manager)
        push(Variables[0x1001])

        label('endless_arm_game_start_16', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'endless_arm_game_start_15', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(2)
        branch('endless_arm_game_start_16')

        label('endless_arm_game_start_15', manager = fevent_manager)
        branch('endless_arm_game_start_17')

        label('endless_arm_game_start_12', manager = fevent_manager)
        wait(2)

        label('endless_arm_game_start_17', manager = fevent_manager)
        return_()

        label('endless_arm_game_start_11', manager = fevent_manager)
        wait(4)
        branch_in_thread(0x10, 'sub_0x7')
        start_thread_here_and_branch(0x00, 'endless_arm_game_start_18')
        emit_command(0x0066, [-0x01, 0x00])
        set_animation(Self, 0x01)
        emit_command(0x0098, [-0x01, 0x07, 0x01, 0x0000, -0x0001, 0x01, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        emit_command(0x00BD, [-0x01, 0x00, 0x013F, 0x00C0, 0x005E])
        return_()

        label('endless_arm_game_start_18', manager = fevent_manager)
        branch_in_thread(0x11, 'sub_0x8')
        start_thread_here_and_branch(0x01, 'endless_arm_game_start_3')
        emit_command(0x0066, [-0x01, 0x00])
        set_animation(Self, 0x01)
        emit_command(0x0098, [-0x01, 0x07, 0x01, 0x0000, -0x0001, 0x01, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        emit_command(0x00BD, [-0x01, 0x00, 0x0117, 0x00C0, 0x0045])
        return_()

        label('endless_arm_game_start_3', manager = fevent_manager)
    
    script.header.actors[6] = (
        script.header.actors[6][0],
        script.header.actors[6][1],
        script.header.actors[6][2],
        (script.header.actors[6][3] & 0xFFFF0000) + (len(script.subroutines) - 1),
        script.header.actors[6][4],
    )

    script.subroutines[0x12].commands[0] = CodeCommandWithOffsets(0x004B, [0x0C, 0x00, PLACEHOLDER_OFFSET], offset_arguments = {2: 'arm_center_subtract_coins_check'})
    script.subroutines[0x12].commands[-2] = CodeCommandWithOffsets(0x004B, [0x08, 0x00, PLACEHOLDER_OFFSET], offset_arguments = {2: 'arm_center_lose_life'})
    
    @subroutine(subs = script.subroutines, hdr = script.header)
    def arm_center_subtract_coins_check(sub: Subroutine):
        branch_if(Variables[0x500D], '==', 0x4, 'arm_coin_subtract_abort')
        branch('sub_0x1c', type=0x00)
        label('arm_coin_subtract_abort', manager = fevent_manager)
    
    @subroutine(subs = script.subroutines, hdr = script.header)
    def arm_center_lose_life(sub: Subroutine):
        branch_if(Variables[0x500D], '==', 0x4, 'sub_0x9', invert=True)
        Variables[0x9009] -= 1
        branch_in_thread(0x13, 'lives_display')
        branch_if(Variables[0x9009], '<', 0x0, 'arm_halt', invert=True)
        return_()
        
        label('arm_halt', manager = fevent_manager)
        branch('sub_0x9', type=0x00)
        return_()

        label('lives_display', manager = fevent_manager)
        wait(11)
        branch_if(Variables[0x9009], '<', 0x0, 'arm_life_down_sound')
        emit_command(0x01CE, [0x000201C6, 0x06, 0x0000, 0x0000, 0x0001, 0x00])
        label('arm_life_down_sound', manager = fevent_manager)

        call('arm_center_lives_display')

    script.subroutines[0xE].commands[57] = CodeCommandWithOffsets(0x004B, [Variables[0xA00E], 0x00, PLACEHOLDER_OFFSET], offset_arguments = {2: 'arm_center_score_display'})
    script.subroutines[0x9].commands[27] = CodeCommandWithOffsets(0x004B, [Variables[0xA00E], 0x00, PLACEHOLDER_OFFSET], offset_arguments = {2: 'arm_center_score_display'})

    @subroutine(subs = script.subroutines, hdr = script.header)
    def arm_center_lives_display(sub: Subroutine):
        branch_if(Variables[0x9009], '>', 0x5, 'arm_life_cap', invert=True)
        Variables[0x9009] = 5
        label('arm_life_cap', manager = fevent_manager)

        emit_command(0x0063, [0x18, 0x00])
        branch_if(Variables[0x9009], '>=', 0x5, 'arm_life_5_pass', invert=True)
        emit_command(0x0063, [0x18, 0x01])
        label('arm_life_5_pass', manager = fevent_manager)
        
        emit_command(0x0063, [0x17, 0x00])
        branch_if(Variables[0x9009], '>=', 0x4, 'arm_life_4_pass', invert=True)
        emit_command(0x0063, [0x17, 0x01])
        label('arm_life_4_pass', manager = fevent_manager)
        
        emit_command(0x0063, [0x16, 0x00])
        branch_if(Variables[0x9009], '>=', 0x3, 'arm_life_3_pass', invert=True)
        emit_command(0x0063, [0x16, 0x01])
        label('arm_life_3_pass', manager = fevent_manager)
        
        emit_command(0x0063, [0x15, 0x00])
        branch_if(Variables[0x9009], '>=', 0x2, 'arm_life_2_pass', invert=True)
        emit_command(0x0063, [0x15, 0x01])
        label('arm_life_2_pass', manager = fevent_manager)
        
        emit_command(0x0063, [0x14, 0x00])
        branch_if(Variables[0x9009], '>=', 0x1, 'arm_life_1_pass', invert=True)
        emit_command(0x0063, [0x14, 0x01])
        label('arm_life_1_pass', manager = fevent_manager)

        branch_if(Variables[0x9009], '<', 0x0, 'arm_ded')
        return_()

        label('arm_ded', manager = fevent_manager)
        branch_in_thread(0x06, 'arm_ded_end')
        emit_command(0x007E, [0x06, 0x100])
        emit_command(0x0063, [0x12, 0x00])
        wait(20)
        emit_command(0x01D7, [0x01, 60])
        wait(60)
        wait(20)
        Variables[0xE97F] = 0
        Variables[0x500D] = 0
        
        branch_if(Variables[0x6055], '==', 0x2, 'arm_coin_10_pass', invert=True)
        Variables[0xC000] = Variables[0x900A] * 10
        label('arm_coin_10_pass', manager = fevent_manager)
        
        branch_if(Variables[0x6055], '==', 0x1, 'arm_coin_5_pass', invert=True)
        Variables[0xC000] = Variables[0x900A] * 5
        label('arm_coin_5_pass', manager = fevent_manager)
        
        branch_if(Variables[0x6055], '==', 0x0, 'arm_coin_3_pass', invert=True)
        Variables[0xC000] = Variables[0x900A] * 3
        label('arm_coin_3_pass', manager = fevent_manager)

        Variables[0xEB14] = 0x1
        Variables[0xEB15] = 0x1
        branch_if(Variables[0xC000], '==', 0x0, 'arm_coin_celebrate_pass')
        emit_command(0x01CD, [0x02000089, 0x0080, 0x0060, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x01CD, [0x400000BC, 0x0080, 0x0060, 90, 0x0000, 0x0001, 0x00])
        branch('arm_coin_celebrate_end', type=0x00)

        label('arm_coin_celebrate_pass', manager = fevent_manager)
        emit_command(0x01CE, [0x4000006F, 0x00, 0, 0x0000, 0x0001, 0x00])
        emit_command(0x01CE, [0x4000003E, 0x01, 0, 0x0000, 0x0001, 0x00])
        branch('arm_coin_celebrate_end', type=0x00)

        label('arm_coin_celebrate_end', manager = fevent_manager)
        add_coins(Variables[0xC000])
        emit_command(0x01BB, [-0x8000, 0x0010, 0x00, 0x00, 0x03, 0x00, -0x01, -0x01, -0x0001, 0x01, 0x00, 0x00000000, coin_mes_box_id, 0x00, 0x08, 0x00, 0x0000, -0x01], Variables[0x1000])
        wait_for_textbox()
        
        wait(20)
        emit_command(0x014B, [0x7F, -0x10, 0x0010])
        emit_command(0x014C)
        Variables[0xEB14] = 0x0
        Variables[0xEB15] = 0x0
        emit_command(0x01BF, [0x01])
        emit_command(0x0063, [0x13, 0x00])
        emit_command(0x00F6, [0x01, 0x03])
        wait(1)
        emit_command(0x004E, [0x10])
        emit_command(0x004E, [0x11])
        emit_command(0x0063, [0x10, 0x00])
        emit_command(0x0063, [0x11, 0x00])
        emit_command(0x004E, [0x0E])
        emit_command(0x004E, [0x0F])
        emit_command(0x0063, [0x0E, 0x00])
        emit_command(0x0063, [0x0F, 0x00])
        unk_thread_branch_0x004a(0x00, 'arm_end_mario_restore')
        emit_command(0x00BD, [-0x01, 0x00, 0x013E, 0x00C0, 0x0050])
        emit_command(0x00F0, [0x00])
        set_animation(Actors.MARIO, 0x03, unk3=0x00)
        emit_command(0x00D1, [0x00, 0x00, 0x06])
        set_animation(Actors.MARIO, 0x03, unk3=0x00)
        emit_command(0x00A0, [-0x01, 0x05, 0x01])
        emit_command(0x0066, [-0x01, 0x01])
        return_()

        label('arm_end_mario_restore', manager = fevent_manager)
        unk_thread_branch_0x004a(0x01, 'arm_end_luigi_restore')
        emit_command(0x00BD, [-0x01, 0x00, 0x0116, 0x00C0, 0x0030])
        emit_command(0x00F0, [0x01])
        set_animation(Actors.LUIGI, 0x03, unk3=0x00)
        emit_command(0x00D1, [0x01, 0x00, 0x06])
        set_animation(Actors.LUIGI, 0x03, unk3=0x00)
        emit_command(0x00A0, [-0x01, 0x05, 0x01])
        emit_command(0x0066, [-0x01, 0x01])
        return_()

        label('arm_end_luigi_restore', manager = fevent_manager)
        emit_command(0x0192, [0x00, Variables[0x3000]])
        emit_command(0x01D4, [0x00])
        emit_command(0x01D4, [0x01])
        emit_command(0x01D5)
        emit_command(0x01D6, [0x00, 0x00, 0x01])
        emit_command(0x01D6, [0x01, 0x00, 0x00])
        emit_command(0x011E, [0x001B, 0x0000, 0x0000, 0x0000, 0x00, 0x00, 0x0003, -0x00000003, 0x01])

        label('arm_ded_end', manager = fevent_manager)
        
    @subroutine(subs = script.subroutines, hdr = script.header)
    def arm_center_score_display(sub: Subroutine):
        branch_if(Variables[0x500D], '==', 0x4, 'sub_0xc', invert=True)
        branch_if(Variables[0x900A], '>', 9999, 'arm_score_truncate', invert=True)
        Variables[0x900A] = 9999

        label('arm_score_truncate', manager = fevent_manager)
        branch_if(Variables[0xC000], '==', Variables[0x900A], 'arm_score_display_abort')
        Variables[0xC000] = Variables[0x900A]
        emit_command(0x01BB, [0x0098, 0x0096, 0x00, 0x05, 0x03, 0x00, -0x01, -0x01, -0x0001, 0x00, 0x01, 0x00000000, 0x0C, 0x10, 0x00, 0x00, 0x0000, -0x01], Variables[0x1000])
        
        branch_if(Variables[0x900A], '>=', arm_center_score_level_threshold * 6, 'arm_score_upgrade_next', invert=True)
        branch_if(Variables[0x6055], '==', 2, 'arm_score_display_abort')
        Variables[0x6055] = 2
        call('sub_0x15')
        Variables[0x9009] += 1
        emit_command(0x01CE, [0x0002002E, 0x06, 0x0000, 0x0000, 0x0001, 0x00])
        call('arm_center_lives_display')
        emit_command(0x0063, [-0x01, 0x00])
        # wait(20)
        emit_command(0x0063, [-0x01, 0x01])
        branch('arm_sub_0xc_replacement', type=0x00)
        return_()

        label('arm_score_upgrade_next', manager = fevent_manager)
        branch_if(Variables[0x900A], '>=', arm_center_score_level_threshold * 3, 'arm_score_display_abort', invert=True)
        branch_if(Variables[0x6055], '==', 1, 'arm_score_display_abort')
        Variables[0x6055] = 1
        call('sub_0x14')
        Variables[0x9009] += 1
        emit_command(0x01CE, [0x0002002E, 0x06, 0x0000, 0x0000, 0x0001, 0x00])
        call('arm_center_lives_display')
        emit_command(0x0063, [-0x01, 0x00])
        # wait(20)
        emit_command(0x0063, [-0x01, 0x01])
        branch('arm_sub_0xc_replacement', type=0x00)
        return_()

        label('arm_score_display_abort', manager = fevent_manager)
        branch('arm_sub_0xc_replacement', type=0x00)
        return_()

        label('arm_sub_0xc_replacement', manager = fevent_manager)
        random_below(0x64, Variables[0xA000])
        branch_if(Variables[0xA000], '<', 0x32, 'arm_sub_0xc_replacement_0', invert=True)
        Variables[0xA001] = 0x0
        Variables[0xA005] = 0x1
        Variables[0x9001] = 0x134
        Variables[0x9002] = 0x6A
        Variables[0x9004] = 0x30
        branch('arm_sub_0xc_replacement_1')

        label('arm_sub_0xc_replacement_0', manager = fevent_manager)
        Variables[0xA001] = 0x30
        Variables[0xA005] = 0x2
        Variables[0x9001] = 0x10D
        Variables[0x9002] = 0x4F
        Variables[0x9004] = 0x30

        label('arm_sub_0xc_replacement_1', manager = fevent_manager)
        Variables[0xA000] = 0x24
        Variables[0xA000] = Variables[0xA000] + Variables[0xA001]
        Variables[0xA003] = Variables[0x6055] * 0x4
        Variables[0xA000] = Variables[0xA000] + Variables[0xA003]
        load_data_from_array('sub_0x1a', Variables[0xA000], res=Variables[0xA001])
        Variables[0xA000] = Variables[0xA000] + 0x1
        load_data_from_array('sub_0x1a', Variables[0xA000], res=Variables[0xA002])
        Variables[0xA000] = Variables[0xA000] + 0x1
        load_data_from_array('sub_0x1a', Variables[0xA000], res=Variables[0xA003])
        Variables[0xA000] = Variables[0xA000] + 0x1
        load_data_from_array('sub_0x1a', Variables[0xA000], res=Variables[0xA004])
        Variables[0x1000] = Variables[0xA002] - Variables[0xA001]
        Variables[0x1000] = Variables[0x1000] + 0x1
        random_below(Variables[0x1000], Variables[0x1001])
        Variables[0xA001] = Variables[0x1001] + Variables[0xA001]
        Variables[0x9003] = Variables[0xA001] & 0xFE
        Variables[0x1000] = Variables[0xA004] - Variables[0xA003]
        Variables[0x1000] = Variables[0x1000] + 0x1
        random_below(Variables[0x1000], Variables[0x1001])
        Variables[0xA003] = Variables[0x1001] + Variables[0xA003]
        Variables[0x9004] = Variables[0xA003] & 0xFE
        branch_if(Variables[0xEB3E], '==', 0x0, 'arm_sub_0xc_replacement_2', invert=True)
        Variables[0x9001] = 0x134
        Variables[0x9002] = 0x6A
        Variables[0x9003] = 0x50
        Variables[0x9004] = 0x4C
        Variables[0xA005] = 0x1
        Variables[0xEB3E] = 0x1
        branch('arm_sub_0xc_replacement_3')

        label('arm_sub_0xc_replacement_2', manager = fevent_manager)
        branch_if(Variables[0xEB03], '==', 0x1, 'arm_sub_0xc_replacement_3', invert=True)
        Variables[0x9001] = 0x134
        Variables[0x9002] = 0x6A
        Variables[0x9003] = 0x32
        Variables[0x9004] = 0x3C
        Variables[0xA005] = 0x3

        label('arm_sub_0xc_replacement_3', manager = fevent_manager)
        branch_in_thread(0x0D, 'arm_ball_move_modded')
        set_animation(Self, 0x01)
        emit_command(0x0091, [-0x01, -0x01, Variables[0xA005], -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        get_actor_attribute(-0x01, ActorAttribute.Z_POSITION, res=Variables[0x1000])
        Variables[0x1000] = Variables[0x9002] - Variables[0x1000]
        Variables[0x1001] = Variables[0x900A] // arm_center_score_level_threshold
        branch_if(Variables[0x1001], '>', 15, 'arm_endless_random_pattern_all_cap_speed', invert=True)
        Variables[0x1001] = 15
        label('arm_endless_random_pattern_all_cap_speed', manager = fevent_manager)
        Variables[0x1002] = Variables[0x9003] * 30
        Variables[0x1001] = Variables[0x9003] * Variables[0x1001]
        Variables[0x9003] = Variables[0x1002] - Variables[0x1001]
        Variables[0x9003] = Variables[0x9003] // 30

        emit_command(0x00C0, [-0x01, Variables[0x1000], Variables[0x9004], Variables[0x9003]])
        emit_command(0x00B3, [-0x01, 0x00, Variables[0x9001], 0x00C0, Variables[0x9002], Variables[0x9003], 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
    
    @subroutine(subs = script.subroutines, hdr = script.header)
    def arm_ball_move_modded(sub: Subroutine):
        branch_if(Variables[0xEB03], '==', 0x1, 'endless_arm_ball_move_0')
        Variables[0x1000] = Variables[0x6055]
        branch('endless_arm_ball_move_1')
        branch('endless_arm_ball_move_2')

        label('endless_arm_ball_move_1', manager = fevent_manager)
        branch_if(0x0, '!=', Variables[0x1000], 'endless_arm_ball_move_3')
        Variables[0xA00D] = 0x22
        branch('endless_arm_ball_move_2')

        label('endless_arm_ball_move_3', manager = fevent_manager)
        branch_if(0x1, '!=', Variables[0x1000], 'endless_arm_ball_move_4')
        Variables[0xA00D] = 0x27
        branch('endless_arm_ball_move_2')

        label('endless_arm_ball_move_4', manager = fevent_manager)
        branch_if(0x2, '!=', Variables[0x1000], 'endless_arm_ball_move_2')
        Variables[0xA00D] = 0x28

        label('endless_arm_ball_move_2', manager = fevent_manager)
        Variables[0x1000] = Variables[0x900A] // arm_center_score_level_threshold
        branch_if(Variables[0x1000], '>', 15, 'arm_endless_random_pattern_cap_likelihood', invert=True)
        Variables[0x1000] = 15

        label('arm_endless_random_pattern_cap_likelihood', manager = fevent_manager)
        Variables[0x1000] = Variables[0x1000] * 3
        Variables[0xA00D] += Variables[0x1000] # random patterns become more likely to appear every 5 hits

        Variables[0x9017] = Variables[0x9017] + Variables[0xA00D]
        branch_if(Variables[0x9017], '>=', 0x64, 'endless_arm_ball_move_0', invert=True)

        label('endless_arm_ball_move_5', manager = fevent_manager)
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Z_POSITION, res=Variables[0x1000])
        wait(1)
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Z_POSITION, res=Variables[0x1001])
        branch_if(Variables[0x1001], '>', Variables[0x1000], 'endless_arm_ball_move_5')
        unk_thread_branch_0x004a(0x02, 'endless_arm_ball_move_6')
        emit_command(0x00BC, [-0x01])
        emit_command(0x0066, [-0x01, 0x00])
        emit_command(0x00C2, [-0x01])
        wait(6)
        Variables[0x1000] = Variables[0x9018]
        branch('endless_arm_ball_move_7')
        branch('endless_arm_ball_move_8')

        label('endless_arm_ball_move_7', manager = fevent_manager)
        branch_if(0x0, '!=', Variables[0x1000], 'endless_arm_ball_move_9')
        fx_multiply(0x168000, 0x1000, Variables[0x1000])
        Variables[0x1001] = Variables[0x900A] // arm_center_score_level_threshold
        branch_if(Variables[0x1001], '>', 15, 'arm_endless_random_pattern_0_cap_speed', invert=True)
        Variables[0x1001] = 15
        label('arm_endless_random_pattern_0_cap_speed', manager = fevent_manager)
        Variables[0x1001] = 0x20 - Variables[0x1001]
        
        emit_command(0x00B8, [-0x01, 0x0D, 0x0000, 0x0000, -0x0018, Variables[0x1000], Variables[0x1001], 0x01, 0x0100, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        Variables[0xA00F] = 0x2
        branch('endless_arm_ball_move_8')

        label('endless_arm_ball_move_9', manager = fevent_manager)
        branch_if(0x1, '!=', Variables[0x1000], 'endless_arm_ball_move_10')
        fx_multiply(0x168000, 0x1000, Variables[0x1000])
        Variables[0x1001] = Variables[0x900A] // arm_center_score_level_threshold
        branch_if(Variables[0x1001], '>', 15, 'arm_endless_random_pattern_1_cap_speed', invert=True)
        Variables[0x1001] = 15
        label('arm_endless_random_pattern_1_cap_speed', manager = fevent_manager)
        Variables[0x1001] = Variables[0x1001] * 2
        Variables[0x1001] = 0x30 - Variables[0x1001]
        emit_command(0x00B8, [-0x01, 0x0D, 0x0000, 0x0000, 0x000C, Variables[0x1000], Variables[0x1001], -0x01, 0x0040, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        Variables[0xA00F] = 0x2
        branch('endless_arm_ball_move_8')

        label('endless_arm_ball_move_10', manager = fevent_manager)
        branch_if(0x2, '!=', Variables[0x1000], 'endless_arm_ball_move_11')
        Variables[0x1001] = Variables[0x900A] // arm_center_score_level_threshold
        branch_if(Variables[0x1001], '>', 15, 'arm_endless_random_pattern_2_cap_speed', invert=True)
        Variables[0x1001] = 15
        label('arm_endless_random_pattern_2_cap_speed', manager = fevent_manager)
        Variables[0x1001] = 0x1E - Variables[0x1001]
        emit_command(0x00B8, [-0x01, 0x0D, 0x0000, 0x0000, -0x0018, 0x000B4000, Variables[0x1001], -0x01, 0x0080, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        Variables[0xA00F] = 0x30
        branch('endless_arm_ball_move_8')

        label('endless_arm_ball_move_11', manager = fevent_manager)
        branch_if(0x3, '!=', Variables[0x1000], 'endless_arm_ball_move_12')
        Variables[0x1001] = Variables[0x900A] // arm_center_score_level_threshold
        branch_if(Variables[0x1001], '>', 15, 'arm_endless_random_pattern_3_cap_speed', invert=True)
        Variables[0x1001] = 15
        label('arm_endless_random_pattern_3_cap_speed', manager = fevent_manager)
        Variables[0x1001] = Variables[0x1001] // 3
        Variables[0x1001] = 0xC - Variables[0x1001]
        emit_command(0x00B8, [-0x01, 0x0D, 0x0000, 0x0000, -0x0018, 0x000B4000, Variables[0x1001], 0x01, 0x0800, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        Variables[0xA00F] = 0x30
        branch('endless_arm_ball_move_8')

        label('endless_arm_ball_move_12', manager = fevent_manager)
        branch_if(0x4, '!=', Variables[0x1000], 'endless_arm_ball_move_13')
        Variables[0x1001] = Variables[0x900A] // arm_center_score_level_threshold
        branch_if(Variables[0x1001], '>', 15, 'arm_endless_random_pattern_4_cap_speed', invert=True)
        Variables[0x1001] = 15
        label('arm_endless_random_pattern_4_cap_speed', manager = fevent_manager)
        Variables[0x1001] = Variables[0x1001] // 3
        Variables[0x1001] = Variables[0x1001] * 2
        Variables[0x1001] = 0x14 - Variables[0x1001]
        emit_command(0x00B8, [-0x01, 0x0D, -0x0028, 0x0000, 0x0018, 0x0005A000, Variables[0x1001], 0x01, 0x0100, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        emit_command(0x00B8, [-0x01, 0x0D, 0x0028, 0x0000, 0x0018, 0x0005A000, Variables[0x1001], -0x01, 0x0100, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        Variables[0xA00F] = 0x30
        branch('endless_arm_ball_move_8')

        label('endless_arm_ball_move_13', manager = fevent_manager)
        branch_if(0x5, '!=', Variables[0x1000], 'endless_arm_ball_move_14')
        Variables[0x1001] = Variables[0x900A] // arm_center_score_level_threshold
        branch_if(Variables[0x1001], '>', 15, 'arm_endless_random_pattern_5_cap_speed', invert=True)
        Variables[0x1001] = 15
        label('arm_endless_random_pattern_5_cap_speed', manager = fevent_manager)
        Variables[0x1001] = Variables[0x1001] // 3
        Variables[0x1001] = Variables[0x1001] * 2
        Variables[0x1001] = 0x14 - Variables[0x1001]
        emit_command(0x00B8, [-0x01, 0x0D, -0x0024, 0x0000, -0x0024, 0x0005A000, Variables[0x1001], -0x01, 0x0180, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        emit_command(0x00B8, [-0x01, 0x0D, 0x0024, 0x0000, -0x0024, 0x0005A000, Variables[0x1001], 0x01, 0x0180, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        Variables[0xA00F] = 0x2
        branch('endless_arm_ball_move_8')

        label('endless_arm_ball_move_14', manager = fevent_manager)
        branch_if(0x6, '!=', Variables[0x1000], 'endless_arm_ball_move_8')
        fx_multiply(0x168000, 0x1000, Variables[0x1000])
        Variables[0x1001] = Variables[0x900A] // arm_center_score_level_threshold
        branch_if(Variables[0x1001], '>', 15, 'arm_endless_random_pattern_6_cap_speed', invert=True)
        Variables[0x1001] = 15
        label('arm_endless_random_pattern_6_cap_speed', manager = fevent_manager)
        Variables[0x1001] = 0x18 - Variables[0x1001]
        emit_command(0x00B8, [-0x01, 0x0D, 0x0000, 0x0000, -0x0010, Variables[0x1000], Variables[0x1001], 0x01, 0x0100, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        emit_command(0x00B8, [-0x01, 0x0D, 0x0000, 0x0000, 0x0010, Variables[0x1000], Variables[0x1001], -0x01, 0x0100, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        Variables[0xA00F] = 0x2

        label('endless_arm_ball_move_8', manager = fevent_manager)
        Variables[0xA000] = Variables[0x9003] // 0x2
        get_actor_attribute(-0x01, ActorAttribute.Z_POSITION, res=Variables[0x1000])
        Variables[0x1000] = Variables[0x9002] - Variables[0x1000]
        emit_command(0x00C0, [-0x01, Variables[0x1000], Variables[0xA00F], Variables[0xA000]])
        emit_command(0x00B3, [-0x01, 0x00, Variables[0x9001], 0x00C0, Variables[0x9002], Variables[0xA000], 0x00, 0x00, 0x01, 0x01])
        return_()

        label('endless_arm_ball_move_6', manager = fevent_manager)
        Variables[0x9017] = Variables[0x9017] - 0x64
        Variables[0x9018] = Variables[0x9018] + 0x1
        branch_if(Variables[0x9018], '>', 0x6, 'endless_arm_ball_move_0', invert=True)
        Variables[0x9018] = 0x0

        label('endless_arm_ball_move_0', manager = fevent_manager)

    script.header.subroutine_table = [0] * len(script.subroutines)
    for i in range(len(script.header.array5)): # update offsets in array5
        script.header.array5[i] += (len(script.subroutines) - subroutine_num) * 2
    update_commands_with_offsets(fevent_manager, [script.header.post_table_subroutine, *script.subroutines], len(script.header.to_bytes(fevent_manager)))
