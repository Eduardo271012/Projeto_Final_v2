from flask import redirect, url_for, flash
from database import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
import re
from validate_docbr import CPF

def select_funcionarios():
    funcionarios_select = (
        select(Funcionario).
        join(Setor, Setor.id == Funcionario.setor_id)
    )
    funcionarios = db_session.execute(funcionarios_select).scalars().all()
    return funcionarios

def validar_funcionario(nome, cpf, email, setor_id, funcionarios, ultimo_setor):
    cpf_formatado = re.sub(r"\D", "", cpf)

    regex_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    setor_id = int(setor_id)

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
        flash("O nome é muito longo", "error")
        return True
    if len(cpf_formatado) != 11:
        flash("Insira um CPF no formato válido", "error")
        return True
    elif not CPF().validate(cpf_formatado):
        flash("O CPF inserido não é válido, insira um CPF válido", "error")
        return True
    for funcionario, setor in funcionarios:
        if funcionario.cpf == cpf_formatado:
            flash("O CPF já foi cadastrado antes, insira um CPF não cadastrado", "error")
            return True
    if not re.match(regex_email, email):
        flash("Insira um email de formato válido", "error")
        return True
    for funcionario, setor in funcionarios:
        if funcionario.email == email:
            flash("O email já foi cadastrado antes, insira um emial não cadastrado", "error")
            return True
    if setor_id <= 0 or setor_id > ultimo_setor:
        flash("O setor selecionado não existe", "error")
        return True

def salvar(nome, cpf, email, setor_id):
    try:
        funcionario_novo = Funcionario(nome=nome, cpf=cpf, email=email, setor_id=setor_id)
        db_session.add(funcionario_novo)
        db_session.commit()
        flash("Funcionário cadastrado com sucesso", "success")
        return redirect(url_for("funcionarios"))
    except SQLAlchemyError:
        db_session.rollback()
        flash("Erro ao cadastrar funcionário no banco de dados", "error")
        return redirect(url_for("cadastro_funcionario"))
    except Exception:
        db_session.rollback()
        flash("Erro inesperado", "error")
        return redirect(url_for("cadastro_funcionario"))