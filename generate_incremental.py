"""
Word-level meter-constrained generation.

The idea (per the design): the LM proposes the next word; we keep only the words
that, appended to the line so far, keep the running vazn a valid PREFIX of the
target; a beam is accepted only when it fills the WHOLE vazn. Whole-line filtering
almost never hits the target by chance, so this per-word pruning is what actually
yields matches.

Core = `constrained_word_beam_search`, which is independent of any model: you pass a
`propose_fn(text, n) -> {word: weight}`. `HFWordProposer` is one such proposer built
on a Hugging Face causal LM; swap in an API/model of your choice.
"""

import math
from collections import namedtuple

from syllable import PersianSyllableGenerator

Beam = namedtuple("Beam", "words state score")

NEG_INF = float("-inf")


def _logaddexp(a, b):
    if a == NEG_INF:
        return b
    if b == NEG_INF:
        return a
    m = max(a, b)
    return m + math.log(math.exp(a - m) + math.exp(b - m))


def next_word_distribution(prefix_ids, step_fn, decode, *, on_word=None,
                           word_beam=16, max_tokens=6, min_word_prob=1e-4):
    """Marginalize the LM's *token* distribution into P(next word | context).

    The model gives a distribution over subword tokens, not words. This runs a
    small deterministic beam over tokens: it keeps extending until a token starts a
    NEW word, at which point the accumulated tokens form one candidate word whose
    probability is the sum over all token paths that spell it (log-add-exp). No
    sampling — the candidate set and its probabilities come straight from the
    distribution, so downstream scoring is a true line log-likelihood.

        step_fn(list_of_id_seqs) -> list of {token_id: token_log_prob}
            BATCHED: scores every current token-beam prefix in one call (one model
            forward per depth instead of one per beam node).
        decode(ids)  -> str                          # detokenize

    on_word: optional word -> payload. Applied when a candidate word is complete
        (the earliest point its phonemes are well-defined, since G2P needs a whole
        word). Return None to REJECT the word — this is where the vazn-prefix check
        lives, so only meter-valid next words survive. When given, the result maps
        word -> (probability, payload); otherwise word -> probability.

    Returns the surviving next words, truncated to the explored top tokens.
    """
    beams = [([], 0.0)]                      # (tokens_of_current_word, logprob)
    words = {}                               # word -> logprob (marginal)

    def emit(tokens, lp):
        w = decode(tokens).strip()
        if w:
            words[w] = _logaddexp(words.get(w, NEG_INF), lp)

    for _ in range(max_tokens):
        nxt = []
        dists = step_fn([prefix_ids + tokens for tokens, _ in beams])  # one batch
        for (tokens, lp), dist in zip(beams, dists):
            boundary_mass = 0.0             # P(next token starts a NEW word)
            for tid, tlp in dist.items():
                # A space-leading token is a boundary only if a word is in progress;
                # with no current word it is the START of this word, so extend.
                if tokens and decode([tid])[:1] in (" ", "\n", "\t"):
                    boundary_mass += math.exp(tlp)
                else:
                    nxt.append((tokens + [tid], lp + tlp))
            if tokens and boundary_mass > 0:  # word ends here, once, with its mass
                emit(tokens, lp + math.log(boundary_mass))
        if not nxt:
            break                            # every live beam already emitted
        beams = sorted(nxt, key=lambda b: b[1], reverse=True)[:word_beam]
    else:
        for tokens, lp in beams:             # words still mid-token at max_tokens
            emit(tokens, lp)

    result = {}
    for w, lp in words.items():
        p = math.exp(lp)
        if p < min_word_prob:
            continue
        if on_word is None:
            result[w] = p
        else:
            payload = on_word(w)             # vazn-prefix check happens here
            if payload is not None:          # keep only meter-valid next words
                result[w] = (p, payload)
    return result


