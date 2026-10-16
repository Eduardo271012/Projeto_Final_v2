from flask import Flask, render_template, redirect, url_for, flash, request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from banco import *
from validate_docbr import CPF, CNPJ # Bilioteca para validar dados de documentos brasileiros
from database import *
import re
from datetime import datetime, date
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clientes')
def clientes():
    return render_template('cliente.html')

@app.route('/clientes/cadastro', methods=['GET', 'POST'])
def cadastro_cliente():
    if request.method == "POST":
        # 1 - Pegar os valores digitados no form
        nome = request.form.get("nome").strip()
        data_nascimento = request.form.get("data_nascimento").strip()
        telefone = request.form.get("telefone").strip()
        email = request.form.get("email").strip().lower()
        cpf_cnpj = request.form.get("cpf_cnpj").strip()
        departamento = request.form.get("departamento").strip()

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
        if telefone_existente:
            flash("O telefone já foi utilizado", "error")
            return redirect(url_for("cadastro_clientes"))
        if data_validada.year < 1900:
            flash("A data de nascimento é muito antiga", "error")
            return redirect(url_for("cadastro_clientes"))
        if not re.match(regex_email, email):
            flash("Digite um email válido", "error")
            return redirect(url_for("cadastro_clientes"))
        elif email_existente:
            flash("O email já foi utilizado", "error")
            return redirect(url_for("cadastro_clientes"))
        if len(cpf_cnpj_formatado) == 11:
            if not validar_cpf.validate(cpf_cnpj_formatado):
                flash("CPF inválido", "error")
                return redirect(url_for("cadastro_clientes"))
        elif len(cpf_cnpj_formatado) == 14:
            if not validar_cnpj.validate(cpf_cnpj_formatado):
                flash("CNPJ inválido", "error")
                return redirect(url_for("cadastro_clientes"))
        else:
            flash("Digite somente CPFs ou CNPJs", "error")
            return redirect(url_for("cadastro_clientes"))

        return redirect(url_for('clientes'))

        # 3 - Salvar no banco
       # tabela_time.salvar(nome=nome, numero_camisa=numero_camisa, posicao=posicao, time_id=time_id)
    return render_template('cliente.html')

@app.route('/equipamentos')
def equipamentos():
    return render_template('equipamento.html')

@app.route('/equipamentos/cadastro', methods=['GET', 'POST'])
def cadastro_equipamento():
    if request.method == "POST":
        nome_equipamento = request.form.get("nome_equipamento").strip()
        quantidade_estoque = request.form.get("quantidade_estoque").strip()
        modelo = request.form.get("modelo").strip()
        numero_serie = request.form.get("numero_serie").strip()

        if not nome_equipamento:
            flash("Preencha o nome", "error")
            return redirect(url_for("cadastro_equipamento"))
        if not quantidade_estoque:
            flash("Preencha a quantidade", "error")
            return redirect(url_for("cadastro_equipamento"))
        if not modelo:
            flash("Preencha o modelo", "error")
            return redirect(url_for("cadastro_equipamento"))
        if not numero_serie:
            flash("Preencha o número de série", "error")
            return redirect(url_for("cadastro_equipamento"))

    return render_template('equipamento.html')

@app.route('/servico/ordens', methods=['GET', 'POST'])
def ordens_servico():
    return render_template('ordens_servico.html')

@app.route('/acesso', methods=['GET', 'POST'])
def acesso():
    return render_template('acesso.html')

@app.route('/setor', methods=['GET', 'POST'])
def setor():
    return render_template('setor.html')

@app.route('/funcionarios/cadastro', methods=['GET', 'POST'])
def cadastro_funcionario():
    return render_template('funcionario.html')



# Iniciar aplicação web
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
# Nada deve ser colocado abaixo