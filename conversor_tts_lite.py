import os
import sys
import subprocess

def verificar_sistema():
    print("\n🔍 Verificando ambiente de execução...")
    is_termux = 'TERMUX_VERSION' in os.environ
    if is_termux:
        print("✅ Executando no Termux")
        return True
    else:
        print("ℹ️ Executando em ambiente não-Termux")
        return False

def verificar_dependencias():
    print("\n🔍 Verificando dependências necessárias...")
    is_termux = verificar_sistema()
    
    # Pacotes específicos do Termux que precisam ser instalados
    if is_termux:
        termux_pkgs = ['python', 'python-pip', 'git']
        for pkg in termux_pkgs:
            try:
                subprocess.run(['pkg', 'list-installed', pkg], check=True, capture_output=True)
                print(f"✅ Pacote Termux {pkg} já está instalado")
            except subprocess.CalledProcessError:
                print(f"⚠️ Instalando pacote Termux {pkg}...")
                try:
                    subprocess.run(['pkg', 'install', '-y', pkg], check=True)
                    print(f"✅ Pacote Termux {pkg} instalado com sucesso!")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Erro ao instalar pacote Termux {pkg}: {e}")
                    sys.exit(1)
    
    # Dependências Python
    dependencias = {
        'edge-tts': 'edge-tts',
        'langdetect': 'langdetect',
        'unidecode': 'unidecode',
        'num2words': 'num2words'
    }

    for pacote, pip_nome in dependencias.items():
        try:
            __import__(pacote)
            print(f"✅ {pacote} já está instalado")
        except ImportError:
            print(f"\n⚠️ Instalando {pacote}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", pip_nome])
                print(f"✅ {pacote} instalado com sucesso!")
            except subprocess.CalledProcessError as e:
                print(f"❌ Erro ao instalar {pacote}: {e}")
                print(f"💡 Tente instalar manualmente com: pip install --user {pip_nome}")
                sys.exit(1)
            except Exception as e:
                print(f"❌ Erro inesperado ao instalar {pacote}: {e}")
                sys.exit(1)

# Verificar dependências antes de importar
verificar_dependencias()

# Importar módulos após verificação
import asyncio
import edge_tts
from pathlib import Path
import signal
from unidecode import unidecode
import re

# Try to import num2words, provide installation instructions if not found
try:
    from num2words import num2words
    print("✅ num2words importado com sucesso!")
except ImportError:
    print("\n❌ Erro ao importar num2words. Tente instalar manualmente:")
    print("pip install --user num2words")
    sys.exit(1)

# Try to import langdetect, provide installation instructions if not found
try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0  # Set seed for consistent language detection
    LANG_DETECT_AVAILABLE = True
except ImportError:
    print("\n⚠️ The langdetect module is not installed.")
    print("To install it, run: pip install langdetect")
    LANG_DETECT_AVAILABLE = False

# Global flag for interruption
interruption_requested = False

# Function to validate Brazilian Portuguese text
def validar_texto_pt_br(texto):
    try:
        # Skip empty text
        if not texto.strip():
            print("\n⚠️ Aviso: O texto está vazio!")
            return False

        # Check if language detection is available
        if LANG_DETECT_AVAILABLE:
            try:
                idioma = detect(texto)
                if idioma != 'pt':
                    print(f"\n⚠️ Aviso: O texto pode não estar em português (idioma detectado: {idioma})")
                    print("Deseja continuar mesmo assim?")
                    print("[1] Sim")
                    print("[2] Não")
                    while True:
                        escolha = input("\n🔹 Sua escolha: ").strip()
                        if escolha in ['1', '2']:
                            return escolha == '1'
                        print("⚠️ Opção inválida! Tente novamente.")
            except Exception as e:
                print(f"\n⚠️ Aviso: Não foi possível detectar o idioma automaticamente: {e}")
        else:
            print("\n⚠️ Aviso: A detecção de idioma não está disponível.")
            print("Deseja continuar mesmo assim?")
            print("[1] Sim")
            print("[2] Não")
            while True:
                escolha = input("\n🔹 Sua escolha: ").strip()
                if escolha in ['1', '2']:
                    return escolha == '1'
                print("⚠️ Opção inválida! Tente novamente.")
        return True

    except Exception as e:
        print(f"\n⚠️ Erro ao verificar texto: {e}")
        print("Deseja continuar mesmo assim?")
        print("[1] Sim")
        print("[2] Não")
        while True:
            escolha = input("\n🔹 Sua escolha: ").strip()
            if escolha in ['1', '2']:
                return escolha == '1'
            print("⚠️ Opção inválida! Tente novamente.")

