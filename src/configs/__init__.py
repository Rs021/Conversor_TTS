manual_converser = {
        'UM': 1, 'UMI': 2, 'UMII': 3, 'UMIII': 4, 'UMIV': 5, 'UMV': 6, 'UMVI': 7,
        'CINCO': 5, 'CINCOI': 6, 'CINCOII': 7, 'CINCOIII': 8, 'CINCOIV': 9, 'CINCOV': 10,
        'UMX': 9, 'DEZ': 10, 'DEZI': 11, 'ONZE': 11, 'DOZE': 12
    }


VOZES_PT_BR = [
    "pt-BR-ThalitaMultilingualNeural",  # Voz padrão
    "pt-BR-FranciscaNeural",
    "pt-BR-AntonioNeural"
]

ENCODINGS_TENTATIVAS = ['utf-8', 'utf-16', 'iso-8859-1', 'cp1252']
BUFFER_IO = 32768
MAX_TENTATIVAS = 3  # Número máximo de tentativas por chunk
CANCELAR_PROCESSAMENTO = False
FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"
LIMITE_SEGUNDOS = 43200  # 12 horas para divisão de arquivos longos