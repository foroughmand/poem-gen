"""
Adapter exposing the local GE2PE / Homo-GE2PE model as a drop-in g2p for
PersianSyllableGenerator (and check_meter / generators).

GE2PE produces a much cleaner phoneme stream than PersianG2p (no spurious/dropped
vowels), which the meter analyzer depends on. Its alphabet:
    long vowels : a (ā), i, u        short: / (a), e, o
    consonants  : b p t d k g q c(č) ;(ž) $(š) @(glottal) f v s z x j h m n l r y w
"""


class GE2PEG2P:
    def __init__(self, model_path="homo-ge2pe", use_rules=True, gpu=False):
        from GE2PE import GE2PE
        self.model = GE2PE(model_path=model_path, GPU=gpu)
        self.use_rules = use_rules

    def __call__(self, text):
        text = (text or "").strip()
        if not text:
            return ""
        try:
            out = self.model.generate([text], use_rules=self.use_rules)
        except Exception:
            # e.g. a token that normalizes to empty (punctuation/number/Latin)
            return ""
        return out[0].strip() if out else ""

    # Drop-in compatibility with code that calls .transliterate(...).
    def transliterate(self, text, tidy=True, secret=True):
        return self.__call__(text)
