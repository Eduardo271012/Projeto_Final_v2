from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cliente', methods=['GET', 'POST'])
def cliente():
    return render_template('cliente.html')

@app.route('/equipamento', methods=['GET', 'POST'])
def equipamento():
    return render_template('equipamento.html')

@app.route('/ordens-servico', methods=['GET', 'POST'])
def ordens_servico():
    return render_template('ordens_servico.html')

@app.route('/acesso', methods=['GET', 'POST'])
def acesso():
    return render_template('acesso.html')

@app.route('/setor', methods=['GET', 'POST'])
def setor():
    return render_template('setor.html')

@app.route('/funcionario', methods=['GET', 'POST'])
def funcionario():
    teste = ""
    return render_template('funcionario.html')