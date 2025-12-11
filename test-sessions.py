#!/usr/bin/env python3
"""Quick test to verify sessions router is working"""

from eva_api.main import app

print("✅ App imports successfully with sessions router!")
print(f"📊 Total routes: {len(app.routes)}")

session_routes = [r for r in app.routes if '/sessions' in str(r)]
print(f"🔌 Session routes: {len(session_routes)}")

for route in session_routes:
    print(f"   - {route.methods} {route.path}")
