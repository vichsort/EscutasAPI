import pytest

def test_busca_rapida_ignora_query_curta(auth_client):
    """
    Se o usuário digitar só 1 letra (ex: 'a'), a API não deve bater no Spotify
    para economizar requisições, retornando uma lista vazia instantaneamente.
    """
    response = auth_client.get('/api/search?q=a')
    data = response.get_json()
    print(data)

    assert response.status_code == 200
    assert data['data'] == []
    assert data['status'] == 'success'


def test_busca_rapida_formata_dados_do_spotify_corretamente(auth_client, mock_spotify):
    """
    Testa se o SearchService está pegando o JSON complexo do Spotify
    e 'achatando' corretamente para o nosso schema SearchResult.
    """
    # 1. Configurando o nosso Dublê (Mock) do Spotify
    # Pegamos o cliente falso que a sua fixture 'mock_spotify' criou
    fake_sp_client = mock_spotify.return_value
    
    # Ensinamos o dublê a devolver um JSON simulado do Spotify quando chamarem .search()
    fake_sp_client.search.return_value = {
        "artists": {
            "items": [{
                "id": "daft_punk_id", 
                "name": "Daft Punk", 
                "images": [{"url": "http://imagem-daft.jpg"}]
            }]
        },
        "albums": {
            "items": [{
                "id": "discovery_id", 
                "name": "Discovery", 
                "images": [{"url": "http://imagem-discovery.jpg"}],
                "artists": [{"name": "Daft Punk"}]
            }]
        },
        "tracks": {
            "items": [{
                "id": "onemoretime_id", 
                "name": "One More Time", 
                "album": {"images": [{"url": "http://imagem-musica.jpg"}]},
                "artists": [{"name": "Daft Punk"}]
            }]
        }
    }

    # 2. Fazemos a requisição (o usuário digitou "daft")
    response = auth_client.get('/api/search?q=daft&limit=1')
    data = response.get_json()['data']

    # 3. Verificações (Asserts)
    assert response.status_code == 200
    assert len(data) == 3 # 1 Artista, 1 Álbum, 1 Música

    # Extraindo para checar os tipos
    tipos = {item['type']: item for item in data}

    # Testando o Artista
    assert 'ARTIST' in tipos
    assert tipos['ARTIST']['name'] == "Daft Punk"
    assert tipos['ARTIST']['subtitle'] == "Artista"
    assert tipos['ARTIST']['image_url'] == "http://imagem-daft.jpg"

    # Testando o Álbum
    assert 'ALBUM' in tipos
    assert tipos['ALBUM']['name'] == "Discovery"
    assert tipos['ALBUM']['subtitle'] == "Daft Punk" # O subtitle puxou o nome da banda certinho!
    
    # Testando a Música
    assert 'TRACK' in tipos
    assert tipos['TRACK']['name'] == "One More Time"
    assert tipos['TRACK']['subtitle'] == "Música de Daft Punk"