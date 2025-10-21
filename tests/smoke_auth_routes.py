#!/usr/bin/env python3
"""
Smoke test for auth routes without running the server.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import app

routes = [
    ("/login", 200),
    ("/register", 200),
    ("/request-password-reset", 200),
    ("/reset-password/invalidtoken", 302),  # should redirect with flash due to invalid/expired token
    ("/verify-email?token=invalid", 302),   # invalid token -> redirect
]

results = []
with app.test_client() as client:
    for path, expected_min in routes:
        resp = client.get(path, follow_redirects=False)
        results.append((path, resp.status_code))

for path, code in results:
    print(f"{path}: {code}")

