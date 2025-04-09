import os
import subprocess
from math import ceil

FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"

EXTENSOES_AUDIO = [".mp3", ".wav", ".m4a"]
EXTENSOES_VIDEO = [".mp4"]
EXTENSOES_SUPORTADAS = EXTENSOES_AUDIO + EXTENSOES_VIDEO

LIMITE_SEGUNDOS = 43200  # 12 horas

def obter_duracao_ffprobe(caminho_arquivo):
    comando = [
        FFPROBE_BIN,
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        caminho_arquivo
    ]
    resultado = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(resultado.stdout.strip())

def acelerar_audio(input_path, output_path, velocidade):
    comando = [
        FFMPEG_BIN,
        '-y',
        '-i', input_path,
        '-filter:a', f"atempo={velocidade}",
        '-vn',
        output_path
    ]
    subprocess.run(comando, check=True)

def criar_video_com_audio(audio_path, video_path, duracao):
    comando = [
        FFMPEG_BIN,
        '-y',
        '-f', 'lavfi',
        '-i', f"color=c=black:s=1280x720:d={int(duracao)}",
        '-i', audio_path,
        '-shortest',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-pix_fmt', 'yuv420p',
        video_path
    ]
    subprocess.run(comando, check=True)

def dividir_em_partes(input_path, duracao_total, duracao_maxima, nome_base_saida, extensao):
    partes = ceil(duracao_total / duracao_maxima)
    for i in range(partes):
        inicio = i * duracao_maxima
        duracao = min(duracao_maxima, duracao_total - inicio)

        output_path = f"{nome_base_saida}_parte{i+1}{extensao}"

        comando = [
            FFMPEG_BIN,
            '-y',
            '-i', input_path,
            '-ss', str(int(inicio)),
            '-t', str(int(duracao)),
            '-c', 'copy',
            output_path
        ]
        subprocess.run(comando, check=True)
        print(f"    Parte {i+1} criada: {output_path}")

def processar_arquivo(arquivo, velocidade, formato_saida):
    nome_base, ext = os.path.splitext(arquivo)
    ext = ext.lower()

    if ext not in EXTENSOES_SUPORTADAS:
        print(f"Arquivo ignorado (formato não suportado): {arquivo}")
        return

    nome_saida_base = f"{nome_base}_x{velocidade}".replace(".", "_")
    temp_audio = f"{nome_saida_base}_temp_audio.mp3"

    print(f"\n[+] Processando: {arquivo}")
    print(f"    Aumentando velocidade ({velocidade}x)...")

    acelerar_audio(arquivo, temp_audio, velocidade)
    duracao = obter_duracao_ffprobe(temp_audio)
    print(f"    Duração após aceleração: {duracao / 3600:.2f} horas")

    extensao_final = ".mp4" if formato_saida == "mp4" else ".mp3"

    if duracao <= LIMITE_SEGUNDOS:
        saida_final = f"{nome_saida_base}{extensao_final}"
        if formato_saida == "mp4":
            print("    Gerando vídeo com tela preta...")
            criar_video_com_audio(temp_audio, saida_final, duracao)
            os.remove(temp_audio)
        else:
            os.rename(temp_audio, saida_final)
        print(f"    Arquivo final salvo: {saida_final}")
    else:
        print("    Dividindo em partes de até 12 horas...")
        if formato_saida == "mp4":
            video_completo = f"{nome_saida_base}_video.mp4"
            criar_video_com_audio(temp_audio, video_completo, duracao)
            dividir_em_partes(video_completo, duracao, LIMITE_SEGUNDOS, nome_saida_base, ".mp4")
            os.remove(video_completo)
        else:
            dividir_em_partes(temp_audio, duracao, LIMITE_SEGUNDOS, nome_saida_base, ".mp3")
        os.remove(temp_audio)
        print("    Arquivos divididos com sucesso.")

def menu_interativo():
    print("=== CONFIGURAÇÕES DO PROCESSAMENTO ===")

    while True:
        try:
            velocidade = float(input("Informe a velocidade de reprodução desejada (ex: 1.25, 1.5, 2.0): ").strip())
            if not (0.5 <= velocidade <= 2.0):
                raise ValueError
            break
        except ValueError:
            print("Valor inválido. Digite um número entre 0.5 e 2.0.")

    while True:
        formato = input("Escolha o formato de saída [mp3 para áudio | mp4 para vídeo]: ").strip().lower()
        if formato in ["mp3", "mp4"]:
            break
        else:
            print("Formato inválido. Digite 'mp3' ou 'mp4'.")

    return velocidade, formato

def main():
    arquivos = [f for f in os.listdir() if os.path.isfile(f) and os.path.splitext(f)[1].lower() in EXTENSOES_SUPORTADAS]

    if not arquivos:
        print("Nenhum arquivo de áudio ou vídeo suportado encontrado.")
        return

    velocidade, formato = menu_interativo()

    print("\nArquivos encontrados:")
    for idx, nome in enumerate(arquivos, 1):
        print(f"  {idx}. {nome}")

    for arquivo in arquivos:
        try:
            processar_arquivo(arquivo, velocidade, formato)
        except Exception as e:
            print(f"Erro ao processar {arquivo}: {e}")

if __name__ == "__main__":
    main()