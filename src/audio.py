import os
import subprocess
import asyncio
import re
from pathlib import Path
import aioconsole
from math import ceil
from configs import *
from menu import Menu
from files_utils import filesUtils
import edge_tts
import shutil


class Audio:

    @staticmethod
    async def converter_texto_para_audio(
        texto: str, voz: str, caminho_saida: str
    ) -> bool:
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
                if (
                    os.path.exists(caminho_saida)
                    and os.path.getsize(caminho_saida) > 1024
                ):
                    return True
                else:
                    print("⚠️ Arquivo de áudio vazio ou muito pequeno")
                    print(texto)
                    if os.path.exists(caminho_saida):
                        os.remove(caminho_saida)
                    return False
            except Exception as e:
                tentativas += 1
                raise Exception(
                    f"\n❌ Erro na conversão (tentativa {tentativas}/{MAX_TENTATIVAS}): {str(e)}"
                )

        return False

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    async def menu_melhorar_audio():
        """Menu para melhorar arquivos de áudio/vídeo existentes."""
        await Menu.exibir_banner()
        print("\n⚡ MELHORAR ÁUDIO EXISTENTE")

        dir_atual = os.path.join(os.path.expanduser("~"), "Desktop")

        while True:
            print(f"\nDiretório atual: {dir_atual}")
            print("\nArquivos de áudio/vídeo disponíveis:")
            arquivos = filesUtils.listar_arquivos(
                dir_atual, [".mp3", ".wav", ".m4a", ".mp4"]
            )

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
                await Audio.processar_melhorar_audio(caminho)
                return
            elif escolha.isdigit():
                indice = int(escolha) - 1
                if 0 <= indice < len(arquivos):
                    arquivo_selecionado = arquivos[indice]
                    caminho_completo = os.path.join(dir_atual, arquivo_selecionado)
                    await Audio.processar_melhorar_audio(caminho_completo)
                    return
                else:
                    print("\n❌ Opção inválida")
                    await asyncio.sleep(1)
            else:
                print("\n❌ Opção inválida")
                await asyncio.sleep(1)

    @staticmethod
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

            Audio.acelerar_audio(arquivo, temp_audio, velocidade)
            duracao = Audio.obter_duracao_ffprobe(temp_audio)
            print(f"    Duração após aceleração: {duracao / 3600:.2f} horas")

            extensao_final = ".mp4" if formato == "mp4" else ".mp3"

            if duracao <= LIMITE_SEGUNDOS:
                saida_final = f"{nome_saida_base}{extensao_final}"
                if formato == "mp4":
                    print("    Gerando vídeo com tela preta...")
                    Audio.criar_video_com_audio(temp_audio, saida_final, duracao)
                    os.remove(temp_audio)
                else:
                    os.rename(temp_audio, saida_final)
                print(f"    Arquivo final salvo: {saida_final}")
            else:
                print("    Dividindo em partes de até 12 horas...")
                if formato == "mp4":
                    video_completo = f"{nome_saida_base}_video.mp4"
                    Audio.criar_video_com_audio(temp_audio, video_completo, duracao)
                    Audio.dividir_em_partes(
                        video_completo,
                        duracao,
                        LIMITE_SEGUNDOS,
                        nome_saida_base,
                        ".mp4",
                    )
                    os.remove(video_completo)
                else:
                    Audio.dividir_em_partes(
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

    @staticmethod
    def unificar_audio(temp_files, arquivo_final) -> bool:
        """Une os arquivos de áudio temporários em um único arquivo final."""
        try:
            if shutil.which(FFMPEG_BIN):
                list_file = os.path.join(
                    os.path.dirname(arquivo_final), "file_list.txt"
                )
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
