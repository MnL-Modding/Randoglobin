"""Run Randoglobin's randomization without the GUI (for testing and batch seeds).

usage: python tools/headless/run.py <in.nds> <out.nds> <seed> [key=value ...]
  treasure=0/1     treasure randomization (default 1)
  unlinear=0/1     "Skip Story and Tutorials" open world (default 1)
  key_items=0/1    shuffle every supported important item (default 0)
  intro=0/1/2      intro skip (default 2)
  debug_mode=0/1   start with all abilities
  force=loc:item,...   testing: force key item placements (see key_items.LOCATIONS)
  migrate=1        testing: let saves made on an unrandomized ROM keep their abilities

Qt is replaced with stubs (tools/headless/stubs), and palette randomization (which needs
the Rust extension) is unavailable. armips must be in randoglobin/files or on PATH.
"""
import sys, types, os
from types import SimpleNamespace as NS
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'stubs'))
sys.path.insert(1, os.path.dirname(os.path.dirname(HERE)))

sys.modules['randoglobin.rust'] = types.SimpleNamespace(modify_maps=lambda *a, **k: None)  # palette rando is off in tests
import randoglobin.main
M = sys.modules['randoglobin.main']

class Box:
    def __init__(self, v): self.v = v
    def isChecked(self): return bool(self.v)
    def currentIndex(self): return self.v
    def value(self): return self.v
    def text(self): return str(self.v)

class Sig:
    def __init__(self, name): self.name = name
    def emit(self, *a):
        if self.name == 'error': print('ERROR:', a[0].replace('<br>', '\n')[:3000]); Sig.errors += 1
        elif self.name == 'log': print('log:', a[1])
Sig.errors = 0

def main():
    src, dst, seed, *opts = sys.argv[1:]
    o = dict(x.split('=') for x in opts)
    flag = lambda k, d: int(o.get(k, d))
    ts = NS(**{n: Box(1) for n in ['rando_dig','rando_block','rando_brick','rando_grass','rando_ball','rando_hide','rando_blitty','rando_puzzle','rando_ishop','rando_gshop','rando_bshop']})
    ts.key_items = Box(flag('key_items', 0))
    for n in ['rando_key_r','rando_key_b','rando_key_g','rando_bill','rando_cure_r','rando_cure_y','rando_cure_g','rando_stingler','rando_hammer','rando_mini','rando_spin','rando_drill','rando_flame','rando_slide','rando_slam','rando_spike','rando_vent','rando_shell','rando_vacuum','rando_badge']:
        setattr(ts, n, Box(flag('key_items', 0)))
    parent = NS(
        custom_seed=Box(seed), write_spoiler=Box(1),
        rand_attacks=Box(0), rand_treasure=Box(flag('treasure', 1)), rand_music=Box(0), rand_colors=Box(0),
        intro=Box(flag('intro', 2)), no_enemies_ml=Box(0), no_enemies_kp=Box(0), exp_mult=Box(1.0),
        starting_level_ml=Box(1), starting_level_kp=Box(1),
        extra_settings=NS(unlinear=Box(flag('unlinear', 1)), no_music=Box(0), endless_arm=Box(0),
                          debug_mode=Box(flag('debug_mode', 0)), challenge_medal=Box(0), impossible=Box(0)),
        treasure_settings=ts, path=src, new_path=dst, lang=["English (NA)", "NA-EN", 1],
        parent=NS(installTranslator=lambda *a: None),
    )
    if 'force' in o:  # e.g. force=trash_pit_hammers:spin_jump,flab_zone_spin:hammer
        import randoglobin.key_items as K
        K.FORCED_PLACEMENT.update(dict(x.split(':') for x in o['force'].split(',')))
    if o.get('migrate') == '1':
        import randoglobin.key_items as K
        K.MIGRATE_VANILLA_SAVES = True
    w = M.RandoWorker.__new__(M.RandoWorker)
    w.parent = parent
    w.log, w.finished, w.failed, w.error = Sig('log'), Sig('finished'), Sig('failed'), Sig('error')
    w.tr = lambda s, *a: s
    w.run()
    sys.exit(1 if Sig.errors else 0)

main()
