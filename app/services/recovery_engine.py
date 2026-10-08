import json
import os
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

from app import get_db_connection, update_job
from app.services.candidate_generator import generate_rule_based_candidates, generate_wordlist_candidates
from app.services.verifier import verify_password


def get_default_wordlist_path():
    candidates = [
        Path(__file__).resolve().parent.parent / 'wordlists' / 'wordlist.txt',
        Path(__file__).resolve().parent.parent / 'wordlists' / 'combined_wordlist.txt',
        Path(__file__).resolve().parent.parent / 'wordlists' / 'common_passwords.txt',
        Path(__file__).resolve().parent.parent / 'wordlists' / 'common.txt',
        Path(__file__).resolve().parent.parent / 'wordlists' / 'defaults.txt',
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return ''


class RecoveryEngine:
    def __init__(self, job_id, archive_id, method, options=None):
        self.job_id = job_id
        self.archive_id = archive_id
        self.method = method
        self.options = options or {}
        self.stop_event = threading.Event()
        self.thread = None

    def start_background(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        return self.job_id

    def run(self):
        job_conn = get_db_connection()
        row = job_conn.execute('SELECT * FROM jobs WHERE job_id = ?', (self.job_id,)).fetchone()
        job_conn.close()
        if not row:
            return

        archive_conn = get_db_connection()
        archive_row = archive_conn.execute('SELECT safe_path FROM archives WHERE id = ?', (self.archive_id,)).fetchone()
        archive_conn.close()
        if not archive_row:
            update_job(self.job_id, status='failed', result='Archive missing')
            return

        archive_path = archive_row['safe_path']
        password = None
        attempts = 0
        start = time.time()
        update_job(self.job_id, status='running', started_at=datetime.utcnow().isoformat())

        try:
            candidates = []
            if self.method == 'wordlist':
                wordlist = (self.options.get('wordlist_path') or get_default_wordlist_path()).strip()
                if not wordlist:
                    raise FileNotFoundError('No wordlist file found. Add a wordlist under the project wordlists folder or select a custom path.')
                candidates = generate_wordlist_candidates(wordlist)
            elif self.method == 'rule':
                base_words = (self.options.get('base_words') or '').splitlines()
                candidates = generate_rule_based_candidates([w for w in base_words if w.strip()])
            else:
                candidates = self.options.get('candidates', [])

            total = len(candidates)
            update_job(self.job_id, total_candidates=total, search_space=json.dumps({'total': total, 'method': self.method}))
            for candidate in candidates:
                if self.stop_event.is_set():
                    update_job(self.job_id, status='cancelled', result='Cancelled by user', elapsed_seconds=time.time() - start)
                    return
                attempts += 1
                ok, detail = verify_password(archive_path, candidate)
                progress = (attempts / total) * 100 if total else 0
                update_job(self.job_id, attempts=attempts, progress=progress, elapsed_seconds=time.time() - start, notes=detail.get('message', 'Testing candidate'))
                if ok:
                    password = candidate
                    update_job(self.job_id, status='recovered', password=candidate, result='PASSWORD_RECOVERED', attempts=attempts, elapsed_seconds=time.time() - start, ended_at=datetime.utcnow().isoformat())
                    return

            update_job(self.job_id, status='completed', result='RECOVERY_COMPLETED', attempts=attempts, elapsed_seconds=time.time() - start, ended_at=datetime.utcnow().isoformat())
        except Exception as exc:
            update_job(self.job_id, status='failed', result=f'ERROR: {exc}', elapsed_seconds=time.time() - start)
