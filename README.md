# Escutas API

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Python](https://img.shields.io/badge/Testing-Pytest-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-black.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-orange.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-blue.svg)
![Redis](https://img.shields.io/badge/Redis-Cloud-red.svg)

Backend robusto para uma rede social de avaliação de álbuns musicais ("Letterboxd para Música").
Construído com **Flask**, **PostgreSQL** e **Spotify API**, focado em Clean Architecture, performance e escalabilidade.

## Tecnologias

* **Core:** Python 3.10+, Flask, SQLAlchemy.
* **Banco de Dados:** PostgreSQL (com índices otimizados).
* **Autenticação:** OAuth2 (Spotify) + Session Cookies.
* **Validação:** Pydantic (Schemas).
* **Cache:** Redis (ou SimpleCache em dev).
* **Integração:** Spotipy.

---

## Pré-requisitos

Antes de começar, certifique-se de ter instalado:

* [Python 3.11+](https://www.python.org/)
* [PostgreSQL](https://www.postgresql.org/)
* [Ngrok](https://ngrok.com/) (Essencial para testar o callback do Spotify)
* [Redis](https://redis.io/) (Opcional, mas recomendado para performance)

---

## Instalação e Configuração

### 1. Clone e Ambiente Virtual

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/escutas-api.git
cd escutas-api

# Crie e ative o ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

```

### 2. Configuração do Spotify Developer

Para que o login funcione, você precisa criar um app no Spotify:

1. Acesse o [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
2. Crie um novo App.
3. Anote o **Client ID** e o **Client Secret**.
4. Nas configurações do App ("Edit Settings"), adicione a Redirect URI.
* *Nota:* Se usar Ngrok (recomendado), você atualizará isso no passo 4.
* Para rodar localmente sem Ngrok: `http://127.0.0.1:5000/api/callback`



### 3. Variáveis de Ambiente (.env)

Crie um arquivo `.env` na raiz do projeto (use o `.env.example` como base):

```ini
# --- Configurações do App ---
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY="sua-chave-secreta-super-segura"

# --- Banco de Dados ---
# Formato: postgresql://usuario:senha@host:porta/nome_banco
DATABASE_URL="postgresql://postgres:suasenha@localhost:5432/escutas"

# --- Spotify Integration ---
SPOTIFY_CLIENT_ID="cole_seu_client_id_aqui"
SPOTIFY_CLIENT_SECRET="cole_seu_client_secret_aqui"
SPOTIFY_REDIRECT_URI="http://127.0.0.1:5000/api/callback" 
# (OBS: Mude a URI acima se for usar Ngrok, veja passo 4)

# --- Cache (Opcional) ---
# Se não definido, usa memória RAM simples
# REDIS_URL="redis://localhost:6379/0"

```

### 4. Configurando o Ngrok (Tunelamento)

Como o Spotify precisa acessar sua máquina para devolver o token de login, o Ngrok cria um endereço HTTPS público para seu localhost.

1. Inicie o servidor Flask (em um terminal):
```bash
python run.py

```


2. Inicie o Ngrok (em outro terminal):
```bash
ngrok http 5000

```


3. Copie a URL HTTPS gerada pelo Ngrok (ex: `https://a1b2-c3d4.ngrok-free.app`).
4. **Atualize no `.env`:**
```ini
SPOTIFY_REDIRECT_URI="https://a1b2-c3d4.ngrok-free.app/api/callback"

```


5. **Atualize no Spotify Dashboard:** Adicione essa mesma URL nas "Redirect URIs" do seu App.

---

## Banco de Dados

O projeto usa **Flask-Migrate** (Alembic) para versionamento do banco.

```bash
# 1. Crie o banco de dados no Postgres (caso não exista)
createdb escutas

# 2. Gere as tabelas e índices
flask db upgrade

# (Opcional) Se fizer alterações nos Models no futuro:
# flask db migrate -m "Descrição da mudança"
# flask db upgrade

```

---

## ▶️ Rodando o Projeto

Com tudo configurado:

```bash
python run.py

```

O servidor estará rodando em `http://127.0.0.1:5000` (ou na URL do Ngrok).

### Testando o Fluxo

1. Abra o navegador e acesse: `/api/login`
2. Você será redirecionado para o Spotify.
3. Após aceitar, voltará para a API e o Token será salvo no banco.
4. Teste uma rota autenticada: `/api/spotify/now-playing`

---

## Arquitetura do Projeto

O projeto segue princípios de **Clean Architecture** adaptados para Flask:

* **`app/api/` (Controllers):** Recebem requisições HTTP, validam input e chamam serviços. Retornam JSON.
* **`app/models/` (Data Layer):** Definições das tabelas do banco e índices.
* **`app/schemas/` (Data Transfer):** Classes **Pydantic** que definem o contrato de dados (entrada e saída), garantindo segurança e tipagem.
* **`app/services/` (Business Logic):** Contêm toda a regra de negócio. Atuam como serviços e entregam apenas a parte lógica e contratual do sistema.
* **`app/utils/` (Repositórios & Ferramentas):** Isolam o processamento pesado. Aqui vivem os Cientistas de Dados (queries complexas em SQLAlchemy) e geradores de templates.

## Arquitetura de testes

Divididos em três subpastas, os tests efetuados com pytest concluem verificações de controllers, data, services e utils.

* **`tests/infrastructure/` (Infra):** Indiferem do restante do sistema, condizem apenas à aplicabilidade sistemática do projeto. No futuro pode servir para responses e demais características, atualmente aplicados para verificar o cacheamento.
* **`tests/integrations/` (Api):** Análise do fluxo completo que simulam contextos inteiros reais, sem efetuar as chamadas à API do spotify por fazer o sequestro das funções realizadoras. Como cirurgias mais precisas que detalham mais os pontos.
* **`tests/unit/` (Unitários):** Presença e atividade de retorno seguindo o esperado, sem adentrar em camadas complexas de processamento, por exemplo.

### Testando o projeto

A API possui uma suíte de testes de integração e infraestrutura rigorosa, utilizando Mocks para simular a API do Spotify e garantir a segurança das regras de negócio sem consumir cotas de rede.

```bash
# Rodar todos os testes
pytest

# Rodar testes com log detalhado de falhas
pytest -v
```

### Principais Otimizações

* **Separação de Responsabilidades (SRP):** Prevenção de "God Objects" delegando matemática de banco de dados para utilitários isolados.
* **Índices e Agregações:** Consultas pesadas de Wrapped e Distribuição de Tiers resolvidas nativamente no PostgreSQL (func.avg, func.count).
* **Eager Loading:** Uso de `joinedload` para eliminar o problema de N+1 queries em listagens.
* **Cache:** Cacheamento e buscas curtas (Omnibox) de buscas do Spotify para economizar cota de API.