import os
import subprocess
import chardet
from configs import *
import os
import subprocess
import asyncio
import aioconsole
from configs import *
from formatText import textFormat
from menu import Menu

class pdfCoverter:

    @staticmethod
    def converter_pdf(path_pdf: str, path_txt: str) -> bool:
        """Converte PDF para TXT utilizando o comando pdftotext."""
        try:
            path_pdf = os.path.abspath(path_pdf)

            if not os.path.isfile(path_pdf):
                raise Exception(f"❌ Arquivo PDF não encontrado: {path_pdf}")

            with open(path_pdf, "rb") as _:
                pass

        except PermissionError:
            raise Exception(f"❌ Sem permissão para acessar o arquivo: {path_pdf}")

        except Exception as e:
            raise Exception(f"❌ Erro ao acessar o arquivo PDF: {str(e)}")

        diretorio_saida = os.path.dirname(path_txt)
        if diretorio_saida and not os.path.exists(diretorio_saida):
            try:
                os.makedirs(diretorio_saida, exist_ok=True)
                print(f"✅ Diretório de saída criado: {diretorio_saida}")
            except Exception as e:
                raise Exception(f"❌ Erro ao criar diretório de saída: {str(e)}")

        try:
            subprocess.run(
                ["pdftotext", "-v"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

        except FileNotFoundError:
            raise Exception(
                "❌ O pdftotext não está instalado no sistema. Instale com: sudo apt-get install poppler-utils"
            )

        resultado = subprocess.run(
            ["pdftotext", "-layout", path_pdf, path_txt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if resultado.returncode != 0:
            raise Exception(f"❌ Erro ao converter o PDF: {resultado.stderr.decode()}")
        
        return True

    @staticmethod
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

    @staticmethod
    async def selecionar_arquivo() -> str:

        from files_utils import filesUtils
        """
        Interface aprimorada para seleção de arquivo com navegação por diretórios.
        Se o usuário selecionar um PDF, ele é convertido para TXT e o arquivo gerado é corrigido.
        Se for um arquivo TXT e o nome não contiver '_formatado', o arquivo é automaticamente corrigido.
        """

        dir_atual = os.path.join(
            os.path.expanduser("~"), "/workspaces/Conversor_TTS/assets"
        )

        while True:
            await Menu.exibir_banner()
            print("\n📂 SELEÇÃO DE ARQUIVO")
            print(f"\nDiretório atual: {dir_atual}")
            print("\nArquivos disponíveis:")
            arquivos = filesUtils.listar_arquivos(dir_atual, [".txt", ".pdf"])
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
                escolha = (
                    (await aioconsole.ainput("\nEscolha uma opção: ")).strip().upper()
                )
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
                        texto_formatado = textFormat.apply_format(texto_original)
                        caminho_txt = (
                            os.path.splitext(caminho_txt)[0] + "_formatado.txt"
                        )
                        with open(caminho_txt, "w", encoding="utf-8") as f:
                            f.write(texto_formatado)
                        print(f"✅ Formatação aplicada e salva em: {caminho_txt}")
                    except Exception as e:
                        print(f"❌ Erro ao aplicar formatação: {e}")
                    caminho_txt = filesUtils.verificar_e_corrigir_arquivo(caminho_txt)
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
                        caminho = filesUtils.verificar_e_corrigir_arquivo(caminho)
                        try:
                            with open(caminho, "r", encoding="utf-8") as f:
                                texto_original = f.read()
                            texto_formatado = textFormat.apply_format(texto_original)
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
                        caminho_txt = filesUtils.verificar_e_corrigir_arquivo(
                            caminho_txt
                        )
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
                            caminho_completo = filesUtils.verificar_e_corrigir_arquivo(
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