# Try to import googletrans for English to Portuguese translation
try:
    from googletrans import Translator
    TRANSLATOR_AVAILABLE = True
    translator = Translator()
except ImportError:
    print("\n⚠️ O módulo googletrans não está instalado.")
    print("Para instalar, execute: pip install googletrans==3.1.0a0")
    TRANSLATOR_AVAILABLE = False

# Function to convert Roman numerals to decimal
def romano_para_decimal(romano):
    valores = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    decimal = 0
    prev_value = 0
    
    for char in reversed(romano.upper()):
        curr_value = valores.get(char, 0)
        if curr_value >= prev_value:
            decimal += curr_value
        else:
            decimal -= curr_value
        prev_value = curr_value
    return decimal

# Function to convert ordinal numbers to text
def converter_ordinal(match):
    numero = int(match.group(1))
    sufixo = match.group(2)
    if sufixo.lower() in ['º', 'ª']:
        try:
            return num2words(numero, lang='pt_BR', ordinal=True)
        except:
            return match.group(0)
    return match.group(0)

# Function to optimize text for TTS
def otimizar_texto_tts(texto):
    # Traduzir texto do inglês para português se disponível
    if TRANSLATOR_AVAILABLE:
        try:
            detected = translator.detect(texto)
            if detected.lang == 'en':
                texto = translator.translate(texto, dest='pt').text
                print("✅ Texto traduzido do inglês para português")
        except Exception as e:
            print(f"⚠️ Erro na tradução: {e}")
    
    # Converter algarismos romanos em capítulos e títulos
    texto = re.sub(r'(CAPÍTULO|Capítulo|TÍTULO|Título|Parte|PARTE|Livro|LIVRO)\s+([IVXLCDM]+)', 
                   lambda m: f"{m.group(1)} {romano_para_decimal(m.group(2))}", 
                   texto)
    
    # Converter números ordinais para texto (incluindo números maiores)
    texto = re.sub(r'(\d+)([ºª])', converter_ordinal, texto)
    
    # Converter números romanos isolados
    texto = re.sub(r'\b([IVXLCDM]+)\b', 
                   lambda m: str(romano_para_decimal(m.group(1))), 
                   texto)
    
    # Dicionário expandido de palavras problemáticas
    palavras_problematicas = {
        # Acentos e pronúncia
        'más': 'mas', 'pôr': 'por', 'têm': 'tem',
        'à': 'a', 'às': 'as', 'é': 'eh',
        'há': 'ha', 'através': 'atraves',
        'após': 'apos', 'até': 'ate',
        # Números por extenso para melhor pronúncia
        '1º': 'primeiro', '2º': 'segundo', '3º': 'terceiro',
        # Abreviações comuns
        'dr.': 'doutor', 'sr.': 'senhor', 'sra.': 'senhora',
        'prof.': 'professor', 'profa.': 'professora',
        # Símbolos especiais
        '%': ' porcento', '&': ' e ',
        '@': ' arroba ', '#': ' hashtag ',
        # Melhorias de pronúncia
        'pra': 'para', 'pro': 'para o',
        'vc': 'você', 'tb': 'também',
        'q': 'que', 'td': 'tudo'
    }
    
    # Otimizar texto para melhor pronúncia
    texto = texto.lower()  # Converter para minúsculas para melhor correspondência
    
    # Substituir palavras problemáticas
    for original, corrigida in palavras_problematicas.items():
        # Usar regex para substituir palavras completas apenas
        texto = re.sub(f'\\b{original}\\b', corrigida, texto, flags=re.IGNORECASE)
    
    # Tratar números
    texto = re.sub(r'\d+', lambda m: num2words(int(m.group()), lang='pt_BR'), texto)
    
    # Melhorar pausas em pontuação
    sinais_pontuacao = {
        '.': '. ',   # Pausa longa
        ',': ', ',   # Pausa curta
        ';': '; ',   # Pausa média
        ':': ': ',   # Pausa média
        '!': '! ',   # Ênfase
        '?': '? ',   # Entonação de pergunta
        '...': '... ' # Pausa de reticências
    }
    
    # Aplicar pausas de pontuação
    for sinal, substituicao in sinais_pontuacao.items():
        texto = texto.replace(sinal, substituicao)
    
    # Tratar reticências
    texto = re.sub(r'\.{3,}', '... ', texto)
    
    # Remover espaços múltiplos e espaços antes de pontuação
    texto = re.sub(r'\s+', ' ', texto)  # Remover espaços múltiplos
    texto = re.sub(r'\s+([.,!?;:])', r'\1', texto)  # Remover espaços antes de pontuação
    
    # Garantir espaço após pontuação
    texto = re.sub(r'([.,!?;:])(?=\S)', r'\1 ', texto)
    
    return texto.strip()

