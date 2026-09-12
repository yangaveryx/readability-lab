import spacy
import textstat

nlp = spacy.load("en_core_web_sm")


def get_tree_depth(token) -> int:
    """
    Find the maximum depth below a token in the dependency tree.

    A token with no children has depth 1.
    """
    children = list(token.children)

    if not children:
        return 1

    return 1 + max(get_tree_depth(child) for child in children)


def analyze_readability(text: str) -> dict:
    """
    Calculate readability and sentence-structure metrics for a piece of text.
    """
    if not text.strip():
        return {
            "flesch_kincaid_grade": 0.0,
            "syllable_count": 0,
            "average_sentence_length": 0.0,
            "average_dependency_depth": 0.0,
            "maximum_dependency_depth": 0,
        }

    doc = nlp(text)
    sentences = list(doc.sents)

    word_counts = [
        sum(1 for token in sentence if not token.is_punct and not token.is_space)
        for sentence in sentences
    ]

    sentence_depths = [
        get_tree_depth(sentence.root)
        for sentence in sentences
    ]

    return {
        "flesch_kincaid_grade": round(
            textstat.flesch_kincaid_grade(text), 2
        ),
        "syllable_count": textstat.syllable_count(text),
        "average_sentence_length": round(
            sum(word_counts) / len(sentences), 2
        ),
        "average_dependency_depth": round(
            sum(sentence_depths) / len(sentences), 2
        ),
        "maximum_dependency_depth": max(sentence_depths),
    }