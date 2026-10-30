from flask import flash
from database import Equipamento, db_session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select


def select_todos():
    # Busca todos os equipamentos para listar na tabela do HTML
    equipamentos_sql = select(Equipamento)
    equipamentos = db_session.execute(equipamentos_sql).scalars().all()
    return equipamentos

def select_ativos():
    equipamentos_sql = select(Equipamento).where(Equipamento.status_delete == 1)
    equipamento = db_session.execute(equipamentos_sql).scalars().all()
    return equipamento

def select_excluidos():
    equipamentos_sql = select(Equipamento).where(Equipamento.status_delete == 0)
    equipamento = db_session.execute(equipamentos_sql).scalars().all()
    return equipamento

def select_id(equipamento_id):
    equipamento_sql = select(Equipamento).where(Equipamento.id == equipamento_id)
    equipamento = db_session.execute(equipamento_sql).scalar_one_or_none()
    return equipamento

def validar_equipamento(nome, quantidade, modelo, custo_equipamento):
    if not nome:
        flash("Preencha o nome", "error")
        return True
    if not quantidade:
        flash("Preencha a quantidade", "error")
        return True
    if not modelo:
        flash("Preencha o modelo", "error")
        return True
    if not custo_equipamento:
        flash("Preencha o custo do equipamento", "error")
        return True

    if len(nome) > 50:
        flash("O nome é muito longo", "error")
        return True
    if len(modelo) > 50:
        flash("O modelo do equipamento é muito grande", "error")
        return True

    try:
        quantidade = int(quantidade)
        # CORREÇÃO: Custo pode ser um número quebrado (float) ou inteiro
        custo_equipamento = float(custo_equipamento)
    except ValueError:
        flash("Digite valores numéricos válidos para quantidade e custo", "error")
        return True

    return False  # Retorna False se não houver erros


# CORREÇÃO: Trocado 'numero_serie' por 'custo_equipamento' para bater com o database.py
def salvar(nome, modelo, quantidade, custo_equipamento):
    try:
        equipamento_novo = Equipamento(
            nome=nome,
            modelo=modelo,
            quantidade=int(quantidade),
            custo_equipamento=float(custo_equipamento)
        )
        db_session.add(equipamento_novo)
        db_session.commit()
        flash("Equipamento cadastrado com sucesso", "success")
        return True
    except SQLAlchemyError as e:
        db_session.rollback()
        print(f"Erro de Banco (Equipamento): {e}")
        flash("Erro ao cadastrar equipamento no banco de dados", "error")
        return False
    except Exception as e:
        db_session.rollback()
        print(f"Erro Inesperado (Equipamento): {e}")
        flash("Erro inesperado", "error")
        return False
