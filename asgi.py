# TEMP TEST HOOK — REMOVE AFTER TESTING
from re_humanizer.rehumanizer import rehumanize

test_text = """
I've been thinking a lot about AI governance lately, and while there are many benefits,
there are also risks. Not this, not that, but rather a careful approach that balances
innovation with safety.
"""

print("=== REHUMANIZER TEST OUTPUT ===")
print(rehumanize(test_text, "get_to_point", "professional"))
print("=== END TEST ===")



from app.server import app

