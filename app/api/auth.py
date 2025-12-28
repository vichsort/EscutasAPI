from flask import Blueprint, redirect, request, jsonify, session, current_app
from app.services.spotify_service import SpotifyService
from app.services.auth_service import AuthService
from app.utils.decorator_util import require_auth # <--- Importante!
from app.schemas.user import UserPublic # Para retornar dados bonitos

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route('/login')
def login():
    """
    Redireciona para o Spotify.
    """
    # CORREÇÃO: Pegamos o objeto OAuth corretamente
    sp_oauth = SpotifyService.get_oauth_object()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@auth_bp.route('/callback')
def callback():
    """
    Recebe o código do Spotify, troca por tokens e loga o usuário.
    """
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "Código não fornecido"}), 400

    try:
        # 1. Troca código por token
        sp_oauth = SpotifyService.get_oauth_object()
        token_info = sp_oauth.get_access_token(code)
        
        # 2. Pega dados do usuário no Spotify
        # Criamos um client temporário só com o token para pegar o ID
        import spotipy
        sp = spotipy.Spotify(auth=token_info['access_token'])
        spotify_user_data = sp.current_user()

        # 3. Lógica de Banco (AuthService)
        user = AuthService.login_or_register_user(spotify_user_data, token_info)

        # 4. Salva na Sessão
        session.clear()
        session['user_id'] = str(user.id) # Usamos 'user_id' padrão
        
        # Redireciona para o Frontend (em dev pode ser JSON)
        # return redirect("http://localhost:5173/dashboard") 
        return jsonify({
            "status": "success",
            "message": "Login realizado!",
            "user": user.display_name
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@auth_bp.route('/logout')
def logout():
    """
    Limpa a sessão.
    """
    session.clear()
    return jsonify({"status": "success", "message": "Logout realizado."})

@auth_bp.route('/me')
@require_auth # <--- CORREÇÃO: Usa o decorator para validar sessão
def me(current_user):
    """
    Retorna o usuário logado.
    """
    # current_user já vem injetado pelo decorator (do banco de dados)
    # Convertemos para Pydantic para padronizar o JSON
    user_dto = UserPublic.model_validate(current_user)
    
    return jsonify({
        "status": "success",
        "logged_in": True,
        "data": user_dto.model_dump()
    })