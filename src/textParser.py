import re
import unicodedata
from configs import *

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
        pattern = r"^(?P<titulo>.+?)\s+(?P<autor>[A-Z][a-z]+(?:\s+[A-Z][a-z]+))\s+(?P<body>.*)$"
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


    @staticmethod
    async def iniciar_conversao() -> None:

        import os
        import asyncio
        import time
        import aioconsole

        from formatText import textFormat
        from menu import Menu
        from files_utils import filesUtils
        from audio import Audio
        from pdfParser import pdfCoverter
        
        """
        Inicia o processo de conversão de texto para áudio de forma concorrente.
        O tamanho dos chunks é calculado dinamicamente.
        """
        global CANCELAR_PROCESSAMENTO
        CANCELAR_PROCESSAMENTO = False

        try:
            caminho_arquivo = await pdfCoverter.selecionar_arquivo()
            if not caminho_arquivo or CANCELAR_PROCESSAMENTO:
                return

            voz_escolhida = await Menu.menu_vozes()
            if voz_escolhida is None or CANCELAR_PROCESSAMENTO:
                return

            print("\n📖 Lendo arquivo...")
            texto = filesUtils.ler_arquivo_texto(caminho_arquivo)
            if not texto or CANCELAR_PROCESSAMENTO:
                print("\n❌ Arquivo vazio ou ilegível")
                await asyncio.sleep(2)
                return

            print("🔄 Processando texto...")
            texto_processado = textFormat.processar_texto(texto)

            partes = textFormat.dividir_texto(texto_processado)
            total_partes = len(partes)
            print(f"\n📊 Texto dividido em {total_partes} parte(s).")
            print("Para interromper a conversão a qualquer momento, pressione CTRL + C.\n")

            nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
            nome_base = filesUtils.limpar_nome_arquivo(nome_base)
            diretorio_saida = os.path.join(
                os.path.dirname(caminho_arquivo), f"{nome_base}_audio"
            )

            if not os.path.exists(diretorio_saida):
                os.makedirs(diretorio_saida)

            temp_files = []
            start_time = time.time()
            semaphore = asyncio.Semaphore(5)  # Limite de 5 tarefas simultâneas

            async def processar_chunk(i, parte):
                async with semaphore:
                    if CANCELAR_PROCESSAMENTO:
                        return None

                    saida_temp = os.path.join(
                        diretorio_saida, f"{nome_base}_temp_{i:03d}.mp3"
                    )
                    temp_files.append(saida_temp)

                    tentativa = 1
                    while tentativa <= MAX_TENTATIVAS:
                        if CANCELAR_PROCESSAMENTO:
                            return None

                        inicio_chunk = time.time()
                        sucesso = await Audio.converter_texto_para_audio(
                            parte, voz_escolhida, saida_temp
                        )

                        if sucesso:
                            tempo_chunk = time.time() - inicio_chunk
                            print(
                                f"✅ Parte {i}/{total_partes} | Tentativa {tentativa}/{MAX_TENTATIVAS} | Tempo: {tempo_chunk:.1f}s"
                            )
                            return True
                        else:
                            print(
                                f"🔄 Tentativa {tentativa}/{MAX_TENTATIVAS} falhou para parte {i}. Reiniciando..."
                            )
                            tentativa += 1
                            await asyncio.sleep(2)  # Intervalo entre tentativas

                    print(
                        f"❌ Falha definitiva na parte {i} após {MAX_TENTATIVAS} tentativas"
                    )
                    return False

            tasks = [processar_chunk(i + 1, p) for i, p in enumerate(partes)]
            results = await asyncio.gather(*tasks)

            # Verificar se todas as partes foram convertidas
            if not all(results):
                print("\n⚠️ Algumas partes falharam. Não é possível unificar.")
                return

            if not CANCELAR_PROCESSAMENTO and any(results):
                print("\n🔄 Unificando arquivos...")
                arquivo_final = os.path.join(diretorio_saida, f"{nome_base}.mp3")

                if Audio.unificar_audio(temp_files, arquivo_final):
                    for f in temp_files:
                        if os.path.exists(f):
                            os.remove(f)
                    overall_time = time.time() - start_time
                    print(
                        f"\n🎉 Conversão concluída em {overall_time:.1f} s! Arquivo final: {arquivo_final}"
                    )

                    # Pergunta se deseja melhorar o áudio
                    melhorar = (
                        (
                            await aioconsole.ainput(
                                "\nDeseja melhorar o áudio gerado (ajustar velocidade)? (s/n): "
                            )
                        )
                        .strip()
                        .lower()
                    )
                    if melhorar == "s":
                        await Audio.processar_melhorar_audio(arquivo_final)
                else:
                    print("\n❌ Falha na unificação dos arquivos.")

            await aioconsole.ainput("\nPressione ENTER para continuar...")

        except asyncio.CancelledError:
            print("\n🚫 Operação cancelada pelo usuário")
        finally:
            CANCELAR_PROCESSAMENTO = True
            if "temp_files" in locals():
                for f in temp_files:
                    if os.path.exists(f):
                        os.remove(f)
            await asyncio.sleep(1)