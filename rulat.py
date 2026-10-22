"""RuLat romanization of Russian text, see misc/rulat_table.png."""
import re
import sys

LETTERS = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'jo',
    'ж': 'x', 'з': 'z', 'и': 'i', 'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'c', 'ш': 'w', 'щ': 'wc', 'ъ': 'q',
    'ы': 'y', 'ь': 'q', 'э': 'eq', 'ю': 'ju', 'я': 'ja',
}

# Soft hyphens and combining marks (stress) inside a word don't split it: при­мер, Ру́сский
JOINERS = '­̀-ͯ'
WORD = re.compile(f'[а-яёА-ЯЁ](?:[{JOINERS}]*[а-яёА-ЯЁ])*')
# Latin words are not romanized, they only give context for all-caps:
# already romanized text (in the userscript) or words like API
CONTEXT_WORD = re.compile(f'{WORD.pattern}|[a-zA-Z](?:[{JOINERS}]*[a-zA-Z])*')
# The last vowel of a romanized letter, where its stress mark goes
STRESSED_VOWEL = re.compile('[aeiouy][̀-ͯ]*(?=[^aeiouy]*$)', re.IGNORECASE)


def _romanize_word(word, caps):
    out = []
    for c in word:
        latin = LETTERS.get(c.lower())
        if latin is None:
            # A stress mark goes on the vowel: Э́ -> Éq, not Eq́
            vowel = STRESSED_VOWEL.search(out[-1]) if out and '̀' <= c <= 'ͯ' else None
            if vowel:
                out[-1] = out[-1][:vowel.end()] + c + out[-1][vowel.end():]
            else:
                out.append(c)
            continue
        if caps:
            latin = latin.upper()
        elif c.isupper():
            latin = latin.capitalize()
        out.append(latin)
    return ''.join(out)


def _letter_count(word):
    return sum(c.isalpha() for c in word)


def _nearest_caps(words, indices):
    """For each word, whether the nearest longer word before it (in the order
    of indices) is all-caps: True/False, or None if there is no such word."""
    result = [None] * len(words)
    last = None
    for i in indices:
        result[i] = last
        if _letter_count(words[i]) > 1:
            last = words[i].isupper()
    return result


def transliterate_parts(parts):
    """Transliterate pieces of one paragraph (e.g. its text split by <b>, <i>
    tags) together, so all-caps is decided across the whole paragraph."""
    words = [w for part in parts for w in CONTEXT_WORD.findall(part)]
    caps = [_letter_count(w) > 1 and w.isupper() for w in words]
    # A single capital letter (Я) is all-caps only if the nearest longer words
    # around it are: Я ЗНАЮ -> JA ZNAJU, but Я знаю -> Ja znaju
    before = _nearest_caps(words, range(len(words)))
    after = _nearest_caps(words, reversed(range(len(words))))
    for i, w in enumerate(words):
        if _letter_count(w) == 1 and w.isupper():
            sides = [s for s in (before[i], after[i]) if s is not None]
            caps[i] = bool(sides) and all(sides)
    cyrillic_caps = iter([c for w, c in zip(words, caps) if WORD.fullmatch(w)])
    return [
        WORD.sub(lambda m: _romanize_word(m.group(), next(cyrillic_caps)), part)
        for part in parts
    ]


def transliterate(text):
    return transliterate_parts([text])[0]


if __name__ == '__main__':
    text = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read()
    print(transliterate(text))
