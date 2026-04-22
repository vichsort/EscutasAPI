from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal

SearchType = Literal['ARTIST', 'ALBUM', 'TRACK', 'REVIEW']

class SearchResult(BaseModel):
    """
    Schema simplificado para resultados de busca rápida.
    Utilizado para alimentar o dropdown de menções (@) no Blog.
    """
    model_config = ConfigDict(from_attributes=True)

    # O ID pode ser o UUID da Review ou o ID alfanumérico do Spotify
    id: str = Field(..., description="ID único da entidade (Spotify ID ou UUID)")

    # O nome que aparecerá no dropdown (ex: 'Pink Floyd' ou 'The Dark Side of the Moon')
    name: str = Field(..., description="Nome ou título da entidade")
    type: SearchType = Field(..., description="Tipo da entidade encontrada")
    image_url: Optional[str] = Field(None, description="URL da imagem para miniatura")

    # (Opcional) Nome do artista para quando o tipo for ALBUM ou TRACK
    # Ajuda o usuário a distinguir entre "Greatest Hits" de bandas diferentes
    subtitle: Optional[str] = Field(None, description="Subtítulo informativo (ex: Nome do Artista)")