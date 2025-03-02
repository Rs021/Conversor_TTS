#!/usr/bin/env python3
import os
import sys
import subprocess
import asyncio
import re
import signal
from pathlib import Path
import select
import platform
import zipfile
import shutil
import time

# Tenta importar o tqdm; se não encontrar, instala-o e adiciona o diretório do usuário ao sys.path
try:
    from tqdm import tqdm
except ModuleNotFoundError:
    print("⚠️ Módulo 'tqdm' não encontrado. Instalando...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "tqdm"])
    try:
        import site
        site.addsitedir(site.getusersitepackages())
    except Exception as e:
        print(f"❌ Erro ao adicionar o diretório de pacotes do usuário: {e}")
    from tqdm import tqdm  # Mesmo que a barra não seja usada, mantemos a instalação

# Garantindo o módulo requests
try:
    import requests
except ModuleNotFoundError:
    print("⚠️ Módulo 'requests' não encontrado. Instalando...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "requests"])
    import requests

# Vozes disponíveis para conversão
VOZES_PT_BR = [
    "pt-BR-ThalitaMultilingualNeural",  # Voz padrão
    "pt-BR-FranciscaNeural",
    "pt-BR-AntonioNeural"
]

ENCODINGS_TENTATIVAS = ['utf-8', 'utf-16', 'iso-8859-1', 'cp1252']
BUFFER_IO = 32768

interrupcao_requisitada = False

def detectar_sistema():
    """Detecta o sistema operacional e ambiente de execução."""
    sistema = {
        'nome': platform.system().lower(),
        'termux': False,
        'android': False,
        'windows': False,
        'linux': False,
        'macos': False,
    }
    if sistema['nome'] == 'windows':
        sistema['windows'] = True
        return sistema
    if sistema['nome'] == 'darwin':
        sistema['macos'] = True
        return sistema
    if sistema['nome'] == 'linux':
        sistema['linux'] = True
        is_android = any([
            'ANDROID_ROOT' in os.environ,
            'TERMUX_VERSION' in os.environ,
            os.path.exists('/data/data/com.termux'),
            os.path.exists('/system/bin/linker64')
        ])
        if is_android:
            sistema['android'] = True
            if any([
                'TERMUX_VERSION' in os.environ,
                os.path.exists('/data/data/com.termux')
            ]):
                sistema['termux'] = True
                os.environ['PATH'] = f"{os.environ.get('PATH', '')}:/data/data/com.termux/files/usr/bin"
    return sistema

def instalar_poppler_windows():
    """Instala o Poppler no Windows automaticamente."""
    try:
        poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v23.11.0-0/Release-23.11.0-0.zip"
        install_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Poppler')
        os.makedirs(install_dir, exist_ok=True)
        print("📥 Baixando Poppler...")
        response = requests.get(poppler_url)
        zip_path = os.path.join(install_dir, "poppler.zip")
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        print("📦 Extraindo arquivos...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(install_dir)
        os.remove(zip_path)
        bin_paths = [
            os.path.join(install_dir, 'bin'),
            os.path.join(install_dir, 'Library', 'bin'),
            os.path.join(install_dir, 'poppler-23.11.0', 'bin'),
            os.path.join(install_dir, 'Release-23.11.0-0', 'bin')
        ]
        bin_path = None
        for path in bin_paths:
            if os.path.exists(path) and any(f.endswith('.exe') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))):
                bin_path = path
                break
        if not bin_path:
            for root, dirs, files in os.walk(install_dir):
                if 'bin' in dirs and any(f.endswith('.exe') for f in os.listdir(os.path.join(root, 'bin')) if os.path.isfile(os.path.join(root, 'bin', f))):
                    bin_path = os.path.join(root, 'bin')
                    break
        if not bin_path:
            print(f"❌ Erro: Diretório bin não encontrado em {install_dir}")
            return False
        print(f"✅ Diretório bin encontrado em: {bin_path}")
        pdftotext_path = os.path.join(bin_path, 'pdftotext.exe')
        if not os.path.exists(pdftotext_path):
            print(f"❌ Erro: pdftotext.exe não encontrado em {bin_path}")
            return False
        if bin_path not in os.environ['PATH']:
            os.environ['PATH'] = f"{bin_path};{os.environ['PATH']}"
        try:
            subprocess.run([pdftotext_path, "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print("✅ Poppler instalado com sucesso!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao verificar pdftotext: {e}")
            return False
    except Exception as e:
        print(f"❌ Erro ao instalar Poppler: {str(e)}")
        return False

def converter_pdf(caminho_pdf: str, caminho_txt: str) -> bool:
    """Converte PDF para TXT utilizando o comando pdftotext."""
    try:
        caminho_pdf = os.path.abspath(caminho_pdf)
        if not os.path.isfile(caminho_pdf):
            print(f"❌ Arquivo PDF não encontrado: {caminho_pdf}")
            return False
        with open(caminho_pdf, 'rb') as _:
            pass
    except PermissionError:
        print(f"❌ Sem permissão para acessar o arquivo: {caminho_pdf}")
        return False
    except Exception as e:
        print(f"❌ Erro ao acessar o arquivo PDF: {str(e)}")
        return False
    diretorio_saida = os.path.dirname(caminho_txt)
    if diretorio_saida and not os.path.exists(diretorio_saida):
        try:
            os.makedirs(diretorio_saida, exist_ok=True)
            print(f"✅ Diretório de saída criado: {diretorio_saida}")
        except Exception as e:
            print(f"❌ Erro ao criar diretório de saída: {str(e)}")
            return False
    sistema = detectar_sistema()
    if sistema['windows']:
        pdftotext_path = None
        for path in os.environ['PATH'].split(';'):
            if not path.strip():
                continue
            test_path = os.path.join(path.strip(), 'pdftotext.exe')
            if os.path.exists(test_path) and os.path.isfile(test_path):
                pdftotext_path = test_path
                break
        if not pdftotext_path:
            print("📦 Poppler não encontrado. Iniciando instalação automática...")
            if not instalar_poppler_windows():
                return False
            for path in os.environ['PATH'].split(';'):
                if not path.strip():
                    continue
                test_path = os.path.join(path.strip(), 'pdftotext.exe')
                if os.path.exists(test_path) and os.path.isfile(test_path):
                    pdftotext_path = test_path
                    break
            if not pdftotext_path:
                print("❌ Não foi possível encontrar o pdftotext mesmo após a instalação")
                return False
    else:
        try:
            subprocess.run(["pdftotext", "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except FileNotFoundError:
            if sistema['macos']:
                print("❌ O pdftotext não está instalado no sistema. Instale com: brew install poppler")
                return False
            elif sistema['linux']:
                if sistema['termux']:
                    print("❌ O pdftotext não está instalado no sistema. Tentando instalar automaticamente com: pkg install poppler")
                    if instalar_poppler():
                        print("✅ Poppler instalado com sucesso! Execute novamente a conversão.")
                    else:
                        print("❌ Falha ao instalar poppler automaticamente.")
                    return False
                else:
                    print("❌ O pdftotext não está instalado no sistema. Instale com: sudo apt-get install poppler-utils")
                    return False
    if sistema['windows'] and pdftotext_path:
        resultado = subprocess.run(
            [pdftotext_path, "-layout", caminho_pdf, caminho_txt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    else:
        resultado = subprocess.run(
            ["pdftotext", "-layout", caminho_pdf, caminho_txt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    if resultado.returncode != 0:
        print(f"❌ Erro ao converter o PDF: {resultado.stderr.decode()}")
        return False
    return True

def verificar_sistema() -> dict:
    """Verifica o sistema operacional e retorna informações sobre ele."""
    print("\n🔍 Verificando ambiente de execução...")
    sistema = detectar_sistema()
    if sistema['termux']:
        print("✅ Executando no Termux (Android)")
    elif sistema['android']:
        print("✅ Executando no Android (não-Termux)")
    elif sistema['windows']:
        print("✅ Executando no Windows")
    elif sistema['macos']:
        print("✅ Executando no macOS")
    elif sistema['linux']:
        print("✅ Executando no Linux")
    else:
        print("⚠️ Sistema operacional não identificado com precisão")
    return sistema

def instalar_dependencia_termux(pkg: str) -> None:
    """Verifica e instala um pacote do Termux, se necessário."""
    try:
        subprocess.run(['pkg', 'update', '-y'], check=True, capture_output=True)
        resultado = subprocess.run(['pkg', 'list-installed', pkg], capture_output=True, text=True)
        if pkg in resultado.stdout:
            print(f"✅ Pacote Termux {pkg} já está instalado")
            return
        print(f"⚠️ Instalando pacote Termux {pkg}...")
        subprocess.run(['pkg', 'install', '-y', pkg], check=True)
        print(f"✅ Pacote Termux {pkg} instalado com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar pacote Termux {pkg}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado ao instalar {pkg}: {e}")
        sys.exit(1)

def instalar_dependencia_python(nome_pkg: str, pip_nome: str) -> None:
    """Verifica e instala uma dependência Python, se necessária."""
    try:
        __import__(nome_pkg)
        print(f"✅ Módulo Python {nome_pkg} já está instalado")
    except ImportError:
        print(f"⚠️ Instalando módulo Python {nome_pkg}...")
        sistema = detectar_sistema()
        pip_cmd = [sys.executable, "-m", "pip", "install", pip_nome]
        if not sistema['termux']:
            pip_cmd.append("--user")
        try:
            subprocess.run(pip_cmd, check=True)
            print(f"✅ Módulo Python {nome_pkg} instalado com sucesso!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar módulo Python {nome_pkg}: {e}")
            sys.exit(1)

def instalar_poppler() -> bool:
    """Instala o pacote poppler (pdftotext) de acordo com o sistema operacional."""
    sistema = detectar_sistema()
    print("⚠️ O pdftotext não está instalado. Tentando instalar automaticamente...")
    try:
        if sistema['termux']:
            subprocess.run(['pkg', 'install', '-y', 'poppler'], check=True)
            print("✅ poppler instalado com sucesso no Termux!")
            return True
        elif sistema['linux']:
            print("⚠️ Instalando poppler-utils no Linux...")
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'poppler-utils'], check=True)
            print("✅ poppler-utils instalado com sucesso no Linux!")
            return True
        elif sistema['macos']:
            print("⚠️ Instalando poppler no macOS via Homebrew...")
            try:
                subprocess.run(['brew', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except FileNotFoundError:
                print("❌ Homebrew não está instalado no macOS. Instale-o e depois execute: brew install poppler")
                return False
            subprocess.run(['brew', 'install', 'poppler'], check=True)
            print("✅ poppler instalado com sucesso no macOS!")
            return True
        elif sistema['windows']:
            print("⚠️ Instalando Poppler no Windows...")
            import tempfile
            import urllib.request
            import winreg
            poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v23.11.0-0/Release-23.11.0-0.zip"
            try:
                temp_dir = tempfile.mkdtemp()
                zip_path = os.path.join(temp_dir, "poppler.zip")
                print("📥 Baixando Poppler...")
                urllib.request.urlretrieve(poppler_url, zip_path)
                program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
                poppler_dir = os.path.join(program_files, "Poppler")
                os.makedirs(poppler_dir, exist_ok=True)
                print("📦 Extraindo arquivos...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    root_dirs = {item.split('/')[0] for item in zip_ref.namelist() if '/' in item}
                    if len(root_dirs) == 1:
                        root_dir = root_dirs.pop()
                        zip_ref.extractall(temp_dir)
                        extracted_dir = os.path.join(temp_dir, root_dir)
                        for item in os.listdir(extracted_dir):
                            src = os.path.join(extracted_dir, item)
                            dst = os.path.join(poppler_dir, item)
                            if os.path.exists(dst):
                                if os.path.isdir(dst):
                                    shutil.rmtree(dst)
                                else:
                                    os.remove(dst)
                            shutil.move(src, dst)
                    else:
                        zip_ref.extractall(poppler_dir)
                print("🔧 Adicionando ao PATH do sistema...")
                bin_dir = os.path.join(poppler_dir, "bin")
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
                    try:
                        path, _ = winreg.QueryValueEx(key, "PATH")
                        if bin_dir.lower() not in path.lower():
                            new_path = path + ";" + bin_dir
                            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                            subprocess.run(["setx", "PATH", new_path], check=True, capture_output=True)
                    except FileNotFoundError:
                        winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, bin_dir)
                    finally:
                        winreg.CloseKey(key)
                except Exception as e:
                    print(f"⚠️ Erro ao atualizar o PATH no Windows: {e}")
                os.environ["PATH"] = bin_dir + ";" + os.environ.get("PATH", "")
                shutil.rmtree(temp_dir, ignore_errors=True)
                print("✅ Poppler instalado com sucesso no Windows!")
                print("⚠️ Você pode precisar reiniciar o terminal para que as alterações no PATH tenham efeito.")
                try:
                    subprocess.run([os.path.join(bin_dir, "pdftotext"), "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("⚠️ Poppler foi instalado, mas o pdftotext ainda não está disponível.")
                    return False
            except Exception as e:
                print(f"❌ Erro durante a instalação automática do Poppler: {str(e)}")
                return False
        else:
            print("❌ Sistema operacional não suportado para instalação automática.")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar poppler: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado ao instalar poppler: {e}")
        return False

def verificar_dependencias() -> None:
    """Verifica e instala as dependências necessárias para o sistema atual."""
    sistema = verificar_sistema()
    if sistema['termux']:
        pacotes_termux = ['python', 'python-pip', 'git', 'poppler', 'termux-api']
        for pkg in pacotes_termux:
            instalar_dependencia_termux(pkg)
    dependencias_python = {
        'edge_tts': 'edge-tts>=6.1.5',
        'langdetect': 'langdetect>=1.0.9',
        'unidecode': 'unidecode>=1.3.6',
        'num2words': 'num2words>=0.5.12',
        'chardet': 'chardet>=5.0.0',
        'requests': 'requests>=2.31.0',
    }
    for nome_pkg, pip_nome in dependencias_python.items():
        instalar_dependencia_python(nome_pkg, pip_nome)
    try:
        subprocess.run(['pdftotext', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ pdftotext (poppler) está funcionando corretamente")
    except FileNotFoundError:
        sistema = detectar_sistema()
        if sistema['windows']:
            print("📦 Poppler não encontrado. Iniciando instalação automática...")
            if not instalar_poppler_windows():
                print("❌ Não foi possível instalar o pdftotext automaticamente.")
        elif sistema['macos']:
            print("❌ O pdftotext não está instalado no sistema. Instale com: brew install poppler")
        elif sistema['termux']:
            print("❌ O pdftotext não está instalado no sistema. Tente executar: pkg install poppler")
        else:
            print("❌ O pdftotext não está instalado no sistema. Instale com: sudo apt-get install poppler-utils")

import asyncio
import edge_tts
from unidecode import unidecode
import chardet

try:
    from num2words import num2words
    print("✅ num2words importado com sucesso!")
except ImportError:
    print("\n❌ Erro ao importar num2words. Tente instalar manualmente: pip install --user num2words")
    sys.exit(1)

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
    LANG_DETECT_AVAILABLE = True
except ImportError:
    print("\n⚠️ O módulo langdetect não está instalado. Para instalar, execute: pip install langdetect")
    LANG_DETECT_AVAILABLE = False

def limpar_tela() -> None:
    """Limpa a tela do terminal de forma compatível com todos os sistemas."""
    sistema = detectar_sistema()
    if sistema['windows']:
        os.system("cls")
    else:
        os.system("clear")

def obter_opcao(prompt: str, opcoes: list) -> str:
    """Solicita ao usuário uma entrada que esteja dentre as opções válidas."""
    while True:
        escolha = input(prompt).strip()
        if escolha in opcoes:
            return escolha
        print("⚠️ Opção inválida! Tente novamente.")

def gravar_progresso(arquivo_progresso: str, indice: int) -> None:
    """Grava o índice da última parte processada em arquivo."""
    with open(arquivo_progresso, 'w') as f:
        f.write(str(indice))

def ler_progresso(arquivo_progresso: str) -> int:
    """Lê o índice da última parte processada a partir do arquivo de progresso."""
    try:
        with open(arquivo_progresso, 'r') as f:
            return int(f.read().strip())
    except Exception:
        return 0

def limpar_nome_arquivo(nome: str) -> str:
    """Remove ou substitui caracteres inválidos em sistemas de arquivos."""
    nome_limpo = re.sub(r'[<>:"/\\|?*]', '', nome)
    nome_limpo = nome_limpo.replace(' ', '_')
    return nome_limpo

def unificar_audio(temp_files, arquivo_final) -> bool:
    """Une os arquivos de áudio temporários em um único arquivo final."""
    try:
        if shutil.which("ffmpeg"):
            list_file = os.path.join(os.path.dirname(arquivo_final), "file_list.txt")
            with open(list_file, "w") as f:
                for temp in temp_files:
                    f.write(f"file '{os.path.abspath(temp)}'\n")
            subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", arquivo_final], check=True)
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

def atualizar_script() -> None:
    """Atualiza o script para a versão mais recente do GitHub."""
    exibir_banner()
    print("\n🔄 ATUALIZAÇÃO DO SCRIPT")
    print("\nIsso irá baixar a versão mais recente do script do GitHub.")
    confirmar = obter_opcao("Deseja continuar? (s/n): ", ['s', 'n'])
    if confirmar != 's':
        print("\n❌ Atualização cancelada pelo usuário.")
        input("\nPressione ENTER para continuar...")
        return
    print("\n🔄 Baixando a versão mais recente...")
    script_atual = os.path.abspath(__file__)
    script_backup = script_atual + ".backup"
    try:
        shutil.copy2(script_atual, script_backup)
        print(f"✅ Backup criado: {script_backup}")
    except Exception as e:
        print(f"⚠️ Não foi possível criar backup: {str(e)}")
        input("\nPressione ENTER para continuar...")
        return
    sistema = detectar_sistema()
    url = "https://raw.githubusercontent.com/JonJonesBR/Conversor_TTS/main/conversor_tts_lite.py"
    try:
        if sistema['windows']:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    with open(script_atual, 'wb') as f:
                        f.write(response.content)
                    print("✅ Script atualizado com sucesso!")
                else:
                    raise Exception(f"Erro ao baixar: código {response.status_code}")
            except ImportError:
                resultado = subprocess.run(["curl", "-o", script_atual, url], capture_output=True, text=True)
                if resultado.returncode != 0:
                    raise Exception(f"Erro curl: {resultado.stderr}")
                print("✅ Script atualizado com sucesso!")
        else:
            resultado = subprocess.run(["curl", "-o", script_atual, url], capture_output=True, text=True)
            if resultado.returncode != 0:
                raise Exception(f"Erro curl: {resultado.stderr}")
            print("✅ Script atualizado com sucesso!")
        print("\n🔄 O script será reiniciado para aplicar as atualizações.")
        input("Pressione ENTER para continuar...")
        python_exec = sys.executable
        os.execl(python_exec, python_exec, script_atual)
    except Exception as e:
        print(f"\n❌ Erro durante a atualização: {str(e)}")
        print(f"\n🔄 Restaurando backup...")
        try:
            shutil.copy2(script_backup, script_atual)
            print("✅ Backup restaurado com sucesso!")
        except Exception as e2:
            print(f"❌ Erro ao restaurar backup: {str(e2)}")
            print(f"⚠️ O backup está disponível em: {script_backup}")
        input("\nPressione ENTER para continuar...")

def exibir_banner() -> None:
    """Exibe o banner do programa."""
    limpar_tela()
    print("""
╔════════════════════════════════════════════╗
║         CONVERSOR TTS - EDGE TTS           ║
║        Text-to-Speech em PT-BR             ║
╚════════════════════════════════════════════╝
""")

def menu_principal() -> str:
    """Exibe o menu principal e retorna a opção escolhida."""
    exibir_banner()
    print("\nEscolha uma opção:")
    print("1. 🚀 INICIAR")
    print("2. 🎙️ VOZES")
    print("3. ❓ AJUDA")
    print("4. 🔄 ATUALIZAR")
    print("5. 🚪 SAIR")
    return obter_opcao("\nOpção: ", ['1', '2', '3', '4', '5'])

def menu_vozes() -> str:
    """Exibe o menu de seleção de vozes e retorna a voz escolhida."""
    exibir_banner()
    print("\nVozes disponíveis:")
    for i, voz in enumerate(VOZES_PT_BR, 1):
        print(f"{i}. {voz}")
    print(f"{len(VOZES_PT_BR) + 1}. Voltar")
    opcoes = [str(i) for i in range(1, len(VOZES_PT_BR) + 2)]
    escolha = obter_opcao("\nEscolha uma voz: ", opcoes)
    if escolha == str(len(VOZES_PT_BR) + 1):
        return None
    return VOZES_PT_BR[int(escolha) - 1]

def exibir_ajuda() -> None:
    """Exibe o guia de ajuda do programa."""
    exibir_banner()
    print("""
📖 GUIA DE USO:

1. Prepare seu arquivo de texto (.txt) ou PDF (.pdf) e salve-o em um local acessível

2. Escolha 'INICIAR' no menu principal

3. Navegue pelos diretórios e selecione o arquivo desejado
   - Você pode escolher um arquivo da lista numerada
   - Mudar para outro diretório usando a opção 'D'
   - Digitar o caminho completo manualmente usando a opção 'M'

4. Escolha uma das vozes disponíveis

5. Aguarde a conversão ser concluída e a unificação dos chunks em um único arquivo mp3

⚠️ OBSERVAÇÕES:
• O texto é dividido automaticamente em chunks menores para agilizar a conversão.
• O tamanho dos chunks é ajustado dinamicamente com base no tamanho total do texto para otimizar a performance.
• A cada chunk convertido, uma mensagem é exibida informando a parte concluída, a velocidade atual e o tempo restante estimado.
• Ao final, os arquivos temporários são unificados em um único mp3 e removidos.
""")
    input("\nPressione ENTER para voltar ao menu principal...")

async def testar_voz(voz: str) -> None:
    """
    Testa uma voz específica com um texto de exemplo e salva a amostra
    em uma pasta na pasta Download do Android. Após a geração, retorna automaticamente.
    """
    import edge_tts
    texto_teste = "Olá! Esta é uma demonstração da minha voz."
    communicate = edge_tts.Communicate(texto_teste, voz)
    sistema = detectar_sistema()
    if sistema['android'] or sistema['termux']:
        download_folder = "/storage/emulated/0/Download"
        test_folder = os.path.join(download_folder, "TTS_Teste_Voz")
        os.makedirs(test_folder, exist_ok=True)
        file_path = os.path.join(test_folder, f"teste_voz_{voz}.mp3")
    else:
        file_path = "teste_voz.mp3"
    try:
        await communicate.save(file_path)
        print(f"\n✅ Arquivo de teste gerado: {file_path}")
        if sistema['termux']:
            if shutil.which("termux-media-player"):
                try:
                    subprocess.run(['termux-media-player', 'play', file_path], timeout=10)
                except subprocess.TimeoutExpired:
                    print("Aviso: reprodução de áudio demorou, continuando...")
            else:
                print("termux-media-player não disponível, áudio não reproduzido.")
        elif sistema['windows']:
            os.startfile(file_path)
        else:
            subprocess.Popen(['xdg-open', file_path])
        await asyncio.sleep(1)
    except Exception as e:
        print(f"\n❌ Erro ao testar voz: {str(e)}")

def listar_arquivos(diretorio: str) -> list:
    """Lista arquivos TXT e PDF no diretório especificado."""
    arquivos = []
    try:
        for item in os.listdir(diretorio):
            caminho_completo = os.path.join(diretorio, item)
            if os.path.isfile(caminho_completo):
                ext = os.path.splitext(item)[1].lower()
                if ext in ['.txt', '.pdf']:
                    arquivos.append(item)
    except Exception as e:
        print(f"\n⚠️ Erro ao listar arquivos: {str(e)}")
    return sorted(arquivos)

def selecionar_arquivo() -> str:
    """Interface aprimorada para seleção de arquivo com navegação por diretórios."""
    sistema = detectar_sistema()
    if sistema['termux'] or sistema['android']:
        dir_atual = '/storage/emulated/0/Download'
    elif sistema['windows']:
        dir_atual = os.path.join(os.path.expanduser('~'), 'Desktop')
    else:
        dir_atual = os.path.join(os.path.expanduser('~'), 'Desktop')
    while True:
        exibir_banner()
        print("\n📂 SELEÇÃO DE ARQUIVO")
        print(f"\nDiretório atual: {dir_atual}")
        print("\nArquivos disponíveis:")
        arquivos = listar_arquivos(dir_atual)
        if not arquivos:
            print("\n⚠️ Nenhum arquivo TXT ou PDF encontrado neste diretório")
        else:
            for i, arquivo in enumerate(arquivos, 1):
                print(f"{i}. {arquivo}")
        print("\nOpções:")
        print("D. Mudar diretório")
        print("M. Digitar caminho manualmente")
        print("V. Voltar ao menu principal")
        escolha = input("\nEscolha uma opção: ").strip().upper()
        if escolha == 'V':
            return ''
        elif escolha == 'D':
            novo_dir = input("\nDigite o caminho do novo diretório: ").strip()
            if os.path.isdir(novo_dir):
                dir_atual = novo_dir
            else:
                print("\n❌ Diretório inválido")
                input("\nPressione ENTER para continuar...")
        elif escolha == 'M':
            caminho = input("\nDigite o caminho completo do arquivo: ").strip()
            if not os.path.exists(caminho):
                print(f"\n❌ Arquivo não encontrado: {caminho}")
                input("\nPressione ENTER para continuar...")
                continue
            ext = os.path.splitext(caminho)[1].lower()
            if ext == '.pdf':
                caminho_txt = os.path.splitext(caminho)[0] + '.txt'
                if not converter_pdf(caminho, caminho_txt):
                    print("\n⚠️ Falha na conversão do PDF. Tente outro arquivo.")
                    input("\nPressione ENTER para continuar...")
                    continue
                editar = input("\nDeseja editar o arquivo TXT gerado para melhorar a narração? (s/n): ").strip().lower()
                if editar == 's':
                    if sistema['android']:
                        print("\nO arquivo TXT convertido foi salvo em seu diretório padrão (normalmente Download).")
                        print("Após editá-lo, reinicie a conversão selecionando-o neste script pela opção 1 do menu inicial.")
                        input("\nPressione ENTER para retornar ao menu principal...")
                        return ''
                    else:
                        if sistema['windows']:
                            os.startfile(caminho_txt)
                        elif sistema['macos']:
                            subprocess.Popen(["open", caminho_txt])
                        else:
                            subprocess.Popen(["xdg-open", caminho_txt])
                        input("\nEdite o arquivo, salve as alterações e pressione ENTER para continuar...")
                return caminho_txt
            elif ext == '.txt':
                return caminho
            else:
                print(f"\n❌ Formato não suportado: {ext}")
                print("💡 Apenas arquivos .txt e .pdf são suportados")
                input("\nPressione ENTER para continuar...")
        elif escolha.isdigit():
            indice = int(escolha) - 1
            if 0 <= indice < len(arquivos):
                arquivo_selecionado = arquivos[indice]
                caminho_completo = os.path.join(dir_atual, arquivo_selecionado)
                if arquivo_selecionado.lower().endswith('.pdf'):
                    caminho_txt = os.path.splitext(caminho_completo)[0] + '.txt'
                    if not converter_pdf(caminho_completo, caminho_txt):
                        print("\n⚠️ Falha na conversão do PDF. Tente outro arquivo.")
                        input("\nPressione ENTER para continuar...")
                        continue
                    editar = input("\nDeseja editar o arquivo TXT gerado para melhorar a narração? (s/n): ").strip().lower()
                    if editar == 's':
                        if sistema['android']:
                            print("\nO arquivo TXT convertido foi salvo em seu diretório padrão (normalmente Download).")
                            print("Após editá-lo, reinicie a conversão selecionando-o neste script pela opção 1 do menu inicial.")
                            input("\nPressione ENTER para retornar ao menu principal...")
                            return ''
                        else:
                            if sistema['windows']:
                                os.startfile(caminho_txt)
                            elif sistema['macos']:
                                subprocess.Popen(["open", caminho_txt])
                            else:
                                subprocess.Popen(["xdg-open", caminho_txt])
                            input("\nEdite o arquivo, salve as alterações e pressione ENTER para continuar...")
                    return caminho_txt
                else:
                    return caminho_completo
            else:
                print("\n❌ Opção inválida")
                input("\nPressione ENTER para continuar...")
        else:
            print("\n❌ Opção inválida")
            input("\nPressione ENTER para continuar...")

def detectar_encoding(caminho_arquivo: str) -> str:
    """Detecta o encoding de um arquivo de texto."""
    import chardet
    try:
        with open(caminho_arquivo, 'rb') as f:
            resultado = chardet.detect(f.read())
        encoding_detectado = resultado['encoding']
        if not encoding_detectado:
            for enc in ['utf-8', 'utf-16', 'iso-8859-1', 'cp1252']:
                try:
                    with open(caminho_arquivo, 'r', encoding=enc) as f:
                        f.read(100)
                    return enc
                except UnicodeDecodeError:
                    continue
            return 'utf-8'
        return encoding_detectado
    except Exception as e:
        print(f"\n⚠️ Erro ao detectar encoding: {str(e)}")
        return 'utf-8'

def ler_arquivo_texto(caminho_arquivo: str) -> str:
    """Lê o conteúdo de um arquivo de texto com detecção automática de encoding."""
    encoding = detectar_encoding(caminho_arquivo)
    try:
        with open(caminho_arquivo, 'r', encoding=encoding) as f:
            conteudo = f.read()
        return conteudo
    except Exception as e:
        print(f"\n❌ Erro ao ler arquivo: {str(e)}")
        return ""

def processar_texto(texto: str) -> str:
    """
    Processa o texto para melhorar a pronúncia e entonação, convertendo abreviações comuns para suas formas completas.
    """
    import re
    from num2words import num2words

    texto = re.sub(r'\s+', ' ', texto)
    abreviacoes = {
        r'\bDr\.\b': 'Doutor',
        r'\bDra\.\b': 'Doutora',
        r'\bSr\.\b': 'Senhor',
        r'\bSra\.\b': 'Senhora',
        r'\bSrta\.\b': 'Senhorita',
        r'\bProf\.\b': 'Professor',
        r'\bProfa\.\b': 'Professora',
        r'\bEng\.\b': 'Engenheiro',
        r'\bEngª\.\b': 'Engenheira',
        r'\bAdm\.\b': 'Administrador',
        r'\bAdv\.\b': 'Advogado',
        r'\bExmo\.\b': 'Excelentíssimo',
        r'\bExma\.\b': 'Excelentíssima',
        r'\bV\.Exa\.\b': 'Vossa Excelência',
        r'\bV\.Sa\.\b': 'Vossa Senhoria',
        r'\bAv\.\b': 'Avenida',
        r'\bR\.\b': 'Rua',
        r'\bKm\.\b': 'Quilômetro',
        r'\betc\.\b': 'etcétera',
        r'\bRef\.\b': 'Referência',
        r'\bPag\.\b': 'Página',
        r'\bDept\.\b': 'Departamento',
        r'\bDepto\.\b': 'Departamento',
        r'\bUniv\.\b': 'Universidade',
        r'\bInst\.\b': 'Instituição',
        r'\bEst\.\b': 'Estado',
        r'\bTel\.\b': 'Telefone',
        r'\bCEP\.\b': 'Código de Endereçamento Postal',
        r'\bCNPJ\.\b': 'Cadastro Nacional da Pessoa Jurídica',
        r'\bCPF\.\b': 'Cadastro de Pessoas Físicas',
        r'\bLtda\.\b': 'Limitada'
    }
    for abrev, expansao in abreviacoes.items():
        texto = re.sub(abrev, expansao, texto)
    def converter_numero(match):
        num = match.group(0)
        try:
            return num2words(int(num), lang='pt_BR')
        except:
            return num
    texto = re.sub(r'\b\d+\b', converter_numero, texto)
    return texto

def calcular_chunk_size(texto: str) -> int:
    """
    Calcula dinamicamente o tamanho do chunk (max_chars) com base no tamanho do texto.
    Para textos pequenos, utiliza um valor padrão; para textos grandes, ajusta para ter aproximadamente 50 chunks.
    """
    total = len(texto)
    if total < 1000:
        return 100
    else:
        target_chunks = 50
        # Garante um valor mínimo de 50 caracteres por chunk
        return max(50, total // target_chunks)

def dividir_texto(texto: str, max_chars: int) -> list:
    """
    Divide o texto em partes menores para processamento, ignorando parágrafos.
    """
    partes = []
    start = 0
    while start < len(texto):
        end = start + max_chars
        partes.append(texto[start:end])
        start = end
    return partes

async def converter_texto_para_audio(texto: str, voz: str, caminho_saida: str) -> bool:
    """Converte texto para áudio usando Edge TTS."""
    import edge_tts
    try:
        communicate = edge_tts.Communicate(texto, voz)
        await communicate.save(caminho_saida)
        return True
    except Exception as e:
        print(f"\n❌ Erro na conversão: {str(e)}")
        return False

async def iniciar_conversao() -> None:
    """
    Inicia o processo de conversão de texto para áudio de forma concorrente.
    O tamanho dos chunks é calculado dinamicamente para equilibrar performance e velocidade.
    A cada chunk convertido, uma mensagem exibe a parte concluída, a velocidade e o tempo restante estimado.
    Ao final, os arquivos temporários são unificados.
    """
    caminho_arquivo = selecionar_arquivo()
    if not caminho_arquivo:
        return

    voz_escolhida = menu_vozes()
    if voz_escolhida is None:
        return

    texto = ler_arquivo_texto(caminho_arquivo)
    if not texto:
        print("\n❌ Arquivo vazio ou ilegível")
        input("\nPressione ENTER para continuar...")
        return

    texto_processado = processar_texto(texto)
    # Calcula o tamanho do chunk com base no tamanho total do texto
    chunk_size = calcular_chunk_size(texto_processado)
    print(f"\n🔧 Tamanho do chunk definido: {chunk_size} caracteres.")

    partes = dividir_texto(texto_processado, max_chars=chunk_size)
    total_partes = len(partes)
    print(f"\n📊 Texto dividido em {total_partes} parte(s).")
    print("Para interromper a conversão a qualquer momento, pressione CTRL + C.\n")

    nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
    nome_base = limpar_nome_arquivo(nome_base)
    diretorio_saida = os.path.join(os.path.dirname(caminho_arquivo), f"{nome_base}_audio")

    if not os.path.exists(diretorio_saida):
        os.makedirs(diretorio_saida)

    temp_files = []
    tasks = []
    for i, parte in enumerate(partes, start=1):
        saida_temp = os.path.join(diretorio_saida, f"{nome_base}_temp_{i:03d}.mp3")
        temp_files.append(saida_temp)
        tasks.append(asyncio.create_task(converter_texto_para_audio(parte, voz_escolhida, saida_temp)))

    start_time = time.time()
    completed = 0

    for task in asyncio.as_completed(tasks):
        await task
        completed += 1
        elapsed = time.time() - start_time
        speed = completed / elapsed if elapsed > 0 else 0
        remaining = total_partes - completed
        est_time = remaining / speed if speed > 0 else 0
        print(f"[{completed}/{total_partes}] parte convertida. Velocidade: {speed:.2f} chunks/s. Tempo restante estimado: {est_time:.1f} s.")

    overall_time = time.time() - start_time
    print("\n🔄 Unificando arquivos...")

    arquivo_final = os.path.join(diretorio_saida, f"{nome_base}.mp3")
    if unificar_audio(temp_files, arquivo_final):
        for f in temp_files:
            os.remove(f)
        print(f"\n🎉 Conversão concluída em {overall_time:.1f} s! Arquivo final: {arquivo_final}")
    else:
        print("\n❌ Falha na unificação dos arquivos.")

    input("\nPressione ENTER para continuar...")

async def main() -> None:
    """Função principal do programa."""
    while True:
        opcao = menu_principal()
        if opcao == '1':
            await iniciar_conversao()
        elif opcao == '2':
            while True:
                voz_escolhida = menu_vozes()
                if voz_escolhida is None:
                    break
                print(f"\n🎙️ Testando voz: {voz_escolhida}")
                await testar_voz(voz_escolhida)
        elif opcao == '3':
            exibir_ajuda()
        elif opcao == '4':
            atualizar_script()
        elif opcao == '5':
            print("\n👋 Obrigado por usar o Conversor TTS!")
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Programa interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")