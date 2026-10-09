SELECT *
FROM clientes;

SELECT *
FROM funcionarios;

SELECT *
FROM setores;

SELECT *
FROM equipamentos;

SELECT *
FROM ordens_servico;

SELECT *
FROM ordens_servico_equipamentos;

-- Todos os SELECT usando JOIN

-- Clientes
SELECT 
	clientes.cpf_cnpj AS "CPF/CNPJ",
    clientes.nome AS "Nome",
    GROUP_CONCAT(CONCAT(ordens_servico.id) SEPARATOR ", ") AS "OS Realizadas (ID)",
    COUNT(ordens_servico.id) AS "Quantidade OS"
FROM clientes
INNER JOIN ordens_servico ON ordens_servico.solicitante_id = clientes.id
GROUP BY clientes.id;

-- Equipamentos
SELECT
	equipamentos.modelo AS "Modelo",
	equipamentos.custo_equipamento AS "Custo Unidade",
	equipamentos.quantidade AS "Quantidade Estoque",
    COUNT(ordens_servico_equipamentos.equipamento_id) AS "Vezes Utilizado",
    GROUP_CONCAT(ordens_servico.id SEPARATOR ", ") AS "Utilizado nas OS (ID)"
FROM equipamentos
INNER JOIN ordens_servico_equipamentos ON ordens_servico_equipamentos.equipamento_id = equipamentos.id
INNER JOIN ordens_servico ON ordens_servico_equipamentos.os_id = ordens_servico.id
GROUP BY equipamentos.id, equipamentos.modelo;

-- Funcionários
SELECT
	funcionarios.nome AS "Nome",
    funcionarios.funcao AS "Função",
    setores.nome AS "Setor",
    COUNT(ordens_servico.responsavel_id) AS "Quantidade de OS (ID)",
    GROUP_CONCAT(ordens_servico.id SEPARATOR ", ") AS "Responsável pelas OS (ID)"
FROM funcionarios
INNER JOIN setores ON funcionarios.setor_id = setores.id
LEFT JOIN ordens_servico ON ordens_servico.responsavel_id = funcionarios.id
GROUP BY funcionarios.id;

-- Setores
SELECT
	setores.nome AS "Nome",
    setores.descricao AS "Descrição",
    COUNT(funcionarios.setor_id) AS "Quantidade de funcionários",
    GROUP_CONCAT(funcionarios.nome SEPARATOR ", ") AS "Funcionários registrados"
FROM setores
INNER JOIN funcionarios ON funcionarios.setor_id = setores.id
GROUP BY setores.id;

-- Ordens de Serviço
SELECT 
	ordens_servico.id AS "ID Ordem Serviço",
    ordens_servico.descricao AS "Descrição",
    clientes.nome AS "Solicitante",
    funcionarios.nome AS "Responsável",
    GROUP_CONCAT(CONCAT(equipamentos.modelo, " ", ordens_servico_equipamentos.quantidade, "x") SEPARATOR ',') AS "Equipamentos"
FROM ordens_servico
INNER JOIN clientes ON ordens_servico.solicitante_id = clientes.id
INNER JOIN funcionarios ON ordens_servico.responsavel_id = funcionarios.id
INNER JOIN ordens_servico_equipamentos ON ordens_servico.id = ordens_servico_equipamentos.os_id
INNER JOIN equipamentos ON equipamentos.id = ordens_servico_equipamentos.equipamento_id
GROUP BY ordens_servico.id;