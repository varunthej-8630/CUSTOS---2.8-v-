# engine.media_resolver — Transparent module alias to engine.evidence.media_resolver
import sys
import engine.evidence.media_resolver as _target_module

# Export all attributes to current module namespace
for _k, _v in _target_module.__dict__.items():
    if not _k.startswith('__'):
        globals()[_k] = _v

# Replace in sys.modules so monkeypatching and direct imports share the exact same module
sys.modules[__name__] = _target_module
