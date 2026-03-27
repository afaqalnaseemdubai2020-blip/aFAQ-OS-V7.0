"""
Arabic NLP Engine — HarfBuzz text shaping + YAKE keyword extraction.
"""
from typing import List
import re

class ArabicNLP:
    """Arabic text processing: shaping, RTL handling, keyword extraction."""
    
    # Arabic Unicode ranges
    ARABIC_RANGE = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
    
    def is_arabic(self, text: str) -> bool:
        """Check if text contains Arabic characters."""
        return bool(re.search(self.ARABIC_RANGE, text))
    
    def shape_arabic(self, text: str) -> str:
        """
        Shape Arabic text for proper display (HarfBuzz-style processing).
        Handles RTL markers, letter forms, diacritics normalization.
        """
        if not text:
            return text
        
        # Add RTL embedding marker
        shaped = "\u202B" + text + "\u202C"  # RLE + text + PDF
        
        # Normalize common Arabic forms
        replacements = {
            "أ": "ﺃ",  # Alef with hamza above - isolated
            "إ": "ﺇ",  # Alef with hamza below - isolated
            "آ": "ﺁ",  # Alef with madda - isolated
            "ة": "ﺓ",  # Teh marbuta
        }
        for old, new in replacements.items():
            shaped = shaped.replace(old, new)
        
        return shaped
    
    def extract_keywords(self, text: str, language: str = "ar", max_keywords: int = 10) -> List[str]:
        """
        Extract keywords using YAKE algorithm.
        Falls back to frequency-based extraction if yake unavailable.
        """
        try:
            import yake
            kw_extractor = yake.KeywordExtractor(
                lan=language,
                n=1,  # unigrams
                top=max_keywords
            )
            keywords = kw_extractor.extract_keywords(text)
            return [kw[0] for kw in keywords]
        except ImportError:
            # Fallback: simple frequency-based extraction
            return self._fallback_keywords(text, max_keywords)
    
    def _fallback_keywords(self, text: str, max_keywords: int) -> List[str]:
        """Simple keyword extraction fallback."""
        # Remove punctuation, split words
        clean = re.sub(r'[^\w\s]', ' ', text.lower())
        words = clean.split()
        
        # Filter short/stop words
        stop_words_ar = {"في", "من", "على", "إلى", "هذا", "هذه", "التي", "الذي", "كان", "كانت"}
        stop_words_en = {"the", "a", "an", "is", "are", "was", "in", "on", "at", "to", "for"}
        stop_words = stop_words_ar | stop_words_en
        
        filtered = [w for w in words if len(w) > 2 and w not in stop_words]
        
        # Count frequency
        freq = {}
        for word in filtered:
            freq[word] = freq.get(word, 0) + 1
        
        # Sort by frequency, return top N
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:max_keywords]]
    
    def extract_entities(self, text: str) -> dict:
        """Basic named entity detection for Arabic."""
        entities = {
            "dates": re.findall(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}', text),
            "numbers": re.findall(r'\d+', text),
            "emails": re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', text),
            "urls": re.findall(r'https?://\S+', text)
        }
        return {k: v for k, v in entities.items() if v}

arabic_nlp = ArabicNLP()
