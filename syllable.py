"""
Persian Syllable Generator
Generates all possible syllabifications from phoneme strings based on Persian syllable structure rules.
Implements poet's freedoms (āzādihā-ye sarāyande) for multiple valid syllabifications.
"""

# قواعد وزن
# منبع: http://www.sorud.info/
# ساختارِ هجا در زبانِ پارسی
# هر هجا (syllable) تنها یک واکه (مصوّت - vowel) دارد، و شمارِ هجاهایِ هر گفته‌ای برابر با شمارِ واکه‌هایش است.
# در زبانِ پارسیِ امروزی، هجا می‌تواند گذشته از هسته‌اش (syllable nucleus) که همان واکه است، دارایِ یک همخوان (صامت - consonant) به عنوانِ آغازه (syllable onset) و یک تا دو همخوان به عنوانِ پایانه (syllable coda) باشد.
# پس هجاها یکی از شش بافتِ زیر را دارند:
# واکه: او
# واکه + یک همخوان: آب
# واکه + دو همخوان: اسب
# همخوان + واکه: پا
# همخوان + واکه + یک همخوان: مور
# همخوان + واکه + دو همخوان: شَست
# گویشِ معیارِ زبانِ پارسی در ایران شش واکه می‌شناسد: سه واکه‌یِ کوتاهِ اَ، اِ، اُ و سه واکه‌یِ بلندِ آ، ای و او.
# پیش از همخوانِ «ن» در درونِ هجا، همه‌یِ واکه ها کوتاه می‌شوند (بر پایه‌یِ چندآواییِ ترکیبی - combinative variation).
# استثنا: واژه‌یِ زینهار
# در چامه‌سنجی زبانِ پارسی با سه گونه هجا رو به رو هستیم:
# هجایِ کوتاه:
# هجاهایی که واکه‌ای کوتاه دارند و دارایِ پایانه نباشند، مانندِ واژه‌هایِ تو و سه
# هجایِ بلند:
# هجاهایی که واکه‌ای کوتاه و پایانه‌ای تک‌همخوان داشته باشند، مانندِ واژه‌هایِ تَن و پُر
# هجاهایی که واکه‌ای بلند دارند و دارایِ پایانه نباشند، مانندِ واژه‌هایِ پا و سی
# هجایِ کشیده:
# هجاهایی که واکه‌ای بلند و پایانه‌ای تک‌همخوان داشته باشند، مانندِ واژه‌هایِ کور و سار
# هجاهایی که پایانه‌شان دو همخوان داشته باشد، مانندٍ واژه‌هایِ دَست و پوست
# آزادی‌هایِ سراینده در هجاپردازی:
# اگرهجایی با واکه‌ای آغاز شود (آغازه نداشته باشد)، می‌تواند همخوانِ پیش از خود را بدزدد و آغازه‌یِ خود سازد.
# اگر واکه‌یِ «ای» درست در پایانِ هجا و درست پیش از واکه‌ای دیگر جای بگیرد، هجایش می‌تواند کوتاه یا بلند باشد.
# اگر واکه‌یِ «او» درست در پایانِ هجا و درست پیش از واکه‌ای دیگر یا پیش از همخوانِ «ی» جای بگیرد، هجایش می‌تواند کوتاه یا بلند باشد. (دوستی بردش سوی خانه‌ی خراب، آهو استاد و نگه کرد و رمید)
# تکواژهایِ زیر به پاسِ پیشینه‌شان در پارسیِ میانه می‌توانند هم هجایِ کوتاه و هم هجایِ بلند بسازند (= اشباع):
# میانجیِ «ـِـ» (کسره‌یِ اضافه)
# میانجیِ «و» (حرفِ ربط conjunction در همپایگیِ زنجیره‌ای copulative coordination)
# میانجی‌ها و ضمیرهایِ پرسشیِ که، چه و چون
# تکواژهایی که به واکه‌یِ «ـه» پایان بیابند (به پاسِ پسوندِ «ـَک» در پارسیِ میانه)
# ضمیرِ شخصیِ «تو»
# شماره‌یِ «دو»
# آهنگ (وزن):
# آهنگِ هر چامه‌یِ پارسی از تکرارِ یک بافتِ هجایی (از 3 تا 9 هجا) فراهم می آید. این بافت را گام (رکن) می‌نامند، که دو تا چهار بار در آهنگ پشتِ سر هم جای می‌گیرد.
# گامِ پایانیِ آهنگ می‌تواند شکسته باشد (یک یا چند هجا از پایانش افتاده باشد.)
# در هر گام تنها هجاهایِ کوتاه و بلند به چشم می‌خورند.
# آهنگِ چامه همیشه به هجایی بلند پایان می‌پذیرد. پس اگر گامِ پایانیِ آهنگ شکسته باشد، هجایِ پایانی‌اش ادایِ بلند به خود می‌گیرد.
# اگر آهنگ تنها دو گام داشته باشد (که شکسته نباشند)، آن آهنگ را دوپاره می نامیم (= وزنِ دوری). آهنگ‌هایِ دیگر تنها یک پاره دارند.
# استثنا: گام‌هایِ هشت‌هجایی که به زنجیره هجایِ «کوتاه - بلند - بلند» پایان بیابند. (مژه‌یِ سیاهت ار کرد به خونِ ما اشارت، گرت چو نوحِ نبي صبر هست در غمِ طوفان)
# آزادی‌هایِ سراینده در آهنگ‌پردازی:
# هر پاره در چامه می‌تواند از چهره‌یِ دگرگون شده‌ای از آهنگِ چامه برخوردار باشد، که چامه‌سرا از راه هایِ زیر به دست می‌آورد:
#
# در پایانِ پاره می‌توان به جایِ هجایِ بلند، هجایی کشیده نشاند.
# به جایِ زنجیره‌یِ «هجایِ بلند - هجایِ کوتاه» می تواند یک هجایِ کشیده نشاند.
# زنحیره‌یِ «کوتاه - کوتاه - بلند - بلند» را می‌توان در آغازِ پاره به «بلند - کوتاه - بلند - بلند» دگرگون کرد.
# زنحیره‌یِ «کوتاه - کوتاه» را می‌توان به «بلند» دگرگون کرد، اگر گامش 3 هجایی باشد، یا در آغازِ پاره نباشد.
# در برخی از آهنگ‌ها می‌توان زنجیره‌یِ «بلند - کوتاه - کوتاه - بلند» را به «کوتاه - بلند - کوتاه - بلند» دگرگون کرد.

