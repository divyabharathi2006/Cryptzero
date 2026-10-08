import os
from pathlib import Path

import py7zr
import pyzipper

from app import create_app


def make_zip_archive(path, password='secret123'):
    with pyzipper.AESZipFile(
        path,
        'w',
        compression=pyzipper.ZIP_DEFLATED,
        encryption=pyzipper.WZ_AES,
    ) as zf:
        zf.setpassword(password.encode())
        zf.writestr('hello.txt', 'hello world')


def make_7z_archive(path, password='7zipsecret'):
    with py7zr.SevenZipFile(path, 'w', password=password) as zf:
        zf.writeall({'hello.txt': b'hello world'})


def test_health_and_capabilities():
    app = create_app()
    client = app.test_client()

    health_resp = client.get('/api/health')
    assert health_resp.status_code == 200
    payload = health_resp.get_json()
    assert payload['success'] is True
    assert 'formats' in payload['capabilities']

    cap_resp = client.get('/api/capabilities')
    assert cap_resp.status_code == 200
    cap = cap_resp.get_json()
    assert 'ZIP' in cap['formats']


def test_zip_upload_and_unlock(tmp_path):
    app = create_app()
    client = app.test_client()

    zip_path = tmp_path / 'sample.zip'
    make_zip_archive(zip_path)

    with open(zip_path, 'rb') as fh:
        upload_resp = client.post('/api/files/upload', data={'file': (fh, 'sample.zip')})
    assert upload_resp.status_code == 200, upload_resp.get_data(as_text=True)
    upload_data = upload_resp.get_json()
    job_id = upload_data['job_id']
    assert upload_data['success'] is True

    unlock_resp = client.post('/api/files/unlock', json={'job_id': job_id, 'credential': 'secret123'})
    assert unlock_resp.status_code == 200, unlock_resp.get_data(as_text=True)
    result = unlock_resp.get_json()
    assert result['success'] is True


def test_wrong_zip_password(tmp_path):
    app = create_app()
    client = app.test_client()

    zip_path = tmp_path / 'bad.zip'
    make_zip_archive(zip_path)

    with open(zip_path, 'rb') as fh:
        upload_resp = client.post('/api/files/upload', data={'file': (fh, 'bad.zip')})
    payload = upload_resp.get_json()
    job_id = payload['job_id']

    unlock_resp = client.post('/api/files/unlock', json={'job_id': job_id, 'credential': 'wrong-pass'})
    assert unlock_resp.status_code == 200
    result = unlock_resp.get_json()
    assert result['success'] is False
    assert result['error_code'] in {'WRONG_PASSWORD', 'PROCESSING_ERROR'}


def test_recovery_api_tracks_job_and_verifies_password(tmp_path):
    app = create_app()
    client = app.test_client()

    zip_path = tmp_path / 'recoverable.zip'
    make_zip_archive(zip_path)

    with open(zip_path, 'rb') as fh:
        upload_resp = client.post('/api/archive/upload', data={'file': (fh, 'recoverable.zip')})
    assert upload_resp.status_code == 200, upload_resp.get_data(as_text=True)
    archive_id = upload_resp.get_json()['archive_id']

    start_resp = client.post('/api/recovery/start', json={'archive_id': archive_id, 'method': 'rule', 'options': {'base_words': 'secret123'}})
    assert start_resp.status_code == 200, start_resp.get_data(as_text=True)
    job_id = start_resp.get_json()['job_id']

    verify_resp = client.post(f'/api/recovery/{job_id}/verify', json={'candidate': 'secret123'})
    assert verify_resp.status_code == 200, verify_resp.get_data(as_text=True)
    payload = verify_resp.get_json()
    assert payload['success'] is True
    assert payload['password_valid'] is True


def test_rar_upload_is_accepted_and_detected(tmp_path):
    app = create_app()
    client = app.test_client()

    rar_path = tmp_path / 'sample.rar'
    rar_path.write_bytes(b'')

    with open(rar_path, 'rb') as fh:
        upload_resp = client.post('/api/files/upload', data={'file': (fh, 'sample.rar')})
    assert upload_resp.status_code == 200, upload_resp.get_data(as_text=True)
    payload = upload_resp.get_json()
    assert payload['success'] is True
    assert payload['analysis']['detected_format'] == 'RAR'

    archive_resp = client.post('/api/archive/upload', data={'file': (rar_path.open('rb'), 'sample.rar')})
    assert archive_resp.status_code == 200, archive_resp.get_data(as_text=True)
