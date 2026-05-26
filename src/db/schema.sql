-- Schema SQLite — espelha o que virá no Oracle (Fase 4)
-- Mantenha tipos compatíveis: DATE, VARCHAR2, NUMBER.

DROP TABLE IF EXISTS Abate;
DROP TABLE IF EXISTS Condenas;
DROP TABLE IF EXISTS Producao;

CREATE TABLE Abate (
    Data                   DATE        NOT NULL,
    Parceiro               VARCHAR(50) NOT NULL,
    Tipo_Suino             VARCHAR(20) NOT NULL,
    Quantidade             INTEGER     NOT NULL,
    Peso_Vivo_Kg           REAL        NOT NULL,
    Peso_Carcaca_Quente_Kg REAL        NOT NULL
);

CREATE TABLE Condenas (
    Data          DATE        NOT NULL,
    Parceiro      VARCHAR(50) NOT NULL,
    Tipo_Condena  VARCHAR(20) NOT NULL,
    Peso_Condena  REAL        NOT NULL
);

CREATE TABLE Producao (
    Data            DATE        NOT NULL,
    Parceiro        VARCHAR(50) NOT NULL,
    SKU             VARCHAR(20) NOT NULL,
    Nome_Produto    VARCHAR(100),
    Familia         VARCHAR(50),
    Total_Produzido REAL        NOT NULL
);

CREATE INDEX idx_abate_data    ON Abate(Data, Parceiro);
CREATE INDEX idx_condenas_data ON Condenas(Data, Parceiro);
CREATE INDEX idx_producao_data ON Producao(Data, Parceiro);