# منبع بعدی: https://prosody.ir/

from itertools import product

# Scansion symbols (کوتاه / بلند / کشیده)
SHORT_SYM = 'ᴗ'
LONG_SYM = '–'
# A "kešide" (extended) syllable occupies two metrical positions: long + short.
EXTENDED_SYM = LONG_SYM + SHORT_SYM

TYPE_TO_SYMBOL = {
    'short': SHORT_SYM,
    'long': LONG_SYM,
    'extended': EXTENDED_SYM,
    'invalid': '?',
}


class PersianSyllableGenerator:
    def __init__(self, g2p=None):
        # Phoneme alphabet = GE2PE / Homo-GE2PE 'secret' output.
        #   long vowels : a (ā), i, u        short vowels: / (a/æ), e, o
        #   consonants  : incl. @ (glottal stop / hamze-ayn), $ (š), ; (ž), c (č),
        #                 x (x), q (ق/غ merged).
        # Diphthongs are emitted as vowel+consonant (ey -> e+y) or collapse to a
        # monophthong (ow -> o/u), so no multi-character vowel units are needed.
        self.short_vowels = ['/', 'e', 'o']
        self.long_vowels = ['a', 'i', 'u']
        self.all_vowels = self.short_vowels + self.long_vowels
        self._vowel_tokens = sorted(self.all_vowels, key=len, reverse=True)

        # Define consonants
        self.consonants = [
            'b', 'p', 't', 'd', 'k', 'g', 'q', 'c', ';', '$', '@', 'f', 'v',
            's', 'z', 'x', 'j', 'h', 'm', 'n', 'l', 'r', 'y', 'w', "'"
        ]

        # Special morphemes for rule 4 (eshbā') that may count short OR long.
        self.special_morphemes = {
            'e': True,          # ezāfe (kasre-ye ezāfe)
            'o': True, 'va': True, 'v/': True,   # conjunction 'o' / 'va'
            'ke': True, 'ce': True, 'con': True,  # question words ke, če, čon
            'to': True,         # pronoun 'to' (you)
            'do': True,         # number 'do' (two)
        }

        self.g2p = g2p
        self._g2p_cache = {}

    # ------------------------------------------------------------------ helpers
    def is_vowel(self, char):
        return char in self.all_vowels

    def is_consonant(self, char):
        return char in self.consonants

    def is_long_vowel(self, char):
        return char in self.long_vowels

    def is_short_vowel(self, char):
        return char in self.short_vowels

    def ends_with_e(self, word):
        return word.endswith('e') or word.endswith('eh')

    def is_special_morpheme(self, word):
        """Whole-word eshbā' morphemes (ke, o, to, do, ...) that may be short or long."""
        return word.lower() in self.special_morphemes

    def _tokenize_phonemes(self, word):
        """Split a phoneme string into a list of known phoneme units.

        Multi-character vowels (if any) are matched first; unknown characters
        (digits, punctuation, Latin left by a bad g2p) are dropped so junk cannot
        masquerade as consonants.
        """
        s = word.lower().replace('-', '').replace('_', '')
        units = []
        i = 0
        while i < len(s):
            if s[i].isspace():
                i += 1
                continue
            match = None
            for tok in self._vowel_tokens:
                if len(tok) > 1 and s.startswith(tok, i):
                    match = tok
                    break
            if match:
                units.append(match)
                i += len(match)
            elif s[i] in self.all_vowels or s[i] in self.consonants:
                units.append(s[i])
                i += 1
            else:
                i += 1                     # drop unknown character
        return units

    def get_syllable_structure(self, syllable):
        """Structure pattern: C = consonant, v = short vowel, V = long vowel."""
        structure = ''
        for unit in self._tokenize_phonemes(syllable):
            if self.is_consonant(unit):
                structure += 'C'
            elif self.is_short_vowel(unit):
                structure += 'v'
            elif self.is_long_vowel(unit):
                structure += 'V'
        return structure

    def _classify(self, nucleus, coda, word=''):
        """Weight of a syllable from its nucleus + coda units: short/long/extended."""
        coda_len = len(coda)

        # Exception: زینهار (zinhār) - 'i' before 'n' stays long.
        is_zinhaar = (word.lower() in ('zinhār', 'zinhâr') and
                      self.is_long_vowel(nucleus) and coda and coda[0] == 'n')
        # Rule: before 'n' inside a syllable, vowels shorten (except زینهار).
        if coda and coda[0] == 'n' and not is_zinhaar:
            is_short = True
        else:
            is_short = self.is_short_vowel(nucleus)

        if is_short and coda_len == 0:
            return 'short'
        if (is_short and coda_len == 1) or (not is_short and coda_len == 0):
            return 'long'
        if coda_len >= 1:  # long+coda, or any 2+ coda
            return 'extended'
        return 'invalid'

    def get_syllable_type(self, syllable, word=''):
        """Determine syllable type: 'short', 'long', 'extended', or 'invalid'."""
        units = self._tokenize_phonemes(syllable)
        nucleus_idx = next((i for i, u in enumerate(units) if self.is_vowel(u)), -1)
        if nucleus_idx == -1:
            return ('invalid', '')
        nucleus = units[nucleus_idx]
        coda = units[nucleus_idx + 1:]
        return (self._classify(nucleus, coda, word), self.get_syllable_structure(syllable))

    # ------------------------------------------------------- core syllabifier
    def _word_syllabifications(self, word):
        """All rule-1 (consonant-stealing) syllabifications of a single word.

        A single intervocalic consonant may be the coda of the left syllable or the
        onset of the right one; longer clusters split every valid way with onset<=1,
        coda<=2. Each returned item is a list of syllable dicts.
        """
        units = self._tokenize_phonemes(word)
        nuclei = [i for i, u in enumerate(units) if self.is_vowel(u)]
        if not nuclei:
            raise ValueError(f"No vowel found in word '{word}' (units={units})")

        leading = units[:nuclei[0]]                      # onset of first syllable
        trailing = units[nuclei[-1] + 1:]                # coda of last syllable
        gaps = [units[nuclei[j] + 1:nuclei[j + 1]] for j in range(len(nuclei) - 1)]

        # For each intervocalic gap, enumerate how many consonants become the
        # onset of the following syllable (0 or 1), with the remainder (<=2) the
        # coda of the preceding syllable.
        gap_onset_options = []
        for gap in gaps:
            L = len(gap)
            opts = [o for o in (0, 1) if 0 <= o <= L and (L - o) <= 2]
            if not opts:
                raise ValueError(f"Unsyllabifiable cluster in '{word}' (gap len {L})")
            gap_onset_options.append(opts)

        results = []
        for choice in product(*gap_onset_options) if gap_onset_options else [()]:
            syllables = []
            for j in range(len(nuclei)):
                onset = leading if j == 0 else gaps[j - 1][len(gaps[j - 1]) - choice[j - 1]:]
                nucleus = [units[nuclei[j]]]
                if j < len(nuclei) - 1:
                    coda = gaps[j][:len(gaps[j]) - choice[j]]
                else:
                    coda = trailing
                text = ''.join(onset + nucleus + coda)
                syl_type, structure = self.get_syllable_type(text, word)
                syllables.append({
                    'syllable': text,
                    'type': syl_type,
                    'structure': structure,
                    'word': word,
                })
            results.append(syllables)

        # Deduplicate structurally-identical splits.
        unique, seen = [], set()
        for syls in results:
            key = tuple((s['syllable'], s['type']) for s in syls)
            if key not in seen:
                seen.add(key)
                unique.append(syls)
        return unique

    def generate_all_syllabifications(self, phoneme_string):
        """All syllabification combinations for a sentence (cartesian over words).

        NOTE: the number of combinations grows multiplicatively with sentence
        length. For meter *matching* prefer `line_matches` / `word_symbol_options`,
        which never materialize the full product.
        """
        words = phoneme_string.lower().split()
        all_word_options = [self._word_syllabifications(w) for w in words]
        return self._generate_combinations(all_word_options)

    def _generate_combinations(self, word_options_list):
        if not word_options_list:
            return [[]]
        result = []
        first, rest = word_options_list[0], self._generate_combinations(word_options_list[1:])
        for opt in first:
            for combo in rest:
                result.append([opt] + combo)
        return result

    # -------------------------------------------------- poet's freedoms (2-4)
    def _flexible_indices(self, syllables, word):
        """Indices of syllables whose weight may flip (rules 2, 3, 4)."""
        flexible = set()
        for i, syl in enumerate(syllables):
            text = syl['syllable']
            nxt = syllables[i + 1]['syllable'] if i + 1 < len(syllables) else ''
            # Rule 2: 'ey' at syllable end, right before another vowel.
            if text.endswith('ey') and nxt and self.is_vowel(self._tokenize_phonemes(nxt)[0]):
                flexible.add(i)
            # Rule 3: 'ow'/'ou' at end before a vowel or 'y'.
            if (text.endswith('ow') or text.endswith('ou')) and nxt:
                head = self._tokenize_phonemes(nxt)[0]
                if self.is_vowel(head) or head == 'y':
                    flexible.add(i)
        # Rule 4 (eshbā'): whole-word morphemes, or words ending in '-e' — only the
        # LAST syllable is flexible, not the whole word.
        if syllables and (self.is_special_morpheme(word) or self.ends_with_e(word)):
            flexible.add(len(syllables) - 1)
        return flexible

    def word_symbol_options(self, word):
        """Set of possible –/ᴗ scansion strings for a single word."""
        options = set()
        for syls in self._word_syllabifications(word):
            flex = self._flexible_indices(syls, word)
            per_syl = []
            for i, syl in enumerate(syls):
                base = TYPE_TO_SYMBOL.get(syl['type'], '?')
                if i in flex and syl['type'] in ('short', 'long'):
                    per_syl.append({SHORT_SYM, LONG_SYM})
                else:
                    per_syl.append({base})
            for combo in product(*per_syl):
                options.add(''.join(combo))
        return options

    # ------------------------------------------------ cross-word (liaison) scan
    # Persian scansion syllabifies the *continuous* phonetic stream: a word-final
    # consonant may become the onset of a following vowel (e.g. dær in -> dæ-rin), so
    # syllabification crosses word boundaries. We work on "tagged units": each
    # phoneme unit paired with a flag marking whether, as a nucleus, it may flip
    # weight under the eshbā' freedom (rule 4). Rules 2/3 (ey/ow/ou) are detected
    # from the unit text at transition time, so they also work across boundaries.

    def _tag_word(self, word):
        """Tokenize one word into [(unit, flex_flag), ...]."""
        units = self._tokenize_phonemes(word)
        # Elide a word-initial glottal stop before a vowel (@in -> in): in aruz the
        # word-initial hamze drops, letting the previous consonant link (liaison).
        if len(units) >= 2 and units[0] == '@' and self.is_vowel(units[1]):
            units = units[1:]
        vowel_idx = [i for i, u in enumerate(units) if self.is_vowel(u)]
        last = vowel_idx[-1] if vowel_idx else None
        eshba_word = self.is_special_morpheme(word)
        ends_e = self.ends_with_e(word)
        tagged = []
        for i, u in enumerate(units):
            flex = self.is_vowel(u) and (eshba_word or (i == last and ends_e))
            tagged.append((u, flex))
        return tagged

    def _tag_line(self, phoneme_string):
        tagged = []
        for wi, w in enumerate(phoneme_string.lower().split()):
            for u, f in self._tag_word(w):
                tagged.append((u, f, wi))          # (unit, flex_flag, word_index)
        return tagged

    def _transitions(self, tagged, i):
        """From syllable-start index `i`, yield (next_index, symbol, is_final).

        A syllable is: optional 1 onset consonant + 1 vowel + 0..2 coda consonants.
        Coda length follows MAXIMAL ONSET within a word (a single consonant before
        the next vowel is that syllable's onset, not this one's coda). The split is
        only free at a word boundary whose next syllable is vowel-initial — the
        consonant-stealing / liaison license (dar in -> da-rin).
        """
        n = len(tagged)
        if i >= n:
            return
        onset = 1 if self.is_consonant(tagged[i][0]) else 0
        nv = i + onset
        if nv >= n or not self.is_vowel(tagged[nv][0]):
            return
        nucleus, flex = tagged[nv][0], tagged[nv][1]
        # consonants between this nucleus and the next vowel
        j = nv + 1
        while j < n and self.is_consonant(tagged[j][0]):
            j += 1
        num_cons = j - (nv + 1)
        if num_cons == 0:
            coda_opts = (0,)
        elif j >= n:
            coda_opts = (min(num_cons, 2),)                      # trailing cluster -> coda
        elif tagged[j - 1][2] == tagged[j][2]:
            coda_opts = (min(num_cons - 1, 2),)                  # last cons = next onset
        else:                                                    # word boundary: liaison choice
            coda_opts = tuple(sorted({min(num_cons - 1, 2), min(num_cons, 2)}))
        for k in coda_opts:
            next_i = nv + 1 + k
            coda = [tagged[nv + 1 + x][0] for x in range(k)]
            base = self._classify(nucleus, coda)
            diph = False
            if k == 0 and next_i < n:                       # rules 2, 3
                head = tagged[next_i][0]
                if nucleus == 'ey' and self.is_vowel(head):
                    diph = True
                elif nucleus in ('ow', 'ou') and (self.is_vowel(head) or head == 'y'):
                    diph = True
            if (flex or diph) and base in ('short', 'long'):
                symbols = (SHORT_SYM, LONG_SYM)
            else:
                symbols = (TYPE_TO_SYMBOL.get(base, '?'),)
            for sym in symbols:
                yield next_i, sym, (next_i == n)

    def line_matches(self, phoneme_string, target):
        """True if the continuous phoneme line can scan as `target` (a –/ᴗ string).

        DP over (stream index, target index); never materializes the exponential set
        of syllabifications. The final metrical position may read long even when the
        syllable is short (آهنگ همیشه به هجای بلند پایان می‌پذیرد).
        """
        tagged = self._tag_line(phoneme_string)
        n, T = len(tagged), len(target)
        seen, stack = {(0, 0)}, [(0, 0)]
        while stack:
            i, t = stack.pop()
            if i == n:
                if t == T:
                    return True
                continue
            for next_i, sym, is_final in self._transitions(tagged, i):
                variants = {sym}
                if is_final and sym.endswith(SHORT_SYM):
                    variants.add(sym[:-1] + LONG_SYM)   # line-final long freedom
                for v in variants:
                    nt = t + len(v)
                    if nt <= T and target[t:nt] == v and (next_i, nt) not in seen:
                        seen.add((next_i, nt))
                        stack.append((next_i, nt))
        return False

    def scan_line(self, phoneme_string, max_results=64):
        """All distinct –/ᴗ scansions of a continuous phoneme line (for inspection)."""
        tagged = self._tag_line(phoneme_string)
        n = len(tagged)
        results = set()

        def rec(i, acc):
            if len(results) >= max_results:
                return
            if i == n:
                results.add(acc)
                return
            for next_i, sym, _ in self._transitions(tagged, i):
                rec(next_i, acc + sym)

        rec(0, '')
        return sorted(results)

    def meter_state(self, target):
        """A fresh incremental MeterState for building a line word-by-word."""
        return MeterState(self, target, frozenset({((), 0)}))

    # -------------------------------------------------- g2p-backed convenience
    def _run_g2p(self, text):
        if self.g2p is None:
            raise RuntimeError("No g2p engine configured on PersianSyllableGenerator")
        if text in self._g2p_cache:            # candidate words repeat across beams
            return self._g2p_cache[text]
        # PersianG2p exposes .transliterate(); support a plain callable too.
        if hasattr(self.g2p, 'transliterate'):
            out = self.g2p.transliterate(text, tidy=True, secret=True)
        else:
            out = self.g2p(text)
        self._g2p_cache[text] = out
        return out

    def get_syllabification(self, text):
        return self.generate_all_syllabifications(self._run_g2p(text))

    def get_meter_simple(self, text):
        return self.get_meter_simple_from_syllabifications(self.get_syllabification(text))

    def get_meter_simple_from_syllabifications(self, all_syllabifications):
        return [[syl['type'] for word_syls in s for syl in word_syls]
                for s in all_syllabifications]

    def get_meter_symbols(self, text):
        """All distinct –/ᴗ scansions of a Persian text (via g2p, with liaison)."""
        return self.scan_line(self._run_g2p(text))

    def text_matches(self, text, target):
        """True if the Persian `text` (grapheme) can scan as `target` (–/ᴗ)."""
        return self.line_matches(self._run_g2p(text), target)

    # -------------------------------------------------------------- formatting
    def format_syllabification(self, syllabification):
        parts = []
        for word_syls in syllabification:
            word_parts = [f"{s['syllable']}[{s['structure']}]({s['type']})" for s in word_syls]
            parts.append(' + '.join(word_parts))
        return ' // '.join(parts)

    def format_all_syllabifications(self, all_syllabifications):
        return [self.format_syllabification(s) for s in all_syllabifications]


