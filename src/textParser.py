
import re
import unicodedata


class ParserTxt:

    def normalizar_texto_corrigir(texto):
        """Normaliza o texto preservando acentos."""
        print("\n[1/5] Normalizando texto...")
        return unicodedata.normalize("NFKC", texto)


    def corrigir_espacamento_corrigir(texto):
        """Corrige espaçamentos desnecessários e remove espaços no início e fim das linhas."""
        print("[2/5] Corrigindo espaçamento...")
        texto = re.sub(r"\s+", " ", texto)
        texto = re.sub(r"^\s+|\s+$", "", texto, flags=re.MULTILINE)
        return texto


    def ajustar_titulo_e_capitulos_corrigir(texto):
        """
        Ajusta título, autor e formata capítulos.
        Tenta separar o cabeçalho (título e autor) se estiver em uma única linha.
        """
        print("[3/5] Ajustando título, autor e capítulos...")
        pattern = (
            r"^(?P<titulo>.+?)\s+(?P<autor>[A-Z][a-z]+(?:\s+[A-Z][a-z]+))\s+(?P<body>.*)$"
        )
        match = re.match(pattern, texto, re.DOTALL)
        if match:
            titulo = match.group("titulo").strip()
            autor = match.group("autor").strip()
            body = match.group("body").strip()
            if not titulo.endswith((".", "!", "?")):
                titulo += "."
            if not autor.endswith((".", "!", "?")):
                autor += "."
            novo_texto = titulo + "\n" + autor + "\n\n" + body
        else:
            linhas = texto.splitlines()
            header = []
            corpo = []
            non_empty_count = 0
            for linha in linhas:
                if linha.strip():
                    non_empty_count += 1
                    if non_empty_count <= 2:
                        header.append(linha.strip())
                    else:
                        corpo.append(linha)
                else:
                    if non_empty_count >= 2:
                        corpo.append(linha)
            if len(header) == 1:
                palavras = header[0].split()
                if (
                    len(palavras) >= 4
                    and palavras[-1][0].isupper()
                    and palavras[-2][0].isupper()
                ):
                    autor = " ".join(palavras[-2:])
                    titulo = " ".join(palavras[:-2])
                    header = [titulo.strip(), autor.strip()]
            if header:
                if not header[0].endswith((".", "!", "?")):
                    header[0] += "."
            if len(header) > 1:
                if not header[1].endswith((".", "!", "?")):
                    header[1] += "."
            novo_texto = "\n".join(header + [""] + corpo)
        novo_texto = re.sub(r"(?i)\b(capítulo\s*\d+)\b", r"\n\n\1.\n\n", novo_texto)
        return novo_texto


    def inserir_quebra_apos_ponto_corrigir(texto):
        """Insere uma quebra de parágrafo após cada ponto final."""
        print("[4/5] Inserindo quebra de parágrafo após cada ponto final...")
        texto = re.sub(r"\.\s+", ".\n\n", texto)
        return texto


    def formatar_paragrafos_corrigir(texto):
        """Formata os parágrafos garantindo uma linha em branco entre eles."""
        print("[5/5] Formatando parágrafos...")
        paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
        return "\n\n".join(paragrafos)


    def expandir_abreviacoes(texto):
        abreviacoes = {
            r"\bDr\.(?=\s)": "Doutor",
            r"\bD\.(?=\s)": "Dona",
            r"\bDra\.(?=\s)": "Doutora",
            r"\bSr\.(?=\s)": "Senhor",
            r"\bSra\.(?=\s)": "Senhora",
            r"\bSrta\.(?=\s)": "Senhorita",
            r"\bProf\.(?=\s)": "Professor",
            r"\bProfa\.(?=\s)": "Professora",
            r"\bEng\.(?=\s)": "Engenheiro",
            r"\bEngª\.(?=\s)": "Engenheira",
            r"\bAdm\.(?=\s)": "Administrador",
            r"\bAdv\.(?=\s)": "Advogado",
            r"\bExmo\.(?=\s)": "Excelentíssimo",
            r"\bExma\.(?=\s)": "Excelentíssima",
            r"\bV\.Exa\.(?=\s)": "Vossa Excelência",
            r"\bV\.Sa\.(?=\s)": "Vossa Senhoria",
            r"\bAv\.(?=\s)": "Avenida",
            r"\bR\.(?=\s)": "Rua",
            r"\bKm\.(?=\s)": "Quilômetro",
            r"\betc\.(?=\s)": "etcétera",
            r"\bRef\.(?=\s)": "Referência",
            r"\bPag\.(?=\s)": "Página",
            r"\bPág\.(?=\s)": "Página",
            r"\bPágs\.(?=\s)": "Páginas",
            r"\bPags\.(?=\s)": "Páginas",
            r"\bFl\.(?=\s)": "Folha",
            r"\bPe\.(?=\s)": "Padre",
            r"\bFls\.(?=\s)": "Folhas",
            r"\bDept\.(?=\s)": "Departamento",
            r"\bDepto\.(?=\s)": "Departamento",
            r"\bUniv\.(?=\s)": "Universidade",
            r"\bInst\.(?=\s)": "Instituição",
            r"\bEst\.(?=\s)": "Estado",
            r"\bTel\.(?=\s)": "Telefone",
            r"\bCEP\.(?=\s)": "Código de Endereçamento Postal",
            r"\bCNPJ\.(?=\s)": "Cadastro Nacional da Pessoa Jurídica",
            r"\bCPF\.(?=\s)": "Cadastro de Pessoas Físicas",
            r"\bEUA\.(?=\s)": "Estados Unidos da América",
            r"\bEd\.(?=\s)": "Edição",
            r"\bLtda\.(?=\s)": "Limitada",
        }
        for abrev, extensao in abreviacoes.items():
            texto = re.sub(abrev, extensao, texto)
        return texto


    def melhorar_texto_corrigido(texto):
        texto = texto.replace("\f", "\n\n")  # Remove form feeds
        import re

        def remover_num_paginas_rodapes(texto):
            return re.sub(
                r"\n?\s*\d+\s+cda_pr_.*?\.indd\s+\d+\s+\d+/\d+/\d+\s+\d+:\d+\s+[APM]{2}",
                "",
                texto,
            )

        def corrigir_hifenizacao(texto):
            return re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", texto)

        def remover_infos_bibliograficas_rodape(texto):
            return re.sub(r"^\s*(cda_pr_.*?\.indd.*?)$", "", texto, flags=re.MULTILINE)

        def converter_capitulos_para_extenso_simples(texto):
            substituicoes = {
                "CAPÍTULO I": "CAPÍTULO UM",
                "CAPÍTULO II": "CAPÍTULO DOIS",
                "CAPÍTULO III": "CAPÍTULO TRÊS",
                "CAPÍTULO IV": "CAPÍTULO QUATRO",
                "CAPÍTULO V": "CAPÍTULO CINCO",
                "CAPÍTULO VI": "CAPÍTULO SEIS",
                "CAPÍTULO VII": "CAPÍTULO SETE",
                "CAPÍTULO VIII": "CAPÍTULO OITO",
                "CAPÍTULO IX": "CAPÍTULO NOVE",
                "CAPÍTULO X": "CAPÍTULO DEZ",
            }
            for original, novo in substituicoes.items():
                texto = texto.replace(original, novo)
            return texto

        def pontuar_finais_de_paragrafo(texto):
            paragrafos = texto.split("\n\n")
            paragrafos_corrigidos = []
            for p in paragrafos:
                p = p.strip()
                if p and not re.search(r"[.!?…]$", p):
                    p += "."
                paragrafos_corrigidos.append(p)
            return "\n\n".join(paragrafos_corrigidos)

        texto = remover_num_paginas_rodapes(texto)
        texto = corrigir_hifenizacao(texto)
        texto = remover_infos_bibliograficas_rodape(texto)
        texto = converter_capitulos_para_extenso_simples(texto)
        texto = pontuar_finais_de_paragrafo(texto)
        texto = ParserTxt.expandir_abreviacoes(texto)
        return texto