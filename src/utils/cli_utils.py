import os
from collections.abc import Callable

from utils.file_utils import calculate_file_hash, get_all_files


def format_timestamp(ts: str) -> str:
    """Format timestamp YYYYMMDD-HHMMSS to YYYY-MM-DD HH:MM:SS"""
    # Guard against malformed input to avoid producing nonsense strings
    if not isinstance(ts, str) or len(ts) < 15 or ts[8] != "-":
        return ts
    try:
        return f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]} {ts[9:11]}:{ts[11:13]}:{ts[13:15]}"
    except (IndexError, TypeError):
        return ts


def resolve_output_folder(output_arg: str | None,
                           config_default: str,
                           user_cwd: str,
                           app_dir: str) -> str:
    """Resolve CLI output folder.
    - output_arg relative to user_cwd (CLI UX)
    - config_default relative to app_dir (config semantics)
    Returns absolute normalized path.
    """
    path: str
    if output_arg:
        if os.path.isabs(output_arg):
            path = output_arg
        else:
            path = os.path.join(user_cwd, output_arg)
    else:
        # Use config default, resolve relative to app directory
        if os.path.isabs(config_default):
            path = config_default
        else:
            path = os.path.join(app_dir, config_default)
    return os.path.abspath(os.path.normpath(path))


def collect_files(files: list[str],
                  folders: list[str],
                  base_dir: str,
                  print_fn: Callable[[str], None] = print) -> list[str]:
    """Collect files from explicit files and recursively from folders.
    Resolves relative paths against base_dir. Prints warnings via print_fn.
    Returns a list of absolute file paths.
    """
    all_files: list[str] = []

    for file in files:
        candidate = file
        if not os.path.isabs(candidate):
            candidate = os.path.join(base_dir, candidate)
        if os.path.isfile(candidate):
            all_files.append(os.path.abspath(candidate))
        else:
            print_fn(f"Warning: File not found: {candidate}")

    for folder in folders:
        candidate = folder
        if not os.path.isabs(candidate):
            candidate = os.path.join(base_dir, candidate)
        if os.path.isdir(candidate):
            folder_files = get_all_files(candidate)
            all_files.extend(folder_files)
        else:
            print_fn(f"Warning: Directory not found: {candidate}")

    return all_files


def compute_hashes(files: list[str],
                   algorithm: str = 'sha256',
                   print_fn: Callable[[str], None] = print,
                   progress_step: int = 10) -> dict[str, str]:
    """Compute hashes for files with simple progress printing."""
    hashes: dict[str, str] = {}
    total = len(files)
    for i, file in enumerate(files):
        try:
            hashes[file] = calculate_file_hash(file, algorithm=algorithm)
        except Exception as e:
            hashes[file] = f"ERROR: {e!s}"
        if ((i + 1) % progress_step == 0) or (i + 1 == total):
            print_fn(f"Processed {i + 1}/{total} files")
    return hashes
