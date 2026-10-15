from syllable import PersianSyllableGenerator
from PersianG2p import Persian_g2p_converter

"""
Persian Poetry Generator with Metrical Constraints
Generates Persian verses that match specific poetic meters (وزن شعر)
"""

import torch
import re
from typing import List, Tuple, Callable, Optional
from dataclasses import dataclass


@dataclass
class BeamState:
    """Represents a beam in beam search"""
    tokens: List[int]
    score: float
    meter: List[str]
    text: str


# class PersianMeterAnalyzer:
#     """
#     Analyzes Persian text to extract metrical pattern.
#     Based on Persian prosody (عروض) rules.
#     """
    
#     # Persian vowels
#     SHORT_VOWELS = ['َ', 'ِ', 'ُ']  # Zabar, Zir, Pish
#     LONG_VOWELS = ['ا', 'و', 'ی', 'آ']
    
#     # Consonants that can form syllables
#     CONSONANTS = [
#         'ب', 'پ', 'ت', 'ث', 'ج', 'چ', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'ژ', 
#         'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ک', 'گ', 'ل', 
#         'م', 'ن', 'و', 'ه', 'ی'
#     ]
    
#     def __init__(self):
#         pass
    
#     def normalize_text(self, text: str) -> str:
#         """Normalize Persian text for meter analysis"""
#         # Remove non-Persian characters except spaces
#         text = re.sub(r'[^\u0600-\u06FF\s]', '', text)
#         # Normalize spaces
#         text = re.sub(r'\s+', ' ', text).strip()
#         return text
    
#     def extract_syllables(self, word: str) -> List[str]:
#         """
#         Extract syllables from a Persian word.
#         Returns list of syllable types: 'short', 'long', 'extended'
        
#         Rules:
#         - CV (consonant + short vowel) = short syllable
#         - CVV (consonant + long vowel) = long syllable  
#         - CVC (consonant + short vowel + consonant) = long syllable
#         - CVVC, CVCC = extended syllable
#         """
#         syllables = []
#         i = 0
#         chars = list(word)
        
#         while i < len(chars):
#             if chars[i] in self.CONSONANTS or chars[i] in [' ', '\u200c']:
#                 # Start of potential syllable
#                 syllable = chars[i]
#                 syllable_type = None
#                 i += 1
                
#                 # Check for vowel
#                 if i < len(chars):
#                     if chars[i] in self.SHORT_VOWELS:
#                         syllable += chars[i]
#                         i += 1
#                         # Check if followed by consonant (CVC = long)
#                         if i < len(chars) and chars[i] in self.CONSONANTS:
#                             syllable += chars[i]
#                             i += 1
#                             # Check for CVCC (extended)
#                             if i < len(chars) and chars[i] in self.CONSONANTS:
#                                 syllable_type = 'extended'
#                                 i += 1
#                             else:
#                                 syllable_type = 'long'
#                         else:
#                             syllable_type = 'short'
                    
#                     elif chars[i] in self.LONG_VOWELS:
#                         syllable += chars[i]
#                         i += 1
#                         # CVV = long, CVVC = extended
#                         if i < len(chars) and chars[i] in self.CONSONANTS:
#                             syllable_type = 'extended'
#                             i += 1
#                         else:
#                             syllable_type = 'long'
#                     else:
#                         # No vowel, might be at word boundary
#                         continue
                
#                 if syllable_type:
#                     syllables.append(syllable_type)
#             else:
#                 i += 1
        
#         return syllables
    
#     def get_meter(self, text: str) -> List[str]:
#         """
#         Get the metrical pattern for a Persian text.
#         Returns list like ['long', 'short', 'long', 'long', ...]
#         """
#         text = self.normalize_text(text)
#         if not text:
#             return []
        
#         words = text.split()
#         meter = []
        
#         for word in words:
#             syllables = self.extract_syllables(word)
#             meter.extend(syllables)
        
#         return meter
    
#     def get_meter_simple(self, text: str) -> List[str]:
#         """
#         Simplified meter extraction based on vowel patterns.
#         More robust for real Persian text without full diacritics.
#         """
#         text = self.normalize_text(text)
#         if not text:
#             return []
        
#         meter = []
#         i = 0
#         chars = list(text)
        
#         while i < len(chars):
#             if chars[i] in self.CONSONANTS:
#                 # Found consonant, look ahead for vowel pattern
#                 if i + 1 < len(chars):
#                     next_char = chars[i + 1]
                    
#                     if next_char in self.LONG_VOWELS:
#                         # Long vowel makes it at least 'long'
#                         if i + 2 < len(chars) and chars[i + 2] in self.CONSONANTS:
#                             meter.append('extended')
#                             i += 3
#                         else:
#                             meter.append('long')
#                             i += 2
                    
