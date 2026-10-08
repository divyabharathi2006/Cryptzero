import os
import zipfile
from pathlib import Path

import pyzipper

try:
    import rarfile
except Exception:  # pragma: no cover
    rarfile = None


def safe_extract_zip(zip_path, password=None):
    try:
        archive_path = Path(zip_path)
        if not archive_path.exists():
            return {'success': False, 'error_code': 'INVALID_FILE', 'message': 'Archive file is missing.'}

        if archive_path.suffix.lower() == '.rar':
            if rarfile is None:
                return {'success': False, 'error_code': 'UNSUPPORTED_FORMAT', 'message': 'RAR extraction is not available because rarfile/unrar support is not installed in this runtime.'}
            try:
                with rarfile.RarFile(str(archive_path), 'r') as rf:
                    if password:
                        rf.setpassword(password)
                    extract_root = archive_path.parent.parent / 'extracted' / archive_path.stem
                    extract_root.mkdir(parents=True, exist_ok=True)
                    rf.extractall(path=str(extract_root), members=rf.infolist())
                return {'success': True, 'output_dir': str(extract_root), 'message': 'RAR archive extracted safely.'}
            except Exception as exc:
                message = str(exc).lower()
                if 'password' in message or 'wrong' in message or 'bad' in message:
                    return {'success': False, 'error_code': 'WRONG_PASSWORD', 'message': 'Password is incorrect or archive is encrypted with unsupported settings.'}
                return {'success': False, 'error_code': 'PROCESSING_ERROR', 'message': f'Extraction failed: {exc}'}

        extract_root = archive_path.parent.parent / 'extracted' / archive_path.stem
        extract_root.mkdir(parents=True, exist_ok=True)

        with pyzipper.AESZipFile(str(archive_path), 'r') as zf:
            for member in zf.infolist():
                candidate = member.filename
                if candidate.startswith('/') or candidate.startswith('\\'):
                    return {'success': False, 'error_code': 'UNSAFE_PATH', 'message': 'Archive contains an unsafe absolute path.'}
                if '..' in candidate.split('/'):
                    return {'success': False, 'error_code': 'UNSAFE_PATH', 'message': 'Archive contains a traversal path.'}
                if member.is_dir():
                    continue
                target = (extract_root / candidate).resolve()
                if extract_root.resolve() not in target.parents and target != extract_root.resolve():
                    return {'success': False, 'error_code': 'UNSAFE_PATH', 'message': 'Archive member escapes the extraction directory.'}

            if password:
                zf.setpassword(password.encode('utf-8'))
            zf.extractall(str(extract_root))

        return {'success': True, 'output_dir': str(extract_root), 'message': 'Archive extracted safely.'}
    except RuntimeError:
        return {'success': False, 'error_code': 'WRONG_PASSWORD', 'message': 'Password is incorrect or archive is encrypted with unsupported settings.'}
    except zipfile.BadZipFile:
        return {'success': False, 'error_code': 'INVALID_ZIP', 'message': 'Archive is corrupt or invalid.'}
    except Exception as exc:
        return {'success': False, 'error_code': 'PROCESSING_ERROR', 'message': f'Extraction failed: {exc}'}
