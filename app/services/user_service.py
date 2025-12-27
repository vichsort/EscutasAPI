from sqlalchemy import or_
from app.models.user import User

class UserService:
    
    @staticmethod
    def search_users(query_str):
        """
        Busca usuários por Nome (parcial) ou Spotify ID (exato).
        """
        if not query_str:
            return []
            
        # Limpa espaços extras
        term = query_str.strip()
        
        # Query Híbrida:
        # 1. display_name CONTÉM o termo (case insensitive)
        # 2. OU spotify_id É IGUAL ao termo
        users = User.query.filter(
            or_(
                User.display_name.ilike(f'%{term}%'),
                User.spotify_id == term
            )
        ).limit(20).all() # Limitamos a 20 para não travar o front se buscar "a"
        
        # Formata o retorno (Dados Públicos apenas!)
        results = []
        for user in users:
            results.append({
                "uuid": str(user.id), # ID interno para links
                "spotify_id": user.spotify_id, # ID visual
                "display_name": user.display_name,
                # Futuro: Adicionar campo 'avatar_url' no banco de dados
            })
            
        return results

    @staticmethod
    def get_user_profile(user_uuid):
        """
        Busca um usuário específico pelo UUID (para abrir o perfil dele).
        """
        user = User.query.get(user_uuid)
        if not user:
            return None
            
        return {
            "uuid": str(user.id),
            "display_name": user.display_name,
            "spotify_id": user.spotify_id,
            "joined_at": user.created_at.isoformat()
        }