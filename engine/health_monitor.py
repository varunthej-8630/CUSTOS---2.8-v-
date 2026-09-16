# engine.health_monitor — Transparent module alias to engine.health.health_monitor
import sys
import engine.health.health_monitor as _target_module

# Export all attributes to current module namespace
for _k, _v in _target_module.__dict__.items():
    if not _k.startswith('__'):
        globals()[_k] = _v

# Replace in sys.modules so monkeypatching and direct imports share the exact same module
sys.modules[__name__] = _target_module
