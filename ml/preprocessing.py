"""
CineCheck - NLP Preprocessing Pipeline
Covers TWSMA Syllabus Module 1.1 & Module 2.1:
- Tokenization, lowercasing, normalization
- Handling elongated words and repeated characters
- Handling excessive punctuation
- URL & whitespace normalization
- Stop-word removal with negation preservation
- Porter stemming with offline fallback
- Linguistic and heuristic indicator extraction for explainability
"""

import re
import string

# Robust fallback stop words list (Standard English stopwords minus negations)
NEGATION_WORDS = {
    'not', 'no', 'never', 'neither', 'nor', 'none', 'hardly', 'scarcely',
    'barely', 'without', 'cannot', "n't", 'aint', 'arent', 'cant', 'couldnt',
    'didnt', 'doesnt', 'dont', 'hadnt', 'hasnt', 'havent', 'isnt', 'mustnt',
    'shouldnt', 'wasnt', 'werent', 'wont', 'wouldnt'
}

STANDARD_STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're",
    "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he',
    'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's",
    'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
    'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because',
    'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
    'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
    'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
    'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just',
    'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y'
}

# Stopwords set excluding negations
FILTERED_STOPWORDS = STANDARD_STOPWORDS - NEGATION_WORDS

# Try importing NLTK PorterStemmer; fallback to simple rule stemmer if needed
try:
    from nltk.stem import PorterStemmer
    _stemmer = PorterStemmer()
    def stem_word(w: str) -> str:
        return _stemmer.stem(w)
except Exception:
    def stem_word(w: str) -> str:
        # Graceful fallback stemmer
        if w.endswith('ing') and len(w) > 5:
            return w[:-3]
        if w.endswith('ed') and len(w) > 4:
            return w[:-2]
        if w.endswith('ly') and len(w) > 4:
            return w[:-2]
        if w.endswith('s') and not w.endswith('ss') and len(w) > 3:
            return w[:-1]
        return w


# Promotional and bot-suspicious phrase patterns
PROMOTIONAL_PATTERNS = [
    r'\ball[\s\-]time[\s\-](blockbuster|superhit|record)\b',
    r'\bblockbuster\b',
    r'\bmust[\s\-]watch\b',
    r'\bgo[\s\-]book\b',
    r'\bbook[\s\-]your[\s\-]tickets\b',
    r'\bpaisa[\s\-]vasool\b',
    r'\bmasterpiece\b',
    r'\bmind[\s\-]blowing\b',
    r'\bworst[\s\-]movie[\s\-]ever\b',
    r'\bdisaster[\s\-]flop\b',
    r'\bboycott\b',
    r'\bpr[\s\-]team\b',
    r'\bhaters[\s\-]gonna[\s\-]cry\b',
    r'\bzero[\s\-]star\b',
    r'\b10/10\b',
    r'\bindustry[\s\-]hit\b',
    r'\bhistorical[\s\-]hit\b',
    r'\bskip[\s\-]this[\s\-]garbage\b'
]


def normalize_repeated_characters(text: str) -> str:
    """
    Compress character repetitions > 2 down to 2 (e.g. 'sooooo goooood' -> 'soo good').
    Preserves normal double letters in words like 'good', 'look', 'sweet'.
    """
    return re.sub(r'(.)\1{2,}', r'\1\1', text)


def normalize_excessive_punctuation(text: str) -> str:
    """
    Normalizes excessive punctuation like '!!!!!' or '?????' to a single instance
    with space padding for tokenization.
    """
    text = re.sub(r'(!)\1+', r' ! ', text)
    text = re.sub(r'(\?)\1+', r' ? ', text)
    text = re.sub(r'(\.)\1+', r' . ', text)
    return text


