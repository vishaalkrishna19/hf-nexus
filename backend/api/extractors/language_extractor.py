import re

class LanguageExtractor:
    """
    Extracts languages and proficiency from resume text.
    Looks for patterns like: 'Languages: English (Fluent), Tamil (Native), Hindi (Basic)'
    or 'Proficient in English, Tamil, Hindi'
    """
    LANGUAGES = [
        'english', 'tamil', 'hindi', 'telugu', 'malayalam', 'kannada', 'marathi', 'bengali',
        'gujarati', 'punjabi', 'urdu', 'oriya', 'assamese', 'sanskrit', 'french', 'german',
        'spanish', 'arabic', 'chinese', 'japanese', 'korean', 'russian', 'portuguese'
    ]
    PROFICIENCY_KEYWORDS = {
        'native': ['native', 'mother tongue', 'first language'],
        'fluent': ['fluent', 'proficient', 'excellent', 'advanced'],
        'intermediate': ['intermediate', 'working knowledge'],
        'basic': ['basic', 'elementary', 'beginner'],
    }

    def extract_languages(self, text):
        text_lower = text.lower()
        found = []
        for lang in self.LANGUAGES:
            if lang in text_lower:

                prof = self._extract_proficiency(text_lower, lang)
                found.append({'language': lang.capitalize(), 'proficiency': prof})
        return found

    def _extract_proficiency(self, text, lang):

        for prof, keywords in self.PROFICIENCY_KEYWORDS.items():
            for kw in keywords:

                if re.search(rf"{lang}\s*[\(\[]?\s*{kw}", text) or re.search(rf"{kw}\s*(in|with)?\s*{lang}", text):
                    return prof.capitalize()
        return "Mentioned"