# Function to handle SIGINT (Ctrl+C)
def signal_handler(signum, frame):
    global interruption_requested
    interruption_requested = True
    print("\n\n🛑 Pressione Ctrl+C novamente para interromper a conversão...")

# Set up signal handler
signal.signal(signal.SIGINT, signal_handler)

# Function to handle interrupted conversion
async def handle_interruption(temp_files, arquivo_saida):
    print("\n\n🛑 Conversão interrompida!")
    print("\nEscolha uma opção:")
    print("[1] Manter arquivos parciais separados")
    print("[2] Unificar arquivos convertidos")
    print("[3] Excluir arquivos convertidos")
    
    while True:
        escolha = input("\n🔹 Sua escolha: ").strip()
        if escolha in ['1', '2', '3']:
            break
        print("⚠️ Opção inválida! Tente novamente.")
    
    if escolha == '1':
        print("\n✅ Arquivos parciais mantidos separadamente.")
    
    elif escolha == '2':
        print("\n🔄 Unificando arquivos convertidos...")
        try:
            with open(arquivo_saida, 'wb') as outfile:
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        with open(temp_file, 'rb') as infile:
                            outfile.write(infile.read())
                        os.remove(temp_file)
            print("✅ Arquivos unificados com sucesso!")
        except Exception as e:
            print(f"⚠️ Erro ao unificar arquivos: {e}")
    
    else:  # escolha == '3'
        print("\n🗑️ Excluindo arquivos convertidos...")
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"⚠️ Erro ao excluir {temp_file}: {e}")
        print("✅ Arquivos excluídos com sucesso!")
    
    # Ask about keeping progress tracking
    progresso_file = f"{arquivo_saida}.progress"
    if os.path.exists(progresso_file):
        print("\n💾 Deseja manter o registro de progresso para continuar a conversão posteriormente?")
        print("[1] Sim, manter registro de progresso")
        print("[2] Não, apagar registro de progresso")
        
        while True:
            escolha_progresso = input("\n🔹 Sua escolha: ").strip()
            if escolha_progresso in ['1', '2']:
                break
            print("⚠️ Opção inválida! Tente novamente.")
        
        if escolha_progresso == '2':
            try:
                os.remove(progresso_file)
                print("✅ Registro de progresso apagado com sucesso!")
            except Exception as e:
                print(f"⚠️ Erro ao apagar registro de progresso: {e}")
        else:
            print("✅ Registro de progresso mantido para continuação posterior.")
    
    limpar_tela()
    return False

# =============================================================================
# Configurações e Constantes
# =============================================================================
VOZES_PT_BR = [
    "pt-BR-ThalitaMultilingualNeural",  # Voz padrão
    "pt-BR-FranciscaNeural",
    "pt-BR-AntonioNeural"
]

# =============================================================================
# Funções Utilitárias
# =============================================================================
def limpar_tela():
    os.system("clear" if os.name == "posix" else "cls")

def exibir_menu():
    print("\n" + "="*60)
    print("""
    ████████╗████████╗███████╗
    ╚══██╔══╝╚══██╔══╝██╔════╝
       ██║      ██║   ███████╗
       ██║      ██║   ╚════██║
       ██║      ██║   ███████║
       ╚═╝      ╚═╝   ╚══════╝
    """)
    print("="*60)
    print("\n\033[1;36;1m🎯 MENU PRINCIPAL\033[0m")
    print("-"*50)
    print("\n\033[1;32;1m[1] 🚀 INICIAR\033[0m")
    print("\033[1;34;1m[2] 🎙️ VOZES\033[0m")
    print("\033[1;33;1m[3] ❓ AJUDA\033[0m")
    print("\033[1;31;1m[4] 🚪 SAIR\033[0m")
    print("-"*50)
    while True:
        escolha = input("\n\033[1;36;1m🔹 Escolha: \033[0m").strip()
        if escolha in ['1', '2', '3', '4']:
            return escolha
        print("\033[1;31;1m⚠️ Opção inválida!\033[0m")

