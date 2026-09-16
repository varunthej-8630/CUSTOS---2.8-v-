# engine.media_recorder — Transparent module alias to engine.storage.media_recorder
import sys
import engine.storage.media_recorder as _target_module

# Export all attributes to current module namespace
for _k, _v in _target_module.__dict__.items():
    if not _k.startswith('__'):
        globals()[_k] = _v

# Replace in sys.modules so monkeypatching and direct imports share the exact same module
sys.modules[__name__] = _target_module