#                     elif next_char in self.CONSONANTS:
#                         # CC pattern - first consonant with implicit short vowel
#                         meter.append('short')
#                         i += 1
                    
#                     elif next_char == ' ':
#                         # Word boundary - assume short
#                         meter.append('short')
#                         i += 2
#                     else:
#                         i += 1
#                 else:
#                     meter.append('short')
#                     i += 1
#             else:
#                 i += 1
        
#         return meter


class PersianPoemGenerator:
    """
    Generates Persian poetry verses matching specific meters using
    constrained beam search.
    """
    
    def __init__(
        self,
        model,
        tokenizer,
        meter_analyzer: Optional[PersianSyllableGenerator] = None
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.meter_analyzer = meter_analyzer
        
        # Set model to eval mode
        self.model.eval()
    
    def is_prefix_match(
        self,
        current_meter: List[str],
        target_meter: List[str]
    ) -> bool:
        """Check if current meter is valid prefix of target"""
        if len(current_meter) > len(target_meter):
            return False
        return current_meter == target_meter[:len(current_meter)]
    
    def is_complete_match(
        self,
        current_meter: List[str],
        target_meter: List[str]
    ) -> bool:
        """Check if meter is complete"""
        return current_meter == target_meter
    
    def generate_verse(
        self,
        prompt: str,
        target_meter: List[str],
        beam_width: int = 5,
        max_length: int = 50,
        temperature: float = 1.0,
        top_p: float = 0.95,
        verbose: bool = False
    ) -> List[Tuple[str, float, List[str]]]:
        """
        Generate verse matching target meter using beam search.
        
        Args:
            prompt: Initial text prompt (e.g., theme/context)
            target_meter: List of syllable types ['long', 'short', ...]
            beam_width: Number of beams to maintain (k)
            max_length: Maximum number of tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling threshold
            verbose: Print debug information
            
        Returns:
            List of (text, score, meter) tuples for complete verses
        """
        # Encode prompt
        input_ids = self.tokenizer.encode(prompt, return_tensors='pt')[0].tolist()
        prompt_length = len(input_ids)
        
        # Initialize beams
        beams = [BeamState(
            tokens=input_ids,
            score=0.0,
            meter=[],
            text=prompt
        )]
        
        complete_verses = []
        
        for step in range(max_length):
            if verbose:
                print(f"\n--- Step {step + 1} ---")
            
            all_candidates = []
            
            for beam_idx, beam in enumerate(beams):
                if verbose:
                    print(f"Beam {beam_idx}: {beam.text[:50]}... | Meter: {beam.meter}")
                
                # Get model predictions
                with torch.no_grad():
                    input_tensor = torch.tensor([beam.tokens])
                    outputs = self.model(input_tensor)
                    next_token_logits = outputs.logits[0, -1, :]
                    
                    # Apply temperature
                    next_token_logits = next_token_logits / temperature
                    
                    # Get probabilities
                    probs = torch.softmax(next_token_logits, dim=-1)
                    
                    # Top-p (nucleus) sampling candidates
                    sorted_probs, sorted_indices = torch.sort(probs, descending=True)
                    cumsum_probs = torch.cumsum(sorted_probs, dim=-1)
                    
                    # Find cutoff for top-p
                    cutoff_idx = torch.where(cumsum_probs > top_p)[0]
                    if len(cutoff_idx) > 0:
                        cutoff_idx = cutoff_idx[0].item() + 1
                    else:
                        cutoff_idx = len(sorted_probs)
                    
                    # Get top candidates (up to 100 for efficiency)
                    num_candidates = min(cutoff_idx, 100)
                    top_probs = sorted_probs[:num_candidates]
                    top_tokens = sorted_indices[:num_candidates]
                
                # Try each candidate token
                valid_count = 0
                for prob, token_id in zip(top_probs, top_tokens):
                    token_id = token_id.item()
                    prob = prob.item()
                    
                    # Create new token sequence
                    new_tokens = beam.tokens + [token_id]
                    
                    # Decode only the generated part
                    new_text_full = self.tokenizer.decode(new_tokens)
                    generated_text = self.tokenizer.decode(new_tokens[prompt_length:])
                    
                    # Calculate meter for generated text only
                    try:
                        print(f"G step={step} b={beam_idx} p={prob}:")
                        all_sylabifications = self.meter_analyzer.get_syllabification(generated_text)
                        
                        print(f"G :")
                        for idx, syl in enumerate(all_sylabifications, 1):
                            formatted = generator.format_syllabification(syl)
                            print(f"{idx}. {formatted}")

                        new_meters = self.meter_analyzer.get_meter_simple_from_syllabifications(all_sylabifications)
                        print(f"G : {new_meters}")
                        # new_meters = self.meter_analyzer.get_meter_simple(generated_text)
                        for new_meter in new_meters:
                            
                            # Check if meter is valid prefix
                            if self.is_prefix_match(new_meter, target_meter):
                                new_score = beam.score + torch.log(torch.tensor(prob)).item()
                                
                                candidate = BeamState(
                                    tokens=new_tokens,
                                    score=new_score,
                                    meter=new_meter,
                                    text=new_text_full
                                )
                                
                                # Check if complete
                                if self.is_complete_match(new_meter, target_meter):
                                    # Check if this is a good stopping point
                                    decoded_token = self.tokenizer.decode([token_id])
                                    if decoded_token.strip() in ['', '.', '،', '\n'] or \
                                    token_id == self.tokenizer.eos_token_id:
                                        complete_verses.append(
                                            (generated_text, new_score, new_meter)
                                        )
                                        if verbose:
                                            print(f"  ✓ Complete verse found!")
                                else:
                                    all_candidates.append(candidate)
                                
                                valid_count += 1
                                break
                    except ValueError as e:
                        print(f"Value Error: {e} text={generated_text} full={new_text_full}")

                    if valid_count >= beam_width:
                        break
                
                if verbose:
                    print(f"  Found {valid_count} valid continuations")

            
            # If no valid candidates, stop
            if not all_candidates:
                if verbose:
                    print("No valid candidates found. Stopping.")
                break
            
            # Keep top-k beams by score
            beams = sorted(all_candidates, key=lambda x: x.score, reverse=True)[:beam_width]

            print(f"Beam after step={step} {beams}")
            
            # If we have enough complete verses, we can stop
            if len(complete_verses) >= beam_width:
                break
        
        # Return complete verses, sorted by score
        if complete_verses:
            return sorted(complete_verses, key=lambda x: x[1], reverse=True)
        else:
            # Return best incomplete beams
            return [(b.text[len(prompt):], b.score, b.meter) for b in beams]


# Example Persian meters (common patterns)
PERSIAN_METERS = {
    'ramal_short': ['long', 'short', 'short', 'long', 'short', 'short'],  # Simplified Ramal
    'hazaj_short': ['short', 'long', 'long', 'short', 'long', 'long'],  # Simplified Hazaj
    'custom_1': ['long', 'long', 'short', 'long'],  # Custom pattern
    'custom_2': ['short', 'long', 'short', 'long', 'long'],  # Custom pattern
}


# def demo_meter_analyzer():
#     """Demonstrate the meter analyzer"""
#     analyzer = PersianSyllableGenerator()
    
#     # Test sentences
#     test_texts = [
#         "سلام دوست",
#         "شب آمد",
#         "باد می آید",
#     ]
    
#     print("=== Meter Analysis Demo ===\n")
#     for text in test_texts:
#         meter = analyzer.get_meter_simple(text)
#         print(f"Text: {text}")
#         print(f"Meter: {meter}")
#         print()


if __name__ == "__main__":
    # Demo the meter analyzer
    # demo_meter_analyzer()
    
    # print("\n" + "="*60)
    # print("Persian Poem Generator with Meter Constraints")
    # print("="*60)
    # print("\nTo use this with a language model:")
    # print("1. Load your Persian LLM (GPT-2, ParsBERT, etc.)")
    # print("2. Create generator: gen = PersianPoemGenerator(model, tokenizer)")
    # print("3. Generate verse: verses = gen.generate_verse(")
    # print("       prompt='شب', ")
    # print("       target_meter=['long', 'short', 'long', 'long'],")
    # print("       beam_width=5")
    # print("   )")
    # print("\nExample meters available in PERSIAN_METERS dict:")
    # for name, pattern in PERSIAN_METERS.items():
    #     print(f"  - {name}: {pattern}")

    

    g2p = Persian_g2p_converter(use_large=True)
    generator = PersianSyllableGenerator(g2p)

    # sentence = "بسی رنج بردم در این سال سی"
    # phenome = g2p.transliterate(sentence, tidy=True, secret=True)

    # all_syllabifications = generator.generate_all_syllabifications(phenome)
    # print(f"Total syllabifications: {len(all_syllabifications)}\n")

    # for idx, syl in enumerate(all_syllabifications, 1):
    #     formatted = generator.format_syllabification(syl)
    #     print(f"{idx}. {formatted} {syl}")

    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch

    model_name = "ai-forever/mGPT-1.3B-persian"

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        dtype=torch.float16,   # or float32 if no FP16 support
        device_map="cpu",            # place model on CPU
        low_cpu_mem_usage=True
    )

    gen = PersianPoemGenerator(model, tokenizer, generator)
    verses = gen.generate_verse(
        prompt='شعری در قالب سنتی با سبک حافظ. واژگان مورد استفاده واژگان شعر حافظ باشد. صنایع ادبی را مشابه حافظ تولید کن.', 
        target_meter=['long', 'short', 'long', 'long'],
        beam_width=5
    )