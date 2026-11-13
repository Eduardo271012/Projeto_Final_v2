--DROP DATABASE quarks_solucoes;
CREATE DATABASE IF NOT EXISTS quarks_solucoes;
USE quarks_solucoes;

CREATE TABLE IF NOT EXISTS usuarios (
	id INT AUTO_INCREMENT PRIMARY KEY,

    nome VARCHAR(50) NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS setores (
	id INT AUTO_INCREMENT PRIMARY KEY,

    nome VARCHAR(50) NOT NULL,
    descricao TEXT,
    status_delete BOOL DEFAULT 1
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

CREATE TABLE IF NOT EXISTS funcionarios (
	id INT AUTO_INCREMENT PRIMARY KEY,
    setor_id INT,

	cpf BIGINT UNIQUE NOT NULL,
    nome VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    funcao VARCHAR(50),
    status_delete BOOL DEFAULT 1,

    CONSTRAINT fk_funcionario_setor
		FOREIGN KEY (setor_id) REFERENCES setores(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ordens_servico (
	id INT AUTO_INCREMENT PRIMARY KEY,
    responsavel_id INT,

    custo_total INT,
    descricao TEXT(1000),
    status_os VARCHAR(25),
    data_solicitacao DATE,
    data_execucao DATE,
    prioridade VARCHAR(25),
    status_delete BOOL DEFAULT 1,

	CONSTRAINT fk_ordem_servico_funcionario
		FOREIGN KEY (responsavel_id) REFERENCES funcionarios(id)
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