def _seq_diff(a, b):
    """Fraction of word positions at which two lines differ (0 = identical)."""
    n = max(len(a), len(b))
    if n == 0:
        return 0.0
    same = sum(1 for i in range(n) if i < len(a) and i < len(b) and a[i] == b[i])
    return 1.0 - same / n


def _diverse_topk(beams, k, min_diff):
    """Greedy diverse selection: take the highest score, then repeatedly take the
    highest-scoring beam that differs by >= min_diff from EVERY beam already kept.
    Prevents the beam from collapsing onto k near-identical variants."""
    kept = []
    for b in sorted(beams, key=lambda x: x.score, reverse=True):
        if len(kept) >= k:
            break
        if all(_seq_diff(b.words, o.words) >= min_diff for o in kept):
            kept.append(b)
    return kept


def constrained_word_beam_search(
    propose_fn,
    generator,
    target,
    *,
    context="",
    beam_width=5,
    max_words=24,
    min_diff=0.3,
    verbose=False,
):
    """Grow a line word-by-word, pruning any word that breaks the target vazn.

    propose_fn(text, advance) -> {word: (prob, new_state)}: the next-word
        distribution, ALREADY filtered so only words that keep the vazn a valid
        prefix survive. `advance(word)` returns the new MeterState or None (reject).
    context: text used to condition the LM but NOT counted toward the meter.
    beam_width: number of live beams to carry forward each step.
    min_diff: diversity threshold (0..1). A kept beam must differ from every other
        kept beam by at least this fraction of its words.

    The search keeps expanding every UNFINISHED beam until it either fills the whole
    vazn (-> completed) or can no longer be extended (dies) — it does NOT stop at the
    first completed line. Selection favors diversity over raw score.

    Returns (completed, partial): completed lines that fill the whole vazn (best
    first), and the best still-open beams if nothing completed.
    """
    beams = [Beam([], generator.meter_state(target), 0.0)]
    completed = []

    def vazn_of(beam):
        pos = beam.state.positions()
        return target[:max(pos)] if pos else ""

    for step in range(max_words):
        scored, done_now = [], []
        for beam in beams:
            text = (context + " " + " ".join(beam.words)).strip()

            def advance(word, _state=beam.state):
                nxt = _state.advance_grapheme(word)
                return nxt if nxt.alive() else None   # None => breaks the vazn

            candidates = propose_fn(text, advance)
            for word, (prob, nxt) in candidates.items():
                nb = Beam(beam.words + [word], nxt,
                          beam.score + math.log(prob + 1e-9))
                (done_now if nxt.is_complete() else scored).append(nb)
        completed.extend(done_now)

        if verbose:
            top = sorted(scored + done_now, key=lambda b: b.score, reverse=True)[:10]
            print(f"\nstep {step+1}: {len(scored)} live, {len(done_now)} newly complete"
                  f" ({len(completed)} total) — 10 best options:")
            for rank, b in enumerate(top, 1):
                mark = "✓" if b.state.is_complete() else " "
                print(f"  {rank:2}. {mark} {b.score:7.2f} | {vazn_of(b):<{len(target)}} | "
                      f"{' '.join(b.words)}")

        # Continue until every beam is finished or dead (no early stop).
        if not scored:
            break
        beams = _diverse_topk(scored, beam_width, min_diff)

    # Rank completed lines by length-normalized score (fair across word counts).
    completed.sort(key=lambda b: b.score / max(len(b.words), 1), reverse=True)
    partial = sorted(beams, key=lambda b: b.score, reverse=True)
    to_lines = lambda bs: [(" ".join(b.words), b.score, len(b.words)) for b in bs]
    return to_lines(completed), to_lines(partial)


