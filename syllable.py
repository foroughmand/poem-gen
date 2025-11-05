"""
Persian Syllable Generator
Generates all possible syllabifications from phoneme strings based on Persian syllable structure rules.
Implements poet's freedoms (āzādihā-ye sarāyande) for multiple valid syllabifications.
"""

class PersianSyllableGenerator:
    def __init__(self, g2p):
        # Define vowels
        self.short_vowels = ['a', 'e', 'o', 'æ']
        self.long_vowels = ['ā', 'i', 'u', 'ey', 'ou', 'ow', 'â', 'î', 'û']
        self.all_vowels = self.short_vowels + self.long_vowels
        
        # Define consonants
        self.consonants = [
            'b', 'p', 't', 'd', 'k', 'g', 'q', 'č', 'j', 'f', 'v', 
            's', 'z', 'š', 'ž', 'x', 'ğ', 'h', 'm', 'n', 'l', 'r', 'y', 'w', '`'
        ]
        
        # Special morphemes for rule 4 (eshbā')
        self.special_morphemes = {
            'e': True,  # ezāfe (kasre-ye ezāfe)
            'o': True,  # conjunction 'o' (va)
            'ke': True, 'če': True, 'čon': True,  # question words
            'to': True,  # pronoun 'to' (you)
            'do': True,  # number 'do' (two)
        }

        self.g2p = g2p
    
    def is_vowel(self, char):
        """Check if character is a vowel"""
        return char in self.all_vowels
    
    def is_consonant(self, char):
        """Check if character is a consonant"""
        return char in self.consonants
    
    def is_long_vowel(self, char):
        """Check if character is a long vowel"""
        return char in self.long_vowels
    
    def is_short_vowel(self, char):
        """Check if character is a short vowel"""
        return char in self.short_vowels
    
    def ends_with_e(self, word):
        """Check if word ends with 'e' sound (for rule 4)"""
        return word.endswith('e') or word.endswith('eh')
    
    def is_special_morpheme(self, word):
        """Check if word is a special morpheme that can be short or long (rule 4)"""
        word_lower = word.lower()
        # Check direct matches
        if word_lower in self.special_morphemes:
            return True
        # Check if ends with 'e' (rule 4)
        if self.ends_with_e(word_lower):
            return True
        return False
    
    def get_syllable_structure(self, syllable):
        """
        Get the syllable structure pattern (e.g., 'Cv', 'CVC', 'V', etc.)
        C = consonant, v = short vowel, V = long vowel
        """
        structure = ''
        for char in syllable:
            if self.is_consonant(char):
                structure += 'C'
            elif self.is_short_vowel(char):
                structure += 'v'
            elif self.is_long_vowel(char):
                structure += 'V'
        return structure
    
    def get_syllable_type(self, syllable, word='', allow_flexible=False):
        """
        Determine syllable type: short, long, or extended
        
        Args:
            syllable: The syllable string
            word: The original word (for context)
            allow_flexible: If True, allows flexible length for special cases (rules 2-4)
        
        Returns:
            tuple: (type, structure) or list of tuples if flexible
        """
        # Find the vowel (nucleus)
        vowel_idx = -1
        nucleus = ''
        
        for i, char in enumerate(syllable):
            if self.is_vowel(char):
                vowel_idx = i
                nucleus = char
                break
        
        if vowel_idx == -1:
            return [('invalid', '')]
        
        # Extract parts
        onset = syllable[:vowel_idx]
        coda = syllable[vowel_idx + 1:]
        
        # Exception: زینهار (zinhār) - 'i' before 'n' stays long
        is_zinhaar_exception = (word.lower() in ['zinhār', 'zinhâr'] and 
                                nucleus in self.long_vowels and 
                                coda.startswith('n'))
        
        # Rule: Before 'n' in coda, all vowels become short (except زینهار)
        if coda.startswith('n') and len(coda) >= 1 and not is_zinhaar_exception:
            is_short = True
        else:
            is_short = self.is_short_vowel(nucleus)
        
        structure = self.get_syllable_structure(syllable)
        
        # Determine syllable length
        base_type = None
        if is_short and len(coda) == 0:
            base_type = 'short'
        elif (is_short and len(coda) == 1) or (not is_short and len(coda) == 0):
            base_type = 'long'
        elif (not is_short and len(coda) == 1) or len(coda) == 2:
            base_type = 'extended'
        else:
            base_type = 'invalid'
        
        # Check if flexibility applies (rule 4 - eshbā')
        if allow_flexible and self.is_special_morpheme(word):
            # Can be both short and long
            if base_type == 'short':
                return [('short', structure), ('long', structure)]
            elif base_type == 'long':
                return [('short', structure), ('long', structure)]
        
        return [(base_type, structure)]
    
    def generate_all_syllabifications(self, phoneme_string):
        """
        Generate all possible syllabifications for a sentence.
        
        Args:
            phoneme_string: String of phonemes with words separated by spaces
            
        Returns:
            List of all valid syllabification combinations
        """
        words = phoneme_string.lower().split()
        
        # Get all possible syllabifications for each word
        all_word_options = []
        for word in words:
            word_syllabifications = self._get_all_word_syllabifications(word)
            all_word_options.append(word_syllabifications)
        
        # Generate all combinations 
        # TODO: It needs to consider between-word combinations and rules.
        return self._generate_combinations(all_word_options)
    
    def _generate_combinations(self, word_options_list):
        """Generate all combinations of word syllabifications"""
        if not word_options_list:
            return [[]]
        
        if len(word_options_list) == 1:
            return [[opt] for opt in word_options_list[0]]
        
        result = []
        first_word_options = word_options_list[0]
        rest_combinations = self._generate_combinations(word_options_list[1:])
        
        for first_option in first_word_options:
            for rest_combo in rest_combinations:
                result.append([first_option] + rest_combo)
        
        return result
    
    def _get_all_word_syllabifications(self, word):
        """
        Get all possible syllabifications for a single word.
        Implements rules 1-4 for poet's freedoms.
        """
        syllabifications = []
        
        # Get basic syllabification
        basic = self._syllabify_word_basic(word)
        syllabifications.append(basic)
        
        # Rule 1: Syllables starting with vowel can steal preceding consonant
        phonemes = word.replace('-', '')
        vowel_positions = self._find_vowel_positions(phonemes)
        
        # Try stealing for each vowel position (except the first one)
        for vowel_idx in range(1, len(vowel_positions)):
            vowel_pos = vowel_positions[vowel_idx]
            
            # Check if this vowel position can steal
            # It must have a consonant immediately before it
            if vowel_pos > 0 and self.is_consonant(phonemes[vowel_pos - 1]):
                # Also check that the consonant is not already an onset
                # (i.e., there's a vowel before the consonant)
                if vowel_pos >= 2 and self.is_vowel(phonemes[vowel_pos - 2]):
                    # This consonant is currently a coda, so it can be stolen
                    alt_syllabification = self._syllabify_with_steal(word, vowel_idx)
                    if alt_syllabification and alt_syllabification != basic:
                        syllabifications.append(alt_syllabification)
        
        # Rules 2-4: Apply flexible length rules to all versions
        flexible_syllabifications = []
        for syl_list in syllabifications:
            flexible_versions = self._apply_flexible_rules(syl_list, word)
            flexible_syllabifications.extend(flexible_versions)
        
        # Remove duplicates
        unique = []
        seen = set()
        for syl_list in flexible_syllabifications:
            key = tuple((s['syllable'], s['type'], s['structure']) for s in syl_list)
            if key not in seen:
                seen.add(key)
                unique.append(syl_list)
        
        return unique if unique else [basic]
    
    def _apply_flexible_rules(self, syl_list, word):
        """
        Apply rules 2-4 to create flexible length versions.
        """
        results = [syl_list]
        
        # Check each syllable for flexibility
        for i, syl in enumerate(syl_list):
            syllable_text = syl['syllable']
            
            # Rule 2: 'ey' at end before another vowel
            if syllable_text.endswith('ey') and i < len(syl_list) - 1:
                next_syl = syl_list[i + 1]
                if next_syl['syllable'] and self.is_vowel(next_syl['syllable'][0]):
                    # Create version where this is short
                    alt_list = syl_list.copy()
                    alt_syl = syl.copy()
                    alt_syl['type'] = 'short' if syl['type'] == 'long' else 'long'
                    alt_list[i] = alt_syl
                    results.append(alt_list)
            
            # Rule 3: 'ow'/'ou' at end before vowel or 'y'
            if (syllable_text.endswith('ow') or syllable_text.endswith('ou')) and i < len(syl_list) - 1:
                next_syl = syl_list[i + 1]
                if next_syl['syllable']:
                    first_char = next_syl['syllable'][0]
                    if self.is_vowel(first_char) or first_char == 'y':
                        alt_list = syl_list.copy()
                        alt_syl = syl.copy()
                        alt_syl['type'] = 'short' if syl['type'] == 'long' else 'long'
                        alt_list[i] = alt_syl
                        results.append(alt_list)
            
            # Rule 4: Special morphemes can be short or long
            if self.is_special_morpheme(word):
                alt_list = syl_list.copy()
                alt_syl = syl.copy()
                if syl['type'] == 'short':
                    alt_syl['type'] = 'long'
                elif syl['type'] == 'long':
                    alt_syl['type'] = 'short'
                alt_list[i] = alt_syl
                results.append(alt_list)
        
        return results
    
    def _find_vowel_positions(self, phonemes):
        """Find positions of all vowels in phoneme string"""
        positions = []
        for i, char in enumerate(phonemes):
            if self.is_vowel(char):
                positions.append(i)
        return positions
    
    def _syllabify_with_steal(self, word, steal_at_vowel_index):
        """
        Create syllabification where vowel at given index steals preceding consonant.
        
        Args:
            word: The word to syllabify
            steal_at_vowel_index: Index of vowel that should steal preceding consonant
        """
        phonemes = word.replace('-', '')
        vowel_positions = self._find_vowel_positions(phonemes)
        
        if steal_at_vowel_index >= len(vowel_positions) or steal_at_vowel_index == 0:
            return None
        
        vowel_pos = vowel_positions[steal_at_vowel_index]
        
        # Check if there's a consonant immediately before this vowel
        if vowel_pos == 0 or not self.is_consonant(phonemes[vowel_pos - 1]):
            return None
        
        # Build syllables with stealing rule
        syllables = []
        i = 0
        current_vowel_idx = 0
        
        while i < len(phonemes):
            syllable = ''
            
            # Onset: 0 or 1 consonant
            # Special case: if this is the stealing vowel, force taking the consonant
            if i < len(phonemes) and self.is_vowel(phonemes[i]):
                if current_vowel_idx == steal_at_vowel_index and i > 0 and self.is_consonant(phonemes[i - 1]):
                    # This vowel steals - but we already passed the consonant
                    # This means we need to remove it from previous syllable
                    if syllables and syllables[-1]['syllable']:
                        prev_syl = syllables[-1]['syllable']
                        if prev_syl and self.is_consonant(prev_syl[-1]):
                            # Remove last consonant from previous syllable
                            syllables[-1]['syllable'] = prev_syl[:-1]
                            # Update previous syllable's type and structure
                            if syllables[-1]['syllable']:
                                syl_types = self.get_syllable_type(syllables[-1]['syllable'], word)
                                syllables[-1]['type'] = syl_types[0][0]
                                syllables[-1]['structure'] = syl_types[0][1]
                            else:
                                # Previous syllable became empty, remove it
                                syllables.pop()
                            # Add stolen consonant to current syllable
                            syllable = prev_syl[-1]
            elif i < len(phonemes) and self.is_consonant(phonemes[i]):
                syllable += phonemes[i]
                i += 1
            
            # Nucleus: exactly 1 vowel (required)
            if i < len(phonemes) and self.is_vowel(phonemes[i]):
                syllable += phonemes[i]
                current_vowel_idx += 1
                i += 1
            else:
                if syllable:  # We have a consonant but no vowel - invalid
                    return None
                break
            
            # Coda: 0, 1, or 2 consonants  
            coda_count = 0
            # Special: don't take consonant if next vowel will steal it
            while i < len(phonemes) and self.is_consonant(phonemes[i]) and coda_count < 2:
                # Check if next position is the stealing vowel
                if (i + 1 < len(phonemes) and 
                    self.is_vowel(phonemes[i + 1]) and 
                    current_vowel_idx == steal_at_vowel_index):
                    # Don't take this consonant, let next syllable steal it
                    break
                syllable += phonemes[i]
                i += 1
                coda_count += 1
            
            if syllable:
                syl_types = self.get_syllable_type(syllable, word)
                syl_type, syl_structure = syl_types[0]
                syllables.append({
                    'syllable': syllable,
                    'type': syl_type,
                    'structure': syl_structure,
                    'word': word
                })
        
        return syllables if syllables else None
    
    def _syllabify_word_basic(self, word):
        """Basic syllabification without stealing"""
        phonemes = word.replace('-', '')
        syllables = []
        i = 0
        
        while i < len(phonemes):
            syllable = ''
            
            # Onset: 0 or 1 consonant
            if i < len(phonemes) and self.is_consonant(phonemes[i]):
                syllable += phonemes[i]
                i += 1
            
            # Nucleus: exactly 1 vowel (required)
            if i < len(phonemes) and self.is_vowel(phonemes[i]):
                syllable += phonemes[i]
                i += 1
            else:
                raise ValueError(f"Error: Invalid syllable structure in word '{word}' at position {i}")
            
            # Coda: 0, 1, or 2 consonants
            coda_count = 0
            while i < len(phonemes) and self.is_consonant(phonemes[i]) and coda_count < 2:
                syllable += phonemes[i]
                i += 1
                coda_count += 1
            
            syl_types = self.get_syllable_type(syllable, word)
            syl_type, syl_structure = syl_types[0]
            syllables.append({
                'syllable': syllable,
                'type': syl_type,
                'structure': syl_structure,
                'word': word
            })
        
        return syllables
    
    def get_meter_simple(self, text):
        all_syllabifications = self.generate_all_syllabifications(self.g2p(text, tidy=True, secret=True))
        return [[syl['type'] for word_syls in syllabification for syl in word_syls ] for syllabification in all_syllabifications]

    def get_syllabification(self, text):
        return self.generate_all_syllabifications(self.g2p(text, tidy=True, secret=True))

    def get_meter_simple_from_syllabifications(self, all_syllabifications):
        return [[syl['type'] for word_syls in syllabification for syl in word_syls ] for syllabification in all_syllabifications]

    
    def format_syllabification(self, syllabification):
        """Format a single syllabification"""
        parts = []
        for word_syls in syllabification:
            word_parts = []
            for syl in word_syls:
                word_parts.append(f"{syl['syllable']}[{syl['structure']}]({syl['type']})")
            parts.append(' + '.join(word_parts))
        return ' // '.join(parts)
    
    def format_all_syllabifications(self, all_syllabifications):
        """Format all syllabifications"""
        return [self.format_syllabification(syl) for syl in all_syllabifications]


