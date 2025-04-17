manual_converser = {
        'UM': 1, 'UMI': 2, 'UMII': 3, 'UMIII': 4, 'UMIV': 5, 'UMV': 6, 'UMVI': 7,
        'CINCO': 5, 'CINCOI': 6, 'CINCOII': 7, 'CINCOIII': 8, 'CINCOIV': 9, 'CINCOV': 10,
        'UMX': 9, 'DEZ': 10, 'DEZI': 11, 'ONZE': 11, 'DOZE': 12
    }

sistema = {"linux": True}

VOZES_PT_BR = [
    "pt-BR-ThalitaMultilingualNeural",  # Voz padrão
    "pt-BR-FranciscaNeural",
    "pt-BR-AntonioNeural"
]

ENCODINGS_TENTATIVAS = ['utf-8', 'utf-16', 'iso-8859-1', 'cp1252']
BUFFER_IO = 32768
MAX_TENTATIVAS = 1 # Número máximo de tentativas por chunk
CANCELAR_PROCESSAMENTO = False
FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"
LIMITE_SEGUNDOS = 43200  # 12 horas para divisão de arquivos longos


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