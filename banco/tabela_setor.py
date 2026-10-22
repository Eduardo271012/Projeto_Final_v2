from flask import redirect, url_for, flash
from database import *
from sqlalchemy.exc import SQLAlchemyError

def validar_setor(nome, descricao):
    if not nome:
        flash("Preencha o nome do setor", "error")
        return True
    if not descricao:
        flash("Preencha a descrição", "error")
        return True

    if len(nome) > 50:
        flash("O nome é muito longo", "error")
        return True
    if len(descricao) > 10000:
        flash("A descrição é muito longa", "error")
        return True

def salvar(nome, descricao):
    try:
        setor_novo = Setor(nome=nome, descricao=descricao)
        db_session.add(setor_novo)
        db_session.commit()
        flash("Setor cadastrado com sucesso", "success")
        return redirect(url_for("setor"))
    except SQLAlchemyError:
        db_session.rollback()
        flash("Erro ao cadastrar setor no banco de dados", "error")
        return redirect(url_for("cadastro_setor"))
    except Exception:
        db_session.rollback()
        flash("Erro inesperado", "error")
        return redirect(url_for("cadastro_setor"))