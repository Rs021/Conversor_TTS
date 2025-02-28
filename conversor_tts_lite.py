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
import requests
import zipfile
import shutil

# =============================================================================
# CONFIGURAÇÃO E CONSTANTES
# =============================================================================
# Vozes disponíveis para conversão
VOZES_PT_BR = [
    "pt-BR-ThalitaMultilingualNeural",  # Voz padrão
    "pt-BR-FranciscaNeural",
    "pt-BR-AntonioNeural"
]

# Diretórios e configurações de encoding e buffer
ENCODINGS_TENTATIVAS = ['utf-8', 'utf-16', 'iso-8859-1', 'cp1252']
BUFFER_IO = 32768

# Global para interrupção via sinal (Ctrl+C)
# Ajuste para permitir que o segundo Ctrl+C finalize o script imediatamente
interrupcao_requisitada = False

# =============================================================================
# FUNÇÕES PARA DETECÇÃO DE SISTEMA OPERACIONAL
# =============================================================================
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
    
    # Detecta Windows
    if sistema['nome'] == 'windows':
        sistema['windows'] = True
        return sistema
    
    # Detecta macOS
    if sistema['nome'] == 'darwin':
        sistema['macos'] = True
        return sistema
    
    # Detecta Linux (incluindo Android/Termux)
    if sistema['nome'] == 'linux':
        sistema['linux'] = True
        
        # Verifica se é Android/Termux
        is_android = any([
            'ANDROID_ROOT' in os.environ,
            'TERMUX_VERSION' in os.environ,
            os.path.exists('/data/data/com.termux'),
            os.path.exists('/system/bin/linker64')  # Comum em Android
        ])
        
        if is_android:
            sistema['android'] = True
            # Verifica especificamente se é Termux
            if any([
                'TERMUX_VERSION' in os.environ,
                os.path.exists('/data/data/com.termux')
            ]):
                sistema['termux'] = True
                # Configura variáveis de ambiente específicas do Termux
                os.environ['PATH'] = f"{os.environ.get('PATH', '')}:/data/data/com.termux/files/usr/bin"
    
    return sistema

# =============================================================================
# FUNÇÕES PARA INSTALAÇÃO DO POPPLER
# =============================================================================
def instalar_poppler_windows():
    """Instala o Poppler no Windows automaticamente."""
    try:
        # URL do Poppler para Windows (versão 23.11.0)
        poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v23.11.0-0/Release-23.11.0-0.zip"
        
        # Diretório de instalação
        install_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Poppler')
        os.makedirs(install_dir, exist_ok=True)
        
        print("📥 Baixando Poppler...")
        response = requests.get(poppler_url)
        zip_path = os.path.join(install_dir, "poppler.zip")
        
        # Salva o arquivo ZIP
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        print("📦 Extraindo arquivos...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extrai todos os arquivos para o diretório de instalação
            zip_ref.extractall(install_dir)
        
        # Remove o arquivo ZIP
        os.remove(zip_path)
        
        # Procura pelo diretório bin em várias localizações possíveis
        bin_paths = [
            os.path.join(install_dir, 'bin'),
            os.path.join(install_dir, 'Library', 'bin'),
            os.path.join(install_dir, 'poppler-23.11.0', 'bin'),
            os.path.join(install_dir, 'Release-23.11.0-0', 'bin')
        ]
        
        # Procura por arquivos .exe para identificar o diretório bin
        bin_path = None
        for path in bin_paths:
            if os.path.exists(path) and any(f.endswith('.exe') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))):
                bin_path = path
                break
        
        # Se não encontrou em caminhos predefinidos, procura recursivamente
        if not bin_path:
            for root, dirs, files in os.walk(install_dir):
                if 'bin' in dirs and any(f.endswith('.exe') for f in os.listdir(os.path.join(root, 'bin')) if os.path.isfile(os.path.join(root, 'bin', f))):
                    bin_path = os.path.join(root, 'bin')
                    break
        
        if not bin_path:
            print(f"❌ Erro: Diretório bin não encontrado em {install_dir}")
            return False
        
        print(f"✅ Diretório bin encontrado em: {bin_path}")
            
        # Verifica se o pdftotext existe no diretório bin
        pdftotext_path = os.path.join(bin_path, 'pdftotext.exe')
        if not os.path.exists(pdftotext_path):
            print(f"❌ Erro: pdftotext.exe não encontrado em {bin_path}")
            return False
            
        # Atualiza o PATH da sessão atual
        if bin_path not in os.environ['PATH']:
            os.environ['PATH'] = f"{bin_path};{os.environ['PATH']}"
            
        # Verifica se o pdftotext está funcionando
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

# =============================================================================
# FUNÇÕES PARA CONVERSÃO DE PDF
# =============================================================================
def converter_pdf(caminho_pdf: str, caminho_txt: str) -> bool:
    """Converte PDF para TXT utilizando o comando pdftotext."""
    try:
        # Verifica se o arquivo PDF existe e é acessível
        try:
            caminho_pdf = os.path.abspath(caminho_pdf)
            if not os.path.isfile(caminho_pdf):
                print(f"❌ Arquivo PDF não encontrado: {caminho_pdf}")
                return False
            # Verifica se o arquivo pode ser lido
            with open(caminho_pdf, 'rb') as _:
                pass
        except PermissionError:
            print(f"❌ Sem permissão para acessar o arquivo: {caminho_pdf}")
            return False
        except Exception as e:
            print(f"❌ Erro ao acessar o arquivo PDF: {str(e)}")
            return False
            
        # Verifica se o diretório de saída existe
        diretorio_saida = os.path.dirname(caminho_txt)
        if diretorio_saida and not os.path.exists(diretorio_saida):
            try:
                os.makedirs(diretorio_saida, exist_ok=True)
                print(f"✅ Diretório de saída criado: {diretorio_saida}")
            except Exception as e:
                print(f"❌ Erro ao criar diretório de saída: {str(e)}")
                return False

        # Verifica se o pdftotext está instalado
        sistema = detectar_sistema()
        if sistema['windows']:
            # No Windows, procura o pdftotext no PATH
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
                # Tenta encontrar o pdftotext novamente após a instalação
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
            # Para outros sistemas, verifica se o pdftotext está disponível
            try:
                subprocess.run(["pdftotext", "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except FileNotFoundError:
                if sistema['macos']:
                    print("❌ O pdftotext não está instalado no sistema.")
                    print("💡 Para instalar o pdftotext no macOS:")
                    print("   brew install poppler")
                    return False
                elif sistema['linux']:
                    if sistema['termux']:
                        print("❌ O pdftotext não está instalado no sistema.")
                        print("💡 Para instalar o pdftotext no Termux:")
                        print("   pkg install poppler")
                    else:
                        print("❌ O pdftotext não está instalado no sistema.")
                        print("💡 Para instalar o pdftotext no Linux:")
                        print("   sudo apt-get install poppler-utils  # Para sistemas baseados em Debian/Ubuntu")
                        print("   sudo pacman -S poppler              # Para sistemas baseados em Arch Linux")
                        print("   sudo dnf install poppler-utils     # Para sistemas baseados em Fedora")
                    return False

        # Converte o PDF para TXT usando o caminho completo no Windows
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

    except Exception as e:
        print(f"❌ Erro ao converter o PDF: {str(e)}")
        return False

# =============================================================================
# FUNÇÕES DE VERIFICAÇÃO DE AMBIENTE E DEPENDÊNCIAS
# =============================================================================
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
        # Atualiza o repositório do Termux primeiro
        subprocess.run(['pkg', 'update', '-y'], check=True, capture_output=True)
        
        # Verifica se o pacote já está instalado
        resultado = subprocess.run(['pkg', 'list-installed', pkg], capture_output=True, text=True)
        if pkg in resultado.stdout:
            print(f"✅ Pacote Termux {pkg} já está instalado")
            return
            
        print(f"⚠️ Instalando pacote Termux {pkg}...")
        subprocess.run(['pkg', 'install', '-y', pkg], check=True)
        print(f"✅ Pacote Termux {pkg} instalado com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar pacote Termux {pkg}: {e}")
        print("💡 Tente executar 'pkg update' manualmente e tente novamente")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado ao instalar {pkg}: {e}")
        sys.exit(1)

def instalar_dependencia_python(nome_pkg: str, pip_nome: str) -> None:
    """Verifica e instala uma dependência Python, se necessária."""
    try:
        # Tenta importar o módulo para verificar se já está instalado
        __import__(nome_pkg)
        print(f"✅ Módulo Python {nome_pkg} já está instalado")
    except ImportError:
        print(f"⚠️ Instalando módulo Python {nome_pkg}...")
        sistema = detectar_sistema()
        
        # Comando base para pip
        pip_cmd = [sys.executable, "-m", "pip", "install", pip_nome]
        
        # Ajusta para instalação de usuário em sistemas não-Termux
        if not sistema['termux']:
            pip_cmd.append("--user")
        
        try:
            subprocess.run(pip_cmd, check=True)
            print(f"✅ Módulo Python {nome_pkg} instalado com sucesso!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar módulo Python {nome_pkg}: {e}")
            print(f"💡 Tente instalar manualmente: pip install {pip_nome}")
            sys.exit(1)

def instalar_poppler() -> bool:
    """Instala o pacote poppler (pdftotext) de acordo com o sistema operacional."""
    sistema = detectar_sistema()
    print("⚠️ O pdftotext não está instalado. Tentando instalar automaticamente...")
    
    try:
        if sistema['termux']:
            # Instala poppler no Termux
            subprocess.run(['pkg', 'install', '-y', 'poppler'], check=True)
            print("✅ poppler instalado com sucesso no Termux!")
            return True
        elif sistema['linux']:
            # Instala poppler-utils no Linux
            print("⚠️ Instalando poppler-utils no Linux...")
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'poppler-utils'], check=True)
            print("✅ poppler-utils instalado com sucesso no Linux!")
            return True
        elif sistema['macos']:
            # Instala poppler no macOS via Homebrew
            print("⚠️ Instalando poppler no macOS via Homebrew...")
            # Verifica se o Homebrew está instalado
            try:
                subprocess.run(['brew', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except FileNotFoundError:
                print("❌ Homebrew não está instalado no macOS.")
                print("💡 Instale o Homebrew primeiro: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
                return False
                
            subprocess.run(['brew', 'install', 'poppler'], check=True)
            print("✅ poppler instalado com sucesso no macOS!")
            return True
        elif sistema['windows']:
            # No Windows, instala automaticamente o Poppler
            print("⚠️ Instalando Poppler no Windows...")
            import tempfile
            import zipfile
            import urllib.request
            import shutil
            import winreg
            
            # URL do Poppler para Windows
            poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v23.11.0-0/Release-23.11.0-0.zip"
            
            try:
                # Cria diretório temporário para download
                temp_dir = tempfile.mkdtemp()
                zip_path = os.path.join(temp_dir, "poppler.zip")
                
                # Download do arquivo
                print("📥 Baixando Poppler...")
                urllib.request.urlretrieve(poppler_url, zip_path)
                
                # Diretório de instalação (Program Files)
                program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
                poppler_dir = os.path.join(program_files, "Poppler")
                
                # Cria diretório se não existir
                os.makedirs(poppler_dir, exist_ok=True)
                
                # Extrai o arquivo ZIP
                print("📦 Extraindo arquivos...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Obtém o nome do diretório raiz dentro do ZIP
                    root_dirs = {item.split('/')[0] for item in zip_ref.namelist() if '/' in item}
                    if len(root_dirs) == 1:
                        root_dir = root_dirs.pop()
                        # Extrai para o diretório temporário primeiro
                        zip_ref.extractall(temp_dir)
                        # Move os arquivos do diretório raiz para o diretório de instalação
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
                        # Se não houver um diretório raiz único, extrai diretamente
                        zip_ref.extractall(poppler_dir)
                
                # Adiciona ao PATH do sistema
                print("🔧 Adicionando ao PATH do sistema...")
                bin_dir = os.path.join(poppler_dir, "bin")
                
                # Abre a chave do registro para o PATH
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
                try:
                    path, _ = winreg.QueryValueEx(key, "PATH")
                    # Verifica se o diretório já está no PATH
                    if bin_dir.lower() not in path.lower():
                        # Adiciona o diretório ao PATH
                        new_path = path + ";" + bin_dir
                        winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                        # Notifica o sistema sobre a mudança
                        subprocess.run(["setx", "PATH", new_path], check=True, capture_output=True)
                except FileNotFoundError:
                    # Se a chave PATH não existir, cria-a
                    winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, bin_dir)
                finally:
                    winreg.CloseKey(key)
                
                # Atualiza o PATH da sessão atual
                os.environ["PATH"] = bin_dir + ";" + os.environ.get("PATH", "")
                
                # Limpa arquivos temporários
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                print("✅ Poppler instalado com sucesso no Windows!")
                print("⚠️ Você pode precisar reiniciar o terminal para que as alterações no PATH tenham efeito.")
                
                # Verifica se a instalação foi bem-sucedida tentando executar pdftotext
                try:
                    subprocess.run([os.path.join(bin_dir, "pdftotext"), "-v"], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("⚠️ Poppler foi instalado, mas o pdftotext ainda não está disponível.")
                    print("💡 Tente reiniciar o terminal e executar o script novamente.")
                    return False
                    
            except Exception as e:
                print(f"❌ Erro durante a instalação automática do Poppler: {str(e)}")
                print("💡 Por favor, instale manualmente:")
                print("   1. Baixe o Poppler para Windows em https://github.com/oschwartz10612/poppler-windows/releases/")
                print("   2. Extraia o arquivo ZIP para uma pasta (ex: C:\\Poppler)")
                print("   3. Adicione o diretório bin (ex: C:\\Poppler\\bin) ao PATH do sistema")
                print("   4. Reinicie o terminal e execute este script novamente")
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
        # Pacotes essenciais para o Termux
        pacotes_termux = ['python', 'python-pip', 'git', 'poppler', 'termux-api']
        for pkg in pacotes_termux:
            instalar_dependencia_termux(pkg)
    
    # Dependências Python comuns para todos os ambientes
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

    # Verifica pdftotext
    try:
        subprocess.run(['pdftotext', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ pdftotext (poppler) está funcionando corretamente")
    except FileNotFoundError:
        # Tenta instalar o poppler automaticamente
        sistema = detectar_sistema()
        if sistema['windows']:
            print("📦 Poppler não encontrado. Iniciando instalação automática...")
            if not instalar_poppler_windows():
                print("❌ Não foi possível instalar o pdftotext automaticamente.")
                print("💡 Para instalar o pdftotext manualmente:")
                print("   - Windows: Baixe e instale o Poppler em https://github.com/oschwartz10612/poppler-windows/releases/")
                print("     Adicione o diretório bin do Poppler ao PATH do sistema")
        elif sistema['macos']:
            print("❌ O pdftotext não está instalado no sistema.")
            print("💡 Para instalar o pdftotext no macOS:")
            print("   - macOS: Execute 'brew install poppler'")
        elif sistema['termux']:
            print("❌ O pdftotext não está instalado no sistema.")
            print("💡 Para instalar o pdftotext no Termux:")
            print("   - Termux: Execute 'pkg install poppler'")
        else:  # Linux genérico
            print("❌ O pdftotext não está instalado no sistema.")
            print("💡 Para instalar o pdftotext no Linux:")
            print("   - Linux: Execute 'sudo apt-get install poppler-utils'")

# Executa a verificação de dependências antes de importar módulos de terceiros
verificar_dependencias()

# =============================================================================
# IMPORTAÇÃO DE MÓDULOS TERCEIRIZADOS
# =============================================================================
import asyncio
import edge_tts
from unidecode import unidecode
import chardet

try:
    from num2words import num2words
    print("✅ num2words importado com sucesso!")
except ImportError:
    print("\n❌ Erro ao importar num2words. Tente instalar manualmente:")
    print("pip install --user num2words")
    sys.exit(1)

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
    LANG_DETECT_AVAILABLE = True
except ImportError:
    print("\n⚠️ O módulo langdetect não está instalado.")
    print("Para instalar, execute: pip install langdetect")
    LANG_DETECT_AVAILABLE = False

# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================
def limpar_tela() -> None:
    """Limpa a tela do terminal de forma compatível com todos os sistemas."""
    sistema = detectar_sistema()
    if sistema['windows']:
        os.system("cls")
    else:  # Linux, macOS, Android/Termux
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
    # Remove caracteres inválidos e substitui espaços por underscores
    nome_limpo = re.sub(r'[<>:"/\\|?*]', '', nome)
    nome_limpo = nome_limpo.replace(' ', '_')
    return nome_limpo

# =============================================================================
# FUNÇÕES DE ATUALIZAÇÃO
# =============================================================================
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
    
    # Obtém o caminho do script atual
    script_atual = os.path.abspath(__file__)
    script_backup = script_atual + ".backup"
    
    # Cria um backup do script atual
    try:
        import shutil
        shutil.copy2(script_atual, script_backup)
        print(f"✅ Backup criado: {script_backup}")
    except Exception as e:
        print(f"⚠️ Não foi possível criar backup: {str(e)}")
        input("\nPressione ENTER para continuar...")
        return
    
    # Baixa a nova versão
    sistema = detectar_sistema()
    url = "https://raw.githubusercontent.com/JonJonesBR/Conversor_TTS/main/conversor_tts_lite.py"
    
    try:
        if sistema['windows']:
            # No Windows, usa o módulo requests se disponível, senão usa curl
            try:
                import requests
                response = requests.get(url)
                if response.status_code == 200:
                    with open(script_atual, 'wb') as f:
                        f.write(response.content)
                    print("✅ Script atualizado com sucesso!")
                else:
                    raise Exception(f"Erro ao baixar: código {response.status_code}")
            except ImportError:
                # Fallback para curl no Windows
                resultado = subprocess.run(
                    ["curl", "-o", script_atual, url],
                    capture_output=True, text=True
                )
                if resultado.returncode != 0:
                    raise Exception(f"Erro curl: {resultado.stderr}")
                print("✅ Script atualizado com sucesso!")
        else:
            # Linux, macOS, Android/Termux
            resultado = subprocess.run(
                ["curl", "-o", script_atual, url],
                capture_output=True, text=True
            )
            if resultado.returncode != 0:
                raise Exception(f"Erro curl: {resultado.stderr}")
            print("✅ Script atualizado com sucesso!")
        
        print("\n🔄 O script será reiniciado para aplicar as atualizações.")
        input("Pressione ENTER para continuar...")
        
        # Reinicia o script
        python = sys.executable
        os.execl(python, python, script_atual)
        
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

# =============================================================================
# FUNÇÕES DE MENU E INTERFACE
# =============================================================================
def exibir_banner() -> None:
    """Exibe o banner do programa."""
    limpar_tela()
    print("""
╔════════════════════════════════════════════╗
║         CONVERSOR TTS - EDGE TTS          ║
║        Text-to-Speech em PT-BR            ║
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
5. Aguarde a conversão ser concluída

⚠️ OBSERVAÇÕES:
• O texto será dividido automaticamente em partes menores
• Números e abreviações serão convertidos automaticamente
• O progresso é salvo em caso de interrupção
• Os arquivos de áudio serão salvos na mesma pasta do texto
• Arquivos PDF serão convertidos automaticamente para TXT
""")
    input("\nPressione ENTER para voltar ao menu principal...")

async def testar_voz(voz: str) -> None:
    """Testa uma voz específica com um texto de exemplo."""
    texto_teste = "Olá! Esta é uma demonstração da minha voz."
    communicate = edge_tts.Communicate(texto_teste, voz)
    
    try:
        await communicate.save("teste_voz.mp3")
        print("\n✅ Arquivo de teste gerado: teste_voz.mp3")
        
        # Tenta reproduzir o arquivo de teste
        sistema = detectar_sistema()
        if sistema['termux']:
            subprocess.run(['termux-media-player', 'play', 'teste_voz.mp3'])
        elif sistema['windows']:
            os.startfile('teste_voz.mp3')
        else:  # Linux e macOS
            subprocess.run(['xdg-open', 'teste_voz.mp3'])
            
        await asyncio.sleep(3)  # Aguarda a reprodução
        
        # Limpa o arquivo de teste
        if os.path.exists("teste_voz.mp3"):
            os.remove("teste_voz.mp3")
            
    except Exception as e:
        print(f"\n❌ Erro ao testar voz: {str(e)}")

# =============================================================================
# FUNÇÕES DE PROCESSAMENTO DE TEXTO E CONVERSÃO
# =============================================================================
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
    
    # Define o diretório inicial baseado no sistema
    if sistema['termux'] or sistema['android']:
        dir_atual = '/storage/emulated/0/Download'
    elif sistema['windows']:
        dir_atual = os.path.join(os.path.expanduser('~'), 'Desktop')
    elif sistema['macos']:
        dir_atual = os.path.join(os.path.expanduser('~'), 'Desktop')
    else:  # Linux
        dir_atual = os.path.join(os.path.expanduser('~'), 'Desktop')
    
    while True:
        exibir_banner()
        print("\n📂 SELEÇÃO DE ARQUIVO")
        print(f"\nDiretório atual: {dir_atual}")
        print("\nArquivos disponíveis:")
        
        # Lista arquivos no diretório atual
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
                    return caminho_txt
                else:  # .txt
                    return caminho_completo
            else:
                print("\n❌ Opção inválida")
                input("\nPressione ENTER para continuar...")
        else:
            print("\n❌ Opção inválida")
            input("\nPressione ENTER para continuar...")


def detectar_encoding(caminho_arquivo: str) -> str:
    """Detecta o encoding de um arquivo de texto."""
    try:
        # Tenta detectar automaticamente com chardet
        with open(caminho_arquivo, 'rb') as f:
            resultado = chardet.detect(f.read())
        encoding_detectado = resultado['encoding']
        
        # Se não conseguir detectar, tenta encodings comuns
        if not encoding_detectado:
            for enc in ENCODINGS_TENTATIVAS:
                try:
                    with open(caminho_arquivo, 'r', encoding=enc) as f:
                        f.read(100)  # Tenta ler alguns caracteres
                    return enc
                except UnicodeDecodeError:
                    continue
            return 'utf-8'  # Fallback para utf-8
        
        return encoding_detectado
    except Exception as e:
        print(f"\n⚠️ Erro ao detectar encoding: {str(e)}")
        return 'utf-8'  # Fallback para utf-8

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
    """Processa o texto para melhorar a pronúncia e entonação."""
    # Remove espaços extras e quebras de linha desnecessárias
    texto = re.sub(r'\s+', ' ', texto)
    
    # Substitui abreviações comuns
    abreviacoes = {
        r'\bDr\.\b': 'Doutor',
        r'\bSr\.\b': 'Senhor',
        r'\bSra\.\b': 'Senhora',
        r'\bProf\.\b': 'Professor',
        r'\bex\.\b': 'exemplo',
        r'\betc\.\b': 'etcétera',
    }
    
    for abrev, expansao in abreviacoes.items():
        texto = re.sub(abrev, expansao, texto)
    
    # Converte números para texto (apenas números isolados)
    def converter_numero(match):
        num = match.group(0)
        try:
            return num2words(int(num), lang='pt_BR')
        except:
            return num
    
    texto = re.sub(r'\b\d+\b', converter_numero, texto)
    
    return texto

def dividir_texto(texto: str, max_chars: int = 2000) -> list:
    """Divide o texto em partes menores para processamento."""
    # Se o texto for menor que o limite, retorna como uma única parte
    if len(texto) <= max_chars:
        return [texto]
    
    partes = []
    # Divide o texto em parágrafos
    paragrafos = re.split(r'\n+', texto)
    
    parte_atual = ""
    for paragrafo in paragrafos:
        # Se adicionar este parágrafo exceder o limite
        if len(parte_atual) + len(paragrafo) > max_chars and parte_atual:
            partes.append(parte_atual)
            parte_atual = paragrafo
        else:
            if parte_atual:
                parte_atual += "\n\n" + paragrafo
            else:
                parte_atual = paragrafo
    
    # Adiciona a última parte se não estiver vazia
    if parte_atual:
        partes.append(parte_atual)
    
    return partes

async def converter_texto_para_audio(texto: str, voz: str, caminho_saida: str) -> bool:
    """Converte texto para áudio usando Edge TTS."""
    try:
        communicate = edge_tts.Communicate(texto, voz)
        await communicate.save(caminho_saida)
        return True
    except Exception as e:
        print(f"\n❌ Erro na conversão: {str(e)}")
        return False

async def iniciar_conversao() -> None:
    """Inicia o processo de conversão de texto para áudio."""
    # Seleciona o arquivo
    caminho_arquivo = selecionar_arquivo()
    if not caminho_arquivo:
        return
    
    # Seleciona a voz
    voz_escolhida = menu_vozes()
    if voz_escolhida is None:
        return
    
    # Lê o conteúdo do arquivo
    texto = ler_arquivo_texto(caminho_arquivo)
    if not texto:
        print("\n❌ Arquivo vazio ou ilegível")
        input("\nPressione ENTER para continuar...")
        return
    
    # Processa o texto
    texto_processado = processar_texto(texto)
    
    # Divide o texto em partes menores
    partes = dividir_texto(texto_processado)
    total_partes = len(partes)
    
    print(f"\n📊 Texto dividido em {total_partes} parte(s)")
    
    # Cria o diretório de saída
    nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
    nome_base = limpar_nome_arquivo(nome_base)
    diretorio_saida = os.path.join(os.path.dirname(caminho_arquivo), f"{nome_base}_audio")
    
    if not os.path.exists(diretorio_saida):
        os.makedirs(diretorio_saida)
    
    # Verifica se há progresso anterior
    arquivo_progresso = os.path.join(diretorio_saida, ".progresso")
    indice_inicial = ler_progresso(arquivo_progresso)
    
    if indice_inicial > 0 and indice_inicial < total_partes:
        print(f"\n🔄 Retomando conversão a partir da parte {indice_inicial + 1} de {total_partes}")
        continuar = obter_opcao("Continuar de onde parou? (s/n): ", ['s', 'n'])
        if continuar == 'n':
            indice_inicial = 0
    
    # Processa cada parte do texto
    for i in range(indice_inicial, total_partes):
        parte = partes[i]
        print(f"\n🔊 Convertendo parte {i + 1} de {total_partes}...")
        
        # Define o caminho do arquivo de saída
        caminho_saida = os.path.join(diretorio_saida, f"{nome_base}_parte_{i+1}.mp3")
        
        # Converte o texto para áudio
        sucesso = await converter_texto_para_audio(parte, voz_escolhida, caminho_saida)
        
        if sucesso:
            print(f"✅ Parte {i + 1} concluída: {caminho_saida}")
            # Salva o progresso
            gravar_progresso(arquivo_progresso, i + 1)
        else:
            print(f"❌ Falha ao processar parte {i + 1}")
            input("\nPressione ENTER para continuar...")
            return
    
    print(f"\n🎉 Conversão concluída! Arquivos salvos em: {diretorio_saida}")
    input("\nPressione ENTER para continuar...")

# Atualiza a função main para chamar a função de conversão
async def main() -> None:
    """Função principal do programa."""
    while True:
        opcao = menu_principal()
        
        if opcao == '1':  # INICIAR
            await iniciar_conversao()
            
        elif opcao == '2':  # VOZES
            while True:
                voz_escolhida = menu_vozes()
                if voz_escolhida is None:
                    break
                print(f"\n🎙️ Testando voz: {voz_escolhida}")
                await testar_voz(voz_escolhida)
                input("\nPressione ENTER para continuar...")
                
        elif opcao == '3':  # AJUDA
            exibir_ajuda()
            
        elif opcao == '4':  # ATUALIZAR
            atualizar_script()
            
        elif opcao == '5':  # SAIR
            print("\n👋 Obrigado por usar o Conversor TTS!")
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Programa interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
