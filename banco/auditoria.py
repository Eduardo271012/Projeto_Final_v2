from database import AuditoriaSistema, Usuario, db_session


def registrar_evento(
    usuario_id,
    area,
    acao,
    registro,
    registro_id,
    alteracoes,
):
    usuario = db_session.get(Usuario, usuario_id) if usuario_id else None
    nome_usuario = usuario.nome if usuario else "Usuário não identificado"
    papel_usuario = usuario.papel if usuario else "desconhecido"

    for campo, valor_anterior, valor_novo in alteracoes:
        if valor_anterior == valor_novo:
            continue
        db_session.add(
            AuditoriaSistema(
                usuario_id=usuario_id,
                usuario_nome=nome_usuario,
                usuario_papel=papel_usuario,
                area=area,
                acao=acao,
                registro=registro,
                registro_id=registro_id,
                campo=campo,
                valor_anterior=str(valor_anterior) if valor_anterior is not None else "-",
                valor_novo=str(valor_novo) if valor_novo is not None else "-",
            )
        )