class HFWordProposer:
    """Turn a causal LM's next-token distribution into P(next word | context).

    Deterministic (no sampling): reads the top-`token_topk` tokens at each position
    and marginalizes them up to the next word boundary via `next_word_distribution`.
    Base LMs propose weak words; use a poetry-finetuned model for good candidates.
    """

    def __init__(self, model_name="ai-forever/mGPT-1.3B-persian", device="cpu",
                 token_topk=40, word_beam=16, max_tokens=6):
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, low_cpu_mem_usage=True).to(device).eval()
        self.device = device
        self.token_topk = token_topk
        self.word_beam = word_beam
        self.max_tokens = max_tokens
        self._decode_cache = {}
        # Special tokens (<|endoftext|>, pad, bos, ...) must never become part of a
        # word: they pollute G2P and fake meter matches. Mask them out of the dist.
        ids = [i for i in set(self.tokenizer.all_special_ids) if i is not None]
        self._special_ids = torch.tensor(sorted(ids)) if ids else None

    def _step(self, id_seqs):
        """Batched: score every prefix in one forward pass (right-padded)."""
        t = self.torch
        pad = self.tokenizer.pad_token_id or self.tokenizer.eos_token_id or 0
        bos = self.tokenizer.bos_token_id or self.tokenizer.eos_token_id or pad
        seqs = [s if s else [bos] for s in id_seqs]     # model needs >=1 token
        maxlen = max(len(s) for s in seqs)
        input_ids = t.full((len(seqs), maxlen), pad, dtype=t.long, device=self.device)
        attn = t.zeros((len(seqs), maxlen), dtype=t.long, device=self.device)
        for i, s in enumerate(seqs):
            input_ids[i, :len(s)] = t.tensor(s, device=self.device)
            attn[i, :len(s)] = 1
        with t.no_grad():
            logits = self.model(input_ids, attention_mask=attn).logits
        out = []
        for i, s in enumerate(seqs):
            logp = t.log_softmax(logits[i, len(s) - 1], dim=-1)   # last real token
            if self._special_ids is not None:
                logp[self._special_ids] = float("-inf")           # drop special tokens
            vals, idx = t.topk(logp, self.token_topk)
            out.append({int(j): float(v) for v, j in zip(vals, idx)})
        return out

    def _decode(self, ids):
        key = tuple(ids)
        if key not in self._decode_cache:
            self._decode_cache[key] = self.tokenizer.decode(ids, skip_special_tokens=True)
        return self._decode_cache[key]

    def __call__(self, text, advance):
        prefix_ids = self.tokenizer.encode(text)
        return next_word_distribution(
            prefix_ids, self._step, self._decode, on_word=advance,
            word_beam=self.word_beam, max_tokens=self.max_tokens)


if __name__ == "__main__":
    from ge2pe_g2p import GE2PEG2P
    from generate_rerank import METERS

    g2p = GE2PEG2P()
    generator = PersianSyllableGenerator(g2p)
    target = METERS["motaqareb"]              # فعولن فعولن فعولن فعل

    # ---- Prompt / context (edit freely) ----------------------------------
    # A base LM does not obey instructions — it CONTINUES text. So we frame the
    # theme as the *opening of a poem*: the model's natural continuation then stays
    # on-topic. (Meter is NOT taken from here; it is enforced programmatically.)
    context = (
        "موضوع: دوستی، وفاداری و مهر میان یاران.\n"
        "شعری کهن و زیبا در ستایش دوستی و یاری:\n"
    )

    proposer = HFWordProposer(token_topk=60, word_beam=24, max_tokens=6)

    # Focus: FIRST mesraʿ only, in the vazn of «بسی رنج بردم در این سال سی».
    print(f"Prompt fed to the model:\n{context}")
    print(f"Target vazn: {target}\n")
    completed, partial = constrained_word_beam_search(
        proposer, generator, target,
        context=context, beam_width=8, max_words=16, min_diff=0.3, verbose=True,
    )

    print("\n" + "=" * 60)
    print("Complete first-mesraʿ candidates matching the vazn (diverse, best first):")
    print("=" * 60)
    for line, score, nw in (completed or partial)[:10]:
        print(f"  ({score:6.1f}, {nw}w)  {line}")
    if not completed:
        print("  [none completed — showing best partial beams]")
