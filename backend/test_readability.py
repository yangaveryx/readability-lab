from pprint import pprint

from readability import analyze_readability


simple_text = """
The dog ran home. It was tired. The dog slept on the rug.
"""

complex_text = """
Although Maya had planned to finish the assignment before dinner,
she continued revising it after everyone else had gone to sleep.
Because the evidence she discovered contradicted her original argument,
she decided that rewriting the conclusion would make the paper clearer.
"""


print("Simple paragraph:")
pprint(analyze_readability(simple_text))

print("\nComplex paragraph:")
pprint(analyze_readability(complex_text))