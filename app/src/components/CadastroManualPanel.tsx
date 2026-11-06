import { useState } from 'react';
import { createOportunidadeManual } from '../api';

type Props = {
  onCreated: (numero: string) => void;
};

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

  async function salvar() {
    setSaving(true);
    setErro('');
    setMsg('');
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
      <p className="drawer__hint">
        Importação em lote por JSON existe no código (API), mas ficou fora do escopo autorizado desta
        etapa e não está disponível nesta tela até avaliação.
      </p>

      {msg && <p className="acomp__ok">{msg}</p>}
      {erro && <p className="acomp__err">{erro}</p>}
    </section>
  );
}
