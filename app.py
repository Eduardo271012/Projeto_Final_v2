from flask import Flask, render_template, redirect, url_for, flash, request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from banco import *
from validate_docbr import CPF, CNPJ # Bilioteca para validar dados de documentos brasileiros

from banco import tabela_cliente
from database import *
import re
from datetime import datetime, date
app = Flask(__name__)
app.secret_key = "quarks-solucoes"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clientes')
def clientes():
    return render_template('cliente.html')

@app.route('/clientes/cadastro', methods=['GET', 'POST'])
def cadastro_cliente():
    if request.method == "POST":
        # 1 - Pegar os valores digitados no formulário
        nome = request.form.get("nome", "").strip()
        data_nascimento = request.form.get("data_nascimento", date.today()).strip()
        telefone = request.form.get("telefone", "").strip()
        email = request.form.get("email", "").strip().lower()
        cpf_cnpj = request.form.get("cpf_cnpj", "").strip()
        departamento = request.form.get("departamento").strip()

        tabela_cliente.validar_cliente(nome=nome, data_nascimento=data_nascimento, telefone=telefone, email=email, cpf_cnpj=cpf_cnpj)

        # 3 - Salvar no banco
        tabela_cliente.salvar(nome=nome, data_nascimento=data_nascimento, telefone=telefone, email=email, cpf_cnpj=cpf_cnpj)
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