def escolher_voz():
    print("\n\033[1;36;1m🎙️ ESCOLHA A VOZ PARA A CONVERSÃO\033[0m")
    print("\n\033[1;33;1m⭐ A voz padrão é 'Thalita' - otimizada para múltiplos idiomas\033[0m")
    for i, voz in enumerate(VOZES_PT_BR, start=1):
        if i == 1:
            print(f"\033[1;32;1m  [{i}] {voz}  (Voz padrão)\033[0m")
        else:
            print(f"\033[1;34;1m  [{i}] {voz}\033[0m")

    while True:
        escolha = input("\n\033[1;36;1m🔹 Digite o número da voz desejada: \033[0m").strip()
        if escolha.isdigit() and 1 <= int(escolha) <= len(VOZES_PT_BR):
            return VOZES_PT_BR[int(escolha) - 1]
        print("\033[1;31;1m⚠️ Opção inválida! Escolha um número da lista.\033[0m")

def exibir_ajuda():
    print("\n" + "-"*50)
    print("\033[1;36;1m📚 GUIA DO CONVERSOR TTS\033[0m")
    print("-"*50)
    print("\n\033[1;33;1m1️⃣ PREPARAÇÃO\033[0m")
    print("\033[1;37;1m• Salve texto em .txt\033[0m")
    print("\033[1;37;1m• Coloque na Downloads\033[0m")
    
    print("\n\033[1;33;1m2️⃣ CONVERSÃO\033[0m")
    print("\033[1;37;1m• Selecione 'Iniciar'\033[0m")
    print("\033[1;37;1m• Escolha o arquivo\033[0m")
    print("\033[1;37;1m• Selecione a voz\033[0m")
    
    print("\n\033[1;33;1m3️⃣ RECURSOS\033[0m")
    print("\033[1;37;1m• Números para texto\033[0m")
    print("\033[1;37;1m• Otimização PT-BR\033[0m")
    print("\033[1;37;1m• Textos longos\033[0m")
    print("\033[1;37;1m• Detecção de idioma\033[0m")
    
    print("\n\033[1;33;1m4️⃣ DICAS\033[0m")
    print("\033[1;37;1m• Teste as vozes\033[0m")
    print("\033[1;37;1m• Use Ctrl+C p/ parar\033[0m")
    print("\033[1;37;1m• Áudio na Downloads\033[0m")
    
    print("\n\033[1;33;1m5️⃣ FORMATOS\033[0m")
    print("\033[1;37;1m• Números ordinais\033[0m")
    print("\033[1;37;1m• Números romanos\033[0m")
    print("\033[1;37;1m• Abreviações\033[0m")
    print("\033[1;37;1m• Símbolos especiais\033[0m")
    
    input("\n\033[1;36;1m🔹 Pressione Enter para voltar...\033[0m")
    limpar_tela()

def escolher_voz():
    print("\n" + "-"*50)
    print("\033[1;36;1m🎙️ ESCOLHA A VOZ PARA A CONVERSÃO\033[0m")
    print("\n\033[1;33;1m⭐ A voz padrão é 'Thalita' - otimizada para múltiplos idiomas\033[0m")
    for i, voz in enumerate(VOZES_PT_BR, start=1):
        if i == 1:
            print(f"\033[1;32;1m  [{i}] {voz}  (Voz padrão)\033[0m")
        else:
            print(f"\033[1;34;1m  [{i}] {voz}\033[0m")

    while True:
        escolha = input("\n\033[1;36;1m🔹 Digite o número da voz desejada: \033[0m").strip()
        if escolha.isdigit() and 1 <= int(escolha) <= len(VOZES_PT_BR):
            return VOZES_PT_BR[int(escolha) - 1]
        print("\033[1;31;1m⚠️ Opção inválida! Escolha um número da lista.\033[0m")

# =============================================================================
# Funções de Processamento
# =============================================================================
def ler_arquivo(caminho):
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"⚠️ Erro ao ler arquivo: {e}")
        return None

