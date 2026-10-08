from app.decryptors.age import AgeDecryptor
from app.decryptors.gpg import GpgDecryptor
from app.decryptors.office import OfficeDecryptor
from app.decryptors.pdf import PdfDecryptor
from app.decryptors.rar import RarDecryptor
from app.decryptors.sevenzip import SevenZipDecryptor
from app.decryptors.zip import ZipDecryptor
from app.decryptors.base import FileDecryptor


def resolve_handler(detected_format):
    mapping = {
        'ZIP': ZipDecryptor(),
        'RAR': RarDecryptor(),
        '7Z': SevenZipDecryptor(),
        'PDF': PdfDecryptor(),
        'OFFICE': OfficeDecryptor(),
        'GPG/PGP': GpgDecryptor(),
        'AGE': AgeDecryptor(),
    }
    return mapping.get(detected_format, FileDecryptor())


def get_capabilities():
    return {
        'formats': ['ZIP', 'RAR', '7Z', 'PDF', 'OFFICE', 'GPG/PGP', 'AGE'],
        'encryption_methods': ['AES', 'RAR_ENCRYPTION', 'PDF_PASSWORD', 'PGP', 'AGE'],
        'supported_types': {
            'ZIP': 'supported',
            'RAR': 'supported_if_rar_dependency_available',
            '7Z': 'supported',
            'PDF': 'supported_if_library_available',
            'OFFICE': 'supported_if_library_available',
            'GPG/PGP': 'supported_if_dependency_available',
            'AGE': 'supported_if_dependency_available',
        },
    }
