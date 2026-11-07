class EscutasError(Exception):
    """
    Exceção base para toda a aplicação.
    Todas as exceções customizadas devem herdar desta.
    """
    def __init__(self, message: str, status_code: int = 400, payload: dict = None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status'] = 'error'
        return rv


# --- Exceções de Autenticação & Permissão (401 / 403) ---

class AuthenticationError(EscutasError):
    def __init__(self, message="Falha na autenticação. Faça login novamente."):
        super().__init__(message, status_code=401)

class AuthorizationError(EscutasError):
    def __init__(self, message="Você não tem permissão para realizar esta ação."):
        super().__init__(message, status_code=403)


# --- Exceções de Recursos (404) ---

class ResourceNotFoundError(EscutasError):
    def __init__(self, resource_name="Recurso"):
        super().__init__(f"{resource_name} não encontrado(a).", status_code=404)


# --- Exceções de Integração Externa (502 / 400) ---

class SpotifyAPIError(EscutasError):
    def __init__(self, message="Erro na comunicação com o Spotify.", status_code=502):
        super().__init__(message, status_code=status_code)

class SpotifyRateLimitError(SpotifyAPIError):
    """
    O Spotify respondeu 429. 'quota_exceeded' indica cota da conta de desenvolvedor
    estourada (reason QUOTA_EXCEEDED); caso contrário é o rate limit comum.
    O retry_after vai no corpo JSON e não no header: o Flask-Limiter
    (RATELIMIT_HEADERS_ENABLED) sobrescreve o Retry-After de toda resposta.
    """
    def __init__(self, quota_exceeded: bool = False, retry_after: int = None):
        if quota_exceeded:
            message = "O limite de uso da API do Spotify foi atingido. Tente novamente mais tarde."
        else:
            message = "O Spotify está recebendo requisições demais. Tente novamente em instantes."
        super().__init__(message, status_code=503)
        self.quota_exceeded = quota_exceeded
        self.retry_after = retry_after
        self.payload = {"retry_after": retry_after} if retry_after is not None else None


# --- Exceções de Regra de Negócio (400) ---

class BusinessRuleError(EscutasError):
    def __init__(self, message="Operação inválida."):
        super().__init__(message, status_code=400)

class DataValidationError(EscutasError):
    def __init__(self, message="Erro de validação nos dados enviados.", errors=None):
        # O payload vai carregar a lista de erros detalhada que o Pydantic gera
        super().__init__(message, status_code=400, payload={"errors": errors or []})