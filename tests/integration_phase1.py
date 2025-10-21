#!/usr/bin/env python3
"""
Phase 1 integration test:
- DB connectivity
- Auth (register/login or ensure user exists)
- Image converter POST
- Usage tracking increments and storage > 0
- Dashboard debug endpoint values are coherent
"""
import io
from PIL import Image
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import app
from models import db, User

USERNAME = "phase1tester"
EMAIL = "phase1tester@example.com"
PASSWORD = "testpass123"

with app.app_context():
    user = User.query.filter_by(username=USERNAME).first()
    if not user:
        user = User(username=USERNAME, email=EMAIL, subscription_tier='free', email_verified=True, is_active=True)
        user.set_password(PASSWORD)
        db.session.add(user)
        db.session.commit()

with app.test_client() as client:
    # Login
    resp = client.post('/login', data={'username_or_email': USERNAME, 'password': PASSWORD}, follow_redirects=True)
    print('Login status:', resp.status_code)

    # Read debug totals before
    before = client.get('/dashboard/api/debug-totals').json
    print('Before:', before)

    # Create a small PNG in memory
    img = Image.new('RGBA', (32, 32), color=(255, 0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    data = {
        'file': (buf, 'test.png'),
        'format': 'pdf'
    }

    # POST to image converter
    resp = client.post('/image-converter', data=data, content_type='multipart/form-data')
    print('Image converter POST:', resp.status_code)

    # Read debug totals after
    after = client.get('/dashboard/api/debug-totals').json
    print('After:', after)

    # Basic assertions in output (not using pytest)
    ok = True
    if after['today_usage']['conversions_count'] < before['today_usage']['conversions_count'] + 1:
        ok = False
        print('ERROR: conversions_count did not increase by at least 1')
    if after['total_conversions_from_usage'] < before['total_conversions_from_usage'] + 1:
        ok = False
        print('ERROR: total_conversions_from_usage did not increase by at least 1')
    if after['total_storage_from_usage_bytes'] <= before['total_storage_from_usage_bytes']:
        ok = False
        print('ERROR: total_storage_from_usage_bytes did not increase')

    print('\nRESULT:', 'PASS' if ok else 'FAIL')