# Example usage
if __name__ == "__main__":
    
    from PersianG2p import Persian_g2p_converter
    g2p = Persian_g2p_converter(use_large=True)
    generator = PersianSyllableGenerator(g2p)

    
    print("=" * 80)
    print("Persian Syllable Generator - All Possible Syllabifications")
    print("Implements Poet's Freedoms (āzādihā-ye sarāyande)")
    print("=" * 80)
    
    # Test sentences
    test_cases = [
        ("mæn ketāb mixānæm", "I read a book"),
        ("beāmæd", "he came (vowel-initial can steal 'b')"),
        ("ke āmæd", "who came (with 'ke' flexibility)"),
        ("do doxtær", "two girls (with 'do' flexibility)"),
        ("xāne-ye man", "my house (with ezāfe flexibility)"),
        ("man o to", "me and you (with 'o' flexibility)"),
        ("dærāmæd", "income (vowel can steal 'r')"),
    ]
    
    # Add g2p examples if available
    g2p_cases = [
        (g2p.transliterate("یاس", tidy=True, secret=True), "یاس"),
        (g2p.transliterate(" یاس ", tidy=True, secret=True), " یاس "),
        (g2p.transliterate("چه", tidy=True, secret=True), " چه "),
        (g2p.transliterate("بسی رنج بردم در این سال سی", tidy=True, secret=True), "بسی رنج بردم در این سال سی"),
        (g2p.transliterate("عجم زنده کردم بدین پارسی", tidy=True, secret=True), "عجم زنده کردم بدین پارسی (Ajam)"),
    ]
    test_cases.extend(g2p_cases)
    
    for sentence, meaning in test_cases:
        print(f"\nInput: {sentence}")
        print(f"Meaning: {meaning}")
        print("-" * 80)
        
        try:
            all_syllabifications = generator.generate_all_syllabifications(sentence)
            print(f"Total syllabifications: {len(all_syllabifications)}\n")
            
            for idx, syl in enumerate(all_syllabifications, 1):
                formatted = generator.format_syllabification(syl)
                print(f"{idx}. {formatted}")
        
        except ValueError as e:
            print(f"Error: {e}")
        
        print("=" * 80)
    
    print("\n=== Usage Example ===")
    print("all_syls = generator.generate_all_syllabifications('mæn ketāb mixānæm')")
    print("for syl in all_syls:")
    print("    print(generator.format_syllabification(syl))")
    
    print("\n" + "=" * 80)
    print("Legend:")
    print("  C = consonant, v = short vowel, V = long vowel")
    print("  Types: short, long, extended")
    print("  // = word boundary, + = syllable boundary within word")
    print("=" * 80)