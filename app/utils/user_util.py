from app.exceptions import AuthorizationError

def resolve_target_user(user_param: str, current_user):
    """
    Resolve o "Magic 'me'".
    Descobre de quem é o perfil que estamos acessando e quem está fazendo o pedido.
    
    Retorna uma tupla: (target_user_id, request_user_id)
    """
    # Se a URL for /api/users/me/...
    if user_param.lower() == 'me':
        if not current_user:
            raise AuthorizationError("Login obrigatório para acessar este recurso.")
        # O alvo é ele mesmo, e quem pede é ele mesmo
        return str(current_user.id), str(current_user.id)
    
    # Se a URL for /api/users/<uuid>/...
    # O request_user_id será o ID de quem tá logado, 
    # ou None se for um visitante anônimo
    request_user_id = str(current_user.id) if current_user else None
    
    return str(user_param), request_user_id