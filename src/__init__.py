import re
from configs import manual_converser

class textFormat:

    def __init__(self):
        pass
        
    def standardize_chapters(self, text: str) -> str:
    
        def substituidor(match):
            chapter = match.group(1).strip().upper()
            title = match.group(2).strip()
            number = manual_converser.get(chapter, title)
            return f"CAPÍTULO {number}: {title.title()}"

        pattern = re.compile(r'CAP[IÍ]TULO\s+([A-Z0-9]+)\s*[:\-]?\s*(.+)', re.IGNORECASE)
        format_text = pattern.sub(substituidor, text)

        return format_text

    def normalize_text(self, text: str) -> str:
        lines = text.splitlines()
        final_text = []

        for line in lines:
            if line.isupper() and len(line.strip()) > 3:
                final_text.append(line.capitalize())
            else:
                final_text.append(line)
        return "\n".join(final_text)

    def separate_chapter(text:str) -> str:
        return re.sub(r'(CAP[IÍ]TULO\s+\d+:)', r'\n\n\1', text)

    def index_gen(text: str) -> str:
        pattern = re.compile(r'CAP[IÍ]TULO\s+(\d+):\s+(.+)', re.IGNORECASE)
        return "\n".join([
            f"{match.group(1)}. {match.group(2).title()}" for match in pattern.finditer(pattern)
        ])

    @staticmethod
    def apply_format(self, text: str) -> str :
        text = self.standardize_chapters(text)
        text = self.normalize_text(text)
        text = self.separate_chapter(text)
        index = self.index_gen(text)
        return index + '\n\n' + text




