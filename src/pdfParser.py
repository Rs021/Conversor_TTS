import os
import subprocess


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
            print(f"❌ Erro ao converter o PDF: {resultado.stderr.decode()}")
            return False
        return True
