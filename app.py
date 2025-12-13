import sys
import os

print("🟢 [DEBUG] app.py imported")
print("🟢 [DEBUG] __file__ =", __file__)
print("🟢 [DEBUG] sys.path (head) =", sys.path[:3])

# ensure it runs from the right folder
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.server import app

print("🟢 [DEBUG] app.server.app imported successfully")