class MeterState:
    """Incremental meter matcher for word-by-word (constrained) generation.

    This is the primitive for pruning during generation: after each new word you
    call `advance(word_phonemes)` and check `alive()`. If it's dead, the line-so-far
    can no longer be completed to the target meter, so prune that branch immediately
    — no need to wait for a full line and search its (exponentially many) readings.

    A state carries, per surviving reading, `(leftover, t)`:
      * leftover — tagged units already consumed from the text but not yet closed
        into a finished syllable (they may still grab a coda/onset from the NEXT
        word — this is how liaison is preserved across word boundaries);
      * t        — how many metrical positions of `target` are matched so far.
    """

    __slots__ = ('gen', 'target', 'frontier', 'word_count')

    def __init__(self, gen, target, frontier, word_count=0):
        self.gen = gen
        self.target = target
        self.frontier = frontier            # frozenset of (leftover_tuple, t)
        self.word_count = word_count        # words advanced so far = next word index

    def _completable(self, leftover):
        # Leftover starts at a syllable boundary, so any consonants before its
        # first vowel must all fit the next syllable's onset (<=1). More than one
        # leading consonant can never be syllabified (e.g. [...d, s, a...] where d
        # and s would both need to be onsets), so such a branch is truly dead.
        if len(leftover) > 6:
            return False
        units = [u for u, _f, _o in leftover]
        first_vowel = next((i for i, u in enumerate(units) if self.gen.is_vowel(u)), None)
        if first_vowel is None:
            return len(units) <= 1               # all-consonant tail: <=1 future onset
        if first_vowel > 1:
            return False                          # >1 onset consonant is impossible
        return sum(1 for u in units if self.gen.is_vowel(u)) <= 1

    def advance(self, word_phonemes):
        """Return a new MeterState after appending one word (phoneme string)."""
        T = len(self.target)
        wi = self.word_count
        add = tuple((u, f, wi) for u, f in self.gen._tag_word(word_phonemes))
        if not add:      # non-lexical word (empty phonemes) -> reject this branch
            return MeterState(self.gen, self.target, frozenset(), self.word_count + 1)
        new = set()
        for leftover, t in self.frontier:
            units = list(leftover) + list(add)
            seen, stack = set(), [(0, t)]
            while stack:
                i, tc = stack.pop()
                if (i, tc) in seen:
                    continue
                seen.add((i, tc))
                rem = tuple(units[i:])
                if tc <= T and self._completable(rem):
                    new.add((rem, tc))                    # stop: rem awaits next word
                for next_i, sym, _ in self.gen._transitions(units, i):
                    nt = tc + len(sym)
                    if nt <= T and self.target[tc:nt] == sym:
                        stack.append((next_i, nt))         # close one more syllable
        return MeterState(self.gen, self.target, frozenset(new), self.word_count + 1)

    def advance_grapheme(self, word):
        """Convenience: g2p a single Persian word, then advance."""
        return self.advance(self.gen._run_g2p(word))

    def alive(self):
        """False once no reading can still reach the target — prune the branch."""
        return bool(self.frontier)

    def is_complete(self):
        """True if some reading exactly fills `target` with nothing left pending.

        Honors the line-final freedom: the last syllable may read long. A reading
        that ends one position short with a single unfinished short syllable also
        counts as complete.
        """
        T = len(self.target)
        for leftover, t in self.frontier:
            if t == T and not leftover:
                return True
            # final-syllable-long: an open final short syllable may be read long.
            if not leftover and t == T:
                return True
        # Try to close any pending final syllable exactly at T (with final-long).
        for leftover, t in self.frontier:
            if not leftover:
                continue
            for next_i, sym, is_final in self.gen._transitions(list(leftover), 0):
                if next_i != len(leftover):
                    continue
                for v in ({sym, sym[:-1] + LONG_SYM} if sym.endswith(SHORT_SYM) else {sym}):
                    if t + len(v) == T:
                        return True
        return False

    def positions(self):
        """The set of metrical-position counts currently reachable (for debugging)."""
        return sorted({t for _, t in self.frontier})


