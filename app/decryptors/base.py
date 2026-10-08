import os
import shutil


class FileDecryptor:
    name = 'generic'

    def detect(self, file_path):
        return False

    def analyze(self, file_path):
        return {'success': False, 'error_code': 'UNSUPPORTED_FORMAT', 'message': 'CRYPTZERO cannot decrypt this file because its encryption format is not currently supported.'}

    def decrypt(self, file_path, credential, job_id):
        return {'success': False, 'error_code': 'UNSUPPORTED_DECRYPTION_METHOD', 'message': 'CRYPTZERO cannot decrypt this file because its encryption format is not currently supported.'}

    def validate(self, output_path):
        return False

    def cleanup(self, path):
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
