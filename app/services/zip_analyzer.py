import os
import zipfile
from pathlib import Path

try:
    import rarfile
except Exception:  # pragma: no cover
    rarfile = None


def analyze_zip_archive(zip_path):
    path = Path(zip_path)
    if not path.exists():
        raise FileNotFoundError('Archive file does not exist.')

    if path.suffix.lower() == '.rar':
        return {
            'filename': path.name,
            'size': path.stat().st_size,
            'entries': 0,
            'encrypted': False,
            'archive_ok': True,
            'safe_entries': [],
            'file_count': 0,
            'compressed_size': 0,
            'uncompressed_size': 0,
            'suspicious': False,
            'zip_bomb_risk': False,
            'reasons': [],
            'notes': 'RAR archive accepted for recovery. Password verification requires RAR support in the runtime.',
            'requires_password': False,
            'detected_format': 'RAR',
        }

    if not zipfile.is_zipfile(str(path)):
        raise ValueError('The uploaded file is not a valid .zip archive.')

    try:
        with zipfile.ZipFile(str(path), 'r') as zf:
            infos = zf.infolist()
            encrypted = any(info.flag_bits & 0x1 for info in infos)
            suspicious = False
            reasons = []
            total_uncompressed = 0
            total_compressed = 0

            for info in infos:
                total_uncompressed += info.file_size
                total_compressed += info.compress_size
                if info.file_size > 100 * 1024 * 1024:
                    suspicious = True
                    reasons.append(f'Large entry detected: {info.filename}')
                if info.filename.startswith('/') or '\\' in info.filename or '..' in info.filename:
                    suspicious = True
                    reasons.append(f'Unsafe path candidate: {info.filename}')

            zip_bomb = total_compressed > 0 and (total_uncompressed / max(total_compressed, 1)) > 200
            if zip_bomb:
                suspicious = True
                reasons.append('High compression ratio suggests ZIP-bomb risk.')

            safe_entries = [info.filename for info in infos[:20] if not info.is_dir()]
            return {
                'filename': path.name,
                'size': path.stat().st_size,
                'entries': len(infos),
                'encrypted': encrypted,
                'archive_ok': True,
                'safe_entries': safe_entries,
                'file_count': len(infos),
                'compressed_size': total_compressed,
                'uncompressed_size': total_uncompressed,
                'suspicious': suspicious,
                'zip_bomb_risk': zip_bomb,
                'reasons': reasons,
                'notes': 'Archive validated and ready for recovery.' if not suspicious else 'Archive contains suspicious characteristics that require cautious recovery.',
                'requires_password': encrypted,
                'detected_format': 'ZIP',
            }
    except zipfile.BadZipFile:
        raise ValueError('ZIP archive is corrupted or invalid.')
