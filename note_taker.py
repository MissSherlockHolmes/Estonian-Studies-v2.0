#!/usr/bin/env python3
"""
Interactive Note Taker for Estonian Studies
Allows adding highlighted notes to markdown files while reading
"""

import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional

class NoteTaker:
    def __init__(self):
        self.note_counter = 1
    
    def find_note_location(self, content: str, search_term: str) -> Optional[int]:
        """Find the best location to insert a note based on search term - place at END of line"""
        if not search_term.strip():
            return None
        
        # Clean both the content and search term for comparison
        clean_content = re.sub(r'\s+', ' ', content)
        clean_search = re.sub(r'\s+', ' ', search_term.strip())
        
        # Try exact match first
        exact_match = clean_content.find(clean_search)
        if exact_match != -1:
            # Map back to original content position
            original_pos = self._map_clean_to_original_position(content, exact_match)
            line_end = content.find('\n', original_pos)
            if line_end == -1:
                line_end = len(content)
            return line_end
        
        # Try case-insensitive match
        case_insensitive = clean_content.lower().find(clean_search.lower())
        if case_insensitive != -1:
            original_pos = self._map_clean_to_original_position(content, case_insensitive)
            line_end = content.find('\n', original_pos)
            if line_end == -1:
                line_end = len(content)
            return line_end
        
        # Try partial match with first few words
        words = clean_search.split()[:3]  # First 3 words
        if len(words) > 0:
            partial_search = ' '.join(words)
            partial_match = clean_content.lower().find(partial_search.lower())
            if partial_match != -1:
                original_pos = self._map_clean_to_original_position(content, partial_match)
                line_end = content.find('\n', original_pos)
                if line_end == -1:
                    line_end = len(content)
                return line_end
        
        return None
    
    def _map_clean_to_original_position(self, original: str, clean_pos: int) -> int:
        """Map position in cleaned text back to original text"""
        clean_chars = 0
        for i, char in enumerate(original):
            if not char.isspace() or char == ' ':
                if clean_chars == clean_pos:
                    return i
                clean_chars += 1
        return len(original)
    
    def create_note_html(self, note_text: str, note_type: str = "note", color: str = "yellow") -> str:
        """Create a highlighted note with HTML/CSS styling and customizable colors"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Color schemes with darker text for better readability
        color_schemes = {
            "yellow": {
                "bg": "#fff8dc",
                "border": "#ffd700", 
                "text": "#2c2c2c"
            },
            "red": {
                "bg": "#ffe6e6",
                "border": "#ff4444",
                "text": "#2c2c2c"
            },
            "blue": {
                "bg": "#e6f3ff",
                "border": "#4da6ff",
                "text": "#2c2c2c"
            },
            "green": {
                "bg": "#e6ffe6",
                "border": "#4dff4d",
                "text": "#2c2c2c"
            },
            "orange": {
                "bg": "#fff2e6",
                "border": "#ff8800",
                "text": "#2c2c2c"
            },
            "purple": {
                "bg": "#f0e6ff",
                "border": "#aa44ff",
                "text": "#2c2c2c"
            },
            "pink": {
                "bg": "#ffe6f0",
                "border": "#ff44aa",
                "text": "#2c2c2c"
            },
            "gray": {
                "bg": "#f5f5f5",
                "border": "#888888",
                "text": "#2c2c2c"
            }
        }
        
        # Note type emojis
        note_emojis = {
            "note": "📝",
            "important": "🚨",
            "question": "❓",
            "idea": "💡",
            "quote": "💬",
            "highlight": "✨",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        
        scheme = color_schemes.get(color, color_schemes["yellow"])
        emoji = note_emojis.get(note_type, "📝")
        
        style = f"background-color: {scheme['bg']}; border-left: 4px solid {scheme['border']}; padding: 12px; margin: 12px 0; border-radius: 6px; color: {scheme['text']}; font-family: Arial, sans-serif;"
        
        note_html = f'''<div style="{style}">
    <strong>{emoji} {note_type.upper()} ({timestamp}):</strong><br>
    {note_text}
</div>'''
        
        return note_html
    
    def add_note_to_file(self, file_path: str, search_term: str, note_text: str, note_type: str = "note", color: str = "yellow") -> bool:
        """Add a note to a markdown file at the specified location"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return False
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find insertion point
        if search_term.strip() == '___APPEND_TO_END___':
            # Special marker for quiz notes - append to very end of document
            insert_pos = len(content)
            print(f"📍 Appending quiz to end of document at position: {insert_pos}")
        elif not search_term.strip():
            # Empty search term - append to end
            insert_pos = len(content)
            print(f"📍 Empty search term - appending to end at position: {insert_pos}")
        else:
            # Normal note placement - find the search term location
            insert_pos = self.find_note_location(content, search_term)
            if insert_pos is None:
                print(f"❌ Could not find '{search_term}' in the file")
                return False
            print(f"🎯 Insert position found: {insert_pos}")
        
        # Create the note
        note_html = self.create_note_html(note_text, note_type, color)
        
        # Insert the note
        new_content = content[:insert_pos] + "\n\n" + note_html + "\n\n" + content[insert_pos:]
        
        # Write back to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Note added successfully to {file_path.name}")
            return True
        except Exception as e:
            print(f"❌ Error writing to file: {e}")
            return False
    
    def list_notes_in_file(self, file_path: str) -> List[Tuple[str, str, str]]:
        """List all notes in a markdown file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all note divs
        note_pattern = r'<strong>([^:]+) \(([^)]+)\):</strong><br>\s*(.*?)</div>'
        matches = re.findall(note_pattern, content, re.DOTALL)
        
        # Convert to (note_type, timestamp, text) format
        notes = []
        for match in matches:
            emoji_and_type = match[0].strip()
            timestamp = match[1].strip()
            text = match[2].strip()
            
            # Extract note type from emoji_and_type (remove emoji if present)
            note_type = re.sub(r'^[^\w\s]+', '', emoji_and_type).strip()
            if not note_type:
                note_type = "note"
            
            notes.append((note_type, timestamp, text))
        
        return notes
    
    def delete_note_from_file(self, file_path: str, note_index: int) -> bool:
        """Delete a note from a markdown file by index"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all note divs with their positions
        note_pattern = r'<div style="[^"]*">\s*<strong>([^:]+) \(([^)]+)\):</strong><br>\s*(.*?)</div>'
        matches = list(re.finditer(note_pattern, content, re.DOTALL))
        
        if not matches or note_index < 1 or note_index > len(matches):
            return False
        
        # Get the match to delete (convert to 0-based index)
        match_to_delete = matches[note_index - 1]
        
        # Remove the note (including surrounding whitespace)
        start_pos = match_to_delete.start()
        end_pos = match_to_delete.end()
        
        # Find surrounding whitespace
        while start_pos > 0 and content[start_pos - 1] in '\n \t':
            start_pos -= 1
        while end_pos < len(content) and content[end_pos] in '\n \t':
            end_pos += 1
        
        # Remove the note
        new_content = content[:start_pos] + content[end_pos:]
        
        # Write back to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        except Exception:
            return False
