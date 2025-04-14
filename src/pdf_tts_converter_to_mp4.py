import os
import subprocess
import asyncio
import re
from pathlib import Path
import shutil
import time
import unicodedata
import edge_tts
import aioconsole
import chardet
from math import ceil
from tqdm import tqdm
from num2words import num2words
from configs import *
from pdfParser import pdfCoverter

# Just for test


sistema = {"linux": True}




async def obter_opcao(prompt: str, opcoes: list) -> str:
    """Solicita ao usuário uma entrada que esteja dentre as opções válidas."""
    while True:
        escolha = (await aioconsole.ainput(prompt)).strip()
        if escolha in opcoes:
            return escolha
        print("⚠️ Opção inválida! Tente novamente.")


def gravar_progresso(arquivo_progresso: str, indice: int) -> None:
    """Grava o índice da última parte processada em arquivo."""
    with open(arquivo_progresso, "w") as f:
        f.write(str(indice))


def ler_progresso(arquivo_progresso: str) -> int:
    """Lê o índice da última parte processada a partir do arquivo de progresso."""
    try:
        with open(arquivo_progresso, "r") as f:
            return int(f.read().strip())
    except Exception:
        return 0


def limpar_nome_arquivo(nome: str) -> str:
    """Remove ou substitui caracteres inválidos em sistemas de arquivos."""
    nome_limpo = re.sub(r'[<>:"/\\|?*]', "", nome)
    nome_limpo = nome_limpo.replace(" ", "_")
    return nome_limpo


def unificar_audio(temp_files, arquivo_final) -> bool:
    """Une os arquivos de áudio temporários em um único arquivo final."""
    try:
        if shutil.which(FFMPEG_BIN):
            list_file = os.path.join(os.path.dirname(arquivo_final), "file_list.txt")
            with open(list_file, "w") as f:
                for temp in temp_files:
                    f.write(f"file '{os.path.abspath(temp)}'\n")
            subprocess.run(
                [
                    FFMPEG_BIN,
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    list_file,
                    "-c",
                    "copy",
                    arquivo_final,
                ],
                check=True,
            )
            os.remove(list_file)
        else:
            # Fallback: concatenação binária (pode não funcionar perfeitamente para mp3)
            with open(arquivo_final, "wb") as outfile:
                for temp in temp_files:
                    with open(temp, "rb") as infile:
                        outfile.write(infile.read())
        return True
    except Exception as e:
        print(f"❌ Erro na unificação dos arquivos: {e}")
        return False


async def exibir_banner() -> None:
    """Exibe o banner do programa."""
    
    print(
        """
╔════════════════════════════════════════════╗
║         CONVERSOR TTS COMPLETO             ║
║ Text-to-Speech + Melhoria de Áudio em PT-BR║
╚════════════════════════════════════════════╝
"""
    )


async def menu_principal() -> str:
    """Exibe o menu principal e retorna a opção escolhida."""
    await exibir_banner()
    print("\nEscolha uma opção:")
    print("1. 🚀 CONVERTER TEXTO PARA ÁUDIO")
    print("2. 🎙️ TESTAR VOZES")
    print("3. ⚡ MELHORAR ÁUDIO EXISTENTE")
    print("4. ❓ AJUDA")
    print("5. 🔄 ATUALIZAR")
    print("6. 🚪 SAIR")
    return await obter_opcao("\nOpção: ", ["1", "2", "3", "4", "5", "6"])


async def menu_vozes() -> str:
    """Exibe o menu de seleção de vozes e retorna a voz escolhida."""
    await exibir_banner()
    print("\nVozes disponíveis:")
    for i, voz in enumerate(VOZES_PT_BR, 1):
        print(f"{i}. {voz}")
    print(f"{len(VOZES_PT_BR) + 1}. Voltar")
    opcoes = [str(i) for i in range(1, len(VOZES_PT_BR) + 2)]
    escolha = await obter_opcao("\nEscolha uma voz: ", opcoes)
    if escolha == str(len(VOZES_PT_BR) + 1):
        return None
    return VOZES_PT_BR[int(escolha) - 1]


