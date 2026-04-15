# Regras de Classificação (Tiers)
# Baseado na nota de 0 a 10

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

# Regras de Curadoria da Comunidade para classificar ou desclassificar um album.
# Quantos votos líquidos (votos positivos - votos negativos) são necessários 
# para a comunidade alterar o status de um álbum na Platina.
CURATION_THRESHOLD = 1