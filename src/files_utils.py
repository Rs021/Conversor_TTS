import os
from textParser import ParserTxt
import re
from pdfParser import pdfCoverter


class filesUtils:

    @staticmethod
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

    @staticmethod
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
        conteudo_corrigido = ParserTxt.melhorar_texto_corrigido(conteudo)
        novo_caminho = base + "_formatado" + ext
        try:
            with open(novo_caminho, "w", encoding="utf-8") as f:
                f.write(conteudo_corrigido)
            print(f"✅ Arquivo corrigido e salvo em: {novo_caminho}")
        except Exception as e:
            print(f"❌ Erro ao salvar o arquivo corrigido: {e}")
            return caminho_txt
        return novo_caminho

    @staticmethod
    def gravar_progresso(arquivo_progresso: str, indice: int) -> None:
        """Grava o índice da última parte processada em arquivo."""
        with open(arquivo_progresso, "w") as f:
            f.write(str(indice))

    @staticmethod
    def ler_progresso(arquivo_progresso: str) -> int:
        """Lê o índice da última parte processada a partir do arquivo de progresso."""
        try:
            with open(arquivo_progresso, "r") as f:
                return int(f.read().strip())
        except Exception:
            return 0

    @staticmethod
    def limpar_nome_arquivo(nome: str) -> str:
        """Remove ou substitui caracteres inválidos em sistemas de arquivos."""
        nome_limpo = re.sub(r'[<>:"/\\|?*]', "", nome)
        nome_limpo = nome_limpo.replace(" ", "_")
        return nome_limpo

    @staticmethod
    def ler_arquivo_texto(caminho_arquivo: str) -> str:
        """Lê o conteúdo de um arquivo de texto com detecção automática de encoding."""
        encoding = pdfCoverter.detectar_encoding(caminho_arquivo)
        try:
            with open(caminho_arquivo, "r", encoding=encoding) as f:
                conteudo = f.read()
            return conteudo
        except Exception as e:
            print(f"\n❌ Erro ao ler arquivo: {str(e)}")
            return ""