async def exibir_ajuda() -> None:
    """Exibe o guia de ajuda do programa."""
    await exibir_banner()
    print(
        """
📖 GUIA DE USO:

1. CONVERSÃO DE TEXTO PARA ÁUDIO:
   • Prepare seu arquivo de texto (.txt) ou PDF (.pdf)
   • Escolha uma voz e aguarde a conversão
   • O áudio resultante pode ser melhorado na opção 3

2. MELHORIA DE ÁUDIO:
   • Acelere arquivos de áudio/vídeo existentes
   • Escolha entre 0.5x e 2.0x de velocidade
   • Converta para MP3 (áudio) ou MP4 (vídeo com tela preta)
   • Arquivos longos são automaticamente divididos

⚠️ OBSERVAÇÕES:
• Para arquivos muito grandes, o processo pode demorar
• Certifique-se de ter espaço em disco suficiente
• No Android/Termux, os arquivos são salvos em /storage/emulated/0/Download
"""
    )
    await aioconsole.ainput("\nPressione ENTER para voltar ao menu principal...")





def listar_arquivos(diretorio: str, extensoes: list = None) -> list:
    """Lista arquivos no diretório especificado, filtrando por extensões se fornecido."""
    arquivos = []
    try:
        for item in os.listdir(diretorio):
            caminho_completo = os.path.join(diretorio, item)
            if os.path.isfile(caminho_completo):
                if not extensoes or os.path.splitext(item)[1].lower() in extensoes:
                    arquivos.append(item)
    except Exception as e:
        print(f"\n⚠️ Erro ao listar arquivos: {str(e)}")
    return sorted(arquivos)


# ================== FUNÇÕES DE CORREÇÃO DE TEXTO ==================


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
    texto = expandir_abreviacoes(texto)
    return texto


def verificar_e_corrigir_arquivo(caminho_txt: str) -> str:
    """
    Verifica se o arquivo TXT já foi processado (contém o sufixo '_formatado').
    Caso não, lê o arquivo, o processa e o salva com o sufixo, retornando o novo caminho.
    """
    base, ext = os.path.splitext(caminho_txt)
    if base.endswith("_formatado"):
        return caminho_txt
    try:
        with open(caminho_txt, "r", encoding="utf-8") as f:
            conteudo = f.read()
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo TXT: {e}")
        return caminho_txt
    conteudo_corrigido = melhorar_texto_corrigido(conteudo)
    novo_caminho = base + "_formatado" + ext
    try:
        with open(novo_caminho, "w", encoding="utf-8") as f:
            f.write(conteudo_corrigido)
        print(f"✅ Arquivo corrigido e salvo em: {novo_caminho}")
    except Exception as e:
        print(f"❌ Erro ao salvar o arquivo corrigido: {e}")
        return caminho_txt
    return novo_caminho


# ================== FUNÇÕES DE MELHORIA DE ÁUDIO ==================


