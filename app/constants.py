# Regras de Curadoria da Comunidade para classificar ou desclassificar um album.
# Quantos votos líquidos (votos positivos - votos negativos) são necessários 
# para a comunidade alterar o status de um álbum na Platina.
CURATION_THRESHOLD = 1

# Regras para classificar os tiers, calculada para cada review e armazenada para
# a tier list automática. Se baseia na nota de 0 a 10 e atribui essas classes 
# para cada álbum, que podem ser usadas para criar uma tier list automática. Ela
# pode ser ajustada para refletir as preferências da comunidade, e é uma maneira
# de organizar os álbuns de acordo com a avaliação média, facilitando a visualização
# e comparação entre eles. O critério de desempate é a nota (mais alta fica na frente)
TIER_THRESHOLDS = [
    {"tier": "S", "min_score": 9.5},
    {"tier": "A", "min_score": 8.0},
    {"tier": "B", "min_score": 6.0},
    {"tier": "C", "min_score": 4.0},
    {"tier": "D", "min_score": 2.0},
    {"tier": "E", "min_score": 0.0},
]

def calculate_tier(average_score: float) -> str:
    """
    Dada uma nota média, retorna a qual Tier o álbum pertence.
    """
    for threshold in TIER_THRESHOLDS:
        if average_score >= threshold["min_score"]:
            return threshold["tier"]
            
    return "C"

# Sistema de ranks que são atribuidos automaticamente pra um usuário por ter 
# alcançado um certo número de reviews, platinas, posts, comentários, votos ou 
# streak. Esses ranks são exibidos no perfil do usuário e servem para reconhecer
# e/ou bonificar de certa forma o user. Quando chama na requisição, é passado o JSON completo
USER_RANKS = {
    'REVIEW': {
        'LEVEL_3': {'min': 150, 'title': "Sommelier de Vinil"},
        'LEVEL_2': {'min': 51, 'title': "Crítico"},
        'LEVEL_1': {'min': 11, 'title': "Explorador Musical"},
        'DEFAULT': "Ouvinte Casual"
    },
    'PLATINUM': {
        'LEVEL_3': {'min': 10, 'title': "Arquivista Mestre"},
        'LEVEL_2': {'min': 5, 'title': "Completista"},
        'LEVEL_1': {'min': 1, 'title': "Fã Dedicado"}
    },
    'POST': {
        'LEVEL_3': {'min': 10, 'title': "Biógrafo"},
        'LEVEL_2': {'min': 5, 'title': "Jornalista Musical"},
        'LEVEL_1': {'min': 1, 'title': "Colunista"}
    },
    'COMMENT': {
        'LEVEL_3': {'min': 100, 'title': "Crítico de Plantão"},
        'LEVEL_2': {'min': 20, 'title': "Comentador Ativo"},
        'LEVEL_1': {'min': 5, 'title': "Participante Engajado"}
    },
    'VOTE': {
        'LEVEL_3': {'min': 500, 'title': "Eleitor de Ouro"},
        'LEVEL_2': {'min': 100, 'title': "Eleitor de Prata"},
        'LEVEL_1': {'min': 20, 'title': "Eleitor de Bronze"}
    },
    'STREAK': {
        'LEVEL_3': {'min': 30, 'title': "Maratonista Musical"},
        'LEVEL_2': {'min': 7, 'title': "Viciado em Música"},
        'LEVEL_1': {'min': 3, 'title': "Ouvinte Dedicado"}
    }
}