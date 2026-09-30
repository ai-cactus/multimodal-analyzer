"""
Compliance body section parser supporting CARF, MHRS, and DBH formats
"""
import re
from typing import List, Tuple, Dict, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ComplianceBodySectionParser:
    """
    Flexible section parser supporting multiple compliance body formats:
    - CARF: Hierarchical alphanumeric (1.B., 5.a.(2)(a)B.)
    - MHRS: Section symbol with dot notation (§3405.1, §3413.16)
    - DBH: Similar to MHRS (§2-559, Rule 5.1)
    """
    
    PATTERNS = {
        'carf': {
            # Matches: 1.B., 5.a.B., 5.a.(1)B., 5.a.(2)(a)B.
            'regex': r'(\d+\.[A-Z]\.(?:[a-z]\.)?(?:\(\d+\))?(?:\([a-z]\))?(?:[A-Z]\.)?)',
            'description': 'Hierarchical alphanumeric with domain suffix'
        },
        'mhrs': {
            # Matches: §3405.1, §3413.16, §2-559
            'regex': r'(§\d+[-\.]?\d*\.?\d*)',
            'description': 'Section symbol with dot notation'
        },
        'dbh': {
            # Similar to MHRS with Rule support
            'regex': r'(§\d+[-\.]?\d*\.?\d*|Rule\s+\d+\.?\d*)',
            'description': 'Section symbol or Rule notation'
        }
    }
    
    def __init__(self, compliance_body: str):
        """
        Initialize parser for specific compliance body
        
        Args:
            compliance_body: "CARF", "MHRS", or "DBH"
        """
        self.body = compliance_body.lower()
        self.pattern = self.PATTERNS.get(self.body, self.PATTERNS['mhrs'])
        logger.info(f"Initialized parser for {compliance_body}: {self.pattern['description']}")
    
    def extract_sections(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Extract all section references with positions
        
        Args:
            text: Full document text
            
        Returns:
            List of tuples: [(section_ref, start_pos, end_pos), ...]
        """
        matches = []
        for match in re.finditer(self.pattern['regex'], text, re.MULTILINE):
            section_ref = match.group(1).strip()
            matches.append((
                section_ref,
                match.start(),
                match.end()
            ))
        
        logger.info(f"Extracted {len(matches)} sections from text")
        return matches
    
    def chunk_by_section(
        self,
        text: str,
        max_chunk_words: int = 1000
    ) -> List[Dict[str, any]]:
        """
        Chunk document by sections, preserving context
        
        Args:
            text: Full document text
            max_chunk_words: Maximum words per chunk (for long sections)
            
        Returns:
            List of section chunks with metadata
        """
        sections = self.extract_sections(text)
        chunks = []
        
        if not sections:
            # No sections found, chunk by words
            logger.warning("No sections found, chunking by word count")
            return self._chunk_by_words(text, max_chunk_words)
        
        for i, (section_ref, start, end) in enumerate(sections):
            # Get text until next section or end
            next_start = sections[i + 1][1] if i + 1 < len(sections) else len(text)
            section_text = text[start:next_start].strip()
            
            # Handle long sections (split further if needed)
            words = section_text.split()
            if len(words) > max_chunk_words:
                # Sub-chunk while preserving section context
                for j in range(0, len(words), max_chunk_words):
                    chunk_words = words[j:j + max_chunk_words]
                    chunk_text = ' '.join(chunk_words)
                    
                    chunks.append({
                        'section_ref': section_ref,
                        'sub_chunk': (j // max_chunk_words + 1) if len(words) > max_chunk_words else None,
                        'text': chunk_text,
                        'compliance_body': self.body,
                        'word_count': len(chunk_words)
                    })
            else:
                chunks.append({
                    'section_ref': section_ref,
                    'sub_chunk': None,
                    'text': section_text,
                    'compliance_body': self.body,
                    'word_count': len(words)
                })
        
        logger.info(f"Created {len(chunks)} chunks from {len(sections)} sections")
        return chunks
    
    def _chunk_by_words(
        self,
        text: str,
        max_chunk_words: int
    ) -> List[Dict[str, any]]:
        """Fallback chunking by word count when no sections detected"""
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), max_chunk_words):
            chunk_words = words[i:i + max_chunk_words]
            chunk_text = ' '.join(chunk_words)
            
            chunks.append({
                'section_ref': f'chunk_{i // max_chunk_words + 1}',
                'sub_chunk': None,
                'text': chunk_text,
                'compliance_body': self.body,
                'word_count': len(chunk_words)
            })
        
        return chunks
    
    def parse_section_range(self, section_str: str) -> List[str]:
        """
        Parse section range notation for filtering
        
        Examples:
            - CARF: "1.B-1.E" → ["1.B.", "1.C.", "1.D.", "1.E."]
            - MHRS: "§3409-3412" → ["§3409", "§3410", "§3411", "§3412"]
            - DBH: Same as MHRS
        
        Args:
            section_str: Section range string
            
        Returns:
            List of individual section references
        """
        if self.body == 'carf':
            return self._parse_carf_range(section_str)
        else:
            return self._parse_numeric_range(section_str)
    
    def _parse_carf_range(self, section_str: str) -> List[str]:
        """Parse CARF letter ranges"""
        
        if '-' not in section_str:
            return [section_str]
        
        try:
            # Parse "1.B-1.E" or "1.B.-1.E."
            parts = section_str.split('-')
            start_section = parts[0].strip()
            end_section = parts[1].strip()
            
            # Extract number and letters
            start_match = re.match(r'(\d+)\.([A-Z])\.?', start_section)
            end_match = re.match(r'(\d+)\.([A-Z])\.?', end_section)
            
            if not start_match or not end_match:
                logger.warning(f"Invalid CARF range format: {section_str}")
                return [section_str]
            
            start_num = start_match.group(1)
            start_letter = start_match.group(2)
            end_letter = end_match.group(2)
            
            # Generate range
            letters = [chr(i) for i in range(ord(start_letter), ord(end_letter) + 1)]
            return [f"{start_num}.{letter}." for letter in letters]
            
        except Exception as e:
            logger.error(f"Error parsing CARF range {section_str}: {e}")
            return [section_str]
    
    def _parse_numeric_range(self, section_str: str) -> List[str]:
        """Parse MHRS/DBH numeric ranges"""
        
        if '-' not in section_str:
            return [section_str]
        
        try:
            # Parse "§3409-3412" or "§3409.1-3412.5"
            # Remove § symbol
            clean_str = section_str.replace('§', '')
            parts = clean_str.split('-')
            
            # Extract base numbers
            start_num = int(re.match(r'(\d+)', parts[0]).group(1))
            end_num = int(re.match(r'(\d+)', parts[1]).group(1))
            
            # Generate range
            sections = [f"§{i}" for i in range(start_num, end_num + 1)]
            return sections
            
        except Exception as e:
            logger.error(f"Error parsing numeric range {section_str}: {e}")
            return [section_str]
    
    def create_section_filter_pattern(self, section_list: List[str]) -> str:
        """
        Create regex pattern for filtering sections
        
        Args:
            section_list: List of section references
            
        Returns:
            Regex pattern string
        """
        # Escape special regex characters and join with OR
        escaped_sections = [re.escape(s) for s in section_list]
        pattern = '|'.join(escaped_sections)
        return f'({pattern})'
