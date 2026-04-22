# Regras de Curadoria da Comunidade para classificar ou desclassificar um album.
# Quantos votos líquidos (votos positivos - votos negativos) são necessários 
# para a comunidade alterar o status de um álbum na Platina.
CURATION_THRESHOLD = 1

# Quantidade de avaliações mínima que precisa ser passada (ou igual) para que ele seja 
# considerado parte do hall da fama representando um album muito valioso em questão
# da sua avaliação.
HALL_OF_FAME_MIN_REVIEWS = 3

# Quantidade de dias máximo em que um dia pode ser considerado tendência (está em alta). 
TRENDING_DAYS_LIMIT = 7

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

# Modelos de título para os meses temáticos. O {genre} é um placeholder que é substituído
# pelo gênero musical do mês, criando títulos envolventes e personalizados para cada edição 
# temática. Esses modelos ajudam a criar uma identidade única para cada mês, incentivando a 
# participação da comunidade e destacando o foco musical de forma criativa.
MONTH_TITLE_PRESETS = [
    "A Fase do {genre}",
    "Mês do {genre}",
    "Imersão {genre}",
    "Imersão no {genre}",
    "Imersão em {genre}",
    "Vibe {genre}",
    "A Era {genre}",
    "A Era do {genre}",
    "Onda {genre}",
    "Explorando o {genre}",
    "Dias de {genre}",
    "Só {genre}",
    "Intensivo de {genre}"
    "{genre} on fire"
]

# Palavras chave que são consumidas em utils/text_util.py para classificar ou 
# limpar os títulos dos álbuns e faixas, e que são armazenadas aqui para facilitar a manutenção.
# Se um álbum tem um desses termos no título, ele pode ser classificado como não-canônico 
# (coletânea, ao vivo, edição especial) e uma faixa que contém um desses termos pode ser marcada 
# como ignorável (bônus, take alternativo, versão ao vivo ou remix).
IGNORED_CONTENT_REGEX = {
    "EDITIONS": [
        'deluxe', 'expanded', 'anniversary', 'bonus', 'special edition', 
        'legacy', 'tour edition', 'remaster', 'mix', 'remix', 'mono', 'stereo'
    ],
    "LIVE": [
        'live', 'ao vivo', 'en vivo', 'sessions', 'unplugged', 'concert', 'bbc'
    ],
    "COMPILATIONS": [
        'greatest hits', 'best of', 'anthology', 'essential', 'ultimate', 'platinum collection'
    ],
    "SKIPPABLE_TRACKS": [
        'take', 'demo', 'instrumental', 'acappella', 'backing track', 
        'early version', 'alternate', 'alt version', 'rehearsal'
    ]
}

# Conteúdo do gerador de templates automático para o wrapped mensal do usuário. 
# Ele é usado para criar um post em Markdown formatado, que é salvo como rascunho (DRAFT) 
# no blog do usuário. O template é uma string com placeholders que são substituídos pelos dados 
# calculados, como o nome do mês, total de reviews, média de avaliações, nome do melhor álbum, 
# artista e URL da playlist. O resultado é um texto envolvente e personalizado que resume a 
# experiência musical do usuário naquele mês, pronto para ser compartilhado com a comunidade.
WRAPPED_MONTHLY_TEMPLATE = """
Fala, galera! O mês de **{nome_mes}** acabou e está na hora de abrir os cofres do que rolou nos meus fones de ouvido. 

Neste mês, eu mergulhei em **{total_reviews} álbuns diferentes**. Foi uma verdadeira montanha-russa sonora, e a minha média de avaliações ficou em **{average_rating} estrelas**. (Fui bonzinho ou carrasco? Fica aí o questionamento).

### 🏆 O Álbum de Ouro
De tudo que eu ouvi, teve uma obra que alugou um triplex na minha cabeça. O grande destaque de {nome_mes} vai para:
> **{best_album_name}**, do(a) **{best_album_artist}** > *(Nota: {best_rating} / 5.0)*

Se você não ouviu esse álbum ainda, faça um favor aos seus ouvidos e dê o play.

### 🎧 A Trilha Sonora do Mês
Como palavra não faz barulho, eu juntei as melhores faixas dos álbuns que receberam nota 4.0 ou mais e criei uma playlist exclusiva no Spotify com o creme de la creme do meu mês.

👉 **[Clique aqui para ouvir a minha Playlist de {nome_mes}]({playlist_url})**

---
*E vocês? O que não saiu do repeat no Spotify de vocês esse mês? Deixa aí nos comentários!*
"""

# Bem autoexplicativo... São os meses do ano (uau) usado para o wrapped
MESES = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }