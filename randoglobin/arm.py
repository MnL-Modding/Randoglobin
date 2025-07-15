import os
import shutil
import subprocess
import itertools
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import ndspy.codeCompression
from cached_path import cached_path
from mnllib.nds import ARM9_OVERLAY_TABLE_PATH, DECOMPRESSED_ARM9_PATH, DECOMPRESSED_OVERLAYS_DIR, fs_std_overlay_path

from randoglobin.constants import FILES_DIR

def apply_arm_patches(rom):
    armips_path = FILES_DIR / f"armips{'.exe' if os.name == 'nt' else ''}"
    if not armips_path.exists():
        # armips doesn't exist in the files directory, use the globally installed one.
        armips_path = shutil.which('armips')
        if armips_path is None:
            return 1,

    bis_code_patch_archive_path = cached_path('https://github.com/MnL-Modding/MnL-Code-Patching/releases/latest/download/bis.zip')
    with TemporaryDirectory() as patching_dir:
        patching_dir = Path(patching_dir)
        with ZipFile(bis_code_patch_archive_path, 'r') as code_patch_archive:
            code_patch_archive.extractall(path=patching_dir)
        bis_data_dir = patching_dir / 'bis-data'
        bis_data_dir.mkdir(exist_ok=True)
        ndspy.codeCompression.decompressToFile(
            rom.arm9, bis_data_dir / DECOMPRESSED_ARM9_PATH
        )
        (bis_data_dir / ARM9_OVERLAY_TABLE_PATH).write_bytes(rom.arm9OverlayTable)
        (bis_data_dir / DECOMPRESSED_OVERLAYS_DIR).mkdir(exist_ok=True)
        original_overlays = rom.loadArm9Overlays()
        for i, overlay in original_overlays.items():
            fs_std_overlay_path(i, data_dir=bis_data_dir).write_bytes(overlay.data)

        # Sets the executable bit of the armips binary.
        try:
            armips_mode = armips_path.stat().st_mode
            armips_mode |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            armips_path.chmod(stat.S_IMODE(armips_mode))
        except Exception:
            pass

        try:
            subprocess.run(
                [
                    armips_path,
                    '-stat',
                    '-strequ', 'PROFILE', 'release',
                    '-definelabel', 'F_ANTI_PIRACY_PATCH', '1',
                    '-definelabel', 'F_MIXED_SHOP', '1',
                    'bis.asm',
                ],
                cwd=patching_dir,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            return 2, e.stdout, e.stderr
        else:
            rom.arm9 = ndspy.code.MainCodeFile(
                (bis_data_dir / DECOMPRESSED_ARM9_PATH).read_bytes(),
                rom.arm9RamAddress,
                rom.arm9CodeSettingsPointerAddress,
            ).save(compress=True)
            rom.arm9OverlayTable = (bis_data_dir / ARM9_OVERLAY_TABLE_PATH).read_bytes()

            overlays = [fs_std_overlay_path(i, data_dir=bis_data_dir).read_bytes() for i in range(len(rom.arm9OverlayTable) // 32)]

            arm9OverlayTable = bytearray((bis_data_dir / ARM9_OVERLAY_TABLE_PATH).read_bytes())
            overlay_num = -1
            for original_overlay, new_overlay in itertools.zip_longest(original_overlays.values(), overlays):
                overlay_num += 1
                if original_overlay is None:
                    new_overlay = ndspy.codeCompression.compress(new_overlay)
                    rom.files.append(new_overlay)
                    arm9OverlayTable[(overlay_num * 32 + 6 * 4) : (overlay_num * 32 + 7 * 4)] = (len(rom.files) - 1).to_bytes(4, 'little')  # The file ID of the newly-inserted overlay file goes here.
                    arm9OverlayTable[(overlay_num * 32 + 7 * 4) : (overlay_num * 32 + 8 * 4)] = (len(new_overlay) | 0x01 << 24).to_bytes(4, 'little')  # Not sure if this second line is required or not, would be good to test on an actual console as well.
                    continue
                elif original_overlay.data == new_overlay:
                    continue
                original_overlay.data = new_overlay  # Reusing the `original_overlay` object since it's an ndspy Overlay
                rom.files[original_overlay.fileID] = original_overlay.save(compress=True)

            rom.arm9OverlayTable = bytes(arm9OverlayTable)

    return 0, rom