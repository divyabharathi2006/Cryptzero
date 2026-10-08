import zipfile
from pathlib import Path

import pyzipper

try:
    import rarfile
except Exception:  # pragma: no cover
    rarfile = None


def verify_password(zip_path, candidate_password):
    archive_path = Path(zip_path)
    suffix = archive_path.suffix.lower()

    if suffix == '.rar':
        if rarfile is None:
            return False, {'error_code': 'UNSUPPORTED_FORMAT', 'message': 'RAR verification requires the rarfile package and an external RAR backend.'}
        try:
            with rarfile.RarFile(str(archive_path), 'r') as rf:
                infos = [info for info in rf.infolist() if not info.isdir()]
                if not infos:
                    return False, {'error_code': 'NO_ENTRIES', 'message': 'Archive has no readable entries.'}
                try:
                    rf.setpassword(candidate_password)
                    rf.read(infos[0].filename, pwd=candidate_password)
                    return True, {'error_code': None, 'message': 'Password verified successfully.'}
                except Exception as exc:
                    message = str(exc).lower()
                    if 'password' in message or 'wrong' in message or 'bad' in message:
                        return False, {'error_code': 'WRONG_PASSWORD', 'message': 'Candidate password is incorrect.'}
                    return False, {'error_code': 'PROCESSING_ERROR', 'message': f'Password verification failed: {exc}'}
        except Exception as exc:
            return False, {'error_code': 'PROCESSING_ERROR', 'message': f'Unable to verify archive: {exc}'}

    try:
        with pyzipper.AESZipFile(zip_path, 'r') as zf:
            infos = [info for info in zf.infolist() if not info.is_dir()]
            if not infos:
                return False, {'error_code': 'NO_ENTRIES', 'message': 'Archive has no readable entries.'}
            target = infos[0]
            try:
                zf.setpassword(candidate_password.encode('utf-8'))
                with zf.open(target, 'r') as fh:
                    fh.read(64)
                return True, {'error_code': None, 'message': 'Password verified successfully.'}
            except RuntimeError:
                return False, {'error_code': 'WRONG_PASSWORD', 'message': 'Candidate password is incorrect.'}
            except Exception as exc:
                return False, {'error_code': 'PROCESSING_ERROR', 'message': f'Password verification failed: {exc}'}
    except zipfile.BadZipFile:
        return False, {'error_code': 'INVALID_ZIP', 'message': 'The archive is corrupted or not a readable ZIP.'}
    except Exception as exc:
        return False, {'error_code': 'PROCESSING_ERROR', 'message': f'Unable to verify archive: {exc}'}
