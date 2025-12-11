"""Quick script to check what routes are registered."""
import sys
sys.path.insert(0, 'src')

from eva_api import main

print('\nAll registered routes:')
for route in main.app.routes:
    if hasattr(route, 'path'):
        methods = list(route.methods) if hasattr(route, 'methods') else ['WS']
        print(f'  {route.path:50} {methods}')
        
route_count = len([r for r in main.app.routes if hasattr(r, 'path')])
print(f'\nTotal routes: {route_count}')

# Check if spaces router is included
spaces_routes = [r for r in main.app.routes if hasattr(r, 'path') and '/spaces' in r.path]
print(f'Spaces routes: {len(spaces_routes)}')
for r in spaces_routes:
    print(f'  {r.path}')
