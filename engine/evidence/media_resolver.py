# engine/media_resolver.py — Authoritative Media File Resolution
import os
from typing import Optional, List
from config import settings as config
from core.logging import app_logger

# Authorized media search directories
def get_media_search_dirs() -> List[str]:
    project_root = os.path.abspath(config.PROJECT_ROOT)
    return [
        os.path.abspath(config.SNAPSHOT_DIR),
        os.path.abspath(config.RECORDING_DIR),
        os.path.abspath(os.path.join(project_root, 'data', 'snapshots')),
        os.path.abspath(os.path.join(project_root, 'data', 'recordings')),
        os.path.abspath(os.path.join(project_root, 'data', 'evidence')),
        os.path.abspath(os.path.join(project_root, 'data', 'people', 'appearances')),
        os.path.abspath(os.path.join(project_root, 'data', 'people', 'profiles')),
        os.path.abspath(os.path.join(project_root, 'data', 'people', 'clusters')),
        os.path.abspath(os.path.join(project_root, 'data', 'faces')),
        os.path.abspath(os.path.join(project_root, 'data')),
    ]

def resolve_media_file(raw_path: Optional[str]) -> Optional[str]:
    """
    Authoritative media file resolver for CUSTOS.
    Given a stored path (bare filename, relative path, or absolute path),
    locates the verified file on disk within authorized CUSTOS directories.
    Returns the normalized absolute path if the file exists and is non-empty (>0 bytes),
    otherwise returns None.
    """
    if not raw_path or not isinstance(raw_path, str):
        return None

    raw_path = raw_path.strip()
    if not raw_path:
        return None

    project_root = os.path.abspath(config.PROJECT_ROOT)
    search_dirs = get_media_search_dirs()

    candidates: List[str] = []

    # 1. Direct path check (if absolute)
    if os.path.isabs(raw_path):
        candidates.append(raw_path)

    # 2. Relative to PROJECT_ROOT
    candidates.append(os.path.join(project_root, raw_path))

    # 3. Base filename across all authorized search directories
    base_name = os.path.basename(raw_path)
    for sdir in search_dirs:
        candidates.append(os.path.join(sdir, base_name))
        candidates.append(os.path.join(sdir, raw_path))

    # 4. Normalized relative paths with subdirectories (e.g., "cluster_001/file.jpg")
    clean_rel = raw_path.replace('\\', '/').lstrip('/')
    candidates.append(os.path.join(project_root, 'data', 'people', 'profiles', clean_rel))
    candidates.append(os.path.join(project_root, 'data', 'people', 'clusters', clean_rel))
    candidates.append(os.path.join(project_root, 'data', 'people', 'appearances', clean_rel))
    candidates.append(os.path.join(project_root, 'data', clean_rel))

    # 5. Extract relative path after any 'data/' segment (handles relocated repositories)
    norm_parts = clean_rel.split('/')
    if 'data' in norm_parts:
        data_idx = norm_parts.index('data')
        rel_from_data = os.path.join(*norm_parts[data_idx:])
        candidates.append(os.path.join(project_root, rel_from_data))
    if 'people' in norm_parts:
        people_idx = norm_parts.index('people')
        rel_from_people = os.path.join(*norm_parts[people_idx:])
        candidates.append(os.path.join(project_root, 'data', rel_from_people))

    for c in candidates:
        try:
            abs_c = os.path.abspath(c)
            # Security verification: must reside inside project_root or authorized search dir
            is_authorized = abs_c.startswith(project_root) or any(abs_c.startswith(d) for d in search_dirs)
            if is_authorized and os.path.isfile(abs_c) and os.path.getsize(abs_c) > 0:
                return abs_c
        except Exception:
            continue

    return None
