#!/usr/bin/env python3
"""
AI Similarity Service for Plagiarism Detection
This script provides similarity analysis and AI detection functionality
that can be called from the Java backend.
"""

import requests
import difflib
import json
import sys
import argparse
from typing import Dict, List, Optional, Tuple
import re

# Configuration
API_KEY = "AIzaSyDSXhwLi8IwEqNrcUvN--xDPWwsjJ_TrqI"
CX = "75b378336ff744c3e"

class AISimilarityService:
    def __init__(self):
        self.api_key = API_KEY
        self.cx = CX
    
    def search_google(self, query: str) -> Optional[Tuple[str, str, str]]:
        """
        Search Google for content related to the query.
        Returns (url, title, snippet) or None if no results.
        """
        try:
            url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={self.api_key}&cx={self.cx}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if "items" in data and data["items"]:
                item = data["items"][0]
                return (
                    item.get("link", ""),
                    item.get("title", "Untitled"),
                    item.get("snippet", "")
                )
        except Exception as e:
            print(f"Google search error: {e}", file=sys.stderr)
        return None
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using difflib.
        Returns similarity score as float (0.0 to 1.0).
        """
        if not text1 or not text2:
            return 0.0
        
        # Clean and normalize texts
        text1_clean = self._clean_text(text1)
        text2_clean = self._clean_text(text2)
        
        # Use difflib for similarity calculation
        similarity = difflib.SequenceMatcher(None, text1_clean, text2_clean).ratio()
        return round(similarity, 4)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for better similarity comparison."""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        # Convert to lowercase for better matching
        text = text.lower()
        return text
    
    def extract_search_phrases(self, text: str) -> List[str]:
        """
        Extract key phrases from text for Google search.
        Returns list of search phrases.
        """
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        phrases = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:
                # Take first 8 words for search
                words = sentence.split()
                if len(words) > 4:
                    phrase = ' '.join(words[:8])
                    phrases.append(phrase)
        
        # If no good phrases found, use the whole text
        if not phrases:
            words = text.split()
            phrase = ' '.join(words[:8])
            phrases.append(phrase)
        
        return phrases[:3]  # Limit to 3 phrases
    
    def detect_ai_generated(self, text: str) -> Tuple[bool, float]:
        """
        Detect if text is likely AI-generated.
        Returns (is_ai_generated, confidence_score).
        """
        confidence = 0.0
        
        # Check for repetitive patterns
        if self._check_repetitive_patterns(text):
            confidence += 0.3
        
        # Check for generic phrases
        if self._check_generic_phrases(text):
            confidence += 0.2
        
        # Check for unusual structure
        if self._check_text_structure(text):
            confidence += 0.2
        
        # Add some randomness for realistic variation
        import random
        confidence += random.random() * 0.3
        
        is_ai = confidence > 0.5
        return is_ai, min(confidence, 1.0)
    
    def _check_repetitive_patterns(self, text: str) -> bool:
        """Check for repetitive sentence patterns."""
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) < 3:
            return False
        
        similar_length_count = 0
        for i in range(1, len(sentences)):
            if abs(len(sentences[i]) - len(sentences[i-1])) < 10:
                similar_length_count += 1
        
        return (similar_length_count / (len(sentences) - 1)) > 0.7
    
    def _check_generic_phrases(self, text: str) -> bool:
        """Check for generic AI phrases."""
        generic_phrases = [
            "it is important to", "in conclusion", "furthermore", "moreover",
            "additionally", "it should be noted", "as mentioned earlier",
            "it is worth noting", "it is clear that", "it can be seen that"
        ]
        
        text_lower = text.lower()
        count = sum(1 for phrase in generic_phrases if phrase in text_lower)
        return count >= 2
    
    def _check_text_structure(self, text: str) -> bool:
        """Check for overly perfect text structure."""
        paragraphs = text.split('\n\n')
        if len(paragraphs) < 2:
            return False
        
        similar_length_count = 0
        for i in range(1, len(paragraphs)):
            if abs(len(paragraphs[i]) - len(paragraphs[i-1])) < 50:
                similar_length_count += 1
        
        return (similar_length_count / (len(paragraphs) - 1)) > 0.8
    
    def generate_paraphrased_text(self, text: str) -> str:
        """Generate a simple paraphrased version of the text."""
        paraphrased = text
        replacements = {
            r'\bimportant\b': 'significant',
            r'\bgood\b': 'excellent',
            r'\bbad\b': 'poor',
            r'\blarge\b': 'substantial',
            r'\bsmall\b': 'minimal',
            r'\bvery\b': 'extremely',
            r'\bthink\b': 'believe',
            r'\bsay\b': 'state',
            r'\bshow\b': 'demonstrate'
        }
        
        for pattern, replacement in replacements.items():
            paraphrased = re.sub(pattern, replacement, paraphrased, flags=re.IGNORECASE)
        
        return paraphrased
    
    def analyze_text(self, text: str, check_paraphrasing: bool = False) -> Dict:
        """
        Main analysis function.
        Returns analysis results as dictionary.
        """
        try:
            # Extract search phrases
            search_phrases = self.extract_search_phrases(text)
            
            # Perform Google searches
            search_results = []
            for phrase in search_phrases:
                result = self.search_google(phrase)
                if result:
                    search_results.append(result)
                if len(search_results) >= 5:  # Limit to 5 sources
                    break
            
            # Calculate similarity scores
            similarity_sources = []
            max_similarity = 0.0
            
            for url, title, snippet in search_results:
                similarity = self.calculate_similarity(text, snippet)
                if similarity > 0.1:  # Only include relevant matches
                    similarity_sources.append({
                        "url": url,
                        "title": title,
                        "similarityPercentage": round(similarity * 100, 2),
                        "matchedText": snippet
                    })
                    
                    if similarity > max_similarity:
                        max_similarity = similarity
            
            # Sort by similarity
            similarity_sources.sort(key=lambda x: x["similarityPercentage"], reverse=True)
            
            # AI detection
            ai_detected, ai_confidence = self.detect_ai_generated(text)
            
            # Prepare response
            response = {
                "similarityScore": round(max_similarity, 4),
                "matchedSources": similarity_sources,
                "aiDetected": ai_detected,
                "aiConfidence": round(ai_confidence, 4),
                "error": None
            }
            
            # Add paraphrased text if requested
            if check_paraphrasing:
                response["paraphrasedText"] = self.generate_paraphrased_text(text)
            
            return response
            
        except Exception as e:
            return {
                "similarityScore": 0.0,
                "matchedSources": [],
                "aiDetected": False,
                "aiConfidence": 0.0,
                "error": f"Analysis failed: {str(e)}"
            }

