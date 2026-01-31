from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from app.services.spotify_service import SpotifyService
from app.utils.response_util import success_response, APIError
from app.schemas.user import UserPublic 

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/spotify-url', methods=['GET'])
def get_spotify_url():
    """Gera a URL para o botão do Frontend"""
    redirect_uri = request.args.get('redirect_uri', "http://127.0.0.1:5173/auth/callback")

    sp_oauth = SpotifyService.get_oauth_object(redirect_uri=redirect_uri)
    auth_url = sp_oauth.get_authorize_url()
    
    return jsonify({"url": auth_url})

@auth_bp.route('/callback', methods=['GET'])
def callback():
    """
    Recebe code -> Chama Service -> Retorna JWT e UserDTO
    """
    code = request.args.get('code')
    
    # O front deve mandar a redirect_uri que usou, ou usamos a padrão
    # O Spotify exige que seja EXATAMENTE a mesma usada para gerar a URL
    redirect_uri = "http://127.0.0.1:5173/auth/callback" 

    if not code:
        raise APIError("Código de autorização não fornecido.", 400)

    try:
        user, api_token = AuthService.execute_login(code, redirect_uri)
        user_dto = UserPublic.model_validate(user).model_dump()

        return success_response(
            data={
                "access_token": api_token,
                "user": user_dto
            },
            message="Login realizado com sucesso!"
        )

    except ValueError as e:
        raise APIError(str(e), 400)
    except Exception as e:
        print(f"Erro Auth: {e}")
        raise APIError("Falha interna na autenticação.", 500)