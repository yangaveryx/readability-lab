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

result = simplify_text(
    text=original_text,
    target_grade=target_grade,
    max_attempts=3,
)

print("ORIGINAL TEXT")
print("-------------")
print(original_text.strip())

print("\nORIGINAL METRICS")
print("----------------")
pprint(analyze_readability(original_text))

print("\nATTEMPTS")
print("--------")

for attempt in result["attempts"]:
    print(f"\nAttempt {attempt['attempt']}")
    print(
        "Measured grade:",
        attempt["metrics"]["flesch_kincaid_grade"],
    )
    print(attempt["text"])

print("\nBEST RESULT")
print("-----------")
print(result["text"])

print("\nBEST RESULT METRICS")
print("-------------------")
pprint(result["metrics"])

print("\nTOTAL ATTEMPTS")
print("--------------")
print(result["attempt_count"])