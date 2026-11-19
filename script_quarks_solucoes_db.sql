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

    categoria VARCHAR(30) NOT NULL DEFAULT 'Manutenção',
    custo_total INT,
    descricao TEXT(1000),
    status_os VARCHAR(25),
    data_solicitacao DATE,
    data_execucao DATE,
    prioridade VARCHAR(25),
    status_delete BOOL DEFAULT 1,

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
    (responsavel_id, custo_total, descricao, status_os, data_solicitacao, data_execucao, prioridade, status_delete)
SELECT NULL, 850, 'Revisão preventiva do torno mecânico', 'Aberta', '2026-11-10', NULL, 'Baixa', 1
WHERE NOT EXISTS (SELECT 1 FROM ordens_servico WHERE descricao = 'Revisão preventiva do torno mecânico');

INSERT INTO ordens_servico
    (responsavel_id, custo_total, descricao, status_os, data_solicitacao, data_execucao, prioridade, status_delete)
SELECT NULL, 2400, 'Substituição de sensor da esteira', 'Em andamento', '2026-11-12', NULL, 'Alta', 1
WHERE NOT EXISTS (SELECT 1 FROM ordens_servico WHERE descricao = 'Substituição de sensor da esteira');

INSERT INTO ordens_servico
    (responsavel_id, custo_total, descricao, status_os, data_solicitacao, data_execucao, prioridade, status_delete)
SELECT NULL, 620, 'Inspeção do compressor de ar', 'Pausada', '2026-11-14', NULL, 'Média', 1
WHERE NOT EXISTS (SELECT 1 FROM ordens_servico WHERE descricao = 'Inspeção do compressor de ar');

INSERT INTO ordens_servico
    (responsavel_id, custo_total, descricao, status_os, data_solicitacao, data_execucao, prioridade, status_delete)
SELECT NULL, 1350, 'Calibração da prensa hidráulica', 'Concluída', '2026-11-01', '2026-11-03', 'Baixa', 1
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