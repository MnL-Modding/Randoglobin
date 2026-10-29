"""Round-trip test for ScriptRelocator against real game data.

Needs an extracted BIS data directory (mnllib layout: data/FEvent/FEvent.dat and
overlay.dec/overlay_0003.dec.bin, overlay_0006.dec.bin):

    BIS_DATA_DIR=/path/to/extracted python tests/test_script_reloc.py

For every script it inserts a marker command at the start and middle of every code
subroutine, fixes the offsets, serializes, reparses, removes the markers again and checks
the result is byte-identical to the original.
"""
import io
import os
import sys
import types
from pathlib import Path

_pkg = types.ModuleType("randoglobin")
_pkg.__path__ = [str(Path(__file__).resolve().parent.parent / "randoglobin")]
sys.modules.setdefault("randoglobin", _pkg)

import mnllib  # noqa: E402
import mnllib.bis  # noqa: E402
from randoglobin.script_reloc import ScriptRelocator  # noqa: E402

MARK = 0xEC3F


def is_mark(cmd):
    return isinstance(cmd, mnllib.CodeCommand) and cmd.command_id == 0x0008 and cmd.result_variable == mnllib.Variable(MARK)


def main():
    data_dir = os.environ["BIS_DATA_DIR"]
    manager = mnllib.bis.FEventScriptManager(data_dir=data_dir)
    checked = 0
    for index, triple in enumerate(manager.fevent_chunks):
        for t in range(2):
            script = triple[t]
            if not isinstance(script, mnllib.bis.FEventScript):
                continue
            original = script.to_bytes(manager)

            reloc = ScriptRelocator(manager, script)
            for sub in [script.header.post_table_subroutine, *script.subroutines]:
                if any(isinstance(c, mnllib.DataCommand) for c in sub.commands):
                    continue
                sub.commands.insert(len(sub.commands) // 2, mnllib.CodeCommand(0x0008, [0], mnllib.Variable(MARK)))
                sub.commands.insert(0, mnllib.CodeCommand(0x0008, [0], mnllib.Variable(MARK)))
            reloc.apply()

            reparsed = mnllib.bis.FEventScript.from_bytes(manager, script.to_bytes(manager), script.index)
            reloc = ScriptRelocator(manager, reparsed)
            for sub in [reparsed.header.post_table_subroutine, *reparsed.subroutines]:
                sub.commands = [c for c in sub.commands if not is_mark(c)]
            reloc.apply()
            assert reparsed.to_bytes(manager) == original, f"script {index:#x}/{t} changed"
            checked += 1
    print(f"ok: {checked} scripts round-tripped")


if __name__ == "__main__":
    main()
