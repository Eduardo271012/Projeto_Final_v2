from flask import redirect, url_for, flash
from database import *
from sqlalchemy.exc import SQLAlchemyError
import re
from validate_docbr import CPF, CNPJ

def validar_cliente(nome, data_nascimento, telefone, email, cpf_cnpj):
    # Transforma o CPF/CNPJ em números limpos
    cpf_cnpj_formatado = re.sub(r"\D", "", cpf_cnpj)
    # Transforma o telefone digitado em números limpos
    telefone_fomatado = re.sub(r'\D', '', telefone)
    # Verifica se já existe um email igual no banco de dados
    email_existente = db_session.query(Cliente).filter_by(email=email).first()
    # Verifica se já existe um telefone igual no banco de dados
    telefone_existente = db_session.query(Cliente).filter_by(telefone=telefone).first()

    # Explicação da Regex:
    # ^[1-9]{2} = DDD válido (dois dígitos de 1 a 9)
    # (?:[2-8]|9[1-9]) = Telefones fixos começam de 2 a 8. Celulares começam com 9 e o segundo dígito não é 0.
    # [0-9]{7}$ = O restante dos números (7 dígitos)
    regex_telefone = r'^[1-9]{2}(?:[2-8]|9[1-9])[0-9]{7}$'
    #  Regex padrão para validar e-mails (verifica se tem @, pontos e domínio)
    regex_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    validar_cpf = CPF()
    validar_cnpj = CNPJ()

    # 2 - Verificar se foi digitado
    if not nome:
        flash("Preencha o nome", "error")
        return redirect(url_for("cadastro_cliente"))
    if not data_nascimento:
        flash("Preencha a data de nascimento", "error")
        return redirect(url_for("cadastro_cliente"))
    if not telefone:
        flash("Preencha o telefone", "error")
        return redirect(url_for("cadastro_cliente"))
    if not email:
        flash("Preencha o email", "error")
        return redirect(url_for("cadastro_cliente"))
    if not cpf_cnpj:
        flash("Preencha o CPF ou CNPJ", "error")
        return redirect(url_for("cadastro_cliente"))
    if not departamento:
        flash("Selecione o departamento", "error")
        return redirect(url_for("cadastro_cliente"))

    try:
        data_validada = datetime.strptime(data_nascimento, "Y%-m%-d%").date()
    except ValueError:
        flash("A data inserida não existe ou está no formato errado", "error")
        return redirect(url_for("cadastro_clientes"))

    # Validar os dados antes de subir no banco
    if len(nome) > 50:
        flash("O nome é muito longo", "error")
        return redirect(url_for("cadastro_clientes"))
    # Compara para ver se o telefone formatado está de acordo com o modelo de telefone padrão
    if not re.match(regex_telefone, telefone_fomatado):
        flash("Digite um telefone válido", "error")
        return redirect(url_for("cadastro_clientes"))
    # Exibe uma mensagem e retorna erro caso já exista um telefone igual
    if telefone_existente:
        flash("O telefone já foi utilizado", "error")
        return redirect(url_for("cadastro_clientes"))
    # Verifica se a data inserida é muito antiga, tornando-a inválida
    if data_validada.year < 1900:
        flash("A data de nascimento é muito antiga", "error")
        return redirect(url_for("cadastro_clientes"))
    # Verifica se o email está no formato adequado
    if not re.match(regex_email, email):
        flash("Digite um email válido", "error")
        return redirect(url_for("cadastro_clientes"))
    # Exibe uma mensagem e retorna erro caso já exista um telefone igual
    elif email_existente:
        flash("O email já foi utilizado", "error")
        return redirect(url_for("cadastro_clientes"))
    # Verifica se o email enviado está no tamanho adequado
    if len(email) > 100:
        flash("O email digitado é muito longo", "error")
        return redirect(url_for("cadastro_clientes"))
    # Verifica se o documento enviado é um CPF ou CNPJ
    if len(cpf_cnpj_formatado) == 11:
        # Verifica se o CPF é válido
        if not validar_cpf.validate(cpf_cnpj_formatado):
            flash("CPF inválido", "error")
            return redirect(url_for("cadastro_clientes"))
    elif len(cpf_cnpj_formatado) == 14:
        # Verifica se o CNPJ é válido
        if not validar_cnpj.validate(cpf_cnpj_formatado):
            flash("CNPJ inválido", "error")
            return redirect(url_for("cadastro_clientes"))
    # Caso o documento enviado não esteja nos tamanhos respectivos aos CPF e CNPJ, retorna erro
    else:
        flash("Digite somente CPFs ou CNPJs", "error")
        return redirect(url_for("cadastro_clientes"))

def salvar(nome, data_nascimento, telefone, email, cpf_cnpj):
    try:
        cliente_novo = Cliente(nome=nome, data_nascimento=data_nascimento, telefone=telefone, email=email, cpf_cnpj=cpf_cnpj)
        db_session.add(cliente_novo)
        db_session.commit()
        flash("Cliente cadastrado com sucesso", "success")
        return redirect(url_for("clientes"))
    except SQLAlchemyError:
        db_session.rollback()
        flash("Erro ao cadastrar cliente no banco de dados", "error")
        return redirect(url_for("cadastro_clientes"))
    except Exception:
        db_session.rollback()
        flash("Erro inesperado", "error")
        return redirect(url_for("cadastro_clientes"))