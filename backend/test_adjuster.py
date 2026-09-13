from pprint import pprint

from adjuster import adjust_text
from readability import analyze_readability


original_text = """
Photosynthesis is the biochemical process through which plants,
algae, and certain bacteria convert light energy into chemical
energy. During this process, organisms use sunlight, water, and
carbon dioxide to produce glucose and release oxygen.
"""

target_grade = 5

result = adjust_text(
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

print("\nDIRECTION")
print("---------")
print(result["direction"])

print("\nATTEMPTS")
print("--------")

if result["attempts"]:
    for attempt in result["attempts"]:
        print(f"\nAttempt {attempt['attempt']}")
        print(
            "Measured grade:",
            attempt["metrics"]["flesch_kincaid_grade"],
        )
        print(attempt["text"])
else:
    print("No rewrite was needed because the text was already near the target.")

print("\nBEST RESULT")
print("-----------")
print(result["text"])

print("\nBEST RESULT METRICS")
print("-------------------")
pprint(result["metrics"])

print("\nTOTAL ATTEMPTS")
print("--------------")
print(result["attempt_count"])