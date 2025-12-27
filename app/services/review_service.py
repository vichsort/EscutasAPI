import bleach
from datetime import datetime
from app.extensions import db
from app.models.review import AlbumReview, TrackReview
from app.models.user import User
from app.utils.response_util import APIError
from sqlalchemy import extract, and_

class ReviewService:
    
    @staticmethod
    def create_review(user: User, data: dict) -> dict:
        """
        Contém TODA a regra de negócio para criar uma review.
        Lança APIError se algo estiver errado.
        """
        # 1. Validação de Dados (Sanitization)
        raw_text = data.get('review_text', '')
        clean_text = bleach.clean(raw_text, tags=[], strip=True)

        if len(clean_text) > 5000:
            raise APIError("Texto muito longo. Máximo 5000 caracteres.", 400)

        album_data = data.get('album')
        tracks_data = data.get('tracks', [])

        if not album_data or not tracks_data:
            raise APIError("Dados do álbum ou faixas estão faltando.", 400)

        # 2. Lógica de Persistência
        try:
            review = AlbumReview(
                user_id=user.id,
                spotify_album_id=album_data['id'],
                album_name=album_data['name'],
                artist_name=album_data['artist'],
                cover_url=album_data['cover'],
                review_text=clean_text
            )

            for t_data in tracks_data:
                # Validação extra de nota
                score = float(t_data['userScore'])
                if not (0 <= score <= 10):
                    raise APIError(f"Nota inválida na faixa {t_data.get('name')}", 400)

                track = TrackReview(
                    spotify_track_id=t_data['id'],
                    track_name=t_data['name'],
                    track_number=t_data['track_number'],
                    score=score
                )
                review.tracks.append(track)

            review.update_stats()
            
            db.session.add(review)
            db.session.commit()
            
            return review.to_dict()

        except APIError:
            raise # Repassa erros que nós mesmos criamos
        except Exception as e:
            db.session.rollback()
            # Logar o erro real aqui seria o ideal
            print(f"Erro no banco: {e}") 
            raise APIError("Falha ao salvar review no banco de dados.", 500)

    @staticmethod
    def get_reviews(user_id, page=1, per_page=20, filters=None):
        """
        Busca reviews com filtros dinâmicos e paginação.
        
        Args:
            user_id: UUID do usuário
            page: Número da página
            per_page: Itens por página
            filters: Dict com 'start_date', 'end_date', 'album_id'
        
        Returns:
            SQLAlchemy Pagination Object
        """
        # 1. Query Base
        query = AlbumReview.query.filter_by(user_id=user_id)
        
        # 2. Aplicação de Filtros Dinâmicos
        if filters:
            # Filtro por Álbum Específico (Histórico do Álbum)
            if filters.get('album_id'):
                query = query.filter_by(spotify_album_id=filters['album_id'])
            
            # Filtro de Data Inicial (Para Calendário/Feed)
            if filters.get('start_date'):
                try:
                    # Espera formato YYYY-MM-DD
                    dt_start = datetime.strptime(filters['start_date'], '%Y-%m-%d')
                    # Ajusta para o início do dia (00:00:00)
                    query = query.filter(AlbumReview.created_at >= dt_start)
                except ValueError:
                    pass # Ignora data inválida ou lança erro

            # Filtro de Data Final
            if filters.get('end_date'):
                try:
                    dt_end = datetime.strptime(filters['end_date'], '%Y-%m-%d')
                    # Ajusta para o final do dia (hack simples: adicionar filtro < dia seguinte ou ajustar time)
                    # Aqui vamos assumir comparação simples com o dia
                    query = query.filter(AlbumReview.created_at <= dt_end)
                except ValueError:
                    pass

        # 3. Ordenação (Mais recente primeiro)
        query = query.order_by(AlbumReview.created_at.desc())
        
        # 4. Paginação
        # error_out=False impede que retorne 404 se a página não existir (retorna lista vazia)
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_calendar_data(user_id, month, year):
        """
        Retorna as reviews organizadas por dia para o calendário.
        
        Estrutura de Retorno:
        {
            "27": [ {Review A}, {Review B} ],
            "28": [ {Review C} ]
        }
        
        A lista é ordenada da mais recente para a mais antiga.
        Assim, o índice [0] é sempre o último álbum ouvido no dia (o que aparece na capa).
        """
        # 1. Query: Filtra Mês/Ano e ordena por data DESC (mais recente primeiro)
        reviews = AlbumReview.query.filter(
            and_(
                AlbumReview.user_id == user_id,
                extract('month', AlbumReview.created_at) == month,
                extract('year', AlbumReview.created_at) == year
            )
        ).order_by(AlbumReview.created_at.desc()).all()
        
        calendar_map = {}
        
        for review in reviews:
            day = str(review.created_at.day)
            
            # Se o dia ainda não existe no mapa, cria uma lista vazia
            if day not in calendar_map:
                calendar_map[day] = []
            
            # Adiciona uma versão "leve" da review (sem tracks nem textão)
            # Isso deixa o calendário rápido de carregar.
            review_summary = {
                "id": str(review.id),
                "album_name": review.album_name,
                "artist_name": review.artist_name,
                "cover_url": review.cover_url,
                "score": review.average_score,
                "tier": review.tier,
                "created_at": review.created_at.isoformat()
            }
            
            calendar_map[day].append(review_summary)
                
        return calendar_map