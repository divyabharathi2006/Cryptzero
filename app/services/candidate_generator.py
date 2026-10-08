import itertools
import re
from pathlib import Path


def generate_wordlist_candidates(wordlist_path):
    if not wordlist_path or not Path(wordlist_path).exists():
        raise FileNotFoundError('Wordlist file not found.')
    candidates = []
    with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as fh:
        for line in fh:
            word = line.strip()
            if word:
                candidates.append(word)
    return candidates


def generate_mask_candidates(pattern, charset, minimum_length=1, maximum_length=8):
    if not pattern:
        return []
    char_map = {
        '#': charset.get('digits', '0123456789'),
        '?': charset.get('lowercase', 'abcdefghijklmnopqrstuvwxyz'),
        '@': charset.get('symbols', '!@#$%^&*'),
        'A': charset.get('uppercase', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
    }
    expanded = []
    for token in pattern:
        expanded.append(char_map.get(token, token))
    if len(expanded) == 1 and expanded[0] == pattern:
        return [pattern]

    results = []
    positions = []
    for i, ch in enumerate(pattern):
        if ch in char_map:
            positions.append(i)
    if not positions:
        return [pattern]

    for chars in itertools.product(*[char_map.get(pattern[i], pattern[i]) for i in range(len(pattern)) if pattern[i] in char_map]):
        candidate = list(pattern)
        for idx, value in zip([i for i in range(len(pattern)) if pattern[i] in char_map], chars):
            candidate[idx] = value
        results.append(''.join(candidate))
    return results


def generate_rule_based_candidates(base_words, years=None, custom_suffixes=None):
    outputs = []
    years = years or ['2024', '2025', '2026']
    custom_suffixes = custom_suffixes or ['!', '@', '1', '123']
    substitutions = {'a': '@', 'e': '3', 'i': '1', 'o': '0', 's': '$'}

    for word in base_words:
        tokens = [word, word.lower(), word.upper(), word.capitalize()]
        for token in list(tokens):
            outputs.append(token)
            outputs.append(token + '1')
            outputs.append(token + '123')
            for year in years:
                outputs.append(token + year)
                outputs.append(year + token)
            for suffix in custom_suffixes:
                outputs.append(token + suffix)
                outputs.append(suffix + token)
            transformed = ''.join(substitutions.get(ch.lower(), ch) for ch in token)
            if transformed != token:
                outputs.append(transformed)
    unique = []
    seen = set()
    for item in outputs:
        if item and item not in seen:
            unique.append(item)
            seen.add(item)
    return unique[:5000]