def obter_duracao_ffprobe(caminho_arquivo):
    """Obtém a duração de um arquivo de mídia usando ffprobe."""
    comando = [
        FFPROBE_BIN,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        caminho_arquivo,
    ]
    resultado = subprocess.run(
        comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    return float(resultado.stdout.strip())


def acelerar_audio(input_path, output_path, velocidade):
    """Acelera um arquivo de áudio usando o filtro atempo do FFmpeg."""
    comando = [
        FFMPEG_BIN,
        "-y",
        "-i",
        input_path,
        "-filter:a",
        f"atempo={velocidade}",
        "-vn",
        output_path,
    ]
    subprocess.run(comando, check=True)


def criar_video_com_audio(audio_path, video_path, duracao):
    """Cria um vídeo com tela preta a partir de um arquivo de áudio."""
    comando = [
        FFMPEG_BIN,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=black:s=1280x720:d={int(duracao)}",
        "-i",
        audio_path,
        "-shortest",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-pix_fmt",
        "yuv420p",
        video_path,
    ]
    subprocess.run(comando, check=True)


def dividir_em_partes(
    input_path, duracao_total, duracao_maxima, nome_base_saida, extensao
):
    """Divide um arquivo de mídia em partes menores."""
    partes = ceil(duracao_total / duracao_maxima)
    for i in range(partes):
        inicio = i * duracao_maxima
        duracao = min(duracao_maxima, duracao_total - inicio)

        output_path = f"{nome_base_saida}_parte{i+1}{extensao}"

        comando = [
            FFMPEG_BIN,
            "-y",
            "-i",
            input_path,
            "-ss",
            str(int(inicio)),
            "-t",
            str(int(duracao)),
            "-c",
            "copy",
            output_path,
        ]
        subprocess.run(comando, check=True)
        print(f"    Parte {i+1} criada: {output_path}")


async def menu_melhorar_audio():
    """Menu para melhorar arquivos de áudio/vídeo existentes."""
    await exibir_banner()
    print("\n⚡ MELHORAR ÁUDIO EXISTENTE")

    dir_atual = os.path.join(os.path.expanduser("~"), "Desktop")

    while True:
        print(f"\nDiretório atual: {dir_atual}")
        print("\nArquivos de áudio/vídeo disponíveis:")
        arquivos = listar_arquivos(dir_atual, [".mp3", ".wav", ".m4a", ".mp4"])

        if not arquivos:
            print("\n⚠️ Nenhum arquivo de áudio/vídeo encontrado neste diretório")
        else:
            for i, arquivo in enumerate(arquivos, 1):
                print(f"{i}. {arquivo}")

        print("\nOpções:")
        print("D. Mudar diretório")
        print("M. Digitar caminho manualmente")
        print("V. Voltar ao menu principal")

        escolha = (await aioconsole.ainput("\nEscolha uma opção: ")).strip().upper()

        if escolha == "V":
            return
        elif escolha == "D":
            novo_dir = (
                await aioconsole.ainput("\nDigite o caminho do novo diretório: ")
            ).strip()
            if os.path.isdir(novo_dir):
                dir_atual = novo_dir
            else:
                print("\n❌ Diretório inválido")
                await asyncio.sleep(1)
        elif escolha == "M":
            caminho = (
                await aioconsole.ainput("\nDigite o caminho completo do arquivo: ")
            ).strip()
            if not os.path.exists(caminho):
                print(f"\n❌ Arquivo não encontrado: {caminho}")
                await asyncio.sleep(1)
                continue
            ext = os.path.splitext(caminho)[1].lower()
            if ext not in [".mp3", ".wav", ".m4a", ".mp4"]:
                print("\n❌ Formato não suportado. Use MP3, WAV, M4A ou MP4.")
                await asyncio.sleep(1)
                continue
            await processar_melhorar_audio(caminho)
            return
        elif escolha.isdigit():
            indice = int(escolha) - 1
            if 0 <= indice < len(arquivos):
                arquivo_selecionado = arquivos[indice]
                caminho_completo = os.path.join(dir_atual, arquivo_selecionado)
                await processar_melhorar_audio(caminho_completo)
                return
            else:
                print("\n❌ Opção inválida")
                await asyncio.sleep(1)
        else:
            print("\n❌ Opção inválida")
            await asyncio.sleep(1)


from pathlib import Path


async def processar_melhorar_audio(arquivo):
    """Processa a melhoria de um arquivo de áudio/vídeo."""
    global CANCELAR_PROCESSAMENTO
    CANCELAR_PROCESSAMENTO = False

    try:
        nome_base, ext = os.path.splitext(arquivo)
        ext = ext.lower()

        if ext not in [".mp3", ".wav", ".m4a", ".mp4"]:
            print(f"\n❌ Formato não suportado: {ext}")
            await asyncio.sleep(1)
            return

        # Configurações de velocidade
        while True:
            try:
                velocidade = float(
                    (
                        await aioconsole.ainput(
                            "\nInforme a velocidade de reprodução desejada (ex: 1.25, 1.5, 2.0): "
                        )
                    ).strip()
                )
                if not (0.5 <= velocidade <= 2.0):
                    raise ValueError
                break
            except ValueError:
                print("Valor inválido. Digite um número entre 0.5 e 2.0.")

        # Formato de saída
        while True:
            formato = (
                (
                    await aioconsole.ainput(
                        "\nEscolha o formato de saída [mp3 para áudio | mp4 para vídeo]: "
                    )
                )
                .strip()
                .lower()
            )
            if formato in ["mp3", "mp4"]:
                break
            else:
                print("Formato inválido. Digite 'mp3' ou 'mp4'.")

        # Normaliza nome de saída
        nome_saida_base = f"{nome_base}_x{velocidade}".replace(".", "_")
        nome_saida_base = re.sub(
            r"_+", "_", nome_saida_base
        )  # Remove underlines duplos

        # Cria diretório de saída, se necessário
        Path(os.path.dirname(nome_saida_base)).mkdir(parents=True, exist_ok=True)

        temp_audio = f"{nome_saida_base}_temp_audio.mp3"

        print(f"\n[+] Processando: {arquivo}")
        print(f"    Aumentando velocidade ({velocidade}x)...")

        acelerar_audio(arquivo, temp_audio, velocidade)
        duracao = obter_duracao_ffprobe(temp_audio)
        print(f"    Duração após aceleração: {duracao / 3600:.2f} horas")

        extensao_final = ".mp4" if formato == "mp4" else ".mp3"

        if duracao <= LIMITE_SEGUNDOS:
            saida_final = f"{nome_saida_base}{extensao_final}"
            if formato == "mp4":
                print("    Gerando vídeo com tela preta...")
                criar_video_com_audio(temp_audio, saida_final, duracao)
                os.remove(temp_audio)
            else:
                os.rename(temp_audio, saida_final)
            print(f"    Arquivo final salvo: {saida_final}")
        else:
            print("    Dividindo em partes de até 12 horas...")
            if formato == "mp4":
                video_completo = f"{nome_saida_base}_video.mp4"
                criar_video_com_audio(temp_audio, video_completo, duracao)
                dividir_em_partes(
                    video_completo, duracao, LIMITE_SEGUNDOS, nome_saida_base, ".mp4"
                )
                os.remove(video_completo)
            else:
                dividir_em_partes(
                    temp_audio, duracao, LIMITE_SEGUNDOS, nome_saida_base, ".mp3"
                )
            os.remove(temp_audio)
            print("    Arquivos divididos com sucesso.")

        await aioconsole.ainput("\nPressione ENTER para continuar...")

    except Exception as e:
        print(f"\n❌ Erro ao processar arquivo: {str(e)}")
        await aioconsole.ainput("\nPressione ENTER para continuar...")
    finally:
        CANCELAR_PROCESSAMENTO = True


# ================== FUNÇÕES DE LEITURA E PROCESSAMENTO DE ARQUIVOS ==================


def detectar_encoding(caminho_arquivo: str) -> str:
    """Detecta o encoding de um arquivo de texto."""
    try:
        with open(caminho_arquivo, "rb") as f:
            resultado = chardet.detect(f.read())
        encoding_detectado = resultado["encoding"]
        if not encoding_detectado:
            for enc in ENCODINGS_TENTATIVAS:
                try:
                    with open(caminho_arquivo, "r", encoding=enc) as f:
                        f.read(100)
                    return enc
                except UnicodeDecodeError:
                    continue
            return "utf-8"
        return encoding_detectado
    except Exception as e:
        print(f"\n⚠️ Erro ao detectar encoding: {str(e)}")
        return "utf-8"


def ler_arquivo_texto(caminho_arquivo: str) -> str:
    """Lê o conteúdo de um arquivo de texto com detecção automática de encoding."""
    encoding = detectar_encoding(caminho_arquivo)
    try:
        with open(caminho_arquivo, "r", encoding=encoding) as f:
            conteudo = f.read()
        return conteudo
    except Exception as e:
        print(f"\n❌ Erro ao ler arquivo: {str(e)}")
        return ""


def processar_texto(texto: str) -> str:
    """Processa o texto para melhorar a qualidade da conversão TTS."""
    # Remover caracteres não imprimíveis
    texto = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", texto)
    texto = texto.encode("utf-8", "ignore").decode("utf-8")

    texto = re.sub(r"\s+", " ", texto)
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


async def converter_texto_para_audio(texto: str, voz: str, caminho_saida: str) -> bool:
    """Converte texto para áudio usando Edge TTS."""
    tentativas = 0
    while tentativas < MAX_TENTATIVAS:
        try:
            if not texto.strip():
                print("⚠️ Texto vazio detectado")
                return False

            communicate = edge_tts.Communicate(texto, voz)
            await communicate.save(caminho_saida)

            # Verifica se o arquivo foi criado e tem tamanho mínimo
            if os.path.exists(caminho_saida) and os.path.getsize(caminho_saida) > 0:
                return True
            else:
                print("⚠️ Arquivo de áudio vazio ou muito pequeno")
                if os.path.exists(caminho_saida):
                    os.remove(caminho_saida)
                return False
        except Exception as e:
            tentativas += 1
            raise Exception(
                f"\n❌ Erro na conversão (tentativa {tentativas}/{MAX_TENTATIVAS}): {str(e)}"
            )
            
    return False


# ================== FUNÇÕES DE SELEÇÃO E CONVERSÃO DE ARQUIVOS ==================


async def selecionar_arquivo() -> str:
    """
    Interface aprimorada para seleção de arquivo com navegação por diretórios.
    Se o usuário selecionar um PDF, ele é convertido para TXT e o arquivo gerado é corrigido.
    Se for um arquivo TXT e o nome não contiver '_formatado', o arquivo é automaticamente corrigido.
    """

    dir_atual = os.path.join(
        os.path.expanduser("~"), "/workspaces/Conversor_TTS/assets"
    )
    
    while True:
        await exibir_banner()
        print("\n📂 SELEÇÃO DE ARQUIVO")
        print(f"\nDiretório atual: {dir_atual}")
        print("\nArquivos disponíveis:")
        arquivos = listar_arquivos(dir_atual, [".txt", ".pdf"])
        if not arquivos:
            print("\n⚠️ Nenhum arquivo TXT ou PDF encontrado neste diretório")
        else:
            for i, arquivo in enumerate(arquivos, 1):
                print(f"{i}. {arquivo}")
        print("\nOpções:")
        print("D. Mudar diretório")
        print("M. Digitar caminho manualmente")
        print("V. Voltar ao menu principal")
        try:
            escolha = (await aioconsole.ainput("\nEscolha uma opção: ")).strip().upper()
        except asyncio.TimeoutError:
            return ""

        if escolha == "V":
            return ""
        elif escolha == "D":
            novo_dir = (
                await aioconsole.ainput("\nDigite o caminho do novo diretório: ")
            ).strip()
            if os.path.isdir(novo_dir):
                dir_atual = novo_dir
            else:
                print("\n❌ Diretório inválido")
                await asyncio.sleep(1)
        elif escolha == "M":
            caminho = (
                await aioconsole.ainput("\nDigite o caminho completo do arquivo: ")
            ).strip()
            if not os.path.exists(caminho):
                print(f"\n❌ Arquivo não encontrado: {caminho}")
                await asyncio.sleep(1)
                continue
            ext = os.path.splitext(caminho)[1].lower()
            if ext == ".pdf":
                caminho_txt = os.path.splitext(caminho)[0] + ".txt"
                if not pdfCoverter.converter_pdf(caminho, caminho_txt):
                    print("\n⚠️ Falha na conversão do PDF. Tente outro arquivo.")
                    await asyncio.sleep(1)
                    continue
                # Após converter, verifica se o TXT já foi corrigido
                try:
                    with open(caminho_txt, "r", encoding="utf-8") as f:
                        texto_original = f.read()
                    texto_formatado = aplicar_formatacao(texto_original)
                    caminho_txt = os.path.splitext(caminho_txt)[0] + "_formatado.txt"
                    with open(caminho_txt, "w", encoding="utf-8") as f:
                        f.write(texto_formatado)
                    print(f"✅ Formatação aplicada e salva em: {caminho_txt}")
                except Exception as e:
                    print(f"❌ Erro ao aplicar formatação: {e}")
                caminho_txt = verificar_e_corrigir_arquivo(caminho_txt)
                editar = (
                    (
                        await aioconsole.ainput(
                            "\nDeseja editar o arquivo TXT corrigido? (s/n): "
                        )
                    )
                    .strip()
                    .lower()
                )
                if editar == "s":
                    if sistema["android"]:
                        print(
                            "\nO arquivo TXT corrigido foi salvo no diretório padrão (normalmente Download)."
                        )
                        print(
                            "Após editá-lo, reinicie a conversão selecionando-o neste script pela opção 1 do menu inicial."
                        )
                        await aioconsole.ainput(
                            "\nPressione ENTER para retornar ao menu principal..."
                        )
                        return ""
                    else:
                        if sistema["windows"]:
                            os.startfile(caminho_txt)
                        elif sistema["macos"]:
                            subprocess.Popen(["open", caminho_txt])
                        else:
                            subprocess.Popen(["xdg-open", caminho_txt])
                        await aioconsole.ainput(
                            "\nEdite o arquivo, salve as alterações e pressione ENTER para continuar..."
                        )
                return caminho_txt
            elif ext == ".txt":
                # Se o arquivo TXT não contém o sufixo _formatado, corrige-o automaticamente
                if not os.path.basename(caminho).lower().endswith("_formatado.txt"):
                    caminho = verificar_e_corrigir_arquivo(caminho)
                    try:
                        with open(caminho, "r", encoding="utf-8") as f:
                            texto_original = f.read()
                        texto_formatado = aplicar_formatacao(texto_original)
                        caminho_formatado = (
                            os.path.splitext(caminho)[0] + "_formatado.txt"
                        )
                        with open(caminho_formatado, "w", encoding="utf-8") as f:
                            f.write(texto_formatado)
                        print(
                            f"✅ Formatação aplicada ao TXT e salva em: {caminho_formatado}"
                        )
                        caminho = caminho_formatado
                    except Exception as e:
                        print(f"❌ Erro ao aplicar formatação ao TXT: {e}")
                return caminho
            else:
                print(f"\n❌ Formato não suportado: {ext}")
                print("💡 Apenas arquivos .txt e .pdf são suportados")
                await asyncio.sleep(1)
        elif escolha.isdigit():
            indice = int(escolha) - 1
            if 0 <= indice < len(arquivos):
                arquivo_selecionado = arquivos[indice]
                caminho_completo = os.path.join(dir_atual, arquivo_selecionado)
                ext = os.path.splitext(arquivo_selecionado)[1].lower()
                if ext == ".pdf":
                    caminho_txt = os.path.splitext(caminho_completo)[0] + ".txt"
                    if not pdfCoverter.converter_pdf(caminho_completo, caminho_txt):
                        print("\n⚠️ Falha na conversão do PDF. Tente outro arquivo.")
                        await asyncio.sleep(1)
                        continue
                    # Corrige o TXT gerado, se necessário
                    caminho_txt = verificar_e_corrigir_arquivo(caminho_txt)
                    editar = (
                        (
                            await aioconsole.ainput(
                                "\nDeseja editar o arquivo TXT corrigido? (s/n): "
                            )
                        )
                        .strip()
                        .lower()
                    )
                    if editar == "s":
                        if sistema["android"]:
                            print(
                                "\nO arquivo TXT corrigido foi salvo no diretório padrão (normalmente Download)."
                            )
                            print(
                                "Após editá-lo, reinicie a conversão selecionando-o neste script pela opção 1 do menu inicial."
                            )
                            await aioconsole.ainput(
                                "\nPressione ENTER para retornar ao menu principal..."
                            )
                            return ""
                        else:
                            if sistema["windows"]:
                                os.startfile(caminho_txt)
                            elif sistema["macos"]:
                                subprocess.Popen(["open", caminho_txt])
                            else:
                                subprocess.Popen(["xdg-open", caminho_txt])
                            await aioconsole.ainput(
                                "\nEdite o arquivo, salve as alterações e pressione ENTER para continuar..."
                            )
                    return caminho_txt
                elif ext == ".txt":
                    if (
                        not os.path.basename(caminho_completo)
                        .lower()
                        .endswith("_formatado.txt")
                    ):
                        caminho_completo = verificar_e_corrigir_arquivo(
                            caminho_completo
                        )
                    return caminho_completo
                else:
                    return caminho_completo
            else:
                print("\n❌ Opção inválida")
                await asyncio.sleep(1)
        else:
            print("\n❌ Opção inválida")
            await asyncio.sleep(1)


# ================== FUNÇÕES DE CONVERSÃO TTS ==================


async def iniciar_conversao() -> None:
    """
    Inicia o processo de conversão de texto para áudio de forma concorrente.
    O tamanho dos chunks é calculado dinamicamente.
    """
    global CANCELAR_PROCESSAMENTO
    CANCELAR_PROCESSAMENTO = False

    try:
        caminho_arquivo = await selecionar_arquivo()
        if not caminho_arquivo or CANCELAR_PROCESSAMENTO:
            return

        voz_escolhida = await menu_vozes()
        if voz_escolhida is None or CANCELAR_PROCESSAMENTO:
            return

        print("\n📖 Lendo arquivo...")
        texto = ler_arquivo_texto(caminho_arquivo)
        if not texto or CANCELAR_PROCESSAMENTO:
            print("\n❌ Arquivo vazio ou ilegível")
            await asyncio.sleep(2)
            return

        print("🔄 Processando texto...")
        texto_processado = processar_texto(texto)

        partes = dividir_texto(texto_processado)
        total_partes = len(partes)
        print(f"\n📊 Texto dividido em {total_partes} parte(s).")
        print("Para interromper a conversão a qualquer momento, pressione CTRL + C.\n")

        nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
        nome_base = limpar_nome_arquivo(nome_base)
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
                    sucesso = await converter_texto_para_audio(
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

            if unificar_audio(temp_files, arquivo_final):
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
                    await processar_melhorar_audio(arquivo_final)
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


async def main() -> None:
    """Função principal do programa."""

    while True:
        opcao = await menu_principal()
        if opcao == "1":
            await iniciar_conversao()
        elif opcao == "2":
            while True:
                voz_escolhida = await menu_vozes()
                if voz_escolhida is None:
                    break
                print(f"\n🎙️ Testando voz: {voz_escolhida}")
                await testar_voz(voz_escolhida)
        elif opcao == "3":
            await menu_melhorar_audio()
        elif opcao == "4":
            await exibir_ajuda()

        elif opcao == "6":
            print("\n👋 Obrigado por usar o Conversor TTS Completo!")
            break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Programa interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
