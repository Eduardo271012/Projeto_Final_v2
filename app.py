from flask import Flask, render_template, redirect, url_for, flash, request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from banco import *
import re
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "chave_secreta_para_os_flash_messages"  # Obrigatório para usar flash()


@app.route('/')
def index():
    return render_template('index.html')


# --- ROTAS DE CLIENTES ---
@app.route('/clientes', methods=['GET'])
def clientes():
    return render_template('cliente.html')


@app.route('/clientes/cadastro', methods=['GET', 'POST'])
def cadastro_cliente():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        data_nascimento = request.form.get("data_nascimento", "").strip()
        telefone = request.form.get("telefone", "").strip()
        email = request.form.get("email", "").strip().lower()
        cpf_cnpj = request.form.get("cpf_cnpj", "").strip()
        departamento = request.form.get("departamento", "").strip()

        cpf_cnpj_formatado = re.sub(r"\D", "", cpf_cnpj)
        telefone_fomatado = re.sub(r'\D', '', telefone)

        email_existente = db_session.query(Cliente).filter(Cliente.email == email).first()

        regex_telefone = r'^[1-9]{2}(?:[2-8]|9[1-9])[0-9]{7}$'
        regex_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not nome or not data_nascimento or not telefone or not email or not cpf_cnpj or not departamento:
            flash("Preencha todos os campos obrigatórios", "error")
            return redirect(url_for("cadastro_cliente"))

        try:
            data_validada = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
        except ValueError:
            flash("A data inserida não existe ou está no formato errado", "error")
            return redirect(url_for("cadastro_cliente"))

        if len(nome) > 50:
            flash("O nome é muito longo", "error")
            return redirect(url_for("cadastro_cliente"))
        if not re.match(regex_telefone, telefone_fomatado):
            flash("Digite um telefone válido", "error")
            return redirect(url_for("cadastro_cliente"))
        if data_validada.year < 1900:
            flash("A data de nascimento é muito antiga", "error")
            return redirect(url_for("cadastro_cliente"))
        if not re.match(regex_email, email):
            flash("Digite um email válido", "error")
            return redirect(url_for("cadastro_cliente"))
        elif email_existente:
            flash("O email já foi utilizado", "error")
            return redirect(url_for("cadastro_cliente"))

        # Lógica para salvar no banco futuramente...
        return redirect(url_for('clientes'))

    return render_template('cliente.html')


# --- ROTAS DE EQUIPAMENTOS ---
@app.route('/equipamentos', methods=['GET'])
def equipamentos():
    return render_template('equipamento.html')


@app.route('/equipamentos/cadastro', methods=['GET', 'POST'])
def cadastro_equipamento():
    if request.method == "POST":
        nome_equipamento = request.form.get("nome_equipamento", "").strip()
        quantidade_estoque = request.form.get("quantidade_estoque", "").strip()
        modelo = request.form.get("modelo", "").strip()
        numero_serie = request.form.get("numero_serie", "").strip()

        if not nome_equipamento or not quantidade_estoque or not modelo or not numero_serie:
            flash("Preencha todos os campos do equipamento", "error")
            return redirect(url_for("cadastro_equipamento"))

        # Lógica para salvar no banco futuramente...
        return redirect(url_for('equipamentos'))

    return render_template('equipamento.html')


# --- ROTAS DE ORDENS DE SERVIÇO ---
@app.route('/servico/ordens', methods=['GET'])
def ordens_servico():
    return render_template('ordens_servico.html')


@app.route('/servico/ordens/cadastro', methods=['GET', 'POST'])
def cadastro_ordem():
    if request.method == "POST":
        titulo_os = request.form.get("titulo_os", "").strip()
        cliente = request.form.get("cliente", "").strip()
        descricao = request.form.get("descricao", "").strip()
        status = request.form.get("status")
        prioridade = request.form.get("prioridade")
        datasolicitacao = request.form.get("datasolicitacao")
        dataentrega = request.form.get("dataentrega")

        if not titulo_os or not cliente or not descricao:
            flash("Preencha os campos obrigatórios da OS", "error")
            return redirect(url_for("cadastro_ordem"))

        # Lógica para salvar no banco futuramente...
        return redirect(url_for('ordens_servico'))

    return render_template('ordens_servico.html')


# --- ROTAS DE SETORES ---
@app.route('/setor', methods=['GET'])
def setor():
    return render_template('setor.html')


@app.route('/setor/cadastro', methods=['GET', 'POST'])
def cadastro_setor():
    if request.method == "POST":
        nome_setor = request.form.get("nome_setor", "").strip()
        if not nome_setor:
            flash("Preencha o nome do setor", "error")
            return redirect(url_for("cadastro_setor"))

        # Lógica para salvar no banco futuramente...
        return redirect(url_for('setor'))

    return render_template('setor.html')


# --- ROTAS DE FUNCIONÁRIOS ---
@app.route('/funcionarios', methods=['GET'])
def funcionarios():
    # CORREÇÃO: Nova rota criada para renderizar a página de funcionários sem o formulário aberto
    return render_template('funcionario.html')


@app.route('/funcionarios/cadastro', methods=['GET', 'POST'])
def cadastro_funcionario():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        cpf = request.form.get("cpf", "").strip()
        email = request.form.get("email", "").strip()
        setor = request.form.get("setor")
        funcao = request.form.get("funcao")

        if not nome or not email:
            flash("Nome e Email são obrigatórios", "error")
            return redirect(url_for("cadastro_funcionario"))

        # Lógica para salvar no banco futuramente...
        return redirect(url_for('funcionarios'))

    return render_template('funcionario.html')


# --- DEMAIS ROTAS ---
@app.route('/acesso', methods=['GET', 'POST'])
def acesso():
    return render_template('acesso.html')


# Iniciar aplicação web
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
# Nada deve ser colocado abaixo
