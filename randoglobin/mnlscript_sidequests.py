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

ITEM_SFX = [
    0x2002000F, # coin
    0x20020024, # consumable
    0x020000A1, # key item (replaces 1-up sound)
]


##################################################################################
##################################################################################
##################################################################################


def assemble_blitty_rewards(fevent_manager, treasure_list, treasure_strings, badge_dict):
    room_id = 0x028D
    script = fevent_manager.fevent_chunks[room_id][0]

    available_objects = [0x09, 0x0A, 0x0B] # this list of objects does NOT need to be expanded
    treasure_textbox_base_id = 0x1F
    current_treasure_list = []
    return_treasure = []

    index = 0
    while len(current_treasure_list) != 3:
        current_treasure_list.append(treasure_list[index])
        index += 1
    return_treasure.extend(treasure_list[index:])
        
    for i in range(3):
        script.header.sprite_groups[available_objects[i]] = current_treasure_list[i].obj
        for j in range(6):
            if not fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + j]:
                continue
            
            fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + j].entries[treasure_textbox_base_id + i] = current_treasure_list[i].textbox[j]
            fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + j].textbox_sizes[treasure_textbox_base_id + i] = current_treasure_list[i].textbox_sizes[j]
    
    fevent_manager.fevent_chunks[room_id][2].text_tables[FEVENT_PADDING_TEXT_TABLE_ID] = b""
    language_table_size = len(fevent_manager.fevent_chunks[room_id][2].to_bytes())
    fevent_manager.fevent_chunks[room_id][2].text_tables[FEVENT_PADDING_TEXT_TABLE_ID] = (
        b"\x00"
        * (
            (-(language_table_size + 1) % LANGUAGE_TABLE_ALIGNMENT)
            + 1
        )
    )

    # for i, treasure in enumerate(current_treasure_list):
    #     print(f"!!assemble_blitty_rewards!! treasure number {i}: {treasure.textbox[1]}")

    cast(SubroutineExt, script.subroutines[0x1A]).name = 'sub_0x1a'
    cast(SubroutineExt, script.subroutines[0x4C]).name = 'sub_0x4c'

    @subroutine(subs = script.subroutines, hdr = script.header)
    def blitty_prize(sub: Subroutine):
        wait(32)
        Variables[0xB001] = 0x0
        branch_if(Variables[0x2022], '==', 0x1, 'blitty_0')
        branch_if(Variables[0x6026], '>=', 0x4, 'blitty_1', invert=True)
        branch_if(Variables[0xEAB9], '==', 0x0, 'blitty_1', invert=True)
        Variables[0xEAB9] = 0x1
        say(0x04, 0x24147, 0x1E, post_anim=0x00, tail_hoffset=0xFF)
        emit_command(0x0094, [0x04, 0x0000, 0x01])
        wait(40)
        emit_command(0x009A, [0x00, 0x0000003D])
        emit_command(0x01A9)
        set_animation(Actors.BOWSER, 0x00)
        emit_command(0x009B, [0x02, 0x00, 0x0000, 0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        emit_command(0x0093, [0x02])
        Variables[0xB001] = 0x1
        start_thread_here_and_branch(0x0F, 'blitty_2')
        emit_command(0x0063, [-0x01, 0x01])
        emit_command(0x0064, [-0x01, 0x01])
        set_animation(Self, 0x01)
        emit_command(0x0091, [-0x01, 0x09, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Z_POSITION, res=Variables[0x1002])
        Variables[0x1000] = Variables[0x1000] + -0xE
        Variables[0x1001] = Variables[0x1001] + 0x10
        Variables[0x1002] = Variables[0x1002] + 0x50
        if current_treasure_list[0].no_string:
            Variables[0x1002] = Variables[0x1002] - 8
        emit_command(0x00BD, [-0x01, 0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002]])
        return_()

        label('blitty_2', manager = fevent_manager)
        emit_command(0x01CE, [ITEM_SFX[current_treasure_list[0].sfx], 0x02, 0x0000, 0x0000, 0x0001, 0x00])
        current_treasure_list[0].to_script_command()
        if not current_treasure_list[0].no_string:
            emit_command(0x01BB, [-0x8000, 0x0010, 0x00, 0x00, 0x03, 0x00, -0x01, -0x01, -0x0001, 0x01, 0x00, 0x00000000, 0x1F, 0x00, 0x08, 0x00, 0x0000, -0x01], Variables[0x1000])
            wait_for_textbox()
        else:
            wait(60)

        label('blitty_1', manager = fevent_manager)
        branch_if(Variables[0x6026], '>=', 0x8, 'blitty_3', invert=True)
        branch_if(Variables[0xEABA], '==', 0x0, 'blitty_3', invert=True)
        Variables[0xEABA] = 0x1
        branch_if(Variables[0xB001], '==', 0x0, 'blitty_4', invert=True)
        say(0x04, 0x24147, 0x1E, post_anim=0x00, tail_hoffset=0xFF)
        emit_command(0x0094, [0x04, 0x0000, 0x01])
        emit_command(0x009A, [0x00, 0x0000003D])
        emit_command(0x01A9)
        set_animation(Actors.BOWSER, 0x00)
        emit_command(0x009B, [0x02, 0x00, 0x0000, 0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        emit_command(0x0093, [0x02])
        Variables[0xB001] = 0x1

        label('blitty_4', manager = fevent_manager)
        start_thread_here_and_branch(0x0F, 'blitty_5')
        emit_command(0x0063, [-0x01, 0x01])
        emit_command(0x0064, [-0x01, 0x01])
        set_animation(Self, 0x01)
        emit_command(0x0091, [-0x01, 0x0A, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Z_POSITION, res=Variables[0x1002])
        Variables[0x1000] = Variables[0x1000] + -0xE
        Variables[0x1001] = Variables[0x1001] + 0x10
        Variables[0x1002] = Variables[0x1002] + 0x50
        if current_treasure_list[1].no_string:
            Variables[0x1002] = Variables[0x1002] - 8
        emit_command(0x00BD, [-0x01, 0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002]])
        return_()

        label('blitty_5', manager = fevent_manager)
        emit_command(0x01CE, [ITEM_SFX[current_treasure_list[1].sfx], 0x02, 0x0000, 0x0000, 0x0001, 0x00])
        wait(40)
        current_treasure_list[1].to_script_command()
        if not current_treasure_list[1].no_string:
            emit_command(0x01BB, [-0x8000, 0x0010, 0x00, 0x00, 0x03, 0x00, -0x01, -0x01, -0x0001, 0x01, 0x00, 0x00000000, 0x20, 0x00, 0x08, 0x00, 0x0000, -0x01], Variables[0x1000])
            wait_for_textbox()
        else:
            wait(60)

        label('blitty_3', manager = fevent_manager)
        branch_if(Variables[0x6026], '>=', 0xC, 'blitty_6', invert=True)
        branch_if(Variables[0xEABB], '==', 0x0, 'blitty_6', invert=True)
        Variables[0xEABB] = 0x1
        branch_if(Variables[0xB001], '==', 0x0, 'blitty_7', invert=True)
        say(0x04, 0x24147, 0x1E, post_anim=0x00, tail_hoffset=0xFF)
        emit_command(0x0094, [0x04, 0x0000, 0x01])
        emit_command(0x009A, [0x00, 0x0000003D])
        emit_command(0x01A9)
        set_animation(Actors.BOWSER, 0x00)
        emit_command(0x009B, [0x02, 0x00, 0x0000, 0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        emit_command(0x0093, [0x02])
        Variables[0xB001] = 0x1

        label('blitty_7', manager = fevent_manager)
        start_thread_here_and_branch(0x0F, 'blitty_8')
        emit_command(0x0063, [-0x01, 0x01])
        emit_command(0x0064, [-0x01, 0x01])
        set_animation(Self, 0x01)
        emit_command(0x0091, [-0x01, 0x0B, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(Actors.BOWSER, ActorAttribute.Z_POSITION, res=Variables[0x1002])
        Variables[0x1000] = Variables[0x1000] + -0xE
        Variables[0x1001] = Variables[0x1001] + 0x10
        Variables[0x1002] = Variables[0x1002] + 0x50
        if current_treasure_list[2].no_string:
            Variables[0x1002] = Variables[0x1002] - 8
        emit_command(0x00BD, [-0x01, 0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002]])
        return_()

        label('blitty_8', manager = fevent_manager)
        emit_command(0x01CE, [ITEM_SFX[current_treasure_list[2].sfx], 0x02, 0x0000, 0x0000, 0x0001, 0x00])
        wait(40)
        current_treasure_list[2].to_script_command()
        if not current_treasure_list[2].no_string:
            emit_command(0x01BB, [-0x8000, 0x0010, 0x00, 0x00, 0x03, 0x00, -0x01, -0x01, -0x0001, 0x01, 0x00, 0x00000000, 0x21, 0x00, 0x08, 0x00, 0x0000, -0x01], Variables[0x1000])
            wait_for_textbox()
        else:
            wait(60)

        label('blitty_6', manager = fevent_manager)
        emit_command(0x0063, [0x0F, 0x00])
        emit_command(0x0064, [0x0F, 0x00])
        set_animation(Actors.BOWSER, 0x01)
        emit_command(0x0091, [0x02, 0x03, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        set_animation(Actors.BOWSER, 0x03)
        emit_command(0x00D1, [0x02, 0x00, 0x00])
        branch_if(Variables[0x6026], '==', 0xF, 'blitty_0', invert=True)
        wait(30)
        say(0x04, 0x24147, 0x23, post_anim=0x00, tail_hoffset=0xFF)
        emit_command(0x0094, [0x04, 0x0000, 0x01])
        wait(30)
        set_animation(0x04, 0x01)
        emit_command(0x0091, [0x04, -0x01, 0x0002, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        say(0x04, 0x24147, 0x24, anim=None, post_anim=None, tail_hoffset=0xFF)
        wait(30)
        start_thread_here_and_branch(0x04, 'blitty_9')
        wait(30)
        set_animation(0x04, 0x00)
        emit_command(0x0091, [0x04, -0x01, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x01])
        return_()

        label('blitty_9', manager = fevent_manager)
        start_thread_here_and_branch(0x02, 'blitty_10')
        wait(30)
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x6 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'blitty_11', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'blitty_12', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('blitty_13')

        label('blitty_12', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('blitty_13', manager = fevent_manager)
        push(Variables[0x1001])

        label('blitty_15', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'blitty_14', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(3)
        branch('blitty_15')

        label('blitty_14', manager = fevent_manager)
        branch('blitty_16')

        label('blitty_11', manager = fevent_manager)
        wait(3)

        label('blitty_16', manager = fevent_manager)
        return_()

        label('blitty_10', manager = fevent_manager)
        unk_thread_branch_0x004a(0x05, 'blitty_17')
        emit_command(0x01CE, [0x20020006, 0x05, 0x0000, 0x0000, 0x0001, 0x00])
        set_animation(Self, 0x00)
        emit_command(0x0091, [-0x01, -0x01, 0x0002, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0002, 0x01])
        emit_command(0x00BE, [-0x01, 0x00005000, 0x000004CC])
        emit_command(0x00B2, [-0x01, 0x01, 0x0000, 0x0040, 0x0000, 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        set_animation(Self, 0x01)
        emit_command(0x0091, [-0x01, -0x01, 0x0005, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        emit_command(0x008B, [-0x01, 0x01, 0x00])
        emit_command(0x00B5, [-0x01, 0x02, -0x0048, 0x0000, 0x0000, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        set_animation(Self, 0x01)
        emit_command(0x0091, [-0x01, -0x01, 0x0006, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        return_()

        label('blitty_17', manager = fevent_manager)
        emit_command(0x01CE, [0x4000012D, 0x05, 0x0000, 0x0000, 0x0001, 0x00])
        say(0x05, Sound.NONE, 0x00, anim=None, post_anim=None, tail_hoffset=0xFF)
        wait(30)
        emit_command(0x009A, [0x00, 0x00000047])
        emit_command(0x01A9)
        set_animation(Actors.BOWSER, 0x01)
        emit_command(0x009B, [0x02, 0x00, 0x0001, -0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        Variables[0x1000] = -0x1
        Variables[0x1001] = -0x3C
        emit_command(0x01C6, [0x25, 0x00], Variables[0x1007])
        emit_command(0x01C6, [0x25, 0x01], Variables[0x1006])
        call('sub_0x4c')
        say((Variables[0x1002], Variables[0x1005]), Sound.SPEECH_BOWSER, 0x25, tail=Variables[0x1006], tail_direction=Variables[0x1000], hoffsets_arg=Variables[0x1003], unk14=Variables[0x1004])
        emit_command(0x0092, [0x02])
        emit_command(0x0097, [0x02])
        wait(30)
        set_animation(0x04, 0x01)
        emit_command(0x0091, [0x04, -0x01, 0x0002, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        say(0x04, 0x24147, 0x26, anim=None, post_anim=0x00, tail_hoffset=0xFF)
        emit_command(0x0091, [0x04, -0x01, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x01])
        wait(30)
        emit_command(0x01CE, [0x4000012D, 0x05, 0x0000, 0x0000, 0x0001, 0x00])
        say(0x05, Sound.NONE, 0x00, anim=None, post_anim=None, tail_hoffset=0xFF)
        wait(30)
        get_actor_attribute(Actors.BOWSER, 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x0 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'blitty_18', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'blitty_19', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('blitty_20')

        label('blitty_19', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('blitty_20', manager = fevent_manager)
        push(Variables[0x1001])

        label('blitty_22', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'blitty_21', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [0x02, 0x01, Variables[0x1002]])
        wait(3)
        branch('blitty_22')

        label('blitty_21', manager = fevent_manager)
        branch('blitty_23')

        label('blitty_18', manager = fevent_manager)
        wait(3)

        label('blitty_23', manager = fevent_manager)
        wait(10)
        emit_command(0x009A, [0x00, 0x00000023])
        emit_command(0x01A9)
        set_animation(Actors.BOWSER, 0x01)
        emit_command(0x009B, [0x02, 0x00, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        say(Actors.BOWSER, Sound.SPEECH_BOWSER, 0x27, anim=None, post_anim=None, tail_hoffset=0xFF)
        emit_command(0x0092, [0x02])
        emit_command(0x0097, [0x02])
        wait(30)
        set_animation(0x04, 0x01)
        emit_command(0x0091, [0x04, -0x01, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        say(0x04, 0x24147, 0x28, anim=None, post_anim=0x00, tail_hoffset=0xFF)
        emit_command(0x0094, [0x04, 0x0000, 0x01])
        wait(30)
        emit_command(0x009A, [0x00, 0x00000023])
        emit_command(0x01A9)
        set_animation(Actors.BOWSER, 0x01)
        emit_command(0x009B, [0x02, 0x00, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        say(Actors.BOWSER, Sound.SPEECH_BOWSER, 0x29, anim=None, post_anim=None, tail_hoffset=0xFF)
        emit_command(0x0092, [0x02])
        emit_command(0x0097, [0x02])
        wait(30)
        say(0x04, 0x24147, 0x2C, post_anim=0x00, tail_hoffset=0xFF)
        emit_command(0x0094, [0x04, 0x0000, 0x01])
        wait(30)
        emit_command(0x009A, [0x00, 0x00000023])
        emit_command(0x01A9)
        set_animation(Actors.BOWSER, 0x01)
        emit_command(0x009B, [0x02, 0x00, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        say(Actors.BOWSER, Sound.SPEECH_BOWSER, 0x2D, anim=None, post_anim=None, tail_hoffset=0xFF)
        emit_command(0x0092, [0x02])
        emit_command(0x0097, [0x02])
        wait(30)
        get_actor_attribute(Actors.BOWSER, 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x6 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'blitty_24', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'blitty_25', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('blitty_26')

        label('blitty_25', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('blitty_26', manager = fevent_manager)
        push(Variables[0x1001])

        label('blitty_28', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'blitty_27', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [0x02, 0x01, Variables[0x1002]])
        wait(3)
        branch('blitty_28')

        label('blitty_27', manager = fevent_manager)
        branch('blitty_29')

        label('blitty_24', manager = fevent_manager)
        wait(3)

        label('blitty_29', manager = fevent_manager)
        emit_command(0x009A, [0x00, 0x00000047])
        emit_command(0x01A9)
        set_animation(Actors.BOWSER, 0x01)
        emit_command(0x009B, [0x02, 0x00, 0x0001, -0x0001, 0x01])
        emit_command(0x0094, [0x02, 0x0000, 0x00])
        Variables[0x1000] = -0x1
        Variables[0x1001] = -0x3C
        emit_command(0x01C6, [0x2E, 0x00], Variables[0x1007])
        emit_command(0x01C6, [0x2E, 0x01], Variables[0x1006])
        call('sub_0x4c')
        say((Variables[0x1002], Variables[0x1005]), Sound.SPEECH_BOWSER, 0x2E, tail=Variables[0x1006], tail_direction=Variables[0x1000], hoffsets_arg=Variables[0x1003], unk14=Variables[0x1004])
        emit_command(0x0092, [0x02])
        emit_command(0x0097, [0x02])
        wait(10)
        emit_command(0x01CE, [0x4000012D, 0x05, 0x0000, 0x0000, 0x0001, 0x00])
        say(0x05, Sound.NONE, 0x00, anim=None, post_anim=None, tail_hoffset=0xFF)
        wait(10)
        emit_command(0x01CD, [0x020000A1, 0x0080, 0x0060, 0x0000, 0x0000, 0x0001, 0x00])
        emit_command(0x01BB, [-0x8000, 0x0010, 0x00, 0x00, 0x03, 0x00, -0x01, -0x01, -0x0001, 0x01, 0x00, 0x00000000, 0x2A, 0x00, 0x08, 0x00, 0x0000, -0x01], Variables[0x1000])
        wait_for_textbox()
        Variables[0x2022] = 0x1
        branch_if(Variables[0xC004], '==', 0x0, 'blitty_30', invert=True)
        emit_command(0x0196, [0x108F, 0x00, 0x01, 0x100F])
        emit_command(0x005F, [0x00, 0x001B0034])
        emit_command(0x0063, [0x07, 0x00])
        emit_command(0x0064, [0x07, 0x00])
        emit_command(0x0063, [0x05, 0x00])
        emit_command(0x0064, [0x05, 0x00])
        emit_command(0x00D1, [0x02, 0x00, 0x00])
        wait(30)
        emit_command(0x014B, [-0x10, 0x00, 0x0010])
        emit_command(0x014C)
        branch('blitty_0', type=0x00)

        label('blitty_30', manager = fevent_manager)
        wait(30)
        emit_command(0x014B, [0x7F, -0x10, 0x0010])
        emit_command(0x014C)
        emit_command(0x0063, [0x07, 0x00])
        emit_command(0x0064, [0x07, 0x00])
        emit_command(0x0063, [0x05, 0x00])
        emit_command(0x0064, [0x05, 0x00])
        emit_command(0x00D1, [0x02, 0x00, 0x00])
        wait(30)
        emit_command(0x014B, [-0x10, 0x00, 0x0010])
        emit_command(0x014C)

        label('blitty_0', manager = fevent_manager)
        wait(30)
        set_animation(0x04, 0x01)
        branch_if(Variables[0x2022], '==', 0x1, 'blitty_31', invert=True)
        say(0x04, 0x24147, 0x2B, anim=None, post_anim=None, tail_hoffset=0xFF)
        branch('blitty_32')

        label('blitty_31', manager = fevent_manager)
        say(0x04, 0x24147, 0x1D, anim=None, post_anim=None, tail_hoffset=0xFF)

        label('blitty_32', manager = fevent_manager)
        set_animation(0x04, 0x00)
        emit_command(0x0094, [0x04, 0x0000, 0x01])
        wait(30)
        branch_if(Variables[0xEABC], '==', 0x0, 'blitty_33')
        emit_command(0x0135, [Variables[0x3000], 0x0000, 0x0000, 0x0400, 0x01, 0x01])
        emit_command(0x0137)
        Variables[0xEB3F] = 0x0
        branch_if(0x1, '==', 0x1, 'blitty_34', invert=True)
        emit_command(0x01A0)
        branch('blitty_35')

        label('blitty_34', manager = fevent_manager)
        emit_command(0x01A1)

        label('blitty_35', manager = fevent_manager)
        Variables[0xEABC] = 0x0
        emit_command(0x00F5, [0x01, 0x01, 0x00])
        call('sub_0x1a')
        Variables[0x1000] = 0x0
        branch_if(Variables[0x3008], '==', 0x1, 'blitty_36', invert=True)
        Variables[0x1000] = Variables[0x1000] | 0xC0

        label('blitty_36', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], Variables[0x1000]], Variables[0x1007])

        label('blitty_33', manager = fevent_manager)
        wait(30)
        emit_command(0x0063, [0x06, 0x01])
        emit_command(0x0064, [0x06, 0x01])

    #for i, command in enumerate(script.subroutines[0x0A].commands):
    #    print(i)
    #    print(hex(command.command_id))

    script.subroutines[0x0A].commands[37] = CodeCommandWithOffsets(0x0003, [0x01, PLACEHOLDER_OFFSET], offset_arguments = {1: 'blitty_prize'})
    script.header.subroutine_table = [0] * len(script.subroutines)
    update_commands_with_offsets(fevent_manager, [script.header.post_table_subroutine, *script.subroutines], len(script.header.to_bytes(fevent_manager)))

    for i, treasure in enumerate(current_treasure_list):
        if treasure.item & 0xF000 == 0x3000:
            badge_dict[treasure.item] = f"{treasure_strings[4][0]} - {treasure_strings[4][1]} x {[4, 8, 12][i]}"

    return return_treasure, badge_dict


##################################################################################
##################################################################################
##################################################################################


def assemble_mushroom_derby(fevent_manager, treasure_list, treasure_strings, badge_dict):
    room_id = 0x0128
    script = fevent_manager.fevent_chunks[room_id][0]

    available_objects = [0x0B, 0x12, 0x13, 0x14, 0x15, 0x16, 0x18, 0x19, 0x1A, 0x1B] # this list of objects needs to be expanded
    treasure_textbox_base_id = 0x2D
    current_treasure_list = []
    return_treasure = []

    used_objects = set([0x01000026, 0x010002FD])
    index = 0
    while len(current_treasure_list) != 16:
        objects_full = len(script.header.sprite_groups) - len(available_objects) + len(used_objects) == 30
        if objects_full and (treasure_list[index].obj not in used_objects):
            return_treasure.append(treasure_list[index])
            print(f"!!assemble_mushroom_derby!! rejected item number {index} because the object pool is full")
        else:
            used_objects.add(treasure_list[index].obj)
            current_treasure_list.append(treasure_list[index])
        index += 1
    return_treasure.extend(treasure_list[index:])
        
    for i in range(16):
        for j in range(6):
            if not fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + j]:
                continue
            
            fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + j].entries[treasure_textbox_base_id + i] = current_treasure_list[i].textbox[j]
            fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + j].textbox_sizes[treasure_textbox_base_id + i] = current_treasure_list[i].textbox_sizes[j]
    
    fevent_manager.fevent_chunks[room_id][2].text_tables[FEVENT_PADDING_TEXT_TABLE_ID] = b""
    language_table_size = len(fevent_manager.fevent_chunks[room_id][2].to_bytes())
    fevent_manager.fevent_chunks[room_id][2].text_tables[FEVENT_PADDING_TEXT_TABLE_ID] = (
        b"\x00"
        * (
            (-(language_table_size + 1) % LANGUAGE_TABLE_ALIGNMENT)
            + 1
        )
    )
    
    print(f"!!assemble_mushroom_derby!! no. of used objects: {len(used_objects)}")
    for i, obj in enumerate(used_objects):
        if i < len(available_objects):
            script.header.sprite_groups[available_objects[i]] = obj
        else:
            script.header.sprite_groups.append(obj)

    @subroutine(subs = script.subroutines, hdr = script.header)
    def derby_prize(sub: Subroutine):
        set_animation(Variables[0x3002], 0x01)
        Variables[0xC000] = Variables[0x6021] - Variables[0x6022]
        branch_if(Variables[0xC000], '==', 0x1, 'derby_0', invert=True)
        say(Variables[0x3002], 0x24147, 0x2A, anim=None, post_anim=None, tail_hoffset=0xFF, force_wait_command=False)
        branch('derby_1')

        label('derby_0', manager = fevent_manager)
        say(Variables[0x3002], 0x24147, 0x2B, anim=None, post_anim=None, tail_hoffset=0xFF, force_wait_command=False)

        label('derby_1', manager = fevent_manager)
        wait_for_textbox()
        set_animation(Variables[0x3002], 0x03)

        label('derby_84', manager = fevent_manager)
        wait(30)
        get_actor_attribute(Variables[0x3002], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x0 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'derby_2', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'derby_3', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('derby_4')

        label('derby_3', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('derby_4', manager = fevent_manager)
        push(Variables[0x1001])

        label('derby_6', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'derby_5', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3002], 0x01, Variables[0x1002]])
        wait(3)
        branch('derby_6')

        label('derby_5', manager = fevent_manager)
        branch('derby_7')

        label('derby_2', manager = fevent_manager)
        wait(3)

        label('derby_7', manager = fevent_manager)
        wait(30)
        set_animation(Variables[0x3002], 0x01)
        emit_command(0x007E, [Variables[0x3002], 0x0200])
        wait(40)
        set_animation(Variables[0x3002], 0x03)
        emit_command(0x007E, [Variables[0x3002], 0x0100])
        get_actor_attribute(Actors.MARIO, ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(Variables[0x3002], ActorAttribute.X_POSITION, res=Variables[0x1001])
        Variables[0x1000] = Variables[0x1000] - Variables[0x1001]
        get_actor_attribute(Actors.MARIO, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(Variables[0x3002], ActorAttribute.Y_POSITION, res=Variables[0x1002])
        Variables[0x1001] = Variables[0x1001] - Variables[0x1002]
        atan2(Variables[0x1001], Variables[0x1000], Variables[0x1002])
        Variables[0x1002] = Variables[0x1002] + 0x1D9
        Variables[0x1002] = Variables[0x1002] // 0x2D
        Variables[0x1007] = Variables[0x1002] & 0x7
        get_actor_attribute(Variables[0x3002], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = Variables[0x1007] - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'derby_8', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'derby_9', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('derby_10')

        label('derby_9', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('derby_10', manager = fevent_manager)
        push(Variables[0x1001])

        label('derby_12', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'derby_11', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3002], 0x01, Variables[0x1002]])
        wait(3)
        branch('derby_12')

        label('derby_11', manager = fevent_manager)
        branch('derby_13')

        label('derby_8', manager = fevent_manager)
        wait(3)

        label('derby_13', manager = fevent_manager)
        wait(30)
        say(Variables[0x3002], 0x24147, 0x2C, tail_hoffset=0xFF)
        wait(30)
        get_actor_attribute(Actors.MARIO, 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x4 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'derby_14', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'derby_15', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('derby_16')

        label('derby_15', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('derby_16', manager = fevent_manager)
        push(Variables[0x1001])

        label('derby_18', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'derby_17', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [0x00, 0x01, Variables[0x1002]])
        wait(3)
        branch('derby_18')

        label('derby_17', manager = fevent_manager)
        branch('derby_19')

        label('derby_14', manager = fevent_manager)
        wait(3)

        for k in range(2): # (k == 0 means mario is mini, k == 1 means mario is big)
            label(f'derby_{k + 19}', manager = fevent_manager)
            if k == 0:
                emit_command(0x00F4, [0x00, 0x01], Variables[0xA00F])
                branch_if(Variables[0xA00F], '==', 0x20, 'derby_20', invert=True) # checks if mario is mini
            start_thread_here_and_branch(0x11, f'derby_{[21, 40][k]}')
            get_actor_attribute(Actors.MARIO, ActorAttribute.X_POSITION, res=Variables[0x1000])
            get_actor_attribute(Actors.MARIO, ActorAttribute.Y_POSITION, res=Variables[0x1001])
            get_actor_attribute(Actors.MARIO, ActorAttribute.Z_POSITION, res=Variables[0x1002])
            Variables[0x1000] = Variables[0x1000] + 0x6
            Variables[0x1001] = Variables[0x1001] + 0x3
            Variables[0x1002] = Variables[0x1002] + [0x1E, 0x2F][k]
            emit_command(0x00BD, [-0x01, 0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002]])
            emit_command(0x0063, [-0x01, 0x01])
            get_actor_attribute(Actors.MARIO, 0x0A, res=Variables[0x1000])
            Variables[0x1000] = Variables[0x1000] - 0x1
            Variables[0x1001] = Variables[0x1000] & 0xF
            Variables[0x1002] = Variables[0x1000] & 0xF0
            Variables[0x1002] = Variables[0x1002] >> 0x4
            Variables[0x1003] = Variables[0x1001] - Variables[0x1002]
            emit_command(0x0078, [-0x01, Variables[0x1003]])
            Variables[0x1000] = Variables[0x6022]
            branch(f'derby_{[23, 42][k]}')

            for i in range(16): # loop: displays the item, and plays the sfx
                if i == 15: j = -2
                else: j = i
                
                label_const = [22, 41][k]
                current_obj = script.header.sprite_groups.index(current_treasure_list[i].obj)

                branch(f'derby_{label_const}')
                label(f'derby_{i + (label_const + 1)}', manager = fevent_manager)
                branch_if(i, '!=', Variables[0x1000], f'derby_{j + (label_const + 2)}')
                emit_command(0x01CE, [ITEM_SFX[current_treasure_list[i].sfx], 0x11, 0x0000, 0x0000, 0x0001, 0x00]) # this command is the treasure's sound effect
                
                if current_treasure_list[i].no_string: # if the object is a coin, move it down into mario's palm
                    get_actor_attribute(-0x1, ActorAttribute.X_POSITION, res=Variables[0x1000])
                    get_actor_attribute(-0x1, ActorAttribute.Y_POSITION, res=Variables[0x1001])
                    get_actor_attribute(-0x1, ActorAttribute.Z_POSITION, res=Variables[0x1002])
                    Variables[0x1002] = Variables[0x1002] - 8
                    emit_command(0x00BD, [-0x01, 0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002]])
                set_animation(Self, 0x01)
                emit_command(0x0091, [-0x01, current_obj, 0x0000, -0x0001, 0x01]) # arg 1 in this command is loaded obj number
                emit_command(0x0094, [-0x01, 0x0000, 0x00])

            label(f'derby_{[22, 41][k]}', manager = fevent_manager)
            return_()

            label(f'derby_{[21, 40][k]}', manager = fevent_manager)
            set_animation(Actors.MARIO, 0x00)
            emit_command(0x0091, [0x00, [0x0D, 0x05][k], 0x0000, 0x0001, 0x01])
            emit_command(0x0094, [0x00, 0x0000, 0x00])
            emit_command(0x0093, [0x00])

            if k == 0:
                branch('derby_39')

        label('derby_39', manager = fevent_manager)
        wait(20)
        Variables[0x1000] = Variables[0x6022]
        branch('derby_59')

        for i in range(16): # loop: gives treasure, and displays textbox
            if i == 15: j = -2
            else: j = i
            branch('derby_58')
            label(f'derby_{i + 59}', manager = fevent_manager)
            branch_if(i, '!=', Variables[0x1000], f'derby_{j + 60}')

            current_treasure_list[i].to_script_command() # this command is the given treasure

            if not current_treasure_list[i].no_string:
                emit_command(0x01BB, [-0x8000, 0x0010, 0x00, 0x00, 0x03, 0x00, -0x01, -0x01, -0x0001, 0x01, 0x00, 0x00000000, treasure_textbox_base_id + i, 0x00, 0x08, 0x00, 0x0000, -0x01], Variables[0x1000])
                wait_for_textbox()
            else:
                wait(60)

        label('derby_58', manager = fevent_manager)
        emit_command(0x0063, [0x11, 0x00])
        emit_command(0x0092, [0x00])
        emit_command(0x0097, [0x00])
        get_actor_attribute(Variables[0x3002], ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(Actors.MARIO, ActorAttribute.X_POSITION, res=Variables[0x1001])
        Variables[0x1000] = Variables[0x1000] - Variables[0x1001]
        get_actor_attribute(Variables[0x3002], ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Y_POSITION, res=Variables[0x1002])
        Variables[0x1001] = Variables[0x1001] - Variables[0x1002]
        atan2(Variables[0x1001], Variables[0x1000], Variables[0x1002])
        Variables[0x1002] = Variables[0x1002] + 0x1D9
        Variables[0x1002] = Variables[0x1002] // 0x2D
        Variables[0x1007] = Variables[0x1002] & 0x7
        get_actor_attribute(Actors.MARIO, 0x0E, res=Variables[0x1000])
        Variables[0x1001] = Variables[0x1007] - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'derby_75', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'derby_76', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('derby_77')

        label('derby_76', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('derby_77', manager = fevent_manager)
        push(Variables[0x1001])

        label('derby_79', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'derby_78', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [0x00, 0x01, Variables[0x1002]])
        wait(3)
        branch('derby_79')

        label('derby_78', manager = fevent_manager)
        branch('derby_80')

        label('derby_75', manager = fevent_manager)
        wait(3)

        label('derby_80', manager = fevent_manager)
        wait(20)
        Variables[0x6024] -= 1
        Variables[0x6022] += 1
        branch_if(Variables[0x6022], '!=', Variables[0x6021], 'derby_81', invert=True)
        set_animation(Variables[0x3002], 0x01)
        Variables[0xC000] = Variables[0x6021] - Variables[0x6022]
        branch_if(Variables[0xC000], '==', 0x1, 'derby_82', invert=True)
        say(Variables[0x3002], 0x24147, 0x3F, anim=None, post_anim=None, tail_hoffset=0xFF, force_wait_command=False)
        branch('derby_83')

        label('derby_82', manager = fevent_manager)
        say(Variables[0x3002], 0x24147, 0x40, anim=None, post_anim=None, tail_hoffset=0xFF, force_wait_command=False)

        label('derby_83', manager = fevent_manager)
        wait_for_textbox()
        set_animation(Variables[0x3002], 0x03)
        branch('derby_84', type=0x00)

        label('derby_81', manager = fevent_manager)
        branch_if(Variables[0x6021], '!=', 0x10, 'derby_85', invert=True)
        Variables[0xC001] = 0x10 - Variables[0x6021]
        set_animation(Variables[0x3002], 0x01)
        branch_if(Variables[0xC001], '==', 0x1, 'derby_86', invert=True)
        say(Variables[0x3002], 0x24147, 0x3D, anim=None, post_anim=None, tail_hoffset=0xFF, force_wait_command=False)
        branch('derby_87')

        label('derby_86', manager = fevent_manager)
        say(Variables[0x3002], 0x24147, 0x3E, anim=None, post_anim=None, tail_hoffset=0xFF, force_wait_command=False)

        label('derby_87', manager = fevent_manager)
        wait_for_textbox()
        branch_if(Variables[0x6021], '==', 0x6, 'derby_88', invert=True)
        say(Variables[0x3002], 0x24147, 0x4D, anim=None, post_anim=None, tail_hoffset=0xFF)
        branch('derby_89')

        label('derby_88', manager = fevent_manager)
        branch_if(Variables[0x6021], '==', 0xC, 'derby_90', invert=True)
        say(Variables[0x3002], 0x24147, 0x4E, anim=None, post_anim=None, tail_hoffset=0xFF)
        branch('derby_89')

        label('derby_90', manager = fevent_manager)
        Variables[0x1000] = 0x9
        Variables[0x1000] = Variables[0x1000] + 0x1
        random_below(Variables[0x1000], Variables[0x1001])
        Variables[0xA001] = Variables[0x1001] + 0x1
        branch_if(Variables[0xA001], '==', 0x1, 'derby_91', invert=True)
        say(Variables[0x3002], 0x24147, 0x45, anim=None, post_anim=None, tail_hoffset=0xFF)
        branch('derby_89')

        label('derby_91', manager = fevent_manager)
        branch_if(Variables[0xA001], '==', 0x2, 'derby_92', invert=True)
        say(Variables[0x3002], 0x24147, 0x46, anim=None, post_anim=None, tail_hoffset=0xFF)
        branch('derby_89')

        label('derby_92', manager = fevent_manager)
        branch_if(Variables[0xA001], '==', 0x3, 'derby_93', invert=True)
        say(Variables[0x3002], 0x24147, 0x47, anim=None, post_anim=None, tail_hoffset=0xFF)
        branch('derby_89')

        label('derby_93', manager = fevent_manager)
        branch_if(Variables[0xA001], '==', 0x4, 'derby_94', invert=True)
        say(Variables[0x3002], 0x24147, 0x48, anim=None, post_anim=None, tail_hoffset=0xFF)
        branch('derby_89')

        label('derby_94', manager = fevent_manager)
        branch_if(Variables[0xA001], '==', 0x5, 'derby_95', invert=True)
        say(Variables[0x3002], 0x24147, 0x49, anim=None, post_anim=None, tail_hoffset=0xFF)
        branch('derby_89')

        label('derby_95', manager = fevent_manager)
        branch_if(Variables[0xA001], '==', 0x6, 'derby_96', invert=True)
        say(Variables[0x3002], 0x24147, 0x4A, anim=None, post_anim=None, tail_hoffset=0xFF)
        branch('derby_89')

        label('derby_96', manager = fevent_manager)
        branch_if(Variables[0xA001], '==', 0x7, 'derby_97', invert=True)
        say(Variables[0x3002], 0x24147, 0x4B, anim=None, post_anim=None, tail_hoffset=0xFF)
        branch('derby_89')

        label('derby_97', manager = fevent_manager)
        branch_if(Variables[0xA001], '==', 0x8, 'derby_98', invert=True)
        say(Variables[0x3002], 0x24147, 0x4C, anim=None, post_anim=None, tail_hoffset=0xFF)
        branch('derby_89')

        label('derby_98', manager = fevent_manager)
        say(Variables[0x3002], 0x24147, 0x4B, anim=None, post_anim=None, tail_hoffset=0xFF)

        label('derby_89', manager = fevent_manager)
        set_animation(Variables[0x3002], 0x03)
        branch('derby_99')

        label('derby_85', manager = fevent_manager)
        say(Variables[0x3002], 0x24147, 0x41, tail_hoffset=0xFF)

        label('derby_99', manager = fevent_manager)
        wait(30)
        set_animation(Variables[0x3002], 0x03)
        branch_if(Variables[0x3019], '==', 0x0, 'derby_100', invert=True)
        emit_command(0x00F5, [0x00, 0x01, 0x00])
        branch_if(0x0, '==', 0x0, 'derby_101', invert=True)

        label('derby_102', manager = fevent_manager)
        wait(1)
        branch_if(Variables[0x3017], '==', 0x1, 'derby_102')

        label('derby_101', manager = fevent_manager)
        branch('derby_103')

        label('derby_100', manager = fevent_manager)
        branch_if(Variables[0x3008], '==', 0x0, 'derby_104', invert=True)
        emit_command(0x00F5, [0x01, 0x01, 0x00])
        branch_if(0x0, '==', 0x0, 'derby_105', invert=True)

        label('derby_106', manager = fevent_manager)
        wait(1)
        branch_if(Variables[0x3018], '==', 0x1, 'derby_106')

        label('derby_105', manager = fevent_manager)
        branch('derby_103')

        label('derby_104', manager = fevent_manager)
        emit_command(0x00F5, [0x00, 0x01, 0x00])
        branch_if(0x0, '==', 0x0, 'derby_103', invert=True)

        label('derby_107', manager = fevent_manager)
        wait(1)
        branch_if(Variables[0x3017], '==', 0x1, 'derby_107')

        label('derby_103', manager = fevent_manager)
        branch_if(Variables[0x3008], '==', 0x0, 'derby_108', invert=True)
        emit_command(0x018C, [Variables[0x3008], 0x0000], Variables[0x1007])
        branch('derby_109')

        label('derby_108', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], 0x00C0], Variables[0x1007])

        label('derby_109', manager = fevent_manager)
        branch_if(0x1, '==', 0x1, 'derby_110', invert=True)
        emit_command(0x01A0)
        branch('derby_111')

        label('derby_110', manager = fevent_manager)
        emit_command(0x01A1)

        label('derby_111', manager = fevent_manager)

    print(f"!!assemble_mushroom_derby!! length of sub 0x5E: {len(script.subroutines[0x5E].commands)}")
    script.subroutines[0x1B].commands[23] = CodeCommandWithOffsets(0x0002, [0x01, Variables[0x6022], Variables[0x6021], 0x00000001, PLACEHOLDER_OFFSET], offset_arguments = {4: 'derby_prize'})
    script.header.subroutine_table = [0] * len(script.subroutines)
    update_commands_with_offsets(fevent_manager, [script.header.post_table_subroutine, *script.subroutines], len(script.header.to_bytes(fevent_manager)))

    for i, treasure in enumerate(current_treasure_list):
        if treasure.item & 0xF000 == 0x3000:
            badge_dict[treasure.item] = f"{treasure_strings[5][0]} - {treasure_strings[5][1]} x {i + 1}"
    
    return return_treasure, badge_dict


##################################################################################
##################################################################################
##################################################################################


def assemble_hide_seek_toad(fevent_manager, treasure_list, treasure_strings, badge_dict):
    room_id = 0x0129
    script = fevent_manager.fevent_chunks[room_id][0]

    available_object = 0x04
    treasure_textbox_id = 0x0F

    current_treasure = treasure_list[0]
    return_treasure = treasure_list[1:]
        
    script.header.sprite_groups[available_object] = current_treasure.obj
    for i in range(6):
        if not fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + i]:
            continue
            
        fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + i].entries[treasure_textbox_id] = current_treasure.textbox[i]
        fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + i].textbox_sizes[treasure_textbox_id] = current_treasure.textbox_sizes[i]
    
    fevent_manager.fevent_chunks[room_id][2].text_tables[FEVENT_PADDING_TEXT_TABLE_ID] = b""
    language_table_size = len(fevent_manager.fevent_chunks[room_id][2].to_bytes())
    fevent_manager.fevent_chunks[room_id][2].text_tables[FEVENT_PADDING_TEXT_TABLE_ID] = (
        b"\x00"
        * (
            (-(language_table_size + 1) % LANGUAGE_TABLE_ALIGNMENT)
            + 1
        )
    )

    cast(SubroutineExt, script.subroutines[0x10]).name = 'sub_0x10'
    cast(SubroutineExt, script.subroutines[0x2E]).name = 'sub_0x2e'
    cast(SubroutineExt, script.subroutines[0x2F]).name = 'sub_0x2f'
    script.subroutines.pop() # this might cause issues but idk lmao, the room just refuses to load if i don't get rid of the last sub tho

    @subroutine(subs = script.subroutines, hdr = script.header)
    def hide_and_seek(sub: Subroutine):
        Variables[0xE9A1] = 0x1
        emit_command(0x00F4, [0x00, 0x01], Variables[0xA001])
        branch_if(Variables[0xA001], '==', 0x22, 'seek_toad_0', invert=True)
        emit_command(0x0113, [0x00, 0xFFFF])
        emit_command(0x0114, [0x00])
        branch('seek_toad_1')

        label('seek_toad_0', manager = fevent_manager)
        branch_if(Variables[0xA001], '==', 0x23, 'seek_toad_1', invert=True)
        emit_command(0x0113, [0x00, 0xFFFF])
        emit_command(0x0114, [0x00])

        label('seek_toad_1', manager = fevent_manager)
        emit_command(0x00C1, [0x00])
        emit_command(0x00C1, [0x01])
        emit_command(0x00E8, [0x00])
        wait(1)
        start_thread_here_and_branch(0x00, 'seek_toad_2')
        emit_command(0x006E, [-0x01, 0x00, 0x00])
        emit_command(0x00B2, [-0x01, 0x00, 0x01B6, 0x017E, 0x0020, 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x0 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'seek_toad_3', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'seek_toad_4', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('seek_toad_5')

        label('seek_toad_4', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('seek_toad_5', manager = fevent_manager)
        push(Variables[0x1001])

        label('seek_toad_7', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'seek_toad_6', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(3)
        branch('seek_toad_7')

        label('seek_toad_6', manager = fevent_manager)
        branch('seek_toad_8')

        label('seek_toad_3', manager = fevent_manager)
        wait(3)

        label('seek_toad_8', manager = fevent_manager)
        return_()

        label('seek_toad_2', manager = fevent_manager)
        start_thread_here_and_branch(0x01, 'seek_toad_9')
        emit_command(0x006E, [-0x01, 0x00, 0x00])
        emit_command(0x00B2, [-0x01, 0x00, 0x01D0, 0x017E, 0x0020, 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x0 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'seek_toad_10', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'seek_toad_11', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('seek_toad_12')

        label('seek_toad_11', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('seek_toad_12', manager = fevent_manager)
        push(Variables[0x1001])

        label('seek_toad_14', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'seek_toad_13', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(3)
        branch('seek_toad_14')

        label('seek_toad_13', manager = fevent_manager)
        branch('seek_toad_15')

        label('seek_toad_10', manager = fevent_manager)
        wait(3)

        label('seek_toad_15', manager = fevent_manager)
        return_()

        label('seek_toad_9', manager = fevent_manager)
        unk_thread_branch_0x004a(0x10, 'seek_toad_16')
        emit_command(0x0071, [-0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
        emit_command(0x00B2, [-0x01, 0x00, 0x01C3, 0x0160, 0x0020, 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [-0x01])
        set_animation(Self, 0x03)
        emit_command(0x00D1, [-0x01, 0x00, 0x04])
        return_()

        label('seek_toad_16', manager = fevent_manager)
        emit_command(0x0071, [0x0E, 0x00, 0x00, 0x00, 0x00, 0x00])
        join_thread(0x00)
        wait(30)
        say(0x10, Sound.SPEECH_TOAD, 0x0E, tail_direction=0x00, tail_hoffset=0xFF)
        wait(30)
        get_actor_attribute(Actors.MARIO, 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x4 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'seek_toad_17', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'seek_toad_18', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('seek_toad_19')

        label('seek_toad_18', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('seek_toad_19', manager = fevent_manager)
        push(Variables[0x1001])

        label('seek_toad_21', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'seek_toad_20', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [0x00, 0x01, Variables[0x1002]])
        wait(3)
        branch('seek_toad_21')

        label('seek_toad_20', manager = fevent_manager)
        branch('seek_toad_22')

        label('seek_toad_17', manager = fevent_manager)
        wait(3)

        label('seek_toad_22', manager = fevent_manager)
        get_actor_attribute(Actors.LUIGI, 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x6 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'seek_toad_23', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'seek_toad_24', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('seek_toad_25')

        label('seek_toad_24', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('seek_toad_25', manager = fevent_manager)
        push(Variables[0x1001])

        label('seek_toad_27', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'seek_toad_26', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [0x01, 0x01, Variables[0x1002]])
        wait(3)
        branch('seek_toad_27')

        label('seek_toad_26', manager = fevent_manager)
        branch('seek_toad_28')

        label('seek_toad_23', manager = fevent_manager)
        wait(3)

        label('seek_toad_28', manager = fevent_manager)
        wait(30)
        emit_command(0x00F4, [0x00, 0x01], Variables[0xA00F])
        branch_if(Variables[0xA00F], '==', 0x20, 'seek_toad_29', invert=True)
        start_thread_here_and_branch(0x13, 'seek_toad_30')
        set_animation(Self, 0x01)
        emit_command(0x0091, [-0x01, 0x04, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        get_actor_attribute(Actors.MARIO, ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Z_POSITION, res=Variables[0x1002])
        Variables[0x1000] = Variables[0x1000] + 0x6
        Variables[0x1001] = Variables[0x1001] + 0x14
        Variables[0x1002] = Variables[0x1002] + 0x2F
        if current_treasure.no_string: # if the object is a coin, move it down into mario's palm
            Variables[0x1002] = Variables[0x1002] - 8
        emit_command(0x00BD, [-0x01, 0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002]])
        emit_command(0x0063, [-0x01, 0x01])
        return_()

        label('seek_toad_30', manager = fevent_manager)
        set_animation(Actors.MARIO, 0x00)
        emit_command(0x0091, [0x00, 0x11, 0x0000, 0x0001, 0x01])
        emit_command(0x0094, [0x00, 0x0000, 0x00])
        emit_command(0x0093, [0x00])
        branch('seek_toad_31')

        label('seek_toad_29', manager = fevent_manager)
        start_thread_here_and_branch(0x13, 'seek_toad_32')
        set_animation(Self, 0x01)
        emit_command(0x0091, [-0x01, 0x04, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        get_actor_attribute(Actors.MARIO, ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Z_POSITION, res=Variables[0x1002])
        Variables[0x1000] = Variables[0x1000] + 0x6
        Variables[0x1001] = Variables[0x1001] + 0x14
        Variables[0x1002] = Variables[0x1002] + 0x40
        if current_treasure.no_string: # if the object is a coin, move it down into mario's palm
            Variables[0x1002] = Variables[0x1002] - 8
        emit_command(0x00BD, [-0x01, 0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002]])
        emit_command(0x0063, [-0x01, 0x01])
        return_()

        label('seek_toad_32', manager = fevent_manager)
        set_animation(Actors.MARIO, 0x00)
        emit_command(0x0091, [0x00, 0x0D, 0x0000, 0x0001, 0x01])
        emit_command(0x0094, [0x00, 0x0000, 0x00])
        emit_command(0x0093, [0x00])

        label('seek_toad_31', manager = fevent_manager)
        emit_command(0x01CE, [ITEM_SFX[current_treasure.sfx], 0x00, 0x0000, 0x0000, 0x0001, 0x00])
        current_treasure.to_script_command()
        if not current_treasure.no_string:
            emit_command(0x01BB, [-0x8000, 0x0010, 0x00, 0x00, 0x03, 0x00, -0x01, -0x01, -0x0001, 0x01, 0x00, 0x00000000, 0x0F, 0x00, 0x08, 0x00, 0x0000, -0x01], Variables[0x1000])
            wait_for_textbox()
        else:
            wait(60)
        wait(30)
        set_animation(0x13, 0x01)
        emit_command(0x0091, [0x13, 0x0F, 0x0000, -0x0001, 0x01])
        emit_command(0x0094, [0x13, 0x0000, 0x00])
        emit_command(0x0063, [0x13, 0x00])
        start_thread_here_and_branch(0x00, 'seek_toad_33')
        emit_command(0x0092, [-0x01])
        emit_command(0x0097, [-0x01])
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x0 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'seek_toad_34', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'seek_toad_35', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('seek_toad_36')

        label('seek_toad_35', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('seek_toad_36', manager = fevent_manager)
        push(Variables[0x1001])

        label('seek_toad_38', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'seek_toad_37', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(3)
        branch('seek_toad_38')

        label('seek_toad_37', manager = fevent_manager)
        branch('seek_toad_39')

        label('seek_toad_34', manager = fevent_manager)
        wait(3)

        label('seek_toad_39', manager = fevent_manager)
        return_()

        label('seek_toad_33', manager = fevent_manager)
        unk_thread_branch_0x004a(0x01, 'seek_toad_40')
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x0 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'seek_toad_41', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'seek_toad_42', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('seek_toad_43')

        label('seek_toad_42', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('seek_toad_43', manager = fevent_manager)
        push(Variables[0x1001])

        label('seek_toad_45', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'seek_toad_44', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(3)
        branch('seek_toad_45')

        label('seek_toad_44', manager = fevent_manager)
        branch('seek_toad_46')

        label('seek_toad_41', manager = fevent_manager)
        wait(3)

        label('seek_toad_46', manager = fevent_manager)
        return_()

        label('seek_toad_40', manager = fevent_manager)
        join_thread(0x00)
        say(0x10, Sound.SPEECH_TOAD, 0x10, tail_hoffset=0xFF)
        emit_command(0x0071, [0x10, 0x01, 0x01, 0x01, 0x01, 0x01])
        branch_if(0x0, '==', 0x0, 'seek_toad_47', invert=True)
        get_actor_attribute(Actors.MARIO, 0x0E, res=Variables[0x1000])
        Variables[0x1000] = Variables[0x1000] + 0x4
        Variables[0x1000] = Variables[0x1000] & 0x7
        load_data_from_array('sub_0x2e', Variables[0x1000], res=Variables[0x1001])
        load_data_from_array('sub_0x2f', Variables[0x1000], res=Variables[0x1002])
        Variables[0x1000] = Variables[0x1000] & 0x1
        branch_if(Variables[0x1000], '==', 0x0, 'seek_toad_48', invert=True)
        Variables[0x1001] = Variables[0x1001] * 0x14
        Variables[0x1002] = Variables[0x1002] * 0x14
        branch('seek_toad_49')

        label('seek_toad_48', manager = fevent_manager)
        Variables[0x1001] = Variables[0x1001] * 0xF
        Variables[0x1002] = Variables[0x1002] * 0xF

        label('seek_toad_49', manager = fevent_manager)
        get_actor_attribute(Actors.MARIO, ActorAttribute.X_POSITION, res=Variables[0x1003])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Y_POSITION, res=Variables[0x1004])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Z_POSITION, res=Variables[0x1005])
        Variables[0x1001] = Variables[0x1001] + Variables[0x1003]
        Variables[0x1002] = Variables[0x1002] + Variables[0x1004]
        emit_command(0x00B2, [0x01, 0x00, Variables[0x1001], Variables[0x1002], Variables[0x1005], 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x01])
        emit_command(0x00D2, [0x01, 0x00])

        label('seek_toad_47', manager = fevent_manager)
        emit_command(0x00E9, [0x00, 0x00])
        emit_command(0x00BB, [0x01])
        emit_command(0x006E, [0x00, 0x01, 0x01])
        emit_command(0x006E, [0x01, 0x01, 0x01])
        emit_command(0x0073, [0x0E])
        call('sub_0x10')

    script.subroutines[0x11].commands[16] = CodeCommandWithOffsets(0x0002, [0x00, Variables[0xE9A0], 0x00000001, 0x00000001, PLACEHOLDER_OFFSET], offset_arguments = {4: 'hide_and_seek'})
    script.header.subroutine_table = [0] * len(script.subroutines)
    update_commands_with_offsets(fevent_manager, [script.header.post_table_subroutine, *script.subroutines], len(script.header.to_bytes(fevent_manager)))

    if current_treasure.item & 0xF000 == 0x3000:
        badge_dict[current_treasure.item] = {treasure_strings[6][0]}
    
    return return_treasure, badge_dict


##################################################################################
##################################################################################
##################################################################################


def assemble_kuzzle_puzzles(fevent_manager, treasure_list, treasure_strings, badge_dict):
    room_id = 0x0287
    script = fevent_manager.fevent_chunks[room_id][0]

    available_objects = [0x12, 0x13, 0x14] # this list of objects needs to be expanded
    treasure_textbox_base_id = 0x3C # this takes advantage of 3 unused textboxes to make the previously duplicated treasure unique
    current_treasure_list = []
    return_treasure = []

    used_objects = set([0x010002FD])
    index = 0
    while len(current_treasure_list) != 12:
        objects_full = len(script.header.sprite_groups) - len(available_objects) + len(used_objects) == 23
        if objects_full and (treasure_list[index].obj not in used_objects):
            return_treasure.append(treasure_list[index])
            print(f"!!assemble_kuzzle_puzzles!! rejected item number {index} because the object pool is full")
        elif treasure_list[index].obj == 0x01000009:
            return_treasure.append(treasure_list[index])
            print(f"!!assemble_kuzzle_puzzles!! rejected item number {index} because it was a single coin")
        else:
            used_objects.add(treasure_list[index].obj)
            current_treasure_list.append(treasure_list[index])
        index += 1
    return_treasure.extend(treasure_list[index:])
        
    for i in range(4):
        for j in range(6):
            if not fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + j]:
                continue
            
            textbox = current_treasure_list[i * 3].textbox[j].replace(b"\xff\x11\x01\xff\x0a\x00", b"\xff\x11\x00\xff\x01\x00") # replace "end textbox" with "continue textbox"
            textbox += current_treasure_list[(i * 3) + 1].textbox[j].replace(b"\xff\x11\x01\xff\x0a\x00", b"\xff\x11\x00\xff\x01\x00") # replace "end textbox" with "continue textbox"
            textbox += current_treasure_list[(i * 3) + 2].textbox[j]

            textbox_size = [0, 0]
            textbox_size[0] = max(current_treasure_list[i * 3].textbox_sizes[j][0], current_treasure_list[(i * 3) + 1].textbox_sizes[j][0], current_treasure_list[(i * 3) + 2].textbox_sizes[j][0])
            textbox_size[1] = max(current_treasure_list[i * 3].textbox_sizes[j][1], current_treasure_list[(i * 3) + 1].textbox_sizes[j][1], current_treasure_list[(i * 3) + 2].textbox_sizes[j][1])

            fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + j].entries[treasure_textbox_base_id + i] = textbox
            fevent_manager.fevent_chunks[room_id][2].text_tables[0x43 + j].textbox_sizes[treasure_textbox_base_id + i] = textbox_size
    
    fevent_manager.fevent_chunks[room_id][2].text_tables[FEVENT_PADDING_TEXT_TABLE_ID] = b""
    language_table_size = len(fevent_manager.fevent_chunks[room_id][2].to_bytes())
    fevent_manager.fevent_chunks[room_id][2].text_tables[FEVENT_PADDING_TEXT_TABLE_ID] = (
        b"\x00"
        * (
            (-(language_table_size + 1) % LANGUAGE_TABLE_ALIGNMENT)
            + 1
        )
    )
    
    print(f"!!assemble_kuzzle_puzzles!! no. of used objects: {len(used_objects)}")
    for i, obj in enumerate(used_objects):
        if i < len(available_objects):
            script.header.sprite_groups[available_objects[i]] = obj
        else:
            script.header.sprite_groups.append(obj)
    
    cast(SubroutineExt, script.subroutines[0x0F]).name = 'sub_0xf'
    cast(SubroutineExt, script.subroutines[0x20]).name = 'sub_0x20'
    cast(SubroutineExt, script.subroutines[0x21]).name = 'sub_0x21'
    cast(SubroutineExt, script.subroutines[0x2D]).name = 'sub_0x2d'

    @subroutine(subs = script.subroutines, hdr = script.header)
    def puzzle_prizes(sub: Subroutine):
        wait(30)
        Variables[0x1000] = 0 # number of completed puzzles
        Variables[0x1000] += Variables[0xEAD9]
        Variables[0x1000] += Variables[0xEADA]
        Variables[0x1000] += Variables[0xEADB]
        Variables[0x1000] += Variables[0xEADC]
        
        # in the original there's a check for mini mario, but if you talk to kuzzle as mini mario you automatically become big so idk
        set_animation(Actors.MARIO, 0x00)
        emit_command(0x0091, [0x00, 0x07, 0x0000, 0x0001, 0x01])
        emit_command(0x0094, [0x00, 0x0000, 0x00])
        emit_command(0x0093, [0x00])

        for i in range(4):
            branch_if(Variables[0x1000], '!=', i + 1, f'prize_{i}')
            sound = max(current_treasure_list[(i * 3)].sfx, current_treasure_list[(i * 3) + 1].sfx, current_treasure_list[(i * 3) + 2].sfx)
            emit_command(0x01CE, [ITEM_SFX[sound], 0x0F, 0x0000, 0x0000, 0x0001, 0x00]) # this command is the treasure's sound effect
            for j in range(3):
                current_obj = script.header.sprite_groups.index(current_treasure_list[(i * 3) + j].obj)

                get_actor_attribute(Actors.MARIO, ActorAttribute.X_POSITION, res=Variables[0x1000])
                get_actor_attribute(Actors.MARIO, ActorAttribute.Y_POSITION, res=Variables[0x1001])
                get_actor_attribute(Actors.MARIO, ActorAttribute.Z_POSITION, res=Variables[0x1002])
                Variables[0x1000] = Variables[0x1000] + [0x9, 0x10, 0x4][j]
                Variables[0x1002] = Variables[0x1002] + [0x36, 0x2C, 0x2C][j]
                if current_treasure_list[(i * 3) + j].no_string: # if the object is a coin, move it down into mario's palm
                    Variables[0x1002] = Variables[0x1002] - 8
                emit_command(0x00BD, [0x0F + j, 0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002]])

                set_animation(0x0F + j, 0x01)
                emit_command(0x0091, [0x0F + j, current_obj, 0x0000, -0x0001, 0x01]) # arg 1 in this command is loaded obj number
                emit_command(0x0094, [0x0F + j, 0x0000, 0x00])

                get_actor_attribute(Actors.MARIO, 0x0A, res=Variables[0x1000])
                Variables[0x1000] = Variables[0x1000] - 0x1
                Variables[0x1001] = Variables[0x1000] & 0xF
                Variables[0x1002] = Variables[0x1000] & 0xF0
                Variables[0x1002] = Variables[0x1002] >> 0x4
                Variables[0x1003] = Variables[0x1001] - Variables[0x1002]
                emit_command(0x0078, [0x0F + j, Variables[0x1003]])

                emit_command(0x0063, [0x0F + j, 0x01])
                emit_command(0x0064, [0x0F + j, 0x01])
                current_treasure_list[(i * 3) + j].to_script_command() # this command is the given treasure
            emit_command(0x01BB, [-0x8000, 0x0010, 0x00, 0x00, 0x03, 0x00, -0x01, -0x01, -0x0001, 0x01, 0x00, 0x00000000, treasure_textbox_base_id + i, 0x00, 0x08, 0x00, 0x0000, -0x01], Variables[0x1000])
            wait_for_textbox()
            label(f'prize_{i}', manager = fevent_manager)
        wait(60)
    
    @subroutine(subs = script.subroutines, hdr = script.header)
    def sub_0x1(sub: Subroutine): # the original sub 0x01 is too far away for the kuzzle sub to reach, so i have to duplicate it
        label('sub_0x1_replacement_12', manager = fevent_manager)
        wait(1)
        Variables[0x1000] = 0x14
        Variables[0x1000] = Variables[0x1000] + 0x1
        random_below(Variables[0x1000], Variables[0x1001])
        Variables[0xA001] = Variables[0x1001] + 0x14
        wait(Variables[0xA001])
        set_animation(Self, 0x00)
        emit_command(0x0091, [-0x01, -0x01, 0x0018, 0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        emit_command(0x0093, [-0x01])
        Variables[0x1000] = 0x14
        Variables[0x1000] = Variables[0x1000] + 0x1
        random_below(Variables[0x1000], Variables[0x1001])
        Variables[0xA001] = Variables[0x1001] + 0x14
        wait(Variables[0xA001])
        set_animation(Self, 0x03)
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x5 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'sub_0x1_replacement_0', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'sub_0x1_replacement_1', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('sub_0x1_replacement_2')

        label('sub_0x1_replacement_1', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('sub_0x1_replacement_2', manager = fevent_manager)
        push(Variables[0x1001])

        label('sub_0x1_replacement_4', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'sub_0x1_replacement_3', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(5)
        branch('sub_0x1_replacement_4')

        label('sub_0x1_replacement_3', manager = fevent_manager)
        branch('sub_0x1_replacement_5')

        label('sub_0x1_replacement_0', manager = fevent_manager)
        wait(5)

        label('sub_0x1_replacement_5', manager = fevent_manager)
        Variables[0x1000] = 0x1E
        Variables[0x1000] = Variables[0x1000] + 0x1
        random_below(Variables[0x1000], Variables[0x1001])
        Variables[0xA001] = Variables[0x1001] + 0x1E
        wait(Variables[0xA001])
        set_animation(Self, 0x00)
        emit_command(0x0091, [-0x01, -0x01, 0x0019, 0x0001, 0x01])
        emit_command(0x0094, [-0x01, 0x0000, 0x00])
        emit_command(0x0093, [-0x01])
        Variables[0x1000] = 0x1E
        Variables[0x1000] = Variables[0x1000] + 0x1
        random_below(Variables[0x1000], Variables[0x1001])
        Variables[0xA001] = Variables[0x1001] + 0x1E
        wait(Variables[0xA001])
        set_animation(Self, 0x03)
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x3 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'sub_0x1_replacement_6', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'sub_0x1_replacement_7', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('sub_0x1_replacement_8')

        label('sub_0x1_replacement_7', manager = fevent_manager)
        Variables[0x1002] = 0x1

        label('sub_0x1_replacement_8', manager = fevent_manager)
        push(Variables[0x1001])

        label('sub_0x1_replacement_10', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'sub_0x1_replacement_9', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(5)
        branch('sub_0x1_replacement_10')

        label('sub_0x1_replacement_9', manager = fevent_manager)
        branch('sub_0x1_replacement_11')

        label('sub_0x1_replacement_6', manager = fevent_manager)
        wait(5)

        label('sub_0x1_replacement_11', manager = fevent_manager)
        branch('sub_0x1_replacement_12', type=0x00)
    
    @subroutine(subs = script.subroutines, hdr = script.header)
    def kuzzle_reward(sub: Subroutine):
        emit_command(0x0063, [0x06, 0x00])
        emit_command(0x0064, [0x06, 0x00])
        emit_command(0x0063, [0x07, 0x00])
        emit_command(0x0064, [0x07, 0x00])
        emit_command(0x0063, [0x08, 0x00])
        emit_command(0x0064, [0x08, 0x00])
        emit_command(0x0063, [0x09, 0x00])
        emit_command(0x0064, [0x09, 0x00])
        emit_command(0x0063, [0x0A, 0x00])
        emit_command(0x0064, [0x0A, 0x00])
        emit_command(0x0063, [0x0D, 0x00])
        emit_command(0x0064, [0x0D, 0x00])
        emit_command(0x0063, [0x0B, 0x00])
        emit_command(0x0064, [0x0B, 0x00])
        emit_command(0x01D6, [0x00, 0x00, 0x00])
        branch_if(Variables[0xEAE3], '==', 0x1, 'kuzzle_0', invert=True)
        wait(30)
        set_animation(0x04, 0x01)
        emit_command(0x0091, [0x04, -0x01, 0x0013, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        say(0x04, 0x24145, 0x32, anim=None, post_anim=0x01, tail_hoffset=0xFF)
        emit_command(0x0091, [0x04, -0x01, 0x000B, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        set_animation(0x04, 0x03)
        Variables[0xEAE3] = 0x0
        branch('kuzzle_1', type=0x00)
    
        label('kuzzle_0', manager = fevent_manager)
        Variables[0x1000] = Variables[0x900B]
        branch('kuzzle_2')
        branch('kuzzle_3')
    
        label('kuzzle_2', manager = fevent_manager)
        branch_if(0x1, '!=', Variables[0x1000], 'kuzzle_4')
        call('sub_0xf')
        branch('kuzzle_1', type=0x00)
        branch('kuzzle_3')
    
        label('kuzzle_4', manager = fevent_manager)
        branch_if(0x2, '!=', Variables[0x1000], 'kuzzle_5')
        branch_if(Variables[0xEAD9], '==', 0x1, 'kuzzle_6', invert=True)
        call('sub_0xf')
        branch('kuzzle_1', type=0x00)
        branch('kuzzle_7')
    
        label('kuzzle_6', manager = fevent_manager)
        set_animation(0x0E, 0x01)
        emit_command(0x0098, [0x0E, 0x10, 0x08, 0x0000, -0x0001, 0x01, 0x01])
        emit_command(0x0094, [0x0E, 0x0000, 0x00])
    
        label('kuzzle_7', manager = fevent_manager)
        branch('kuzzle_3')
    
        label('kuzzle_5', manager = fevent_manager)
        branch_if(0x3, '!=', Variables[0x1000], 'kuzzle_8')
        branch_if(Variables[0xEADA], '==', 0x1, 'kuzzle_9', invert=True)
        call('sub_0xf')
        branch('kuzzle_1', type=0x00)
        branch('kuzzle_10')
    
        label('kuzzle_9', manager = fevent_manager)
        set_animation(0x0E, 0x01)
        emit_command(0x0098, [0x0E, 0x0F, 0x07, 0x0000, -0x0001, 0x01, 0x01])
        emit_command(0x0094, [0x0E, 0x0000, 0x00])
    
        label('kuzzle_10', manager = fevent_manager)
        branch('kuzzle_3')
    
        label('kuzzle_8', manager = fevent_manager)
        branch_if(0x4, '!=', Variables[0x1000], 'kuzzle_11')
        branch_if(Variables[0xEADB], '==', 0x1, 'kuzzle_12', invert=True)
        call('sub_0xf')
        branch('kuzzle_1', type=0x00)
        branch('kuzzle_13')
    
        label('kuzzle_12', manager = fevent_manager)
        set_animation(0x0E, 0x01)
        emit_command(0x0098, [0x0E, 0x0E, 0x06, 0x0000, -0x0001, 0x01, 0x01])
        emit_command(0x0094, [0x0E, 0x0000, 0x00])
    
        label('kuzzle_13', manager = fevent_manager)
        branch('kuzzle_3')
    
        label('kuzzle_11', manager = fevent_manager)
        branch_if(0x5, '!=', Variables[0x1000], 'kuzzle_3')
        branch_if(Variables[0xEADC], '==', 0x1, 'kuzzle_14', invert=True)
        call('sub_0xf')
        branch('kuzzle_1', type=0x00)
        branch('kuzzle_3')
    
        label('kuzzle_14', manager = fevent_manager)
        set_animation(0x0E, 0x01)
        emit_command(0x0098, [0x0E, 0x11, 0x09, 0x0000, -0x0001, 0x01, 0x01])
        emit_command(0x0094, [0x0E, 0x0000, 0x00])
    
        label('kuzzle_3', manager = fevent_manager)
        branch_if(Variables[0xEAE1], '==', 0x1, 'kuzzle_15', invert=True)
        wait(40)
        emit_command(0x014B, [-0x10, 0x00, 0x0010])
        emit_command(0x014C)
        set_animation(0x04, 0x01)
        emit_command(0x0091, [0x04, -0x01, 0x0013, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        say(0x04, 0x24145, 0x36, anim=None, post_anim=0x01, tail_hoffset=0xFF)
        emit_command(0x0091, [0x04, -0x01, 0x000B, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        set_animation(0x04, 0x03)
        wait(30)
        branch('kuzzle_1', type=0x00)
    
        label('kuzzle_15', manager = fevent_manager)
        emit_command(0x00F5, [0x00, 0x00, 0x01])
        emit_command(0x00F4, [0x00, 0x01], Variables[0xA00F])
        branch_if(Variables[0xA00F], '==', 0x20, 'kuzzle_16', invert=True)
        start_thread_here_and_branch(0x0E, 'kuzzle_17')
        get_actor_attribute(Actors.MARIO, ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Z_POSITION, res=Variables[0x1002])
        Variables[0x1000] = Variables[0x1000] + 0x6
        Variables[0x1001] = Variables[0x1001] + 0x0
        Variables[0x1002] = Variables[0x1002] + 0x1B
        emit_command(0x00BD, [-0x01, 0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002]])
        emit_command(0x0063, [-0x01, 0x01])
        emit_command(0x0064, [-0x01, 0x01])
        get_actor_attribute(Actors.MARIO, 0x0A, res=Variables[0x1000])
        Variables[0x1000] = Variables[0x1000] - 0x1
        Variables[0x1001] = Variables[0x1000] & 0xF
        Variables[0x1002] = Variables[0x1000] & 0xF0
        Variables[0x1002] = Variables[0x1002] >> 0x4
        Variables[0x1003] = Variables[0x1001] - Variables[0x1002]
        emit_command(0x0078, [-0x01, Variables[0x1003]])
        return_()
    
        label('kuzzle_17', manager = fevent_manager)
        set_animation(Actors.MARIO, 0x00)
        emit_command(0x0091, [0x00, 0x06, 0x0000, 0x0001, 0x01])
        emit_command(0x0094, [0x00, 0x0000, 0x00])
        emit_command(0x0093, [0x00])
        branch('kuzzle_18')
    
        label('kuzzle_16', manager = fevent_manager)
        start_thread_here_and_branch(0x0E, 'kuzzle_19')
        get_actor_attribute(Actors.MARIO, ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Z_POSITION, res=Variables[0x1002])
        Variables[0x1000] = Variables[0x1000] + 0x6
        Variables[0x1001] = Variables[0x1001] + 0x0
        Variables[0x1002] = Variables[0x1002] + 0x2C
        emit_command(0x00BD, [-0x01, 0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002]])
        emit_command(0x0063, [-0x01, 0x01])
        emit_command(0x0064, [-0x01, 0x01])
        get_actor_attribute(Actors.MARIO, 0x0A, res=Variables[0x1000])
        Variables[0x1000] = Variables[0x1000] - 0x1
        Variables[0x1001] = Variables[0x1000] & 0xF
        Variables[0x1002] = Variables[0x1000] & 0xF0
        Variables[0x1002] = Variables[0x1002] >> 0x4
        Variables[0x1003] = Variables[0x1001] - Variables[0x1002]
        emit_command(0x0078, [-0x01, Variables[0x1003]])
        return_()
    
        label('kuzzle_19', manager = fevent_manager)
        set_animation(Actors.MARIO, 0x00)
        emit_command(0x0091, [0x00, 0x07, 0x0000, 0x0001, 0x01])
        emit_command(0x0094, [0x00, 0x0000, 0x00])
        emit_command(0x0093, [0x00])
    
        label('kuzzle_18', manager = fevent_manager)
        emit_command(0x00D1, [0x01, 0x00, 0x01])
        emit_command(0x01CD, [0x02000090, 0x0080, 0x0060, 0x0000, 0x0000, 0x0001, 0x00])
        wait(60)
        set_animation(0x04, 0x01)
        emit_command(0x0091, [0x04, -0x01, 0x0013, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        say(0x04, 0x24145, 0x1D, anim=None, post_anim=0x01, tail_hoffset=0xFF)
        emit_command(0x0091, [0x04, -0x01, 0x000B, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        set_animation(0x04, 0x03)
        wait(30)
        set_animation(0x04, 0x01)
        emit_command(0x0091, [0x04, -0x01, 0x0013, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        say(0x04, 0x24145, 0x1E, anim=None, post_anim=0x01, tail_hoffset=0xFF)
        emit_command(0x0091, [0x04, -0x01, 0x000B, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        set_animation(0x04, 0x03)
        wait(30)
        emit_command(0x01CE, [0x00020039, 0x0E, 0x0000, 0x0000, 0x0001, 0x00])
        get_actor_attribute(0x0E, ActorAttribute.X_POSITION, res=Variables[0x1000])
        get_actor_attribute(0x0E, ActorAttribute.Y_POSITION, res=Variables[0x1001])
        get_actor_attribute(0x0E, ActorAttribute.Z_POSITION, res=Variables[0x1002])
        Variables[0x1000] = Variables[0x1000] + 0x0
        Variables[0x1001] = Variables[0x1001] + 0x64
        Variables[0x1002] = Variables[0x1002] + 0x6C
        emit_command(0x0161, [0x00, Variables[0x1000], Variables[0x1001], Variables[0x1002], 0x0100], Variables[0xA009])
        wait(8)
        emit_command(0x014B, [0x7F, 0x10, 0x0020])
        emit_command(0x014C)
        emit_command(0x0063, [0x0E, 0x00])
        emit_command(0x0064, [0x0E, 0x00])
        emit_command(0x0092, [0x00])
        emit_command(0x0097, [0x00])
        wait(30)
        Variables[0x1000] = Variables[0x900B]
        branch('kuzzle_20')
        branch('kuzzle_21')
    
        label('kuzzle_20', manager = fevent_manager)
        branch_if(0x2, '!=', Variables[0x1000], 'kuzzle_22')
        emit_command(0x0129, [0x00])
        Variables[0xEAD9] = 0x1
        branch('kuzzle_21')
    
        label('kuzzle_22', manager = fevent_manager)
        branch_if(0x3, '!=', Variables[0x1000], 'kuzzle_23')
        emit_command(0x0129, [0x03])
        Variables[0xEADA] = 0x1
        branch('kuzzle_21')
    
        label('kuzzle_23', manager = fevent_manager)
        branch_if(0x4, '!=', Variables[0x1000], 'kuzzle_24')
        emit_command(0x0129, [0x01])
        Variables[0xEADB] = 0x1
        branch('kuzzle_21')
    
        label('kuzzle_24', manager = fevent_manager)
        branch_if(0x5, '!=', Variables[0x1000], 'kuzzle_21')
        emit_command(0x0129, [0x02])
        Variables[0xEADC] = 0x1
    
        label('kuzzle_21', manager = fevent_manager)
        wait(30)
        emit_command(0x014B, [0x10, 0x00, 0x0020])
        emit_command(0x014C)
        wait(30)
        Variables[0x1000] = Variables[0x900B]
        branch('kuzzle_25')
        branch('kuzzle_26')
    
        label('kuzzle_25', manager = fevent_manager)
        branch_if(0x2, '!=', Variables[0x1000], 'kuzzle_27')
        start_thread_here_and_branch(0x00, 'kuzzle_28')
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x7 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'kuzzle_29', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'kuzzle_30', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('kuzzle_31')
    
        label('kuzzle_30', manager = fevent_manager)
        Variables[0x1002] = 0x1
    
        label('kuzzle_31', manager = fevent_manager)
        push(Variables[0x1001])
    
        label('kuzzle_33', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'kuzzle_32', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(3)
        branch('kuzzle_33')
    
        label('kuzzle_32', manager = fevent_manager)
        branch('kuzzle_34')
    
        label('kuzzle_29', manager = fevent_manager)
        wait(3)
    
        label('kuzzle_34', manager = fevent_manager)
        return_()
    
        label('kuzzle_28', manager = fevent_manager)
        start_thread_here_and_branch(0x01, 'kuzzle_35')
        wait(3)
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x7 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'kuzzle_36', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'kuzzle_37', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('kuzzle_38')
    
        label('kuzzle_37', manager = fevent_manager)
        Variables[0x1002] = 0x1
    
        label('kuzzle_38', manager = fevent_manager)
        push(Variables[0x1001])
    
        label('kuzzle_40', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'kuzzle_39', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(3)
        branch('kuzzle_40')
    
        label('kuzzle_39', manager = fevent_manager)
        branch('kuzzle_41')
    
        label('kuzzle_36', manager = fevent_manager)
        wait(3)
    
        label('kuzzle_41', manager = fevent_manager)
        return_()
    
        label('kuzzle_35', manager = fevent_manager)
        branch_if(0x4, '==', 0xFF, 'kuzzle_42', invert=True)
        emit_command(0x0192, [0x00, -0x01])
        branch('kuzzle_43')
    
        label('kuzzle_42', manager = fevent_manager)
        emit_command(0x0192, [0x01, 0x04])
    
        label('kuzzle_43', manager = fevent_manager)
        set_animation(0x04, 0x03)
        emit_command(0x00B2, [0x04, 0x00, 0x00C2, 0x00CC, 0x0000, 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x04])
        wait(30)
        set_animation(0x04, 0x01)
        emit_command(0x0091, [0x04, -0x01, 0x0017, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        say(0x04, 0x24145, 0x2D, anim=None, post_anim=0x01, tail_hoffset=0xFF)
        emit_command(0x0091, [0x04, -0x01, 0x000F, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        set_animation(0x04, 0x03)
        wait(30)
        branch('kuzzle_26')
    
        label('kuzzle_27', manager = fevent_manager)
        branch_if(0x3, '!=', Variables[0x1000], 'kuzzle_44')
        start_thread_here_and_branch(0x00, 'kuzzle_45')
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x1 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'kuzzle_46', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'kuzzle_47', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('kuzzle_48')
    
        label('kuzzle_47', manager = fevent_manager)
        Variables[0x1002] = 0x1
    
        label('kuzzle_48', manager = fevent_manager)
        push(Variables[0x1001])
    
        label('kuzzle_50', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'kuzzle_49', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(3)
        branch('kuzzle_50')
    
        label('kuzzle_49', manager = fevent_manager)
        branch('kuzzle_51')
    
        label('kuzzle_46', manager = fevent_manager)
        wait(3)
    
        label('kuzzle_51', manager = fevent_manager)
        return_()
    
        label('kuzzle_45', manager = fevent_manager)
        start_thread_here_and_branch(0x01, 'kuzzle_52')
        wait(3)
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x1 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'kuzzle_53', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'kuzzle_54', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('kuzzle_55')
    
        label('kuzzle_54', manager = fevent_manager)
        Variables[0x1002] = 0x1
    
        label('kuzzle_55', manager = fevent_manager)
        push(Variables[0x1001])
    
        label('kuzzle_57', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'kuzzle_56', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(3)
        branch('kuzzle_57')
    
        label('kuzzle_56', manager = fevent_manager)
        branch('kuzzle_58')
    
        label('kuzzle_53', manager = fevent_manager)
        wait(3)
    
        label('kuzzle_58', manager = fevent_manager)
        return_()
    
        label('kuzzle_52', manager = fevent_manager)
        branch_if(0x4, '==', 0xFF, 'kuzzle_59', invert=True)
        emit_command(0x0192, [0x00, -0x01])
        branch('kuzzle_60')
    
        label('kuzzle_59', manager = fevent_manager)
        emit_command(0x0192, [0x01, 0x04])
    
        label('kuzzle_60', manager = fevent_manager)
        set_animation(0x04, 0x03)
        emit_command(0x00B2, [0x04, 0x00, 0x0140, 0x00CC, 0x0000, 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x04])
        wait(30)
        set_animation(0x04, 0x01)
        emit_command(0x0091, [0x04, -0x01, 0x0011, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        say(0x04, 0x24145, 0x2E, anim=None, post_anim=0x01, tail_hoffset=0xFF)
        emit_command(0x0091, [0x04, -0x01, 0x0009, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        set_animation(0x04, 0x03)
        wait(30)
        branch('kuzzle_26')
    
        label('kuzzle_44', manager = fevent_manager)
        branch_if(0x4, '!=', Variables[0x1000], 'kuzzle_61')
        emit_command(0x0135, [0x04, 0x0000, 0x0028, 0x0300, 0x01, 0x01])
        emit_command(0x0137)
        start_thread_here_and_branch(0x00, 'kuzzle_62')
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x4 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'kuzzle_63', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'kuzzle_64', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('kuzzle_65')
    
        label('kuzzle_64', manager = fevent_manager)
        Variables[0x1002] = 0x1
    
        label('kuzzle_65', manager = fevent_manager)
        push(Variables[0x1001])
    
        label('kuzzle_67', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'kuzzle_66', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(3)
        branch('kuzzle_67')
    
        label('kuzzle_66', manager = fevent_manager)
        branch('kuzzle_68')
    
        label('kuzzle_63', manager = fevent_manager)
        wait(3)
    
        label('kuzzle_68', manager = fevent_manager)
        return_()
    
        label('kuzzle_62', manager = fevent_manager)
        start_thread_here_and_branch(0x01, 'kuzzle_69')
        wait(3)
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x4 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'kuzzle_70', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'kuzzle_71', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('kuzzle_72')
    
        label('kuzzle_71', manager = fevent_manager)
        Variables[0x1002] = 0x1
    
        label('kuzzle_72', manager = fevent_manager)
        push(Variables[0x1001])
    
        label('kuzzle_74', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'kuzzle_73', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(3)
        branch('kuzzle_74')
    
        label('kuzzle_73', manager = fevent_manager)
        branch('kuzzle_75')
    
        label('kuzzle_70', manager = fevent_manager)
        wait(3)
    
        label('kuzzle_75', manager = fevent_manager)
        return_()
    
        label('kuzzle_69', manager = fevent_manager)
        unk_thread_branch_0x004a(0x04, 'kuzzle_76')
        push(0x2)
    
        label('kuzzle_90', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'kuzzle_77', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        wait(6)
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x5 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'kuzzle_78', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'kuzzle_79', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('kuzzle_80')
    
        label('kuzzle_79', manager = fevent_manager)
        Variables[0x1002] = 0x1
    
        label('kuzzle_80', manager = fevent_manager)
        push(Variables[0x1001])
    
        label('kuzzle_82', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'kuzzle_81', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(6)
        branch('kuzzle_82')
    
        label('kuzzle_81', manager = fevent_manager)
        branch('kuzzle_83')
    
        label('kuzzle_78', manager = fevent_manager)
        wait(6)
    
        label('kuzzle_83', manager = fevent_manager)
        wait(6)
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x3 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'kuzzle_84', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'kuzzle_85', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('kuzzle_86')
    
        label('kuzzle_85', manager = fevent_manager)
        Variables[0x1002] = 0x1
    
        label('kuzzle_86', manager = fevent_manager)
        push(Variables[0x1001])
    
        label('kuzzle_88', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'kuzzle_87', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(6)
        branch('kuzzle_88')
    
        label('kuzzle_87', manager = fevent_manager)
        branch('kuzzle_89')
    
        label('kuzzle_84', manager = fevent_manager)
        wait(6)
    
        label('kuzzle_89', manager = fevent_manager)
        wait(20)
        branch('kuzzle_90')
    
        label('kuzzle_77', manager = fevent_manager)
        return_()
    
        label('kuzzle_76', manager = fevent_manager)
        wait(20)
        say(0x04, 0x24145, 0x2F, anim=None, post_anim=None, tail_hoffset=0xFF)
        wait(30)
        emit_command(0x0135, [0x04, 0x001E, -0x0020, 0x0300, 0x01, 0x01])
        emit_command(0x0137)
        branch('kuzzle_26')
    
        label('kuzzle_61', manager = fevent_manager)
        branch_if(0x5, '!=', Variables[0x1000], 'kuzzle_26')
        emit_command(0x0133, [0x00, 0x0080, 0x0000, 0x0200, 0x0000, 0x0200, 0x0200, 0x01, 0x01])
        start_thread_here_and_branch(0x00, 'kuzzle_91')
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x0 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'kuzzle_92', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'kuzzle_93', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('kuzzle_94')
    
        label('kuzzle_93', manager = fevent_manager)
        Variables[0x1002] = 0x1
    
        label('kuzzle_94', manager = fevent_manager)
        push(Variables[0x1001])
    
        label('kuzzle_96', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'kuzzle_95', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(3)
        branch('kuzzle_96')
    
        label('kuzzle_95', manager = fevent_manager)
        branch('kuzzle_97')
    
        label('kuzzle_92', manager = fevent_manager)
        wait(3)
    
        label('kuzzle_97', manager = fevent_manager)
        return_()
    
        label('kuzzle_91', manager = fevent_manager)
        start_thread_here_and_branch(0x01, 'kuzzle_98')
        wait(3)
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x0 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'kuzzle_99', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'kuzzle_100', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('kuzzle_101')
    
        label('kuzzle_100', manager = fevent_manager)
        Variables[0x1002] = 0x1
    
        label('kuzzle_101', manager = fevent_manager)
        push(Variables[0x1001])
    
        label('kuzzle_103', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'kuzzle_102', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(3)
        branch('kuzzle_103')
    
        label('kuzzle_102', manager = fevent_manager)
        branch('kuzzle_104')
    
        label('kuzzle_99', manager = fevent_manager)
        wait(3)
    
        label('kuzzle_104', manager = fevent_manager)
        return_()
    
        label('kuzzle_98', manager = fevent_manager)
        branch_if(0x4, '==', 0xFF, 'kuzzle_105', invert=True)
        emit_command(0x0192, [0x00, -0x01])
        branch('kuzzle_106')
    
        label('kuzzle_105', manager = fevent_manager)
        emit_command(0x0192, [0x01, 0x04])
    
        label('kuzzle_106', manager = fevent_manager)
        set_animation(0x04, 0x03)
        emit_command(0x00B2, [0x04, 0x00, 0x0100, 0x00A6, 0x0000, 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x04])
        wait(30)
        emit_command(0x0137)
        say(0x04, 0x24145, 0x30, anim=None, tail_hoffset=0xFF)
        wait(30)
    
        label('kuzzle_26', manager = fevent_manager)
        branch_if(0x0, '==', 0xFF, 'kuzzle_107', invert=True)
        emit_command(0x0192, [0x00, -0x01])
        branch('kuzzle_108')
    
        label('kuzzle_107', manager = fevent_manager)
        emit_command(0x0192, [0x01, 0x00])
    
        label('kuzzle_108', manager = fevent_manager)
        emit_command(0x0135, [0x00, -0x001E, -0x0020, 0x0300, 0x01, 0x01])
        emit_command(0x00B2, [0x04, 0x00, 0x0100, 0x0100, 0x0000, 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x04])
        emit_command(0x00D1, [0x04, 0x00, 0x03])
        emit_command(0x00D1, [0x00, 0x00, 0x06])
        emit_command(0x00D1, [0x01, 0x00, 0x07])
        emit_command(0x0137)
        Variables[0x9008] = 0x0
        branch_if(Variables[0xEAD9], '==', 0x1, 'kuzzle_109', invert=True)
        Variables[0x9008] += 1
    
        label('kuzzle_109', manager = fevent_manager)
        branch_if(Variables[0xEADA], '==', 0x1, 'kuzzle_110', invert=True)
        Variables[0x9008] += 1
    
        label('kuzzle_110', manager = fevent_manager)
        branch_if(Variables[0xEADB], '==', 0x1, 'kuzzle_111', invert=True)
        Variables[0x9008] += 1
    
        label('kuzzle_111', manager = fevent_manager)
        branch_if(Variables[0xEADC], '==', 0x1, 'kuzzle_112', invert=True)
        Variables[0x9008] += 1
    
        label('kuzzle_112', manager = fevent_manager)
        set_animation(0x04, 0x03)
        wait(30)
        branch_if(Variables[0x9008], '==', 0x4, 'kuzzle_113', invert=True)
        get_actor_attribute(0x04, 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x0 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'kuzzle_114', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'kuzzle_115', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('kuzzle_116')
    
        label('kuzzle_115', manager = fevent_manager)
        Variables[0x1002] = 0x1
    
        label('kuzzle_116', manager = fevent_manager)
        push(Variables[0x1001])
    
        label('kuzzle_118', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'kuzzle_117', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [0x04, 0x01, Variables[0x1002]])
        wait(3)
        branch('kuzzle_118')
    
        label('kuzzle_117', manager = fevent_manager)
        branch('kuzzle_119')
    
        label('kuzzle_114', manager = fevent_manager)
        wait(3)
    
        label('kuzzle_119', manager = fevent_manager)
        emit_command(0x0135, [0x04, 0x0000, 0x0000, 0x0300, 0x01, 0x01])
        emit_command(0x0137)
        say(0x04, 0x24145, 0x1D, anim=None, tail_hoffset=0xFF)
        wait(30)
        emit_command(0x0133, [0x01, 0x0000, -0x0064, 0x0200, 0x0000, 0x0200, 0x0200, 0x01, 0x01])
        emit_command(0x0137)
        wait(60)
        emit_command(0x0135, [0x04, 0x0000, 0x0000, 0x0300, 0x01, 0x01])
        emit_command(0x0137)
        wait(30)
        branch_in_thread(0x04, 'sub_0x2d')
        join_thread(0x04)
        say(0x04, 0x24145, 0x33, anim=None, tail_hoffset=0xFF)
        wait(30)
        start_thread_here_and_branch(0x04, 'kuzzle_120')
        get_actor_attribute(Variables[0x3006], 0x0E, res=Variables[0x1000])
        Variables[0x1001] = 0x3 - Variables[0x1000]
        branch_if(Variables[0x1001], '!=', 0x0, 'kuzzle_121', invert=True)
        Variables[0x1001] = Variables[0x1001] & 0x7
        branch_if(Variables[0x1001], '>', 0x4, 'kuzzle_122', invert=True)
        Variables[0x1001] = 0x8 - Variables[0x1001]
        Variables[0x1002] = -0x1
        branch('kuzzle_123')
    
        label('kuzzle_122', manager = fevent_manager)
        Variables[0x1002] = 0x1
    
        label('kuzzle_123', manager = fevent_manager)
        push(Variables[0x1001])
    
        label('kuzzle_125', manager = fevent_manager)
        branch_if_stack('==', 0x0, 'kuzzle_124', StackTopModification.DECREMENT_AFTER, StackPopCondition.IF_TRUE)
        emit_command(0x00D1, [Variables[0x3006], 0x01, Variables[0x1002]])
        wait(3)
        branch('kuzzle_125')
    
        label('kuzzle_124', manager = fevent_manager)
        branch('kuzzle_126')
    
        label('kuzzle_121', manager = fevent_manager)
        wait(3)
    
        label('kuzzle_126', manager = fevent_manager)
        return_()
    
        label('kuzzle_120', manager = fevent_manager)
        emit_command(0x0135, [0x04, 0x001E, -0x0020, 0x0300, 0x01, 0x01])
        emit_command(0x0137)
        set_animation(0x04, 0x01)
        emit_command(0x0091, [0x04, -0x01, 0x0013, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        say(0x04, 0x24145, 0x34, anim=None, post_anim=0x01, tail_hoffset=0xFF)
        emit_command(0x0091, [0x04, -0x01, 0x000B, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        set_animation(0x04, 0x03)
        wait(30)
        call('puzzle_prizes')
        emit_command(0x0092, [0x00])
        emit_command(0x0097, [0x00])
        emit_command(0x0063, [0x0F, 0x00])
        emit_command(0x0064, [0x0F, 0x00])
        emit_command(0x0063, [0x10, 0x00])
        emit_command(0x0064, [0x10, 0x00])
        emit_command(0x0063, [0x11, 0x00])
        emit_command(0x0064, [0x11, 0x00])
        wait(30)
        set_animation(0x04, 0x01)
        emit_command(0x0091, [0x04, -0x01, 0x0013, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        say(0x04, 0x24145, 0x36, anim=None, post_anim=0x01, tail_hoffset=0xFF)
        emit_command(0x0091, [0x04, -0x01, 0x000B, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        set_animation(0x04, 0x03)
        Variables[0xEAE1] = 0x1
        wait(30)
        branch('kuzzle_1')
    
        label('kuzzle_113', manager = fevent_manager)
        set_animation(0x04, 0x01)
        emit_command(0x0091, [0x04, -0x01, 0x0013, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        say(0x04, 0x24145, 0x31, anim=None, post_anim=0x01, tail_hoffset=0xFF)
        emit_command(0x0091, [0x04, -0x01, 0x000B, -0x0001, 0x01])
        emit_command(0x0094, [0x04, 0x0000, 0x00])
        set_animation(0x04, 0x03)
        wait(30)
        call('puzzle_prizes')
        emit_command(0x0092, [0x00])
        emit_command(0x0097, [0x00])
        emit_command(0x0063, [0x0F, 0x00])
        emit_command(0x0064, [0x0F, 0x00])
        emit_command(0x0063, [0x10, 0x00])
        emit_command(0x0064, [0x10, 0x00])
        emit_command(0x0063, [0x11, 0x00])
        emit_command(0x0064, [0x11, 0x00])
    
        label('kuzzle_1', manager = fevent_manager)
        branch_if(0x0, '==', 0xFF, 'kuzzle_127', invert=True)
        emit_command(0x0192, [0x00, -0x01])
        branch('kuzzle_128')
    
        label('kuzzle_127', manager = fevent_manager)
        emit_command(0x0192, [0x01, 0x00])
    
        label('kuzzle_128', manager = fevent_manager)
        emit_command(0x0135, [0x00, 0x0000, 0x0000, 0x0200, 0x01, 0x01])
        emit_command(0x00B5, [0x01, 0x00, 0x0014, 0x0000, 0x0000, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x01])
        branch_if(0x0, '==', 0x0, 'kuzzle_129', invert=True)
        get_actor_attribute(Actors.MARIO, 0x0E, res=Variables[0x1000])
        Variables[0x1000] = Variables[0x1000] + 0x4
        Variables[0x1000] = Variables[0x1000] & 0x7
        load_data_from_array('sub_0x20', Variables[0x1000], res=Variables[0x1001])
        load_data_from_array('sub_0x21', Variables[0x1000], res=Variables[0x1002])
        Variables[0x1000] = Variables[0x1000] & 0x1
        branch_if(Variables[0x1000], '==', 0x0, 'kuzzle_130', invert=True)
        Variables[0x1001] = Variables[0x1001] * 0x14
        Variables[0x1002] = Variables[0x1002] * 0x14
        branch('kuzzle_131')
    
        label('kuzzle_130', manager = fevent_manager)
        Variables[0x1001] = Variables[0x1001] * 0xF
        Variables[0x1002] = Variables[0x1002] * 0xF
    
        label('kuzzle_131', manager = fevent_manager)
        get_actor_attribute(Actors.MARIO, ActorAttribute.X_POSITION, res=Variables[0x1003])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Y_POSITION, res=Variables[0x1004])
        get_actor_attribute(Actors.MARIO, ActorAttribute.Z_POSITION, res=Variables[0x1005])
        Variables[0x1001] = Variables[0x1001] + Variables[0x1003]
        Variables[0x1002] = Variables[0x1002] + Variables[0x1004]
        emit_command(0x00B2, [0x01, 0x00, Variables[0x1001], Variables[0x1002], Variables[0x1005], 0x0200, 0x0000, 0x0200, 0x0200, 0x00, 0x00, 0x01, 0x01])
        emit_command(0x00BB, [0x01])
        emit_command(0x00D2, [0x01, 0x00])
    
        label('kuzzle_129', manager = fevent_manager)
        emit_command(0x00E9, [0x00, 0x01])
        emit_command(0x005B, [0x01])
    
        label('kuzzle_132', manager = fevent_manager)
        wait(1)
        branch_if(Variables[0x301F], '!=', 0x1, 'kuzzle_132')
        emit_command(0x0137)
        branch_in_thread(0x04, 'sub_0x1')
        Variables[0xEAFD] = 0x0
        Variables[0xEADD] = 0x0
        branch_if(Variables[0x3019], '==', 0x0, 'kuzzle_133', invert=True)
        emit_command(0x00F5, [0x00, 0x01, 0x00])
        branch_if(0x0, '==', 0x0, 'kuzzle_134', invert=True)
    
        label('kuzzle_135', manager = fevent_manager)
        wait(1)
        branch_if(Variables[0x3017], '==', 0x1, 'kuzzle_135')
    
        label('kuzzle_134', manager = fevent_manager)
        branch('kuzzle_136')
    
        label('kuzzle_133', manager = fevent_manager)
        branch_if(Variables[0x3008], '==', 0x0, 'kuzzle_137', invert=True)
        emit_command(0x00F5, [0x01, 0x01, 0x00])
        branch_if(0x0, '==', 0x0, 'kuzzle_138', invert=True)
    
        label('kuzzle_139', manager = fevent_manager)
        wait(1)
        branch_if(Variables[0x3018], '==', 0x1, 'kuzzle_139')
    
        label('kuzzle_138', manager = fevent_manager)
        branch('kuzzle_136')
    
        label('kuzzle_137', manager = fevent_manager)
        emit_command(0x00F5, [0x00, 0x01, 0x00])
        branch_if(0x0, '==', 0x0, 'kuzzle_136', invert=True)
    
        label('kuzzle_140', manager = fevent_manager)
        wait(1)
        branch_if(Variables[0x3017], '==', 0x1, 'kuzzle_140')
    
        label('kuzzle_136', manager = fevent_manager)
        branch_if(Variables[0x3008], '==', 0x0, 'kuzzle_141', invert=True)
        emit_command(0x018C, [Variables[0x3008], 0x0000], Variables[0x1007])
        branch('kuzzle_142')
    
        label('kuzzle_141', manager = fevent_manager)
        emit_command(0x018C, [Variables[0x3008], 0x00C0], Variables[0x1007])
    
        label('kuzzle_142', manager = fevent_manager)
        branch_if(0x1, '==', 0x1, 'kuzzle_143', invert=True)
        emit_command(0x01A0)
        branch('kuzzle_144')
    
        label('kuzzle_143', manager = fevent_manager)
        emit_command(0x01A1)
    
        label('kuzzle_144', manager = fevent_manager)

    script.subroutines[0x09].commands[68] = CodeCommandWithOffsets(0x0002, [0x01, Variables[0x900B], 0x00000000, 0x00000001, PLACEHOLDER_OFFSET], offset_arguments = {4: 'kuzzle_reward'})
    script.header.subroutine_table = [0] * len(script.subroutines)
    update_commands_with_offsets(fevent_manager, [script.header.post_table_subroutine, *script.subroutines], len(script.header.to_bytes(fevent_manager)))

    for i, treasure in enumerate(current_treasure_list):
        if treasure.item & 0xF000 == 0x3000:
            badge_dict[treasure.item] = f"{treasure_strings[7][0]} - {treasure_strings[7][1]} x {(i // 3) + 2}"
    
    return return_treasure, badge_dict