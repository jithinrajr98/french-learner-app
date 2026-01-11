import re
from typing import List, Tuple

# French abbreviations that should NOT end a sentence
FRENCH_ABBREVIATIONS = {
    'M', 'Mme', 'Mlle', 'Dr', 'Prof', 'Sr', 'Jr', 'St', 'Ste',
    'av', 'bd', 'pl', 'etc', 'ex', 'cf', 'vol', 'p', 'pp',
    'n', 'no', 'tel', 'fax', 'env', 'min', 'max', 'approx'
}


def parse_sentences(text: str) -> List[str]:
    """
    Parse French or English text into sentences, handling edge cases.

    Returns list of sentences with original punctuation preserved.
    """
    if not text or not text.strip():
        return []

    protected_text = text

    # Protect abbreviations by temporarily replacing their periods
    for abbr in FRENCH_ABBREVIATIONS:
        pattern = rf'\b({abbr})\.(?=\s)'
        protected_text = re.sub(pattern, r'\1<DOT>', protected_text, flags=re.IGNORECASE)

    # Protect decimal numbers (e.g., 3.14, 20.39)
    protected_text = re.sub(r'(\d)\.(\d)', r'\1<DECIMAL>\2', protected_text)

    # Protect ellipses
    protected_text = protected_text.replace('...', '<ELLIPSIS>')

    # Protect times like 20h39 (French time format)
    protected_text = re.sub(r'(\d+)h(\d+)', r'\1<HOUR>\2', protected_text)

    # Split on sentence-ending punctuation followed by space and capital letter
    sentence_pattern = r'(?<=[.!?])\s+(?=[A-ZÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ])'
    raw_sentences = re.split(sentence_pattern, protected_text)

    # Restore protected characters
    sentences = []
    for sent in raw_sentences:
        sent = sent.replace('<DOT>', '.')
        sent = sent.replace('<DECIMAL>', '.')
        sent = sent.replace('<ELLIPSIS>', '...')
        sent = sent.replace('<HOUR>', 'h')
        sent = sent.strip()
        if sent:
            sentences.append(sent)

    return sentences


def align_sentences(french_sentences: List[str], english_sentences: List[str]) -> List[Tuple[str, str]]:
    """
    Align French and English sentences into pairs.

    Uses simple 1:1 alignment - pairs what we can based on minimum count.
    """
    pairs = []
    min_len = min(len(french_sentences), len(english_sentences))

    for i in range(min_len):
        pairs.append((french_sentences[i], english_sentences[i]))

    return pairs


def load_and_parse_transcripts(french_path: str, english_path: str) -> List[Tuple[str, str]]:
    """
    Load transcript files and return aligned sentence pairs.

    Args:
        french_path: Path to French transcript file
        english_path: Path to English transcript file

    Returns:
        List of (french_sentence, english_sentence) tuples
    """
    with open(french_path, 'r', encoding='utf-8') as f:
        french_text = f.read()

    with open(english_path, 'r', encoding='utf-8') as f:
        english_text = f.read()

    french_sentences = parse_sentences(french_text)
    english_sentences = parse_sentences(english_text)

    return align_sentences(french_sentences, english_sentences)