async def processar_audio(texto, arquivo_saida, voz, chunk_size=2000):
    try:
        # Initialize temp_files list at the beginning of the function
        temp_files = []
        # Get first line for file naming
        primeira_linha = texto.strip().split('\n')[0].strip()
        if primeira_linha:
            nome_base = Path(arquivo_saida).parent / primeira_linha
            arquivo_saida = f"{nome_base}.mp3"

        # Ask for file unification preference
        print("\n📦 Preferência de arquivos:")
        print("[Enter/N] Unificar arquivos e excluir partes (padrão)")
        print("[S] Manter arquivos separados")
        escolha = input("\n🔹 Sua escolha: ").strip().upper()
        manter_separado = escolha == 'S'

        # Validate text language
        if not validar_texto_pt_br(texto):
            print("\n🛑 Conversão cancelada pelo usuário.")
            return False

        # Optimize text for better pronunciation
        texto = otimizar_texto_tts(texto)

        # Reset interruption flag
        global interruption_requested
        interruption_requested = False

        # Otimizar o tamanho dos chunks e buffer para melhor performance
        chunk_size = max(2000, min(len(texto) // 10, 5000))  # Chunks adaptativos
        partes = [texto[i:i+chunk_size] for i in range(0, len(texto), chunk_size)]
        total_partes = len(partes)
        temp_files = []
        buffer_size = 32768  # Buffer maior para I/O mais eficiente

        print(f"\n🔄 Processando {total_partes} partes...")
        print("\nPressione Ctrl+C para interromper a conversão a qualquer momento.")

        # Carregar progresso anterior se existir
        progresso_file = f"{arquivo_saida}.progress"
        ultima_parte = 0
        if os.path.exists(progresso_file):
            try:
                with open(progresso_file, 'r') as f:
                    ultima_parte = int(f.read().strip())
                print(f"\n📝 Retomando da parte {ultima_parte + 1}")
            except:
                ultima_parte = 0

        for i, parte in enumerate(partes[ultima_parte:], ultima_parte + 1):
            if interruption_requested:
                # Salvar progresso antes de interromper
                with open(progresso_file, 'w') as f:
                    f.write(str(i - 1))
                await handle_interruption(temp_files, arquivo_saida)
                limpar_tela()
                return False

            print(f"\r📊 Progresso: {i}/{total_partes} ({int(i/total_partes*100)}%)" + "="*(i*20//total_partes) + ">", end="")
            
            # Processar texto em lotes para reduzir chamadas à API
            max_tentativas = 5
            tentativa = 0
            while tentativa < max_tentativas:
                try:
                    communicate = edge_tts.Communicate(parte.strip(), voz)
                    arquivo_temp = f"{arquivo_saida}.part{i:03d}.mp3"
                    await communicate.save(arquivo_temp)
                    temp_files.append(arquivo_temp)
                    # Salvar progresso após sucesso
                    with open(progresso_file, 'w') as f:
                        f.write(str(i))
                    break
                except Exception as e:
                    tentativa += 1
                    if tentativa < max_tentativas:
                        tempo_espera = 2 ** tentativa  # Backoff exponencial
                        print(f"\n⚠️ Erro ao processar parte {i}. Tentativa {tentativa}/{max_tentativas}. Aguardando {tempo_espera}s...")
                        await asyncio.sleep(tempo_espera)
                    else:
                        print(f"\n⚠️ Erro ao processar parte {i} após {max_tentativas} tentativas: {e}")
                        continue

        # Handle files based on user preference
        if not interruption_requested:
            if not manter_separado:
                print("\n📦 Combinando arquivos...")
                # Otimizar a combinação dos arquivos com buffer maior e verificação de memória
                with open(arquivo_saida, 'wb') as outfile:
                    for temp_file in temp_files:
                        if not os.path.exists(temp_file):
                            continue
                        try:
                            with open(temp_file, 'rb') as infile:
                                while True:
                                    chunk = infile.read(buffer_size)
                                    if not chunk:
                                        break
                                    outfile.write(chunk)
                                    outfile.flush()  # Garantir que os dados sejam escritos
                            # Close the file before attempting to remove it
                            infile.close()
                            if os.path.exists(temp_file):
                                try:
                                    os.remove(temp_file)  # Remover arquivo temporário após uso
                                    print(f"\r🗑️ Arquivo temporário removido: {temp_file}", end="")
                                except Exception as e:
                                    print(f"\n⚠️ Erro ao excluir arquivo temporário {temp_file}: {e}")
                        except Exception as e:
                            print(f"\n⚠️ Erro ao processar arquivo temporário {temp_file}: {e}")
                            continue
                # Remover arquivo de progresso após conclusão
                if os.path.exists(progresso_file):
                    try:
                        os.remove(progresso_file)
                    except Exception as e:
                        print(f"\n⚠️ Erro ao excluir arquivo de progresso: {e}")
                print("\n✅ Conversão concluída! Arquivo unificado criado.")
            else:
                print("\n✅ Conversão concluída! Arquivos mantidos separados.")
            return True

    except Exception as e:
        print(f"\n⚠️ Erro durante o processamento: {e}")
        # Limpar arquivos temporários em caso de erro
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        return False

# =============================================================================
# Funções Principais
# =============================================================================
async def converter_audio():
    limpar_tela()
    print("\n📖 Conversor de Texto para Fala - Modo Leve\n")

    # Diretório padrão para arquivos TXT no Android
    diretorio_padrao = "/storage/emulated/0/Download"
    if not os.path.exists(diretorio_padrao):
        diretorio_padrao = os.path.expanduser("~/storage/downloads")  # Fallback para Termux
        if not os.path.exists(diretorio_padrao):
            diretorio_padrao = os.path.expanduser("~")  # Último fallback

    try:
        # Verificar se o diretório existe e tem permissão de acesso
        if not os.path.exists(diretorio_padrao):
            print(f"⚠️ Diretório não encontrado: {diretorio_padrao}")
            print("ℹ️ Dica: Verifique se o Termux tem permissão de acesso ao armazenamento.")
            print("   Execute: termux-setup-storage")
            return

        # Listar arquivos TXT no diretório
        arquivos_txt = [f for f in os.listdir(diretorio_padrao) if f.endswith('.txt')]

        if not arquivos_txt:
            print("⚠️ Nenhum arquivo TXT encontrado no diretório de downloads!")
            return

        # Exibir lista de arquivos disponíveis
        print("📄 Arquivos TXT disponíveis:")
        for i, arquivo in enumerate(arquivos_txt, 1):
            print(f"[{i}] {arquivo}")

        # Selecionar arquivo
        while True:
            escolha = input("\n🔹 Digite o número do arquivo desejado: ").strip()
            if escolha.isdigit() and 1 <= int(escolha) <= len(arquivos_txt):
                arquivo_selecionado = arquivos_txt[int(escolha) - 1]
                break
            print("⚠️ Opção inválida! Escolha um número da lista.")

        caminho_completo = os.path.join(diretorio_padrao, arquivo_selecionado)
        print(f"\n📄 Lendo arquivo: {arquivo_selecionado}")
        texto = ler_arquivo(caminho_completo)
        if not texto:
            return

        voz = escolher_voz()
        nome_base = Path(caminho_completo).stem
        diretorio_saida = os.path.join(diretorio_padrao, f"{nome_base}_audio")
        os.makedirs(diretorio_saida, exist_ok=True)

        arquivo_saida = os.path.join(diretorio_saida, f"{nome_base}.mp3")
        await processar_audio(texto, arquivo_saida, voz)
        print(f"\n📂 Arquivos salvos em: {diretorio_saida}")

    except Exception as e:
        print(f"\n⚠️ Erro: {e}")

    input("\n🔹 Pressione Enter para voltar ao menu...")
    limpar_tela()

async def testar_vozes():
    limpar_tela()
    print("\n🔊 Gerando arquivos de teste para cada voz...\n")

    diretorio_testes = "vozes_teste"
    os.makedirs(diretorio_testes, exist_ok=True)

    texto_teste = "Este é um teste da voz para conversão de texto em fala."
    for voz in VOZES_PT_BR:
        print(f"\n🎙️ Testando voz: {voz}")
        arquivo_mp3 = os.path.join(diretorio_testes, f"{voz}.mp3")
        communicate = edge_tts.Communicate(texto_teste, voz)
        await communicate.save(arquivo_mp3)
        print(f"✅ Arquivo salvo: {arquivo_mp3}")

    print("\n✅ Testes concluídos!")
    print(f"📂 Arquivos salvos em: {diretorio_testes}")
    input("\n🔹 Pressione Enter para voltar ao menu...")
    limpar_tela()

# =============================================================================
# Função Principal
# =============================================================================
async def main():
    while True:
        escolha = exibir_menu()
        if escolha == '1':
            await converter_audio()
        elif escolha == '2':
            await testar_vozes()
        elif escolha == '3':
            exibir_ajuda()
        else:  # escolha == '4'
            print("\n👋 Obrigado por usar o Conversor TTS Lite!")
            break

if __name__ == '__main__':
    asyncio.run(main())