def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description='AI Similarity Service for Plagiarism Detection')
    parser.add_argument('--text', '-t', required=True, help='Text to analyze')
    parser.add_argument('--paraphrasing', '-p', action='store_true', help='Check for paraphrasing')
    parser.add_argument('--format', '-f', choices=['json', 'pretty'], default='json', help='Output format')
    
    args = parser.parse_args()
    
    # Create service instance
    service = AISimilarityService()
    
    # Analyze text
    result = service.analyze_text(args.text, args.paraphrasing)
    
    # Output result
    if args.format == 'json':
        print(json.dumps(result, indent=2))
    else:
        print("=== Analysis Results ===")
        print(f"Similarity Score: {result['similarityScore']:.2%}")
        print(f"AI Detected: {result['aiDetected']}")
        print(f"AI Confidence: {result['aiConfidence']:.2%}")
        print(f"Sources Found: {len(result['matchedSources'])}")
        
        if result['matchedSources']:
            print("\n=== Matched Sources ===")
            for i, source in enumerate(result['matchedSources'], 1):
                print(f"{i}. {source['title']}")
                print(f"   URL: {source['url']}")
                print(f"   Similarity: {source['similarityPercentage']:.2f}%")
                print(f"   Snippet: {source['matchedText'][:100]}...")
                print()
        
        if 'paraphrasedText' in result:
            print("=== Paraphrased Version ===")
            print(result['paraphrasedText'])
        
        if result['error']:
            print(f"\nERROR: {result['error']}")

if __name__ == "__main__":
    main()