# Example usage
if __name__ == "__main__":
    from PersianG2p import Persian_g2p_converter
    g2p = Persian_g2p_converter(use_large=True)
    generator = PersianSyllableGenerator(g2p)

    print("=" * 80)
    print("Persian Syllable Generator - All Possible Syllabifications")
    print("Implements Poet's Freedoms (āzādihā-ye sarāyande)")
    print("=" * 80)

    test_cases = [
        ("mæn ketāb mixānæm", "I read a book"),
        ("beāmæd", "he came (vowel-initial can steal 'b')"),
        ("ke āmæd", "who came (with 'ke' flexibility)"),
        ("do doxtær", "two girls (with 'do' flexibility)"),
        ("xāne-ye man", "my house (with ezāfe flexibility)"),
        ("man o to", "me and you (with 'o' flexibility)"),
        ("dærāmæd", "income (vowel can steal 'r')"),
    ]

    for sentence, meaning in test_cases:
        print(f"\nInput: {sentence}\nMeaning: {meaning}")
        print("-" * 80)
        try:
            all_syllabifications = generator.generate_all_syllabifications(sentence)
            print(f"Total syllabifications: {len(all_syllabifications)}\n")
            for idx, syl in enumerate(all_syllabifications, 1):
                print(f"{idx}. {generator.format_syllabification(syl)}")
            print("Scansions (with liaison):", ' | '.join(generator.scan_line(sentence)))
        except ValueError as e:
            print(f"Error: {e}")
        print("=" * 80)

    print("\nLegend: C=consonant  v=short vowel  V=long vowel")
    print(f"        {SHORT_SYM}=short(کوتاه)  {LONG_SYM}=long(بلند)  {EXTENDED_SYM}=extended(کشیده)")
