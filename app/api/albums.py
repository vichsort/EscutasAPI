from flask import Blueprint, request, jsonify
from app.services.spotify_service import SpotifyService

albums_bp = Blueprint('albums', __name__, url_prefix='/api/albums')

@albums_bp.route('/search', methods=['GET'])
def search():
    """
    Busca álbuns públicos.
    Params (Entrada): ?q=termo&limit=10
    Params (Saída): JSON List[{ id, name, artist, cover, release_date }]
    """
    sp = SpotifyService().get_client()
    if not sp: return jsonify({"error": "Unauthorized"}), 401

    query = request.args.get('q')
    limit = request.args.get('limit', 10)
    
    results = sp.search(q=query, limit=limit, type='album')
    
    # Tratamento de dados (Clean Code)
    data = [{
        "id": item['id'],
        "name": item['name'],
        "artist": item['artists'][0]['name'],
        "cover": item['images'][0]['url'] if item['images'] else None,
        "release_date": item['release_date']
    } for item in results['albums']['items']]

    return jsonify(data)

@albums_bp.route('/my-saved', methods=['GET'])
def my_saved():
    """
    Álbuns salvos do usuário.
    Params (Entrada): ?limit=20&offset=0
    Params (Saída): JSON List[{ id, name, artist, cover, added_at }]
    """
    sp = SpotifyService().get_client()
    if not sp: return jsonify({"error": "Unauthorized"}), 401

    limit = request.args.get('limit', 20)
    offset = request.args.get('offset', 0)
    
    results = sp.current_user_saved_albums(limit=limit, offset=offset)
    
    data = [{
        "id": item['album']['id'],
        "name": item['album']['name'],
        "artist": item['album']['artists'][0]['name'],
        "cover": item['album']['images'][0]['url'] if item['album']['images'] else None,
        "added_at": item['added_at']
    } for item in results['items']]

    return jsonify(data)