def clean_text(text: str, preserve_negations: bool = True, apply_stemming: bool = True, remove_stopwords: bool = True) -> str:
    """
    Primary NLP Preprocessing Pipeline:
    1. Check for empty/null text
    2. Lowercase and URL/email strip
    3. Normalize repeated characters ('gooooood' -> 'good')
    4. Normalize excessive punctuation
    5. Tokenize into words
    6. Stop-word removal (preserving negations like 'not', 'never')
    7. Stemming (Porter stemmer)
    """
    if not text or not isinstance(text, str):
        return ""

    raw = text.strip()
    if not raw:
        return ""

    # 1. Lowercase
    cleaned = raw.lower()

    # 2. Remove URLs, emails, and handles
    cleaned = re.sub(r'https?://\S+|www\.\S+', ' ', cleaned)
    cleaned = re.sub(r'\S+@\S+', ' ', cleaned)
    cleaned = re.sub(r'@\w+', ' ', cleaned)

    # 3. Handle repeated characters
    cleaned = normalize_repeated_characters(cleaned)

    # 4. Handle excessive punctuation
    cleaned = normalize_excessive_punctuation(cleaned)

    # 5. Extract words and preserved contractions (e.g., don't, can't)
    tokens = re.findall(r"\b[a-z0-9]+(?:'[a-z]+)?\b", cleaned)

    stopwords_to_use = FILTERED_STOPWORDS if preserve_negations else STANDARD_STOPWORDS

    # 6. Stop-word filtering & stemming
    processed_tokens = []
    for token in tokens:
        # Normalize simple contraction suffixes
        if token.endswith("'t") and token not in stopwords_to_use:
            token = token.replace("'", "")
        
        if remove_stopwords and token in stopwords_to_use:
            continue
        
        if apply_stemming:
            token = stem_word(token)
            
        if len(token) > 1 or token in {'a', 'i'}:
            processed_tokens.append(token)

    return " ".join(processed_tokens)


