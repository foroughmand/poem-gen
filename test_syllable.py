"""
Unit tests for PersianSyllableGenerator (GE2PE phoneme alphabet).

Phoneme strings are fed directly (GE2PE 'secret' romanization: long a/i/u,
short //e/o, @=glottal, $=š, ;=ž, c=č), so these run with no model install.
"""

from syllable import (
    PersianSyllableGenerator,
    SHORT_SYM as S,
    LONG_SYM as L,
    EXTENDED_SYM as E,
)

gen = PersianSyllableGenerator(g2p=None)


def word_type(word):
    syls = gen._word_syllabifications(word)[0]
    assert len(syls) == 1, f"{word!r} split into {len(syls)}: {syls}"
    return syls[0]['type']


def check(label, got, expected):
    ok = got == expected
    print(f"[{'ok ' if ok else 'FAIL'}] {label}: {got!r}" +
          ("" if ok else f"  (expected {expected!r})"))
    return ok


def main():
    passed = True

    # ---- single-syllable weights (کوتاه / بلند / کشیده) -------------------
    passed &= check("to  (تو) short",       word_type('to'),   'short')     # o short, open
    passed &= check("se  (سه) short",       word_type('se'),   'short')
    passed &= check("pa  (پا) long",        word_type('pa'),   'long')      # a long, open
    passed &= check("si  (سی) long",        word_type('si'),   'long')
    passed &= check("t/n (تَن) long",       word_type('t/n'),  'long')      # short + coda
    passed &= check("por (پُر) long",       word_type('por'),  'long')
    passed &= check("kur (کور) extended",   word_type('kur'),  'extended')  # long + coda
    passed &= check("sar (سار) extended",   word_type('sar'),  'extended')
    passed &= check("d/st(دَست) extended",  word_type('d/st'), 'extended')  # short + 2 coda
    passed &= check("ab  (آب) extended",    word_type('ab'),   'extended')

    # ---- GE2PE alphabet basics: / short vs a long, glottal handling -------
    passed &= check("'/' is short",  gen.is_short_vowel('/'), True)
    passed &= check("'a' is long",   gen.is_long_vowel('a'),  True)
    passed &= check("'@' is consonant", gen.is_consonant('@'), True)
    passed &= check("key (کِی) long", word_type('key'), 'long')             # e + coda y
    # word-initial glottal elides in the meter path (@in -> in)
    passed &= check("@in tag drops leading glottal",
                    [u for u, _ in gen._tag_word('@in')], ['i', 'n'])

    # ---- symbol conversion ----------------------------------------------
    passed &= check("kešide symbol = long+short", E, L + S)
    passed &= check("word_symbol_options('pa')", gen.word_symbol_options('pa'), {L})
    passed &= check("word_symbol_options('to') flexible (rule 4)",
                    gen.word_symbol_options('to'), {S, L})

    # ---- consonant-stealing (rule 1) gives >1 syllabification -------------
    passed &= check("'d/rama' has multiple syllabifications",
                    len(gen._word_syllabifications('d/rama')) > 1, True)

    # ---- cross-word liaison + full-line scan (motaqāreb) -----------------
    line = "b/si r/nj bord/m d/r @in sal si"        # بسی رنج بردم در این سال سی
    target = (S + L + L) * 3 + (S + L)              # فعولن فعولن فعولن فعل
    print("\nScansions (with liaison) for:", line)
    print("   target:", target)
    for sc in gen.scan_line(line):
        print(f"   {sc}{'  <-- matches' if sc == target else ''}")
    passed &= check("motaqāreb line matches", gen.line_matches(line, target), True)

    # ---- incremental word-by-word matching (generation primitive) --------
    print("\nIncremental build (prune per word):")
    st = gen.meter_state(target)
    for w in line.split():
        st = st.advance(w)
        print(f"   + {w:7} -> alive={st.alive()}  positions={st.positions()}")
        passed &= check(f"   alive after '{w}'", st.alive(), True)
    passed &= check("full line is_complete", st.is_complete(), True)

    print("\n" + ("ALL PASSED" if passed else "SOME TESTS FAILED"))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
