"""
Safe command insertion for FEvent scripts.

Branches, thread starts and data loads in BIS scripts store their targets as
offsets *relative to the end of the command*. Inserting or removing a command
therefore silently breaks every jump that crosses the edit point (including
jumps between subroutines). `ScriptRelocator` records every such target as a
reference to the command object it points at, lets you edit the command lists
freely, and then rewrites all relative offsets so they point at the same
commands again.

Usage:
    reloc = ScriptRelocator(manager, script)
    script.subroutines[3].commands.insert(5, some_command)
    reloc.apply()
"""

import mnllib

# command id -> index of the argument that is a relative offset
OFFSET_ARGS = {
    0x0002: 4,  # branch_if
    0x0003: 1,  # branch
    0x0007: 3,  # branch_if_stack
    0x0039: 0,  # load_data_from_array
    0x003A: 0,  # load_data
    0x003B: 0,  # debugln (points into the debug message table)
    0x003C: 0,  # debug
    0x0049: 2,  # start_thread_here_and_branch
    0x004A: 2,  # unk_thread_branch_0x004a
    0x004B: 2,  # branch_in_thread
    0x0060: 1,
}


def _all_subroutines(script):
    return [script.header.post_table_subroutine, *script.subroutines]


def _layout(manager, script):
    """Returns ({id(command): (start, length)}, [(sub, start, end_without_footer, end_with_footer)], debug_start)."""
    cmd_pos = {}
    subs = []
    offset = len(script.header.to_bytes(manager))
    header_sub = script.header.post_table_subroutine
    # the post-table subroutine lives inside the header; its offset is the header length minus its own size
    header_sub_len = header_sub.serialized_len(manager, 0, with_footer=True)
    for sub in _all_subroutines(script):
        if sub is header_sub:
            start = offset - header_sub_len
        else:
            if len(sub.commands) > 0 and isinstance(sub.commands[0], mnllib.ArrayCommand):
                offset += (-offset) % 4
            start = offset
        pos = start
        for command in sub.commands:
            length = command.serialized_len(manager, pos)
            cmd_pos[id(command)] = (pos, length)
            pos += length
        end_no_footer = pos
        end = pos + len(sub.footer)
        subs.append((sub, start, end_no_footer, end))
        if sub is not header_sub:
            offset = end
    return cmd_pos, subs, offset


class ScriptRelocator:
    def __init__(self, manager, script):
        self.manager = manager
        self.script = script
        self.refs = []  # (command, arg_index, target)
        cmd_pos, subs, debug_start = _layout(manager, script)

        for sub, _start, _end_nf, _end in subs:
            for command in sub.commands:
                if not isinstance(command, mnllib.CodeCommand):
                    continue
                arg_index = OFFSET_ARGS.get(command.command_id)
                if arg_index is None or arg_index >= len(command.arguments):
                    continue
                value = command.arguments[arg_index]
                if not isinstance(value, int):
                    continue
                pos, length = cmd_pos[id(command)]
                target_abs = pos + length + value
                self.refs.append((command, arg_index, self._resolve(target_abs, cmd_pos, subs, debug_start)))

    def _resolve(self, target_abs, cmd_pos, subs, debug_start):
        if target_abs >= debug_start:
            return ("debug", target_abs - debug_start)
        # the start of a subroutine wins over its first command (so code prepended to a subroutine
        # runs when it's called) and over the end of the previous subroutine (same address)
        for sub, start, end_nf, end in subs:
            if sub is not self.script.header.post_table_subroutine and start == target_abs:
                return ("sub_start", sub, 0)
        for sub, start, end_nf, end in subs:
            if start <= target_abs < end_nf:
                for command in sub.commands:
                    pos, length = cmd_pos[id(command)]
                    if pos <= target_abs < pos + length:
                        delta = target_abs - pos
                        if isinstance(command, mnllib.ArrayCommand):
                            delta -= (-pos) % 4  # measure from the aligned data start
                        return ("cmd", command, delta)
        for sub, start, end_nf, end in subs:
            if start == end_nf == target_abs:
                return ("sub_start", sub, 0)  # empty subroutine
        for sub, start, end_nf, end in subs:
            if target_abs == end_nf:
                return ("sub_end", sub, 0)
            if end_nf < target_abs < end:
                return ("footer", sub, target_abs - end_nf)
        raise ValueError(f"unresolvable offset target {target_abs:#x} in script {self.script.index}")

    def _target_abs(self, target, cmd_pos, subs, debug_start):
        kind = target[0]
        if kind == "debug":
            return debug_start + target[1]
        if kind == "cmd":
            _, command, delta = target
            pos, _length = cmd_pos[id(command)]
            if isinstance(command, mnllib.ArrayCommand):
                delta += (-pos) % 4
            return pos + delta
        _, sub, delta = target
        for s, start, end_nf, _end in subs:
            if s is sub:
                return (start if kind == "sub_start" else end_nf) + delta
        raise ValueError("target subroutine was removed from the script")

    def apply(self):
        # argument values never change command sizes for these commands, but loop to be safe
        for _ in range(4):
            cmd_pos, subs, debug_start = _layout(self.manager, self.script)
            changed = False
            for command, arg_index, target in self.refs:
                if id(command) not in cmd_pos:
                    continue  # the branching command itself was removed
                pos, length = cmd_pos[id(command)]
                new_value = self._target_abs(target, cmd_pos, subs, debug_start) - (pos + length)
                if command.arguments[arg_index] != new_value:
                    command.arguments[arg_index] = new_value
                    changed = True
            if not changed:
                return
        raise RuntimeError(f"offsets did not stabilise in script {self.script.index}")
