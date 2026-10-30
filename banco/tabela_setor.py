from flask import flash
from database import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, func

def select_todos():
    # Adicionada esta função que estava faltando para listar os setores na tabela do HTML
    setor_sql = (
        select(Setor, func.count(Funcionario.id).label("funcionarios")).
        outerjoin(Funcionario, Setor.id == Funcionario.setor_id).
        group_by(Setor.id)
    )
    setor = db_session.execute(setor_sql).all()
    return setor

def select_ativos():
    setor_sql = (
        select(Setor, func.count(Funcionario.id).label("funcionarios")).
        outerjoin(Funcionario, Setor.id == Funcionario.setor_id).
        where(Setor.status_delete == 1).
        group_by(Setor.id)
    )
    setor = db_session.execute(setor_sql).all()
    return setor

def select_excluidos():
    setor_sql = (
        select(Setor, func.count(Funcionario.id).label("funcionarios")).
        outerjoin(Funcionario, Setor.id == Funcionario.setor_id).
        where(Setor.status_delete == 0).
        group_by(Setor.id)
    )
    setor = db_session.execute(setor_sql).all()
    return setor

def select_id(setor_id):
    setor_sql = select(Setor).where(Setor.id == setor_id)
    setor = db_session.execute(setor_sql).scalar_one_or_none()
    return setor

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

    return False

def salvar(nome, descricao):
    try:
        setor = Setor(nome=nome, descricao=descricao)
        db_session.add(setor)
        db_session.commit()
        flash("Setor cadastrado com sucesso", "success")
        return True  # CORREÇÃO 2: Retorna apenas True indicando que salvou no banco local
    except SQLAlchemyError as e:
        db_session.rollback()
        print(f"Erro de Banco (Setor): {e}")
        flash("Erro ao cadastrar setor no banco de dados", "error")
        return False
    except Exception as e:
        db_session.rollback()
        print(f"Erro Inesperado (Setor): {e}")
        flash("Erro inesperado", "error")
        return False