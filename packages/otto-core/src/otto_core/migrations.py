"""Migrações SQLite versionadas e não destrutivas.

Cada id é aplicado no máximo uma vez (tabela schema_migrations).
"""
from __future__ import annotations

import sqlite3

MIGRATIONS: list[tuple[str, str]] = [
    (
        "001_oportunidade_acompanhamento",
        """
        CREATE TABLE IF NOT EXISTS oportunidade_acompanhamento (
          numero_controle_pncp TEXT PRIMARY KEY,
          salva INTEGER NOT NULL DEFAULT 0,
          interesse INTEGER NOT NULL DEFAULT 0,
          decisao TEXT NOT NULL DEFAULT 'sem_decisao',
          observacoes TEXT NOT NULL DEFAULT '',
          justificativa TEXT NOT NULL DEFAULT '',
          atualizado_em TEXT NOT NULL,
          FOREIGN KEY (numero_controle_pncp) REFERENCES oportunidades(numero_controle_pncp)
        );
        CREATE INDEX IF NOT EXISTS idx_acomp_salva ON oportunidade_acompanhamento(salva);
        CREATE INDEX IF NOT EXISTS idx_acomp_interesse ON oportunidade_acompanhamento(interesse);
        CREATE INDEX IF NOT EXISTS idx_acomp_decisao ON oportunidade_acompanhamento(decisao);
        """,
    ),
    (
        "002_documentos_analise_checklist",
        """
        CREATE TABLE IF NOT EXISTS oportunidade_documentos (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          numero_controle_pncp TEXT NOT NULL,
          nome_original TEXT NOT NULL,
          nome_armazenado TEXT NOT NULL,
          tipo_mime TEXT NOT NULL DEFAULT 'application/octet-stream',
          origem TEXT NOT NULL DEFAULT 'upload_local',
          incluido_em TEXT NOT NULL,
          versao INTEGER NOT NULL DEFAULT 1,
          documento_anterior_id INTEGER,
          tamanho_bytes INTEGER NOT NULL DEFAULT 0,
          status_extracao TEXT NOT NULL DEFAULT 'pendente',
          aviso_extracao TEXT NOT NULL DEFAULT '',
          FOREIGN KEY (numero_controle_pncp) REFERENCES oportunidades(numero_controle_pncp),
          FOREIGN KEY (documento_anterior_id) REFERENCES oportunidade_documentos(id)
        );
        CREATE INDEX IF NOT EXISTS idx_docs_opp ON oportunidade_documentos(numero_controle_pncp);

        CREATE TABLE IF NOT EXISTS documento_paginas (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          documento_id INTEGER NOT NULL,
          pagina INTEGER NOT NULL,
          texto TEXT NOT NULL DEFAULT '',
          UNIQUE (documento_id, pagina),
          FOREIGN KEY (documento_id) REFERENCES oportunidade_documentos(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS analise_fichas (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          numero_controle_pncp TEXT NOT NULL UNIQUE,
          status TEXT NOT NULL DEFAULT 'aguardando_documentos',
          atualizado_em TEXT NOT NULL,
          aviso TEXT NOT NULL DEFAULT '',
          FOREIGN KEY (numero_controle_pncp) REFERENCES oportunidades(numero_controle_pncp)
        );

        CREATE TABLE IF NOT EXISTS analise_campos (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ficha_id INTEGER NOT NULL,
          chave TEXT NOT NULL,
          rotulo TEXT NOT NULL,
          valor TEXT NOT NULL DEFAULT '',
          natureza TEXT NOT NULL,
          documento_id INTEGER,
          pagina INTEGER,
          trecho TEXT NOT NULL DEFAULT '',
          atualizado_em TEXT NOT NULL,
          UNIQUE (ficha_id, chave),
          FOREIGN KEY (ficha_id) REFERENCES analise_fichas(id) ON DELETE CASCADE,
          FOREIGN KEY (documento_id) REFERENCES oportunidade_documentos(id)
        );

        CREATE TABLE IF NOT EXISTS checklist_itens (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          numero_controle_pncp TEXT NOT NULL,
          titulo TEXT NOT NULL,
          descricao TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL DEFAULT 'pendente',
          requisito_chave TEXT NOT NULL DEFAULT '',
          evidencia_documento_id INTEGER,
          evidencia_pagina INTEGER,
          evidencia_trecho TEXT NOT NULL DEFAULT '',
          atualizado_em TEXT NOT NULL,
          FOREIGN KEY (numero_controle_pncp) REFERENCES oportunidades(numero_controle_pncp),
          FOREIGN KEY (evidencia_documento_id) REFERENCES oportunidade_documentos(id)
        );
        CREATE INDEX IF NOT EXISTS idx_checklist_opp ON checklist_itens(numero_controle_pncp);
        """,
    ),
    (
        "003_rastreio_fluxo_financeiro_backup",
        """
        ALTER TABLE analise_campos ADD COLUMN precisa_revisao INTEGER NOT NULL DEFAULT 0;
        ALTER TABLE analise_fichas ADD COLUMN motivo_desatualizacao TEXT NOT NULL DEFAULT '';
        ALTER TABLE checklist_itens ADD COLUMN categoria TEXT NOT NULL DEFAULT '';
        ALTER TABLE checklist_itens ADD COLUMN observacao TEXT NOT NULL DEFAULT '';

        CREATE TABLE IF NOT EXISTS oportunidade_fluxo (
          numero_controle_pncp TEXT PRIMARY KEY,
          estado_fluxo TEXT NOT NULL DEFAULT 'nao_avaliada',
          resultado_disputa TEXT NOT NULL DEFAULT 'nao_informado',
          resultado_contratacao TEXT NOT NULL DEFAULT 'nao_informado',
          resultado_execucao TEXT NOT NULL DEFAULT 'nao_informado',
          resultado_recebimento TEXT NOT NULL DEFAULT 'nao_informado',
          notas_resultado TEXT NOT NULL DEFAULT '',
          atualizado_em TEXT NOT NULL,
          FOREIGN KEY (numero_controle_pncp) REFERENCES oportunidades(numero_controle_pncp)
        );

        CREATE TABLE IF NOT EXISTS cenarios_financeiros (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          numero_controle_pncp TEXT NOT NULL,
          nome TEXT NOT NULL DEFAULT 'Cenário 1',
          receita_estimada REAL,
          quantidade REAL,
          custo_unitario REAL,
          frete REAL,
          deslocamento REAL,
          mao_obra REAL,
          despesas_operacionais REAL,
          tributos REAL,
          outros_custos REAL,
          contingencia REAL,
          premissas TEXT NOT NULL DEFAULT '',
          escopo_parcial INTEGER NOT NULL DEFAULT 0,
          atualizado_em TEXT NOT NULL,
          FOREIGN KEY (numero_controle_pncp) REFERENCES oportunidades(numero_controle_pncp)
        );
        CREATE INDEX IF NOT EXISTS idx_cenarios_opp ON cenarios_financeiros(numero_controle_pncp);
        """,
    ),
    (
        "004_orgaos_classificacoes",
        """
        CREATE TABLE IF NOT EXISTS orgao_anotacoes (
          orgao_chave TEXT PRIMARY KEY,
          cnpj TEXT,
          nome_exibicao TEXT NOT NULL DEFAULT '',
          anotacoes TEXT NOT NULL DEFAULT '',
          atualizado_em TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS oportunidade_classificacoes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          numero_controle_pncp TEXT NOT NULL,
          setor TEXT NOT NULL,
          categoria TEXT NOT NULL DEFAULT '',
          subcategoria TEXT NOT NULL DEFAULT '',
          origem TEXT NOT NULL DEFAULT 'automatico',
          revisado_pelo_usuario INTEGER NOT NULL DEFAULT 0,
          atualizado_em TEXT NOT NULL,
          UNIQUE (numero_controle_pncp, setor, categoria, subcategoria),
          FOREIGN KEY (numero_controle_pncp) REFERENCES oportunidades(numero_controle_pncp)
        );
        CREATE INDEX IF NOT EXISTS idx_class_opp ON oportunidade_classificacoes(numero_controle_pncp);
        CREATE INDEX IF NOT EXISTS idx_class_setor ON oportunidade_classificacoes(setor);
        """,
    ),
    (
        "005_checklist_prazo_responsavel_financeiro_realizado",
        """
        ALTER TABLE checklist_itens ADD COLUMN prazo_conhecido TEXT NOT NULL DEFAULT '';
        ALTER TABLE checklist_itens ADD COLUMN responsavel TEXT NOT NULL DEFAULT '';

        ALTER TABLE cenarios_financeiros ADD COLUMN receita_realizada REAL;
        ALTER TABLE cenarios_financeiros ADD COLUMN custos_realizados REAL;
        """,
    ),
    (
        "006_orientacao_caixa_naturezas",
        """
        CREATE TABLE IF NOT EXISTS orientacao_respostas (
          numero_controle_pncp TEXT NOT NULL,
          pergunta_id TEXT NOT NULL,
          resposta TEXT NOT NULL DEFAULT 'nao_respondida',
          detalhe TEXT NOT NULL DEFAULT '',
          atualizado_em TEXT NOT NULL,
          PRIMARY KEY (numero_controle_pncp, pergunta_id),
          FOREIGN KEY (numero_controle_pncp) REFERENCES oportunidades(numero_controle_pncp)
        );

        ALTER TABLE cenarios_financeiros ADD COLUMN prazo_desembolso TEXT NOT NULL DEFAULT '';
        ALTER TABLE cenarios_financeiros ADD COLUMN prazo_recebimento TEXT NOT NULL DEFAULT '';
        """,
    ),
    (
        "007_requisitos_verificacao",
        """
        CREATE TABLE IF NOT EXISTS requisitos_verificacao (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          numero_controle_pncp TEXT NOT NULL,
          descricao TEXT NOT NULL,
          origem TEXT NOT NULL DEFAULT 'usuario',
          estado TEXT NOT NULL DEFAULT 'nao_avaliado',
          evidencia_documento_id INTEGER,
          evidencia_trecho TEXT NOT NULL DEFAULT '',
          observacao TEXT NOT NULL DEFAULT '',
          atualizado_em TEXT NOT NULL,
          FOREIGN KEY (numero_controle_pncp) REFERENCES oportunidades(numero_controle_pncp),
          FOREIGN KEY (evidencia_documento_id) REFERENCES oportunidade_documentos(id)
        );
        CREATE INDEX IF NOT EXISTS idx_req_verif_opp ON requisitos_verificacao(numero_controle_pncp);
        """,
    ),
    (
        "008_manual_fluxo_itens_lotes",
        """
        ALTER TABLE oportunidades ADD COLUMN origem_registro TEXT NOT NULL DEFAULT 'pncp';

        CREATE TABLE IF NOT EXISTS oportunidade_lotes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          numero_controle_pncp TEXT NOT NULL,
          codigo TEXT NOT NULL DEFAULT '',
          descricao TEXT NOT NULL DEFAULT '',
          valor_estimado REAL,
          observacao TEXT NOT NULL DEFAULT '',
          disputa_separada_confirmada INTEGER NOT NULL DEFAULT 0,
          atualizado_em TEXT NOT NULL,
          FOREIGN KEY (numero_controle_pncp) REFERENCES oportunidades(numero_controle_pncp)
        );
        CREATE INDEX IF NOT EXISTS idx_lotes_opp ON oportunidade_lotes(numero_controle_pncp);

        CREATE TABLE IF NOT EXISTS oportunidade_itens (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          numero_controle_pncp TEXT NOT NULL,
          lote_id INTEGER,
          codigo TEXT NOT NULL DEFAULT '',
          descricao TEXT NOT NULL,
          quantidade REAL,
          unidade TEXT NOT NULL DEFAULT '',
          valor_unitario REAL,
          valor_total REAL,
          observacao TEXT NOT NULL DEFAULT '',
          atualizado_em TEXT NOT NULL,
          FOREIGN KEY (numero_controle_pncp) REFERENCES oportunidades(numero_controle_pncp),
          FOREIGN KEY (lote_id) REFERENCES oportunidade_lotes(id)
        );
        CREATE INDEX IF NOT EXISTS idx_itens_opp ON oportunidade_itens(numero_controle_pncp);
        CREATE INDEX IF NOT EXISTS idx_itens_lote ON oportunidade_itens(lote_id);

        CREATE INDEX IF NOT EXISTS idx_fluxo_estado ON oportunidade_fluxo(estado_fluxo);
        """,
    ),
    (
        "009_prazos_resultados_auditoria_itens_setor",
        """
        ALTER TABLE oportunidades ADD COLUMN data_esclarecimento TEXT;
        ALTER TABLE oportunidades ADD COLUMN data_impugnacao TEXT;

        ALTER TABLE oportunidade_fluxo ADD COLUMN tempo_preparacao_horas REAL;
        ALTER TABLE oportunidade_fluxo ADD COLUMN custo_preparacao REAL;

        ALTER TABLE oportunidade_itens ADD COLUMN setor TEXT NOT NULL DEFAULT '';
        ALTER TABLE oportunidade_itens ADD COLUMN categoria TEXT NOT NULL DEFAULT '';

        CREATE TABLE IF NOT EXISTS auditoria_acoes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          acao TEXT NOT NULL,
          numero_controle_pncp TEXT,
          detalhe TEXT NOT NULL DEFAULT '',
          criado_em TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_auditoria_criado ON auditoria_acoes(criado_em);
        """,
    ),
    (
        "010_item_classificacao_origem_sugestao",
        """
        ALTER TABLE oportunidade_itens ADD COLUMN setor_sugerido TEXT NOT NULL DEFAULT '';
        ALTER TABLE oportunidade_itens ADD COLUMN categoria_sugerida TEXT NOT NULL DEFAULT '';
        ALTER TABLE oportunidade_itens ADD COLUMN classificacao_origem TEXT NOT NULL DEFAULT '';
        """,
    ),
    (
        "011_evidencia_pagina_revisao",
        """
        ALTER TABLE requisitos_verificacao ADD COLUMN evidencia_pagina INTEGER;
        ALTER TABLE requisitos_verificacao ADD COLUMN precisa_revisao INTEGER NOT NULL DEFAULT 0;
        ALTER TABLE requisitos_verificacao ADD COLUMN revisao_origem TEXT NOT NULL DEFAULT '';

        ALTER TABLE analise_campos ADD COLUMN revisao_origem TEXT NOT NULL DEFAULT '';
        """,
    ),
    (
        "012_ia_local_analise",
        """
        CREATE TABLE IF NOT EXISTS analise_ia_jobs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          numero_controle_pncp TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pendente',
          documento_ids_json TEXT NOT NULL DEFAULT '[]',
          modelo TEXT NOT NULL DEFAULT '',
          progresso TEXT NOT NULL DEFAULT '',
          cobertura TEXT NOT NULL DEFAULT '',
          erro TEXT NOT NULL DEFAULT '',
          iniciado_em TEXT,
          atualizado_em TEXT NOT NULL,
          concluido_em TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_ia_jobs_numero ON analise_ia_jobs(numero_controle_pncp);

        CREATE TABLE IF NOT EXISTS analise_ia_sugestoes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          job_id INTEGER NOT NULL,
          numero_controle_pncp TEXT NOT NULL,
          tipo TEXT NOT NULL,
          chave TEXT NOT NULL DEFAULT '',
          titulo TEXT NOT NULL DEFAULT '',
          valor TEXT NOT NULL DEFAULT '',
          documento_id INTEGER,
          pagina INTEGER,
          trecho TEXT NOT NULL DEFAULT '',
          referencia_confirmada INTEGER NOT NULL DEFAULT 0,
          aviso_referencia TEXT NOT NULL DEFAULT '',
          estado TEXT NOT NULL DEFAULT 'pendente',
          criado_em TEXT NOT NULL,
          FOREIGN KEY (job_id) REFERENCES analise_ia_jobs(id)
        );
        CREATE INDEX IF NOT EXISTS idx_ia_sug_job ON analise_ia_sugestoes(job_id);
        CREATE INDEX IF NOT EXISTS idx_ia_sug_numero ON analise_ia_sugestoes(numero_controle_pncp);
        """,
    ),
]


def apply_migrations(conn: sqlite3.Connection) -> list[str]:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
          id TEXT PRIMARY KEY,
          aplicada_em TEXT NOT NULL
        )
        """
    )
    aplicadas = {
        r[0] for r in conn.execute("SELECT id FROM schema_migrations").fetchall()
    }
    novas: list[str] = []
    for mid, sql in MIGRATIONS:
        if mid in aplicadas:
            continue
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_migrations (id, aplicada_em) VALUES (?, datetime('now'))",
            (mid,),
        )
        novas.append(mid)
    conn.commit()
    return novas