def extract_linguistic_signals(text: str, rating: float = None, movie_title: str = None) -> dict:
    """
    Extracts heuristic and stylistic signals for explainability and anomaly detection:
    - Uppercase ratio (shouting)
    - Exclamation mark count
    - Question mark count
    - Repeated character counts (elongated words)
    - Promotional buzzwords detected
    - Word count & average word length
    - Rating vs sentiment dissonance
    - Repeated wording detection
    - Generic wording detection
    - Movie keyword relevance checks
    """
    if not text or not isinstance(text, str):
        return {
            "is_empty": True,
            "word_count": 0,
            "warning_indicators": ["Empty or invalid review content"],
            "promotional_phrases": [],
            "uppercase_ratio": 0.0,
            "exclamation_count": 0,
            "repeated_char_words": 0,
            "rating_dissonance": False,
            "repeated_wording_flag": False,
            "generic_wording_flag": False,
            "movie_keyword_relevant": None
        }

    raw = text.strip()
    total_chars = len(raw)
    if total_chars == 0:
        return {
            "is_empty": True,
            "word_count": 0,
            "warning_indicators": ["Empty review content"],
            "promotional_phrases": [],
            "uppercase_ratio": 0.0,
            "exclamation_count": 0,
            "repeated_char_words": 0,
            "rating_dissonance": False,
            "repeated_wording_flag": False,
            "generic_wording_flag": False,
            "movie_keyword_relevant": None
        }

    words = raw.split()
    word_count = len(words)

    # Uppercase analysis
    alpha_chars = [c for c in raw if c.isalpha()]
    upper_chars = [c for c in alpha_chars if c.isupper()]
    uppercase_ratio = (len(upper_chars) / len(alpha_chars)) if alpha_chars else 0.0

    # Punctuation counts
    exclamation_count = raw.count('!')
    question_count = raw.count('?')

    # Elongated words (e.g., 'sooooo', 'cooool')
    elongated_words = [w for w in words if re.search(r'(.)\1{2,}', w)]

    # Promotional patterns check
    lower_raw = raw.lower()
    matched_promos = []
    for pat in PROMOTIONAL_PATTERNS:
        matches = re.findall(pat, lower_raw)
        if matches:
            clean_phrase = pat.replace(r'\b', '').replace(r'\s\-', ' ')
            matched_promos.append(clean_phrase)

    # Warnings accumulator
    warnings = []
    if uppercase_ratio > 0.45 and len(alpha_chars) >= 15:
        warnings.append(f"Excessive capitalization ({uppercase_ratio:.0%} shouting)")
    if exclamation_count >= 4:
        warnings.append(f"Excessive exclamation marks ({exclamation_count} detected)")
    if len(elongated_words) >= 2:
        warnings.append(f"Multiple elongated words found ({', '.join(elongated_words[:3])})")
    if len(matched_promos) >= 2:
        warnings.append(f"Multiple promotional hype patterns detected ({len(matched_promos)} matches)")
    elif len(matched_promos) == 1:
        warnings.append("Promotional phrase pattern detected")

    # Word count thresholds
    if word_count < 4:
        warnings.append("Extremely short review text (low informative value)")
    elif word_count > 300:
        warnings.append("Unusually long review text")

    # Repeated wording detection (internal repetition within review)
    from collections import Counter
    clean_words = [w for w in re.findall(r'\b[a-z]{3,}\b', lower_raw) if w not in STANDARD_STOPWORDS]
    word_counts = Counter(clean_words)
    repeated_words = [w for w, cnt in word_counts.items() if cnt >= 3]
    has_repeated_wording = bool(repeated_words and word_count <= 25)
    if has_repeated_wording:
        warnings.append(f"Excessive repeated wording detected ('{repeated_words[0]}' repeated {word_counts[repeated_words[0]]}x)")

    # Generic wording detection (stock boilerplate praise/hate)
    GENERIC_PATTERNS = [
        r'\b(nice|good|super|great|awesome|bad)\s+movie\b',
        r'\b(loved|liked)\s+it\b',
        r'\btime\s*pass\b',
        r'\bone\s*time\s*watch\b',
        r'\bwaste\s*of\s*(time|money)\b'
    ]
    generic_matches = [pat for pat in GENERIC_PATTERNS if re.search(pat, lower_raw)]
    is_generic = bool(generic_matches and word_count <= 8)
    if is_generic:
        warnings.append("Generic low-information review wording detected")

    # Movie keyword relevance checks
    movie_relevant = None
    if movie_title and isinstance(movie_title, str) and movie_title.strip():
        m_lower = movie_title.strip().lower()
        if m_lower not in ["unspecified movie", "general", "all", "unknown"]:
            m_tokens = [t for t in re.findall(r'\b[a-z0-9]{3,}\b', m_lower) if t not in STANDARD_STOPWORDS]
            if m_tokens:
                movie_relevant = any(mt in lower_raw for mt in m_tokens)

    # Rating vs Sentiment dissonance heuristic
    rating_dissonance = False
    if rating is not None:
        try:
            r = float(rating)
            has_extreme_praise = any(p in lower_raw for p in ['masterpiece', 'all-time blockbuster', '10/10', 'best movie ever'])
            has_extreme_hate = any(h in lower_raw for h in ['worst movie', 'disaster', 'zero star', 'skip this', 'garbage'])
            if r <= 2.0 and has_extreme_praise:
                warnings.append(f"Rating-text mismatch: Low rating ({r}/5) with extreme superlative praise")
                rating_dissonance = True
            elif r >= 4.5 and has_extreme_hate:
                warnings.append(f"Rating-text mismatch: High rating ({r}/5) with extreme negative smear")
                rating_dissonance = True
        except (ValueError, TypeError):
            pass

    return {
        "is_empty": False,
        "word_count": word_count,
        "warning_indicators": warnings,
        "promotional_phrases": matched_promos,
        "uppercase_ratio": round(uppercase_ratio, 3),
        "exclamation_count": exclamation_count,
        "question_count": question_count,
        "repeated_char_words": len(elongated_words),
        "rating_dissonance": rating_dissonance,
        "repeated_wording_flag": has_repeated_wording,
        "generic_wording_flag": is_generic,
        "movie_keyword_relevant": movie_relevant
    }
