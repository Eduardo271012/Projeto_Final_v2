from flask import redirect, url_for, flash
from database import *
from sqlalchemy.exc import SQLAlchemyError

def validar_equipamento(nome, numero_serie, quantidade, modelo):
        if not nome:
            flash("Preencha o nome", "error")
            return True
        if not quantidade:
            flash("Preencha a quantidade", "error")
            return True
        if not modelo:
            flash("Preencha o modelo", "error")
            return True
        if not numero_serie:
            flash("Preencha o número de série", "error")
            return True

        if len(nome) > 50:
            flash("O nome é muito longo", "error")
            return True
        if len(modelo) > 50:
            flash("O modelo do equipamento é muito grande", "error")
            return True

        try:
            quantidade = int(quantidade)
            numero_serie = int(numero_serie)
        except ValueError:
            flash("Digite apenas números inteiros", "error")
            return True

def salvar(nome, modelo, quantidade, numero_serie):
    try:
        equipamento_novo = Equipamento(nome=nome, modelo=modelo, quantidade=quantidade, numero_serie=numero_serie)
        db_session.add(equipamento_novo)
        db_session.commit()
        flash("Equipamento cadastrado com sucesso", "success")
        return redirect(url_for("equipamentos"))
    except SQLAlchemyError:
        db_session.rollback()
        flash("Erro ao cadastrar equipamento no banco de dados", "error")
        return redirect(url_for("cadastro_equipamento"))
    except Exception:
        db_session.rollback()
        flash("Erro inesperado", "error")
        return redirect(url_for("cadastro_equipamento"))