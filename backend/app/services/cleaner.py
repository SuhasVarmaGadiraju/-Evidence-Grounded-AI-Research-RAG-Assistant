import unicodedata
import re
import logging

logger = logging.getLogger("rag_backend.cleaner")

# Regex to match control characters (excluding newline \n and carriage return \r)
CONTROL_CHAR_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')

# Common page numbering regexes
PAGE_NUM_RE = re.compile(r'^(page\s+\d+|\d+\s+of\s+\d+|\d+)$', re.IGNORECASE)

def normalize_unicode(text):
    """Normalizes Unicode characters (resolves ligatures, curly quotes, dashes)."""
    if not text:
        return ""
    # NFKC normalizes ligatures like 'fi' -> 'f'+'i' and maps standard characters
    text = unicodedata.normalize("NFKC", text)
    
    # Map common non-standard smart punctuation to ASCII equivalent
    smart_replacements = {
        '“': '"', '”': '"', '‘': "'", '’': "'",
        '—': '-', '–': '-', '…': '...',
    }
    for char, replacement in smart_replacements.items():
        text = text.replace(char, replacement)
        
    return text

def clean_page_text(text):
    """
    Cleans extracted text from a single page:
    1. Removes control characters.
    2. Performs Unicode NFKC normalization.
    3. Trims whitespace line by line.
    4. Strips headers, footers, or page numbers if isolated on lines.
    5. Collapses excessive consecutive newlines (preserves double newlines for paragraph breaks).
    """
    if not text:
        return ""
        
    # 1. Strip control characters
    text = CONTROL_CHAR_RE.sub('', text)
    
    # 2. Normalize Unicode
    text = normalize_unicode(text)
    
    # 3. Trim line by line & remove page number artifacts
    lines = text.split('\n')
    cleaned_lines = []
    
    for i, line in enumerate(lines):
        trimmed = line.strip()
        
        # Skip lines that are page numbers (typically isolated at start or end of lines)
        # We only check this if they are short and match our page-number pattern
        if len(trimmed) < 15 and PAGE_NUM_RE.match(trimmed):
            # Only ignore page numbers if they appear at the boundary of pages
            if i < 2 or i > len(lines) - 3:
                continue
                
        cleaned_lines.append(trimmed)
        
    # 4. Collapse excessive empty lines (max 1 consecutive blank line for paragraphs)
    collapsed_lines = []
    prev_blank = False
    
    for line in cleaned_lines:
        if line == "":
            if not prev_blank:
                collapsed_lines.append("")
                prev_blank = True
        else:
            collapsed_lines.append(line)
            prev_blank = False
            
    # Join and strip overall text
    result = "\n".join(collapsed_lines).strip()
    return result
