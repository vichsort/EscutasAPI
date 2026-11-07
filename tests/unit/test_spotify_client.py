import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from app.exceptions import SpotifyRateLimitError
from app.services.spotify_service import EscutasSpotify


class _FakeSpotifyHandler(BaseHTTPRequestHandler):
    """Responde na ordem as respostas enfileiradas em server.responses: (status, headers, body)."""

    def do_GET(self):
        self.server.hits += 1
        status, headers, body = self.server.responses.pop(0)
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


@pytest.fixture
def fake_spotify():
    server = HTTPServer(('127.0.0.1', 0), _FakeSpotifyHandler)
    server.responses = []
    server.hits = 0
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    sp = EscutasSpotify(auth='fake_token')
    sp.prefix = f'http://127.0.0.1:{server.server_port}/v1/'

    yield server, sp

    server.shutdown()
    server.server_close()


def _quota_body():
    return {"error": {"status": 429, "message": "Too many requests", "reason": "QUOTA_EXCEEDED"}}


def test_cota_estourada_falha_na_hora_sem_dormir(app, fake_spotify):
    server, sp = fake_spotify
    server.responses = [(429, {'Retry-After': '3600'}, _quota_body())]

    start = time.monotonic()
    with pytest.raises(SpotifyRateLimitError) as exc:
        sp.artist('0OdUWJ0sBjDrqHygGUXeCF')

    assert time.monotonic() - start < 2
    assert server.hits == 1
    assert exc.value.quota_exceeded is True
    assert exc.value.retry_after == 3600
    assert exc.value.status_code == 503


def test_rate_limit_curto_espera_e_tenta_de_novo(app, fake_spotify):
    server, sp = fake_spotify
    server.responses = [
        (429, {'Retry-After': '1'}, {"error": {"status": 429, "message": "Too many requests"}}),
        (200, {}, {"id": "0OdUWJ0sBjDrqHygGUXeCF", "name": "Artista Teste"}),
    ]

    data = sp.artist('0OdUWJ0sBjDrqHygGUXeCF')

    assert data['name'] == 'Artista Teste'
    assert server.hits == 2


def test_429_sem_retry_after_nao_e_cota(app, fake_spotify):
    server, sp = fake_spotify
    server.responses = [(429, {}, {"error": {"status": 429, "message": "Too many requests"}})]

    with pytest.raises(SpotifyRateLimitError) as exc:
        sp.artist('0OdUWJ0sBjDrqHygGUXeCF')

    assert server.hits == 1
    assert exc.value.quota_exceeded is False
    assert exc.value.retry_after is None
