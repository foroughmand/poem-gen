"""
Persian metrical poetry via generate-then-rerank.

Replaces the per-subword-token constrained beam search in test10.py, which was both
too slow (a neural G2P call inside the innermost decoding loop) and linguistically
unsound (meter is undefined on partial BPE tokens). Here we instead:

    1. GENERATE many *complete* candidate lines with any language model.
    2. G2P + syllabify each finished line exactly ONCE.
    3. KEEP the lines whose scansion matches the target meter (with poet's freedoms
       and cross-word liaison handled by PersianSyllableGenerator).

The meter checker (syllable.py) is fully decoupled from the generator, so you can
swap mGPT for a stronger/instruction-tuned model, an API model, or a human list.
"""

from syllable import PersianSyllableGenerator, SHORT_SYM as S, LONG_SYM as L

# Common feet (ارکان عروضی) as –/ᴗ, so meters read like the textbooks.
FEET = {
    'faʿūlun':   S + L + L,   # فعولن   ᴗ – –
    'faʿūl':     S + L,       # فعل     ᴗ –
    'fāʿilun':   L + S + L,   # فاعلن   – ᴗ –
    'fāʿilātun': L + S + L + L,  # فاعلاتن – ᴗ – –
    'mafāʿīlun': S + L + L + L,  # مفاعیلن ᴗ – – –
    'mustafʿilun': L + L + S + L,  # مستفعلن – – ᴗ –
}


def feet_to_target(*feet):
    """Build a –/ᴗ target string from foot names, e.g. feet_to_target('faʿūlun'*3)."""
    return ''.join(FEET[f] if f in FEET else f for f in feet)


# A few ready-made hemistich meters.
METERS = {
    # motaqāreb mosamman maqsur: فعولن فعولن فعولن فعل  (Shahnameh)
    'motaqareb': feet_to_target('faʿūlun', 'faʿūlun', 'faʿūlun', 'faʿūl'),
    # ramal mosamman maqsur: فاعلاتن فاعلاتن فاعلاتن فاعلن
    'ramal': feet_to_target('fāʿilātun', 'fāʿilātun', 'fāʿilātun', 'fāʿilun'),
    # hazaj mosamman salim: مفاعیلن مفاعیلن مفاعیلن مفاعیلن
    'hazaj': feet_to_target('mafāʿīlun', 'mafāʿīlun', 'mafāʿīlun', 'mafāʿīlun'),
}


class MeterFilter:
    """Checks whether a Persian line (grapheme) can be read in a target meter."""

    def __init__(self, g2p, target):
        self.gen = PersianSyllableGenerator(g2p)
        self.target = target

    def matches(self, line):
        try:
            return self.gen.text_matches(line, self.target)
        except (ValueError, RuntimeError):
            return False

    def scansions(self, line):
        """Debug helper: the –/ᴗ readings the checker sees for a line."""
        try:
            return self.gen.get_meter_symbols(line)
        except (ValueError, RuntimeError):
            return []


def rerank(candidates, meter_filter, score_fn=None, limit=None):
    """Keep candidate lines that fit the meter, best first.

    candidates: iterable of full Persian lines (strings).
    meter_filter: a MeterFilter.
    score_fn: optional line -> float (higher = better), e.g. a fluency / LM score.
              Defaults to preferring shorter, de-duplicated lines.
    """
    seen, kept = set(), []
    for line in candidates:
        line = line.strip()
        if not line or line in seen:
            continue
        seen.add(line)
        if meter_filter.matches(line):
            kept.append(line)
    if score_fn is None:
        score_fn = lambda s: -len(s)
    kept.sort(key=score_fn, reverse=True)
    return kept[:limit] if limit else kept


# ---------------------------------------------------------------------------
# Example candidate generator (Hugging Face causal LM). Optional / heavy — only
# imported when you actually run generation.
# ---------------------------------------------------------------------------
class HFLineSampler:
    """Sample complete candidate lines from a causal LM (e.g. mGPT-persian).

    Note: base LMs do not follow instructions well; prefer an instruction-tuned or
    a poetry-finetuned model, and/or seed `prompt` with the opening of a real line.
    """

    def __init__(self, model_name="ai-forever/mGPT-1.3B-persian", device="cpu"):
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, low_cpu_mem_usage=True).to(device).eval()
        self.device = device

    def generate(self, prompt, n=64, max_new_tokens=24, temperature=1.0, top_p=0.95):
        import re
        enc = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        with self.torch.no_grad():
            out = self.model.generate(
                **enc, do_sample=True, num_return_sequences=n,
                max_new_tokens=max_new_tokens, temperature=temperature, top_p=top_p,
                pad_token_id=self.tokenizer.eos_token_id)
        lines = []
        for seq in out:
            text = self.tokenizer.decode(seq[enc["input_ids"].shape[1]:],
                                         skip_special_tokens=True)
            # Take the first line/clause as the candidate hemistich.
            text = re.split(r"[\n.،؛!؟]", text)[0].strip()
            if text:
                lines.append(text)
        return lines


if __name__ == "__main__":
    from ge2pe_g2p import GE2PEG2P

    g2p = GE2PEG2P()
    target = METERS['motaqareb']
    print(f"Target meter (motaqāreb): {target}\n")

    mf = MeterFilter(g2p, target)

    # 1) Sanity check the filter on a known-good line (should match).
    good = "بسی رنج بردم در این سال سی"
    print(f"{good}\n  -> matches: {mf.matches(good)}")
    print(f"  -> scansions seen: {mf.scansions(good)[:5]} ...\n")

    # 2) Generate candidates and keep only the ones that fit the meter.
    sampler = HFLineSampler()
    prompt = "بسی رنج بردم در این سال سی\n"   # seed with a real opening line
    candidates = sampler.generate(prompt, n=100, max_new_tokens=20)
    print(f"Generated {len(candidates)} candidates; filtering by meter...\n")

    winners = rerank(candidates, mf, limit=10)
    print(f"{len(winners)} matched the target meter:")
    for i, line in enumerate(winners, 1):
        print(f"  {i}. {line}")
