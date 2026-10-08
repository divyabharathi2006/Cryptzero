import mimetypes
from pathlib import Path
import zipfile


def _read_head(file_path, max_bytes=2048):
    try:
        with open(file_path, 'rb') as fh:
            return fh.read(max_bytes)
    except OSError:
        return b''


def _detect_zip_encryption(file_path):
    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            infos = zf.infolist()
            for info in infos:
                if info.flag_bits & 0x1:
                    return True, 'AES', 'Password required for AES-encrypted ZIP file.'
        return False, 'NONE', 'Archive is not encrypted.'
    except Exception:
        return False, 'UNKNOWN', 'Unable to inspect ZIP metadata.'


def analyze_file(file_path):
    path = Path(file_path)
    name = path.name.lower()
    size = path.stat().st_size if path.exists() else 0
    head = _read_head(str(path))
    mime_type = mimetypes.guess_type(name)[0] or 'application/octet-stream'

    detected_format = 'UNKNOWN'
    encryption_type = 'NONE'
    status = 'unsupported'
    requires_password = False
    support_status = 'UNSUPPORTED'
    notes = []

    if head.startswith(b'%PDF'):
        detected_format = 'PDF'
        if b'/Encrypt' in head:
            encryption_type = 'PDF_PASSWORD'
            requires_password = True
            status = 'password_required'
            support_status = 'SUPPORTED'
            notes.append('Detected password-protected PDF.')
        else:
            status = 'not_encrypted'
            support_status = 'SUPPORTED'

    elif head.startswith(b'7z\xbc\xaf\x27\x1c'):
        detected_format = '7Z'
        encryption_type = 'AES'
        requires_password = True
        status = 'password_required'
        support_status = 'SUPPORTED'
        notes.append('7-Zip archive detected.')

    elif zipfile.is_zipfile(str(path)):
        detected_format = 'ZIP'
        encrypted, enc_method, msg = _detect_zip_encryption(str(path))
        if encrypted:
            encryption_type = enc_method
            requires_password = True
            status = 'password_required'
            support_status = 'SUPPORTED'
            notes.append(msg)
        else:
            status = 'not_encrypted'
            support_status = 'SUPPORTED'

    elif name.endswith('.gpg') or 'BEGIN PGP MESSAGE' in head.decode('latin-1', errors='ignore'):
        detected_format = 'GPG/PGP'
        encryption_type = 'PGP'
        requires_password = True
        status = 'password_required'
        support_status = 'SUPPORTED_IF_DEPS_AVAILABLE'
        notes.append('GPG/PGP encrypted file detected.')

    elif head.startswith(b'age-encryption.org/v1'):
        detected_format = 'AGE'
        encryption_type = 'AGE'
        requires_password = True
        status = 'password_required'
        support_status = 'SUPPORTED_IF_DEPS_AVAILABLE'
        notes.append('Age-encrypted file detected.')

    elif name.endswith(('.docx', '.xlsx', '.pptx')) or zipfile.is_zipfile(str(path)):
        detected_format = 'OFFICE'
        encryption_type = 'ZIP_CONTAINER'
        requires_password = True
        status = 'password_required'
        support_status = 'SUPPORTED_IF_LIBRARY_AVAILABLE'
        notes.append('Office-compatible package detected.')

    elif name.endswith('.rar') or b'Rar!' in head:
        detected_format = 'RAR'
        encryption_type = 'RAR_ENCRYPTION'
        requires_password = True
        status = 'password_required'
        support_status = 'SUPPORTED_IF_LICENSED_BACKEND_AVAILABLE'
        notes.append('RAR archive detected.')

    elif name.endswith(('.tar', '.gz', '.bz2', '.xz')):
        detected_format = 'TAR'
        status = 'not_encrypted'
        support_status = 'SUPPORTED'
        notes.append('TAR archive detected.')

    else:
        notes.append('CRYPTZERO cannot decrypt this file because its encryption format is not currently supported.')

    return {
        'filename': path.name,
        'size': size,
        'mime_type': mime_type,
        'detected_format': detected_format,
        'encryption_type': encryption_type,
        'status': status,
        'requires_password': requires_password,
        'support_status': support_status,
        'possible_methods': ['ZIP', '7Z', 'PDF', 'OFFICE', 'GPG/PGP', 'AGE'],
        'notes': notes,
    }
