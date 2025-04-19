import re
from configs import manual_converser
from num2words import num2words
from configs import abreviacoes


class textFormat:

    def __init__(self):
        pass

    def standardize_chapters(self, text: str) -> str:

        def substituidor(match):
            chapter = match.group(1).strip().upper()
            title = match.group(2).strip()
            number = manual_converser.get(chapter, title)
            return f"CAPÍTULO {number}: {title.title()}"

        pattern = re.compile(
            r"CAP[IÍ]TULO\s+([A-Z0-9]+)\s*[:\-]?\s*(.+)", re.IGNORECASE
        )
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

    def separate_chapter(text: str) -> str:
        return re.sub(r"(CAP[IÍ]TULO\s+\d+:)", r"\n\n\1", text)

    def index_gen(text: str) -> str:
        pattern = re.compile(r"CAP[IÍ]TULO\s+(\d+):\s+(.+)", re.IGNORECASE)
        return "\n".join(
            [
                f"{match.group(1)}. {match.group(2).title()}"
                for match in pattern.finditer(pattern)
            ]
        )

    @staticmethod
    def apply_format(self, text: str) -> str:
        text = self.standardize_chapters(text)
        text = self.normalize_text(text)
        text = self.separate_chapter(text)
        index = self.index_gen(text)
        return index + "\n\n" + text

    @staticmethod
    def processar_texto(texto: str) -> str:
        """Processa o texto para melhorar a qualidade da conversão TTS."""
        # Remover caracteres não imprimíveis
        texto = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", texto)
        texto = texto.encode("utf-8", "ignore").decode("utf-8")

        texto = re.sub(r"\s+", " ", texto)

        for abrev, expansao in abreviacoes.items():
            texto = re.sub(abrev, expansao, texto)

        def converter_numero(match):
            num = match.group(0)
            try:
                return num2words(int(num), lang="pt_BR")
            except:
                return num

        def converter_valor_monetario(match):
            valor = match.group(1)
            try:
                return f"{num2words(int(valor), lang='pt_BR')} reais"
            except:
                return f"{valor} reais"

        texto = re.sub(r"\b\d+\b", converter_numero, texto)
        texto = re.sub(r"R\$\s*(\d+)", converter_valor_monetario, texto)
        texto = re.sub(
            r"\b(\d+)\s*-\s*(\d+)\b",
            lambda m: f"{num2words(int(m.group(1)), lang='pt_BR')} a {num2words(int(m.group(2)), lang='pt_BR')}",
            texto,
        )

        return texto

    @staticmethod
    def dividir_texto(texto: str) -> list:
        """
        Divide o texto em partes menores para processamento, respeitando os pontos finais.
        """
        partes = []
        start = 0
        while start < len(texto):
            next_period = texto.find(".", start)
            if next_period == -1:
                partes.append(texto[start:].strip())
                break
            end = next_period + 1
            partes.append(texto[start:end].strip())
            start = end
        return [p for p in partes if p]
