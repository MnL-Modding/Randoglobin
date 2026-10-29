"""Headless stand-in for PySide6: every attribute is a permissive dummy, so the
randomizer's non-GUI code can be imported and run without Qt."""
import sys, types

class _Meta(type):
    def __getattr__(cls, name):
        if name.startswith('__'): raise AttributeError(name)
        return Dummy()
    def __or__(cls, o): return cls
    __ror__ = __or__

class Dummy(metaclass=_Meta):
    def __init__(self, *a, **k): pass
    def __getattr__(self, name):
        if name.startswith('__'): raise AttributeError(name)
        return Dummy()
    def __call__(self, *a, **k): return Dummy()
    def __or__(self, o): return self
    __ror__ = __and__ = __add__ = __radd__ = __or__
    def __int__(self): return 0
    def __bool__(self): return False
    def __iter__(self): return iter(())
    def tr(self, s, *a): return s

class _Mod(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith('__'): raise AttributeError(name)
        return Dummy

for sub in ['QtCore', 'QtGui', 'QtWidgets', 'QtMultimedia']:
    m = _Mod(f'PySide6.{sub}')
    sys.modules[f'PySide6.{sub}'] = m
    setattr(sys.modules[__name__], sub, m)

class _QStandardPaths:
    class StandardLocation:
        AppConfigLocation = 0
    @staticmethod
    def writableLocation(*a): return '/tmp/randoglobin-config'
sys.modules['PySide6.QtCore'].QStandardPaths = _QStandardPaths
sys.modules['PySide6.QtCore'].Signal = lambda *a, **k: Dummy()
