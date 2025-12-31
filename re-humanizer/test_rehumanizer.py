from re_humanizer.rehumanizer import rehumanize

text = """
I've been thinking a lot about AI governance lately, and while there are many benefits,
there are also risks. Not this, not that, but rather a careful approach that balances
innovation with safety.
"""

print(rehumanize(text, "get_to_point", "professional"))
