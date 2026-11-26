from flask_login import UserMixin
from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Index, Integer, String, Text, create_engine, \
    DateTime, func
from sqlalchemy.orm import declarative_base, relationship, scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

engine = create_engine("mysql+pymysql://root:senaisp@localhost:3306/quarks_solucoes")
db_session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()


class Setor(Base):
    __tablename__ = 'setores'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(50), nullable=False)
    descricao = Column(String(10000))
    status_delete = Column(Boolean, default=True, nullable=False)
    usuarios = relationship('Usuario', back_populates='setor')

class Equipamento(Base):
    __tablename__ = 'equipamentos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(50), nullable=False)
    modelo = Column(String(50))
    quantidade = Column(Integer)
    custo_equipamento = Column(Float)
    status_delete = Column(Boolean, default=True, nullable=False)

    ordens_servico_associadas = relationship('OrdemServicoEquipamento', back_populates='equipamento')
    equipamento_recurso = relationship('Recurso', back_populates='equipamento_necessario')


class Recurso(Base):
    __tablename__ = 'recursos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    equipamento_id = Column(Integer, ForeignKey('equipamentos.id', ondelete='SET NULL', onupdate='CASCADE'))
    nome = Column(String(50), nullable=False)
    descricao = Column(String(1000))
    status_delete = Column(Boolean, default=True, nullable=False)

    equipamento_necessario = relationship('Equipamento', back_populates='equipamento_recurso')


class OrdemServico(Base):
    __tablename__ = 'ordens_servico'

    id = Column(Integer, primary_key=True, autoincrement=True)
    responsavel_id = Column(Integer, ForeignKey('usuarios.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    tecnico_responsavel_id = Column(Integer, ForeignKey('usuarios.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    setor_id = Column(Integer, ForeignKey('setores.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    identificacao = Column(String(15), nullable=False)
    categoria = Column(String(30), nullable=False)
    custo_total = Column(Integer)
    descricao = Column(String(500), nullable=False)
    status_os = Column(String(25), nullable=False)
    data_solicitacao = Column(Date)
    data_execucao = Column(Date)
    prioridade = Column(String(25))
    status_delete = Column(Boolean, default=True, nullable=False)

    responsavel = relationship(
        'Usuario',
        foreign_keys=[responsavel_id],
        back_populates='ordens_servico_atribuidas',
    )
    tecnico_responsavel = relationship(
        'Usuario',
        foreign_keys=[tecnico_responsavel_id],
        back_populates='ordens_servico_tecnicas',
    )
    setor = relationship('Setor')
    equipamentos_associados = relationship('OrdemServicoEquipamento', back_populates='ordem_servico')


class OrdemServicoEquipamento(Base):
    __tablename__ = 'ordens_servico_equipamentos'

    os_id = Column(Integer, ForeignKey('ordens_servico.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False)
    equipamento_id = Column(Integer, ForeignKey('equipamentos.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False)
    quantidade = Column(Integer, default=1)

    ordem_servico = relationship('OrdemServico', back_populates='equipamentos_associados')
    equipamento = relationship('Equipamento', back_populates='ordens_servico_associadas')


class Usuario(Base, UserMixin):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(50), nullable=False)
    senha_hash = Column(String(255), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    cpf = Column(String(11), unique=True)
    setor_id = Column(Integer, ForeignKey('setores.id', ondelete='SET NULL', onupdate='CASCADE'))
    funcao = Column(String(100))
    papel = Column(String(20), default="usuario", nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, nullable=False, server_default=func.now())
    atualizado_em = Column(DateTime, nullable=False, server_default=func.now())
    setor = relationship('Setor', back_populates='usuarios')
    ordens_servico_atribuidas = relationship(
        'OrdemServico',
        foreign_keys='OrdemServico.responsavel_id',
        back_populates='responsavel',
    )
    ordens_servico_tecnicas = relationship(
        'OrdemServico',
        foreign_keys='OrdemServico.tecnico_responsavel_id',
        back_populates='tecnico_responsavel',
    )

    @property
    def is_active(self):
        return bool(self.ativo)

    def set_password(self, password):
        self.senha_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.senha_hash, password)


class HistoricoOrdemServico(Base):
    __tablename__ = "historico_ordens_servico"
    __table_args__ = (
        Index(
            "ix_historico_ordens_servico_ordem_data",
            "ordem_servico_id",
            "criado_em",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ordem_servico_id = Column(
        Integer,
        ForeignKey("ordens_servico.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    campo = Column(String(100), nullable=False)
    valor_anterior = Column(Text)
    valor_novo = Column(Text)
    criado_em = Column(DateTime, nullable=False, server_default=func.now())

    usuario = relationship("Usuario", foreign_keys=[usuario_id])


Base.metadata.create_all(bind=engine)