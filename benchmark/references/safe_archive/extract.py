from pathlib import Path, PurePosixPath
import stat
import zipfile


def extract_zip(zip_path, destination):
    root = Path(destination)
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ValueError('Invalid destination')
    planned, names, all_targets, total = [], set(), set(), 0
    try:
        with zipfile.ZipFile(zip_path) as archive:
            for entry in archive.infolist():
                name = entry.filename
                parts = PurePosixPath(name).parts
                kind = stat.S_IFMT(entry.external_attr >> 16)
                if (not name or name.startswith('/') or '\\' in name or ':' in name
                        or '..' in parts or not parts or kind not in {0, stat.S_IFREG, stat.S_IFDIR}):
                    raise ValueError('Unsafe archive member')
                canonical = PurePosixPath(name).as_posix().rstrip('/')
                if canonical in names:
                    raise ValueError('Duplicate archive path')
                names.add(canonical)
                target = root.joinpath(*parts)
                all_targets.add(target)
                if target.exists() or target.is_symlink():
                    raise ValueError('Existing path would be overwritten')
                for parent in target.parents:
                    if parent == root.parent:
                        break
                    if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                        raise ValueError('Unsafe parent path')
                if not entry.is_dir():
                    total += entry.file_size
                    if len(planned) >= 100 or total > 1024 * 1024:
                        raise ValueError('Archive exceeds limits')
                    planned.append((canonical, target, archive.read(entry)))
    except (OSError, zipfile.BadZipFile, RuntimeError):
        raise ValueError('Invalid archive') from None
    # All members and bytes are validated before touching the destination.
    file_targets = {target for _, target, _ in planned}
    if any(parent in file_targets for target in all_targets for parent in target.parents):
        raise ValueError('File also used as a directory')
    root.mkdir(parents=True, exist_ok=True)
    for _, target, data in planned:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return sorted(name for name, _, _ in planned)
