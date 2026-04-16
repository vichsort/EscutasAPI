from pydantic import BaseModel, Field, ConfigDict, UUID4, field_validator, model_validator
from typing import List, Optional
from datetime import datetime, timezone

class TrackInput(BaseModel):
    id: Optional[str] = None
    name: str 
    track_number: int
    userScore: Optional[float] = Field(None, ge=0, le=10)
    is_ignored: bool = False

    @model_validator(mode='after')
    def validate_score(self) -> 'TrackInput':
        """Garante que, se a faixa não foi ignorada, ela TEM que ter uma nota válida."""
        if not self.is_ignored and self.userScore is None:
            raise ValueError(f"Você deve dar uma nota para a faixa '{self.name}' ou ignorá-la.")
        return self

class AlbumInput(BaseModel):
    id: Optional[str] = None
    name: str
    artist: str
    cover: Optional[str] = None 

class ReviewCreate(BaseModel):
    album: AlbumInput
    review_text: Optional[str] = None
    listened_date: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    tracks: List[TrackInput]
    is_private: bool = False

    @field_validator('listened_date', mode='before')
    @classmethod
    def parse_brazilian_date(cls, v):
        """Pega a string 'dd/mm/yyyy' do Frontend e cospe um objeto datetime"""
        if not v:
            return datetime.now(timezone.utc)
        if isinstance(v, str):
            try:
                parsed = datetime.strptime(v, "%d/%m/%Y")
                return parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                raise ValueError("Formato de data inválido. Use dd/mm/yyyy.")
        return v

    @model_validator(mode='after')
    def check_at_least_one_track_rated(self) -> 'ReviewCreate':
        """Garante que o usuário não ignorou o álbum inteiro"""
        if all(track.is_ignored for track in self.tracks):
            raise ValueError("Você não pode ignorar todas as faixas do álbum. Pelo menos uma deve ser avaliada.")
        return self

class TrackOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID4
    track_name: str 
    track_number: int
    score: Optional[float] = None
    is_ignored: bool

class ReviewSummary(BaseModel):
    """Para listagens (Sidebar, Library)"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    user_id: UUID4 
    spotify_album_id: str
    album_name: str
    artist_name: str
    cover_url: Optional[str] = None 
    review_text: Optional[str] = None
    average_score: float
    tier: str
    created_at: datetime
    is_private: bool
    artist_genres: list = []

class ReviewFull(ReviewSummary):
    """Para visualização detalhada. Herda tudo acima e adiciona as faixas."""
    tracks: List[TrackOutput]

class TrackUpdate(BaseModel):
    id: str  # Obrigatório para o backend saber qual faixa do banco editar
    userScore: Optional[float] = Field(None, ge=0, le=10)
    is_ignored: Optional[bool] = None

class ReviewUpdate(BaseModel):
    review_text: Optional[str] = None
    is_private: Optional[bool] = None
    tracks: Optional[List[TrackUpdate]] = None