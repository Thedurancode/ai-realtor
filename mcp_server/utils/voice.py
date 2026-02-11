"""Voice normalization utilities for MCP tools."""
import re


def normalize_voice_query(query: str) -> list[str]:
    """Normalize voice input for better matching - returns list of variations."""
    # 1. Remove filler words
    fillers = ['um', 'uh', 'like', 'you know', 'so', 'well', 'the contract for',
               'contracts for', 'the property at', 'the property on', 'the property',
               'property at', 'property on', 'show me', 'check', 'list',
               'get', 'find', 'please', 'can you', 'could you', 'would you',
               'the one on', 'the one at', 'the house on', 'the house at',
               'details for', 'info for', 'info on', 'about the', 'about']
    query_clean = query.lower()
    for filler in fillers:
        query_clean = query_clean.replace(filler, ' ')
    query_clean = ' '.join(query_clean.split())

    # 2. Convert written numbers to digits
    number_words = {
        'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
        'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
        'eleven': '11', 'twelve': '12', 'twenty': '20', 'thirty': '30',
        'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
        'eighty': '80', 'ninety': '90', 'hundred': '100'
    }
    for word, digit in number_words.items():
        query_clean = re.sub(r'\b' + word + r'\b', digit, query_clean)

    # Handle "one forty one" -> "141"
    query_clean = re.sub(r'\b(\d+)\s+(\d+)\s+(\d+)\b', r'\1\2\3', query_clean)
    query_clean = re.sub(r'\b(\d+)\s+(\d+)\b', r'\1\2', query_clean)

    # 3. Expand abbreviations
    abbreviations = {
        r'\bst\b': 'street', r'\bave\b': 'avenue', r'\bblvd\b': 'boulevard',
        r'\bdr\b': 'drive', r'\brd\b': 'road', r'\bln\b': 'lane',
        r'\bct\b': 'court', r'\bpl\b': 'place', r'\bapt\b': 'apartment',
    }
    for abbr, full in abbreviations.items():
        query_clean = re.sub(abbr, full, query_clean)

    # 4. Generate phonetic variations
    variations = [query_clean]
    phonetic_map = {
        'throop': ['troop', 'throup', 'trupe', 'troup'],
        'street': ['strait', 'streat'],
        'avenue': ['avenu', 'av'],
    }

    for correct, alternates in phonetic_map.items():
        if correct in query_clean:
            for alt in alternates:
                variations.append(query_clean.replace(correct, alt))
        for alt in alternates:
            if alt in query_clean:
                variations.append(query_clean.replace(alt, correct))

    return variations
