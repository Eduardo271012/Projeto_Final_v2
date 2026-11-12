import re

from flask import flash
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from validate_docbr import CPF

from database import Funcionario, Setor, db_session


def select_todos():
    funcionarios_sql = select(Funcionario, Setor).join(Setor, Funcionario.setor_id == Setor.id)
    funcionarios = db_session.execute(funcionarios_sql).all()
    return funcionarios


def select_quantidade_total():
    funcionarios_sql = select(func.count(Funcionario.id))
    qtd_total = db_session.execute(funcionarios_sql).scalar()
    return qtd_total


def salvar(nome, cpf, email, setor_id, funcao):
    try:
        funcionario = Funcionario(
            nome=nome,
            cpf=int(cpf),
            email=email,
            funcao=funcao,
            setor_id=int(setor_id),
        )
        db_session.add(funcionario)
        db_session.commit()
        flash("Funcion?rio criado com sucesso", "success")
    except SQLAlchemyError as e:
        db_session.rollback()
        flash("Ocorreu um erro, tente novamente", "error")
        print(f"Erro: {e}")
    except Exception as e:
        db_session.rollback()
        flash("Ocorreu um erro, tente novamente", "error")
        print(f"Erro: {e}")


def select_funcionarios():
    funcionarios_select = select(Funcionario).join(Setor, Setor.id == Funcionario.setor_id)
    funcionarios = db_session.execute(funcionarios_select).scalars().all()
    return funcionarios


def validar_funcionario(nome, cpf, email, setor_id, funcionarios, ultimo_setor):
    cpf_formatado = ''.join(filter(str.isdigit, cpf))
    regex_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not nome:
        flash("Preencha o nome", "error")
        return True
    if not cpf:
        flash("Preencha o CPF", "error")
        return True
    if not email:
        flash("Preencha o email", "error")
        return True
    if not setor_id:
        flash("Preencha o setor", "error")
        return True

    if len(nome) > 50:
        flash("O nome ? muito longo", "error")
        return True
    if len(cpf_formatado) != 11:
        flash("Insira um CPF no formato v?lido", "error")
        return True
    if not CPF().validate(cpf_formatado):
        flash("O CPF inserido n?o ? v?lido, insira um CPF v?lido", "error")
        return True

    for funcionario, setor in funcionarios:
        if int(funcionario.cpf) == int(cpf_formatado):
            flash("O CPF j? foi cadastrado antes, insira um CPF n?o cadastrado", "error")
            return True

    if not re.match(regex_email, email):
        flash("Insira um email de formato v?lido", "error")
        return True

    for funcionario, setor in funcionarios:
        if funcionario.email == email:
            flash("O email j? foi cadastrado antes, insira um email n?o cadastrado", "error")
            return True

    if int(setor_id) <= 0 or int(setor_id) > int(ultimo_setor):
        flash("O setor selecionado n?o existe", "error")
        return True

    return False
