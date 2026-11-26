--DROP DATABASE quarks_solucoes;
CREATE DATABASE IF NOT EXISTS quarks_solucoes;
USE quarks_solucoes;

CREATE TABLE IF NOT EXISTS setores (
	id INT AUTO_INCREMENT PRIMARY KEY,

    nome VARCHAR(50) NOT NULL,
    descricao TEXT,
    status_delete BOOL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS usuarios (
	id INT AUTO_INCREMENT PRIMARY KEY,

    nome VARCHAR(50) NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    cpf VARCHAR(11) UNIQUE,
    setor_id INT,
    funcao VARCHAR(100),
    papel VARCHAR(20) NOT NULL DEFAULT 'usuario',
    ativo BOOL NOT NULL DEFAULT 1,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_usuario_setor
        FOREIGN KEY (setor_id) REFERENCES setores(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS equipamentos (
	id INT AUTO_INCREMENT PRIMARY KEY,

    nome VARCHAR(50) NOT NULL,
    modelo VARCHAR(50),
    quantidade INT,
    custo_equipamento FLOAT,
    status_delete BOOL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS recursos (
	id INT AUTO_INCREMENT PRIMARY KEY,
    equipamento_id INT,

    nome VARCHAR(50) NOT NULL,
    descricao TEXT,
    status_delete BOOL DEFAULT 1,

    CONSTRAINT fk_recurso_equipamento
		FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ordens_servico (
	id INT AUTO_INCREMENT PRIMARY KEY,
    responsavel_id INT,
    tecnico_responsavel_id INT,
    setor_id INT,

    identificacao VARCHAR(30) NOT NULL,
    categoria VARCHAR(30) NOT NULL DEFAULT 'Manutenção',
    custo_total INT,
    descricao TEXT(1000),
    status_os VARCHAR(25),
    data_solicitacao DATE,
    data_execucao DATE,
    agendada_para DATETIME,
    motivo_pausa TEXT,
    previsao_retomada DATE,
    relato_conclusao TEXT,
    aceite_status VARCHAR(20) NOT NULL DEFAULT 'nao_solicitado',
    observacao_aceite TEXT,
    aceite_em DATETIME,
    prioridade VARCHAR(25),
    status_delete BOOL DEFAULT 1,

    CONSTRAINT uq_ordens_servico_identificacao UNIQUE (identificacao),
	CONSTRAINT fk_ordem_servico_usuario
		FOREIGN KEY (responsavel_id) REFERENCES usuarios(id)
		ON UPDATE CASCADE
		ON DELETE SET NULL,
    CONSTRAINT fk_ordem_servico_setor
        FOREIGN KEY (setor_id) REFERENCES setores(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT fk_ordem_servico_tecnico
        FOREIGN KEY (tecnico_responsavel_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS sequencias_os_anuais (
    ano INT NOT NULL PRIMARY KEY,
    ultimo_numero INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS historico_ordens_servico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ordem_servico_id INT NOT NULL,
    usuario_id INT NULL,
    campo VARCHAR(100) NOT NULL,
    valor_anterior TEXT,
    valor_novo TEXT,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_historico_os_ordem
        FOREIGN KEY (ordem_servico_id) REFERENCES ordens_servico(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_historico_os_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    INDEX ix_historico_ordens_servico_ordem_data (ordem_servico_id, criado_em)
);

CREATE TABLE IF NOT EXISTS mensagens_ordens_servico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ordem_servico_id INT NOT NULL,
    usuario_id INT NULL,
    usuario_nome VARCHAR(50) NOT NULL,
    usuario_papel VARCHAR(20) NOT NULL,
    mensagem TEXT NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_mensagem_os_ordem
        FOREIGN KEY (ordem_servico_id) REFERENCES ordens_servico(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_mensagem_os_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    INDEX ix_mensagem_os_ordem_data (ordem_servico_id, criado_em)
);

CREATE TABLE IF NOT EXISTS atividades_ordens_servico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ordem_servico_id INT NOT NULL,
    usuario_id INT NULL,
    usuario_nome VARCHAR(50) NOT NULL,
    usuario_papel VARCHAR(20) NOT NULL,
    tipo VARCHAR(30) NOT NULL DEFAULT 'atividade',
    descricao TEXT NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_atividade_os_ordem
        FOREIGN KEY (ordem_servico_id) REFERENCES ordens_servico(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_atividade_os_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX ix_atividade_os_ordem_data (ordem_servico_id, criado_em)
);

CREATE TABLE IF NOT EXISTS materiais_consumidos_os (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ordem_servico_id INT NOT NULL,
    equipamento_id INT NULL,
    usuario_id INT NULL,
    usuario_nome VARCHAR(50) NOT NULL,
    material_nome VARCHAR(50) NOT NULL,
    quantidade INT NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_material_consumido_os_ordem
        FOREIGN KEY (ordem_servico_id) REFERENCES ordens_servico(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_material_consumido_os_equipamento
        FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_material_consumido_os_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX ix_material_consumido_os (ordem_servico_id, criado_em)
);

CREATE TABLE IF NOT EXISTS anexos_ordens_servico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ordem_servico_id INT NOT NULL,
    usuario_id INT NULL,
    usuario_nome VARCHAR(50) NOT NULL,
    nome_original VARCHAR(255) NOT NULL,
    nome_armazenado VARCHAR(80) NOT NULL UNIQUE,
    mimetype VARCHAR(100) NOT NULL,
    tamanho_bytes INT NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_anexo_os_ordem
        FOREIGN KEY (ordem_servico_id) REFERENCES ordens_servico(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_anexo_os_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX ix_anexo_os_ordem_data (ordem_servico_id, criado_em)
);

CREATE TABLE IF NOT EXISTS auditoria_sistema (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NULL,
    usuario_nome VARCHAR(50) NOT NULL,
    usuario_papel VARCHAR(20) NOT NULL,
    area VARCHAR(50) NOT NULL,
    acao VARCHAR(30) NOT NULL,
    registro VARCHAR(150) NOT NULL,
    registro_id INT NULL,
    campo VARCHAR(100) NOT NULL,
    valor_anterior TEXT,
    valor_novo TEXT,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_auditoria_sistema_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    INDEX ix_auditoria_sistema_criado_em (criado_em),
    INDEX ix_auditoria_sistema_area_acao (area, acao)
);

CREATE TABLE IF NOT EXISTS solicitacoes_restauracao_os (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ordem_servico_id INT NOT NULL,
    usuario_id INT NULL,
    usuario_nome VARCHAR(50) NOT NULL,
    usuario_papel VARCHAR(20) NOT NULL,
    mensagem VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pendente',
    resposta_administrador VARCHAR(500),
    administrador_id INT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolvido_em DATETIME NULL,

    CONSTRAINT fk_solicitacao_restauracao_os
        FOREIGN KEY (ordem_servico_id) REFERENCES ordens_servico(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_solicitacao_restauracao_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT fk_solicitacao_restauracao_administrador
        FOREIGN KEY (administrador_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    INDEX ix_solicitacao_restauracao_status_data (status, criado_em),
    INDEX ix_solicitacao_restauracao_os_usuario (ordem_servico_id, usuario_id)
);

CREATE TABLE IF NOT EXISTS ordens_servico_equipamentos (
	os_id INT NOT NULL,
    equipamento_id INT NOT NULL,

    quantidade INT DEFAULT 1,

    PRIMARY KEY (os_id, equipamento_id),

    CONSTRAINT fk_ordem_servico
		FOREIGN KEY (os_id) REFERENCES ordens_servico(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
	CONSTRAINT fk_equipamento
		FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- Dados de demonstração para testar os formulários e listagens da aplicação.
-- A carga pode ser executada novamente: não apaga nem duplica os registros abaixo.
-- Crie as contas pelo formulário de cadastro; novas contas são usuários comuns.
SET NAMES utf8mb4;

INSERT INTO setores (nome, descricao, status_delete)
SELECT 'Manutenção', 'Responsável pela manutenção preventiva e corretiva.', 1
WHERE NOT EXISTS (SELECT 1 FROM setores WHERE nome = 'Manutenção');

INSERT INTO setores (nome, descricao, status_delete)
SELECT 'Produção', 'Acompanha os equipamentos e processos da linha de produção.', 1
WHERE NOT EXISTS (SELECT 1 FROM setores WHERE nome = 'Produção');

INSERT INTO setores (nome, descricao, status_delete)
SELECT 'Administrativo', 'Apoio administrativo e gestão de operações.', 1
WHERE NOT EXISTS (SELECT 1 FROM setores WHERE nome = 'Administrativo');

INSERT INTO setores (nome, descricao, status_delete)
SELECT 'Almoxarifado (inativo)', 'Setor de demonstração para a listagem de setores excluídos.', 0
WHERE NOT EXISTS (SELECT 1 FROM setores WHERE nome = 'Almoxarifado (inativo)');

INSERT INTO equipamentos (nome, modelo, quantidade, custo_equipamento, status_delete)
SELECT 'Torno Mecânico', 'TM-250', 4, 18500.00, 1
WHERE NOT EXISTS (SELECT 1 FROM equipamentos WHERE nome = 'Torno Mecânico' AND modelo = 'TM-250');

INSERT INTO equipamentos (nome, modelo, quantidade, custo_equipamento, status_delete)
SELECT 'Esteira Industrial', 'EI-100', 2, 12750.50, 1
WHERE NOT EXISTS (SELECT 1 FROM equipamentos WHERE nome = 'Esteira Industrial' AND modelo = 'EI-100');

INSERT INTO equipamentos (nome, modelo, quantidade, custo_equipamento, status_delete)
SELECT 'Compressor de Ar', 'CA-50', 3, 6420.00, 1
WHERE NOT EXISTS (SELECT 1 FROM equipamentos WHERE nome = 'Compressor de Ar' AND modelo = 'CA-50');

INSERT INTO equipamentos (nome, modelo, quantidade, custo_equipamento, status_delete)
SELECT 'Prensa Hidráulica', 'PH-300', 1, 28900.00, 1
WHERE NOT EXISTS (SELECT 1 FROM equipamentos WHERE nome = 'Prensa Hidráulica' AND modelo = 'PH-300');

INSERT INTO equipamentos (nome, modelo, quantidade, custo_equipamento, status_delete)
SELECT 'Furadeira de Bancada', 'FB-10', 1, 950.00, 0
WHERE NOT EXISTS (SELECT 1 FROM equipamentos WHERE nome = 'Furadeira de Bancada' AND modelo = 'FB-10');

INSERT INTO recursos (equipamento_id, nome, descricao, status_delete)
SELECT e.id, 'Óleo lubrificante', 'Lubrificante utilizado na manutenção do torno.', 1
FROM equipamentos e
WHERE e.nome = 'Torno Mecânico' AND e.modelo = 'TM-250'
  AND NOT EXISTS (
      SELECT 1 FROM recursos r
      WHERE r.equipamento_id = e.id AND r.nome = 'Óleo lubrificante'
  )
LIMIT 1;

INSERT INTO recursos (equipamento_id, nome, descricao, status_delete)
SELECT e.id, 'Correia transportadora', 'Peça de reposição para a esteira industrial.', 1
FROM equipamentos e
WHERE e.nome = 'Esteira Industrial' AND e.modelo = 'EI-100'
  AND NOT EXISTS (
      SELECT 1 FROM recursos r
      WHERE r.equipamento_id = e.id AND r.nome = 'Correia transportadora'
  )
LIMIT 1;

INSERT INTO recursos (equipamento_id, nome, descricao, status_delete)
SELECT e.id, 'Filtro de ar', 'Filtro para manutenção periódica do compressor.', 1
FROM equipamentos e
WHERE e.nome = 'Compressor de Ar' AND e.modelo = 'CA-50'
  AND NOT EXISTS (
      SELECT 1 FROM recursos r
      WHERE r.equipamento_id = e.id AND r.nome = 'Filtro de ar'
  )
LIMIT 1;

INSERT INTO ordens_servico
    (responsavel_id, identificacao, custo_total, descricao, status_os, data_solicitacao, data_execucao, prioridade, status_delete)
SELECT NULL, 'seed-torno', 850, 'Revisão preventiva do torno mecânico', 'Aberta', '2026-11-10', NULL, 'Baixa', 1
WHERE NOT EXISTS (SELECT 1 FROM ordens_servico WHERE descricao = 'Revisão preventiva do torno mecânico');

INSERT INTO ordens_servico
    (responsavel_id, identificacao, custo_total, descricao, status_os, data_solicitacao, data_execucao, prioridade, status_delete)
SELECT NULL, 'seed-esteira', 2400, 'Substituição de sensor da esteira', 'Em andamento', '2026-11-12', NULL, 'Alta', 1
WHERE NOT EXISTS (SELECT 1 FROM ordens_servico WHERE descricao = 'Substituição de sensor da esteira');

INSERT INTO ordens_servico
    (responsavel_id, identificacao, custo_total, descricao, status_os, data_solicitacao, data_execucao, prioridade, status_delete)
SELECT NULL, 'seed-compressor', 620, 'Inspeção do compressor de ar', 'Pausada', '2026-11-14', NULL, 'Média', 1
WHERE NOT EXISTS (SELECT 1 FROM ordens_servico WHERE descricao = 'Inspeção do compressor de ar');

INSERT INTO ordens_servico
    (responsavel_id, identificacao, custo_total, descricao, status_os, data_solicitacao, data_execucao, prioridade, status_delete)
SELECT NULL, 'seed-prensa', 1350, 'Calibração da prensa hidráulica', 'Concluída', '2026-11-01', '2026-11-03', 'Baixa', 1
WHERE NOT EXISTS (SELECT 1 FROM ordens_servico WHERE descricao = 'Calibração da prensa hidráulica');

INSERT INTO ordens_servico_equipamentos (os_id, equipamento_id, quantidade)
SELECT os.id, e.id, 1
FROM ordens_servico os
JOIN equipamentos e ON e.nome = 'Torno Mecânico' AND e.modelo = 'TM-250'
WHERE os.descricao = 'Revisão preventiva do torno mecânico'
  AND NOT EXISTS (
      SELECT 1 FROM ordens_servico_equipamentos ose
      WHERE ose.os_id = os.id AND ose.equipamento_id = e.id
  )
LIMIT 1;

INSERT INTO ordens_servico_equipamentos (os_id, equipamento_id, quantidade)
SELECT os.id, e.id, 1
FROM ordens_servico os
JOIN equipamentos e ON e.nome = 'Esteira Industrial' AND e.modelo = 'EI-100'
WHERE os.descricao = 'Substituição de sensor da esteira'
  AND NOT EXISTS (
      SELECT 1 FROM ordens_servico_equipamentos ose
      WHERE ose.os_id = os.id AND ose.equipamento_id = e.id
  )
LIMIT 1;

INSERT INTO ordens_servico_equipamentos (os_id, equipamento_id, quantidade)
SELECT os.id, e.id, 1
FROM ordens_servico os
JOIN equipamentos e ON e.nome = 'Compressor de Ar' AND e.modelo = 'CA-50'
WHERE os.descricao = 'Inspeção do compressor de ar'
  AND NOT EXISTS (
      SELECT 1 FROM ordens_servico_equipamentos ose
      WHERE ose.os_id = os.id AND ose.equipamento_id = e.id
  )
LIMIT 1;

INSERT INTO ordens_servico_equipamentos (os_id, equipamento_id, quantidade)
SELECT os.id, e.id, 1
FROM ordens_servico os
JOIN equipamentos e ON e.nome = 'Prensa Hidráulica' AND e.modelo = 'PH-300'
WHERE os.descricao = 'Calibração da prensa hidráulica'
  AND NOT EXISTS (
      SELECT 1 FROM ordens_servico_equipamentos ose
      WHERE ose.os_id = os.id AND ose.equipamento_id = e.id
  )
LIMIT 1;

CREATE TEMPORARY TABLE os_identificacoes_seed AS
SELECT
    id,
    COALESCE(YEAR(data_solicitacao), YEAR(CURRENT_DATE())) AS ano,
    ROW_NUMBER() OVER (
        PARTITION BY COALESCE(YEAR(data_solicitacao), YEAR(CURRENT_DATE()))
        ORDER BY id
    ) AS numero
FROM ordens_servico;

UPDATE ordens_servico os
JOIN os_identificacoes_seed seed ON seed.id = os.id
SET os.identificacao = CONCAT(
    'OS-',
    LPAD(MOD(seed.ano, 100), 2, '0'),
    '-',
    LPAD(seed.numero, 4, '0')
);

INSERT INTO sequencias_os_anuais (ano, ultimo_numero)
SELECT ano, MAX(numero)
FROM os_identificacoes_seed
GROUP BY ano
ON DUPLICATE KEY UPDATE
    ultimo_numero = GREATEST(ultimo_numero, VALUES(ultimo_numero));

DROP TEMPORARY TABLE os_identificacoes_seed;