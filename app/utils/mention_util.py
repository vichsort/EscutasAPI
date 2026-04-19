from app.schemas.blog import MentionBase

def sync_post_mentions(post_id, new_mentions_dto: list[MentionBase], db_session, mention_model_class):
    """
    Sincroniza as menções de um post. 
    Deleta as que foram removidas e adiciona apenas as novas.
    """
    # Busca as menções atuais do post no banco de dados
    existing_mentions = db_session.query(mention_model_class).filter_by(post_id=post_id).all()

    # Mapeia o que já existe usando uma tupla única (TIPO, ID)
    # Ex: ('ARTIST', 'daft_punk_id')
    existing_map = {(m.target_type, str(m.target_id)): m for m in existing_mentions}
    existing_keys = set(existing_map.keys())

    # Mapeia o que veio do Front-end (Novo array)
    new_map = {(m.target_type, str(m.target_id)): m for m in new_mentions_dto}
    new_keys = set(new_map.keys())

    keys_to_delete = existing_keys - new_keys
    keys_to_add = new_keys - existing_keys

    # Exclui
    for key in keys_to_delete:
        db_session.delete(existing_map[key])

    # Insere
    for key in keys_to_add:
        mention_data = new_map[key]
        new_mention = mention_model_class(
            post_id=post_id,
            target_type=mention_data.target_type,
            target_id=mention_data.target_id,
            target_name=mention_data.target_name
        )
        db_session.add(new_mention)