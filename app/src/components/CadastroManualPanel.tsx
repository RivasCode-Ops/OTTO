import { useState } from 'react';
import { createOportunidadeManual, importOportunidadesManualJson } from '../api';

type Props = {
  onCreated: (numero: string) => void;
};

const EXEMPLO_JSON = `{
  "items": [
    {
      "objeto_compra": "Exemplo — aquisição de material de escritório",
      "orgao_razao_social": "PREFEITURA EXEMPLO",
      "uf": "PI",
      "municipio": "Teresina",
      "modalidade": "Pregão - Eletrônico",
      "data_encerramento": "2026-12-15",
      "valor_total_estimado": 1000
    }
  ]
}`;

export function CadastroManualPanel({ onCreated }: Props) {
  const [objeto, setObjeto] = useState('');
  const [orgao, setOrgao] = useState('');
  const [uf, setUf] = useState('PI');
  const [municipio, setMunicipio] = useState('');
  const [modalidade, setModalidade] = useState('');
  const [valor, setValor] = useState('');
  const [prazo, setPrazo] = useState('');
  const [msg, setMsg] = useState('');
  const [erro, setErro] = useState('');
  const [saving, setSaving] = useState(false);
  const [jsonText, setJsonText] = useState('');
  const [importing, setImporting] = useState(false);
  const [importResumo, setImportResumo] = useState('');

  async function salvar() {
    setSaving(true);
    setErro('');
    setMsg('');
    setImportResumo('');
    try {
      const r = await createOportunidadeManual({
        objeto_compra: objeto,
        orgao_razao_social: orgao,
        uf,
        municipio,
        modalidade,
        valor_total_estimado: valor.trim() ? Number(valor.replace(',', '.')) : null,
        data_encerramento: prazo || null,
      });
      setMsg(r.aviso);
      setObjeto('');
      onCreated(r.item.numero_controle_pncp);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha no cadastro');
    } finally {
      setSaving(false);
    }
  }

  async function importarJson() {
    setImporting(true);
    setErro('');
    setMsg('');
    setImportResumo('');
    try {
      const parsed: unknown = JSON.parse(jsonText);
      const r = await importOportunidadesManualJson(parsed);
      const nOk = r.criados?.length ?? 0;
      const nErr = r.erros?.length ?? 0;
      setMsg(r.aviso || 'Importação concluída.');
      setImportResumo(
        `${nOk} criado(s)` +
          (nErr
            ? ` · ${nErr} erro(s): ${r.erros
                .slice(0, 5)
                .map((e) => `#${e.indice} ${e.erro}`)
                .join('; ')}${nErr > 5 ? '…' : ''}`
            : ''),
      );
      if (r.criados?.length) {
        onCreated(r.criados[r.criados.length - 1]);
      }
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha na importação JSON');
    } finally {
      setImporting(false);
    }
  }

  function onFile(file: File | null) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const t = typeof reader.result === 'string' ? reader.result : '';
      setJsonText(t);
    };
    reader.onerror = () => setErro('Não foi possível ler o arquivo.');
    reader.readAsText(file, 'UTF-8');
  }

  return (
    <section className="table-section">
      <header className="section-head">
        <div>
          <h2>Cadastro manual</h2>
          <p className="muted">
            Cria oportunidade neste computador com origem “manual”. Não substitui nem mistura com a
            coleta PNCP.
          </p>
        </div>
      </header>
      <label className="acomp__label">
        Objeto *
        <textarea rows={3} value={objeto} onChange={(e) => setObjeto(e.target.value)} />
      </label>
      <label className="acomp__label">
        Órgão
        <input value={orgao} onChange={(e) => setOrgao(e.target.value)} />
      </label>
      <label className="acomp__label">
        UF
        <input value={uf} maxLength={2} onChange={(e) => setUf(e.target.value.toUpperCase())} />
      </label>
      <label className="acomp__label">
        Município
        <input value={municipio} onChange={(e) => setMunicipio(e.target.value)} />
      </label>
      <label className="acomp__label">
        Modalidade
        <input value={modalidade} onChange={(e) => setModalidade(e.target.value)} />
      </label>
      <label className="acomp__label">
        Valor estimado (opcional)
        <input value={valor} onChange={(e) => setValor(e.target.value)} placeholder="Vazio = não informado" />
      </label>
      <label className="acomp__label">
        Prazo de proposta (ISO ou texto data, opcional)
        <input value={prazo} onChange={(e) => setPrazo(e.target.value)} placeholder="Ex.: 2026-12-01" />
      </label>
      <button type="button" className="btn btn--primary" disabled={saving} onClick={() => void salvar()}>
        {saving ? 'Guardando…' : 'Cadastrar oportunidade'}
      </button>

      <section className="drawer__block" style={{ marginTop: '1.25rem' }}>
      <h3>Importação JSON em lote</h3>
      <p className="drawer__hint">
        Aceita uma lista <code>[...]</code> ou <code>{`{"items":[...]}`}</code>. Cada item vira
        registro com origem “manual” (números <code>MANUAL-…</code>). Não altera coleta PNCP. Campos
        úteis: objeto_compra, orgao_razao_social, uf, municipio, modalidade, valor_total_estimado,
        data_encerramento.
      </p>
      <label className="acomp__label">
        Arquivo .json (opcional)
        <input
          type="file"
          accept=".json,application/json,text/plain"
          onChange={(e) => onFile(e.target.files?.[0] ?? null)}
        />
      </label>
      <label className="acomp__label">
        JSON
        <textarea
          rows={10}
          value={jsonText}
          onChange={(e) => setJsonText(e.target.value)}
          placeholder={EXEMPLO_JSON}
          spellCheck={false}
        />
      </label>
      <div className="acomp__actions">
        <button
          type="button"
          className="btn btn--primary"
          disabled={importing || !jsonText.trim()}
          onClick={() => void importarJson()}
        >
          {importing ? 'Importando…' : 'Importar JSON'}
        </button>
        <button
          type="button"
          className="btn btn--ghost"
          disabled={importing}
          onClick={() => setJsonText(EXEMPLO_JSON)}
        >
          Colar exemplo
        </button>
      </div>

      {msg && <p className="acomp__ok">{msg}</p>}
      {importResumo && <p className="muted">{importResumo}</p>}
      {erro && <p className="acomp__err">{erro}</p>}
      </section>
    </section>
  );
}
