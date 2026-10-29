from flask import flash, redirect, url_for
from sqlalchemy import select, func
from sqlalchemy.dialects.mssql.information_schema import columns
from sqlalchemy.exc import SQLAlchemyError
from database import Funcionario, db_session, Setor
import re
from validate_docbr import CPF


def select_todos():
    # 1 - Montar o select
    # join(Tabela que eu quero juntar, condição=chave estrangeira igual à chave primaria)
    funcionarios_sql = select(Funcionario, Setor).join(Setor, Funcionario.setor_id == Setor.id)
    # 2 - Executar o select
    #  usar scalars quando tiver somente uma tabela
    funcionarios = db_session.execute(funcionarios_sql).all()
    print(funcionarios)

    return funcionarios

def select_quantidade_total():
    funcionarios_sql = select(func.count(Funcionario.id))
    qtd_total = db_session.execute(funcionarios_sql).scalar()
    return qtd_total

if __name__ == '__main__':
    print(select_quantidade_total())

def salvar(nome, cpf, email, setor_id, funcao):
    try:
        funcionario = Funcionario(nome=nome, cpf=int(cpf),email=email, funcao=funcao, setor_id=int(setor_id))
        db_session.add(funcionario)
        db_session.commit()
        flash("Funcionário criado com sucesso", "success")
    except SQLAlchemyError as e:
        db_session.rollback()
        flash("Ocorreu um erro, tente novamente", "error")
        print(f"Erro: {e}")
    except Exception as e:
        db_session.rollback()
        flash("Ocorreu um erro, tente novamente", "error")
        print(f"Erro: {e}")



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

