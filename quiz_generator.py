#!/usr/bin/env python3
"""
Quiz Generator for Estonian Studies
Generates reading quiz summaries from existing notes using ChatGPT
"""

import re
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class QuizGenerator:
    def __init__(self):
        self.quiz_template = """Master's Reading Quiz Template

I. Comprehension & Recall
Citation: Who wrote it? When? In what context?
Summary: State the main argument/thesis in 2–3 sentences.
Key Concepts: Define 3 terms, theories, or frameworks introduced in the reading.

II. Analysis & Interpretation
4. Argument Structure: What steps does the author use to build the argument?
5. Evidence: What kinds of evidence/examples are used, and how convincing are they?
6. Comparative Angle: How does this perspective align or contrast with another reading in the course?

III. Application & Synthesis
7. Real-World Connection: How could the argument apply to a current Estonian or global issue?
8. Integration: How does this reading connect with themes from previous weeks or other courses?
9. Extension: If you had to design a research project from this reading, what would your question or case study be? How would it apply to your thesis?

IV. Evaluation & Critique
10. Strengths: What is especially strong, innovative, or useful in the argument?
11. Weaknesses: Where is the reasoning thin, outdated, or vulnerable?
12. Bias/Positioning: What assumptions, blind spots, or cultural/political biases are present?
13. Reflection: Did this reading challenge or reinforce your own assumptions? How?

V. Discussion Preparation
14. Two Questions for Class: Formulate open-ended questions that could spark debate.
15. Core Takeaway: One idea or insight to keep in mind long-term."""

    def extract_notes_from_markdown(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract all notes from a markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            notes = []
            # Find all note divs in the markdown
            note_pattern = r'<div style="background-color: ([^"]+);[^>]+>[\s\S]*?<strong>([^<]+)</strong><br>\s*(.*?)\s*</div>'
            matches = re.findall(note_pattern, content, re.MULTILINE)
            
            for match in matches:
                bg_color, note_type_info, note_text = match
                # Extract note type from the type info (e.g., "🔍 HIGHLIGHT (2024-01-15):")
                type_match = re.search(r'([A-Z]+)', note_type_info)
                note_type = type_match.group(1).lower() if type_match else 'unknown'
                
                notes.append({
                    'type': note_type,
                    'text': note_text.strip(),
                    'bg_color': bg_color
                })
            
            return notes
            
        except Exception as e:
            print(f"Error extracting notes from {file_path}: {e}")
            return []

    def extract_keywords_from_content(self, file_path: str, limit: int = 10) -> List[str]:
        """Extract key terms and phrases from the document content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove HTML tags and note divs for cleaner text analysis
            clean_content = re.sub(r'<[^>]+>', '', content)
            clean_content = re.sub(r'\n+', ' ', clean_content)
            
            # Use a simple keyword extraction (could be enhanced with NLP)
            # Look for capitalized terms, quoted terms, and important phrases
            keywords = set()
            
            # Find quoted terms
            quoted_terms = re.findall(r'"([^"]{3,30})"', clean_content)
            keywords.update(quoted_terms[:5])
            
            # Find capitalized terms (potential proper nouns, concepts)
            cap_terms = re.findall(r'\b[A-Z][a-z]{2,15}\b', clean_content)
            # Filter out common words
            common_words = {'The', 'This', 'That', 'When', 'Where', 'What', 'Who', 'How', 'And', 'But', 'For', 'With'}
            cap_terms = [term for term in cap_terms if term not in common_words]
            keywords.update(cap_terms[:5])
            
            return list(keywords)[:limit]
            
        except Exception as e:
            print(f"Error extracting keywords from {file_path}: {e}")
            return []

    def generate_quiz_from_notes(self, file_path: str, notes: List[Dict[str, Any]], keywords: List[str]) -> str:
        """Generate a reading quiz by aggregating notes using ChatGPT"""
        
        # Prepare the prompt for ChatGPT
        notes_text = "\n\n".join([f"[{note['type'].upper()}]: {note['text']}" for note in notes])
        keywords_text = ", ".join(keywords)
        
        prompt = f"""You are helping a student organize their personal reading notes into a structured quiz format. The notes below are the STUDENT'S OWN thoughts, insights, and observations about an academic text - NOT the author's words.

STUDENT'S PERSONAL NOTES:
{notes_text}

KEY TERMS FROM THE TEXT: {keywords_text}

Your task: Use ONLY the student's notes above to fill out this reading quiz. Present each question followed by the answer based on the student's insights. The answers should reflect the student's understanding and analysis, not create new interpretations.

QUIZ TEMPLATE TO FILL OUT:

{self.quiz_template}

CRITICAL INSTRUCTIONS:
- ALWAYS include each question before its answer for clarity
- Use ONLY the student's notes provided - these are their personal insights and observations
- When answering, make it clear these are the student's thoughts (e.g., "Based on my notes..." or "My observation is...")
- Pair the student's insights with the most relevant quiz questions
- Use HTML formatting: <strong>bold</strong>, <br> for line breaks, <ul><li>lists</li></ul>
- Include keywords in <strong>[keyword]</strong> brackets for reference
- If the student's notes don't cover a question, write "<em>[Not covered in my notes]</em>"
- Keep the student's voice and perspective - don't rewrite their insights
- Add <br><br> between sections for proper spacing

FORMAT EXAMPLE:
<strong>1. Citation: Who wrote it? When? In what context?</strong><br>
Based on my notes, [author info from student's observations]<br><br>

<strong>2. Summary: State the main argument/thesis in 2–3 sentences.</strong><br>
My understanding is that [student's summary from their notes]<br><br>
"""

        try:
            # Use ChatGPT API
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                return "Error: OPENAI_API_KEY environment variable not set. Please add your OpenAI API key to use quiz generation."
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are an academic assistant helping create reading quizzes from student notes. Focus on organizing and synthesizing the provided notes into clear, structured answers."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                quiz_content = result['choices'][0]['message']['content']
                
                # Convert markdown formatting to HTML for better display in note div
                formatted_content = self._format_quiz_for_html(quiz_content)
                return formatted_content
            else:
                error_detail = ""
                try:
                    error_data = response.json()
                    error_detail = error_data.get('error', {}).get('message', '')
                except:
                    pass
                return f"Error: ChatGPT API request failed with status {response.status_code}. {error_detail}"
                
        except Exception as e:
            return f"Error generating quiz: {str(e)}"

    def create_quiz_for_document(self, file_path: str) -> Dict[str, Any]:
        """Main function to create a quiz summary for a document"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'File not found: {file_path}'
                }
            
            # Extract notes and keywords
            notes = self.extract_notes_from_markdown(str(file_path))
            keywords = self.extract_keywords_from_content(str(file_path))
            
            if not notes:
                return {
                    'success': False,
                    'error': 'No notes found in the document'
                }
            
            # Generate the quiz
            quiz_content = self.generate_quiz_from_notes(str(file_path), notes, keywords)
            
            return {
                'success': True,
                'quiz_content': quiz_content,
                'notes_count': len(notes),
                'keywords': keywords
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _format_quiz_for_html(self, quiz_content: str) -> str:
        """Convert markdown formatting to HTML for better display in note div"""
        try:
            # Convert markdown formatting to HTML
            formatted = quiz_content
            
            # Convert **bold** to <strong>
            formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted)
            
            # Convert bullet points to HTML lists
            lines = formatted.split('\n')
            in_list = False
            result_lines = []
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('- '):
                    if not in_list:
                        result_lines.append('<ul>')
                        in_list = True
                    result_lines.append(f'<li>{stripped[2:]}</li>')
                else:
                    if in_list:
                        result_lines.append('</ul>')
                        in_list = False
                    
                    if stripped:
                        # Add line breaks for readability
                        result_lines.append(line + '<br>')
                    else:
                        result_lines.append('<br>')
            
            if in_list:
                result_lines.append('</ul>')
            
            return '\n'.join(result_lines)
            
        except Exception as e:
            print(f"Error formatting quiz content: {e}")
            return quiz_content  # Return original if formatting fails

# Global instance
quiz_generator = QuizGenerator()
