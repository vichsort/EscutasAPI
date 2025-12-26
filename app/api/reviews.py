from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User
from app.models.review import AlbumReview, TrackReview
from app.services.spotify_service import SpotifyService

reviews_bp = Blueprint('reviews', __name__, url_prefix='/api/reviews')

def get_authenticated_user():
    """
    Helper interno para validar o token do Spotify e 
    retornar a instância do Usuário (User Model) do nosso banco.
    """
    service = SpotifyService()
    sp_client = service.get_client()
    
    if not sp_client:
        return None
    
    # Pede ao Spotify quem é o dono do token atual
    spotify_user_data = sp_client.current_user()
    spotify_id = spotify_user_data['id']
    
    # Busca no nosso banco pelo Spotify ID
    user = User.query.filter_by(spotify_id=spotify_id).first()
    
    # Se o usuário não existir no nosso banco ainda (primeiro acesso), criamos agora.
    # Isso garante que nunca tenhamos erro de Foreign Key.
    if not user:
        user = User(
            spotify_id=spotify_id,
            display_name=spotify_user_data.get('display_name'),
            email=spotify_user_data.get('email')
        )
        db.session.add(user)
        db.session.commit()
        
    return user

@reviews_bp.route('', methods=['POST'])
def create_review():
    """
    Cria uma nova review completa (Álbum + Faixas + Texto).
    
    Payload Esperado (JSON):
    {
        "album": {
            "id": "spotify_album_id",
            "name": "Nome do Album",
            "artist": "Nome do Artista",
            "cover": "url_da_imagem"
        },
        "review_text": "Achei esse álbum incrível porque...",
        "tracks": [
            { "id": "t1", "name": "Faixa 1", "track_number": 1, "userScore": 9.5 },
            { "id": "t2", "name": "Faixa 2", "track_number": 2, "userScore": 8.0 }
        ]
    }
    """
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Usuário não autenticado"}), 401

    data = request.json
    album_data = data.get('album')
    tracks_data = data.get('tracks', [])
    review_text = data.get('review_text', '')

    if not album_data or not tracks_data:
        return jsonify({"error": "Dados incompletos (album ou tracks faltando)"}), 400

    try:
        # 1. Cria a Review do Álbum (Pai)
        # Note que não checamos se já existe. O usuário pode criar múltiplas reviews (diário).
        review = AlbumReview(
            user_id=user.id, # UUID do usuário
            spotify_album_id=album_data['id'],
            album_name=album_data['name'],
            artist_name=album_data['artist'],
            cover_url=album_data['cover'],
            review_text=review_text
        )

        # 2. Cria as Reviews das Faixas (Filhos)
        for t_data in tracks_data:
            track = TrackReview(
                spotify_track_id=t_data['id'],
                track_name=t_data['name'],
                track_number=t_data['track_number'],
                score=float(t_data['userScore']) # Garante que é float
            )
            # O append popula o album_review_id automaticamente no commit
            review.tracks.append(track)

        # 3. Calcula Média e Tier
        review.update_stats()

        # 4. Salva tudo no banco (Transação Atômica)
        db.session.add(review)
        db.session.commit()

        return jsonify({
            "message": "Review salva com sucesso!",
            "review": review.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@reviews_bp.route('/history', methods=['GET'])
def get_user_history():
    """
    Retorna todas as reviews do usuário logado, da mais recente para a mais antiga.
    """
    user = get_authenticated_user()
    if not user:
        return jsonify({"error": "Usuário não autenticado"}), 401
    
    # Busca reviews desse usuário ordenadas por data
    reviews = AlbumReview.query.filter_by(user_id=user.id)\
        .order_by(AlbumReview.created_at.desc())\
        .all()
        
    return jsonify([r.to_dict() for r in reviews])

@reviews_bp.route('/<uuid:review_id>', methods=['GET'])
def get_review_details(review_id):
    """
    Busca uma review específica pelo UUID.
    Útil para compartilhar links: escutas.com/review/uuid-aqui
    """
    review = AlbumReview.query.get_or_404(review_id)
    return jsonify(review.to_dict())