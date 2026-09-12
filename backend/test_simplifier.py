from pprint import pprint

from readability import analyze_readability
from simplifier import simplify_text


original_text = """
Photosynthesis is the biochemical process through which plants,
algae, and certain bacteria convert light energy into chemical
energy. During this process, organisms use sunlight, water, and
carbon dioxide to produce glucose and release oxygen.
"""

target_grade = 5

simplified_text = simplify_text(original_text, target_grade)

print("ORIGINAL TEXT")
print("-------------")
print(original_text.strip())

print("\nORIGINAL METRICS")
print("----------------")
pprint(analyze_readability(original_text))

print("\nSIMPLIFIED TEXT")
print("---------------")
print(simplified_text)

print("\nSIMPLIFIED METRICS")
print("------------------")
pprint(analyze_readability(simplified_text))