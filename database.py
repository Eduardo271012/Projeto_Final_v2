from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Boolean, BigInteger, Float
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, scoped_session
import pymysql
from flask_login import UserMixin


# ==============================================================================
# 1. PARTE NOVA: CRIA O BANCO SE ELE NÃO EXISTIR NO SEU COMPUTADOR
# ==============================================================================

# conn = pymysql.connect(host="localhost", user="root", password="senaisp", port=3306)
# try:
#     with conn.cursor() as cursor:
#         cursor.execute("CREATE DATABASE IF NOT EXISTS quarks_solucoes;")
# finally:
#     conn.close()


# Conexão com o banco
# Mudar usuário, senha e nome do banco
engine = create_engine("mysql+pymysql://swan:senaisp@10.135.232.28:3306/quarks_solucoes")
db_session =scoped_session(sessionmaker(bind=engine))
Base = declarative_base()


# Tabela setores
class Setor(Base):
    __tablename__ = 'setores'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(50), nullable=False)
    descricao = Column(String(10000))

    # Relacionamento com o setor
    funcionarios = relationship('Funcionario', back_populates='setor')

# Tabela equipamentos
class Equipamento(Base):
    __tablename__ = 'equipamentos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(50), nullable=False)
    modelo = Column(String(50))
    quantidade = Column(Integer)
    custo_equipamento = Column(Float)
    status_delete = Column(Boolean, default=True)

    # Relacionamento com as ordens de serviço
    ordens_servico_associadas = relationship('OrdemServicoEquipamento', back_populates='equipamento')

# Tabela funcionários
class Funcionario(Base, UserMixin):
    __tablename__ = 'funcionarios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    setor_id = Column(Integer, ForeignKey('setores.id', ondelete='SET NULL', onupdate='CASCADE'))
    cpf = Column(BigInteger, nullable=False, unique=True)
    nome = Column(String(50), nullable=False)
    email = Column(String(100), unique=True)
    funcao = Column(String(50))
    status_delete = Column(Boolean, default=True)


    # Relacionamentos com as ordens de serviço e setor
    ordens_servico_atribuidas = relationship('OrdemServico', back_populates='funcionario')
    setor = relationship('Setor', back_populates='funcionarios')

# Tabela ordens de serviço
class OrdemServico(Base):
    __tablename__ = 'ordens_servico'

    id = Column(Integer, primary_key=True, autoincrement=True)
    responsavel_id = Column(Integer, ForeignKey('funcionarios.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    custo_total = Column(Integer)
    descricao = Column(String(10000), nullable=False)
    status_os = Column(String(25), nullable=False)
    data_solicitacao = Column(Date)
    data_execucao = Column(Date)
    prioridade = Column(String(25))
    status_delete = Column(Boolean, default=True)

    # Relacionamentos com o funcionario (responsável) e equipamentos
    funcionario = relationship('Funcionario', back_populates='ordens_servico_atribuidas')
    equipamentos_associados = relationship('OrdemServicoEquipamento', back_populates='ordem_servico')

# Tabela intermediária
# Necessária em uma relação N:N
# Uma ordem de serviço pode ter muitos equipamentos e um equipamento pode estar em mais de uma ordem de serviço
class OrdemServicoEquipamento(Base):
    __tablename__ = 'ordens_servico_equipamentos'

    os_id = Column(Integer, ForeignKey('ordens_servico.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False)
    equipamento_id = Column(Integer, ForeignKey('equipamentos.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False)
    quantidade = Column(Integer, default=1)

    # Relacionamentos ordem de serviço e equipamento
    ordem_servico = relationship('OrdemServico', back_populates='equipamentos_associados')
    equipamento = relationship('Equipamento', back_populates='ordens_servico_associadas')