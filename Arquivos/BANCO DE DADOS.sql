CREATE DATABASE sistema_nota_fiscal;

USE sistema_nota_fiscal;

CREATE TABLE empresas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    cnpj VARCHAR(18) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    telefone VARCHAR(20),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notas_fiscais (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    numero_nota VARCHAR(50) NOT NULL,
    nome_destinatario VARCHAR(255) NOT NULL,
    chave_acesso VARCHAR(44) UNIQUE NOT NULL,
    data_emissao DATE NOT NULL,
    status ENUM('pendente', 'assinado') DEFAULT 'pendente',
    caminho_arquivo VARCHAR(255) NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
);

CREATE TABLE assinaturas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nota_id INT NOT NULL,
    assinatura_imagem VARCHAR(255) NOT NULL,
    foto_imagem VARCHAR(255) NOT NULL,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    horario_assinatura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (nota_id) REFERENCES notas_fiscais(id) ON DELETE CASCADE
);

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    tipo ENUM('admin', 'motorista') NOT NULL,
    status ENUM('ativo', 'inativo') DEFAULT 'ativo',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
