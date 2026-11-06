import { useCallback, useEffect, useState } from 'react';
import {
  createBackup,
  createCenario,
  fetchAnalise,
  listBackups,
  restoreBackupCopy,
  saveFluxo,
  updateCenario,
} from '../api';
import type { CenarioFinanceiro, FluxoOportunidade } from '../types';

type Props = { numero: string };

const ESTADOS: { value: FluxoOportunidade['estado_fluxo']; label: string }[] = [
  { value: 'nao_avaliada', label: 'Não avaliada' },
  { value: 'salva', label: 'Salva' },
  { value: 'em_analise', label: 'Em análise' },
  { value: 'aguardando_informacoes', label: 'Aguardando informações' },
  { value: 'em_preparacao', label: 'Em preparação' },
  { value: 'participacao_registrada', label: 'Participação registrada (local)' },
  { value: 'em_acompanhamento', label: 'Em acompanhamento' },
  { value: 'encerrada', label: 'Encerrada' },
  { value: 'arquivada', label: 'Arquivada' },
];

const RESULTADOS: { value: string; label: string }[] = [
  { value: 'nao_informado', label: 'Não informado' },
  { value: 'nao_aplicavel', label: 'Não aplicável' },
  { value: 'pendente', label: 'Pendente' },
  { value: 'sim', label: 'Sim' },
  { value: 'nao', label: 'Não' },
  { value: 'em_andamento', label: 'Em andamento' },
  { value: 'concluido', label: 'Concluído' },
];

export function ContinuidadePanel({ numero }: Props) {
  const [fluxo, setFluxo] = useState<FluxoOportunidade | null>(null);
  const [cenarios, setCenarios] = useState<CenarioFinanceiro[]>([]);
  const [fluxoCaixa, setFluxoCaixa] = useState<
    { data: string; tipo: string; cenario: string; valor: number | null }[]
  >([]);
  const [backups, setBackups] = useState<{ nome: string; bytes: number }[]>([]);
  const [msg, setMsg] = useState('');
  const [erro, setErro] = useState('');
  const [fin, setFin] = useState({
    nome: 'Cenário 1',
    receita_estimada: '',
    quantidade: '',
    custo_unitario: '',
    frete: '',
    deslocamento: '',
    mao_obra: '',
    despesas_operacionais: '',
    tributos: '',
    outros_custos: '',
    contingencia: '',
    receita_realizada: '',
    custos_realizados: '',
    prazo_desembolso: '',
    prazo_recebimento: '',
    premissas: '',
    escopo_parcial: false,
  });

  const reload = useCallback(async () => {
    setErro('');
    try {
      const data = await fetchAnalise(numero);
      setFluxo(data.fluxo);
      setCenarios(data.cenarios ?? []);
      setFluxoCaixa(data.fluxo_caixa?.eventos ?? []);
      const b = await listBackups();
      setBackups(b.items);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro ao carregar continuidade');
    }
  }, [numero]);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function patchFluxo(partial: Partial<FluxoOportunidade>) {
    try {
      const f = await saveFluxo(numero, partial);
      setFluxo(f);
      setMsg('Fluxo/resultados atualizados (local).');
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha no fluxo');
    }
  }

  function numOrNull(s: string): number | null {
    const t = s.trim();
    if (!t) return null;
    const n = Number(t.replace(',', '.'));
    return Number.isFinite(n) ? n : null;
  }

  async function salvarCenario() {
    try {
      const body = {
        nome: fin.nome || 'Cenário 1',
        receita_estimada: numOrNull(fin.receita_estimada),
        quantidade: numOrNull(fin.quantidade),
        custo_unitario: numOrNull(fin.custo_unitario),
        frete: numOrNull(fin.frete),
        deslocamento: numOrNull(fin.deslocamento),
        mao_obra: numOrNull(fin.mao_obra),
        despesas_operacionais: numOrNull(fin.despesas_operacionais),
        tributos: numOrNull(fin.tributos),
        outros_custos: numOrNull(fin.outros_custos),
        contingencia: numOrNull(fin.contingencia),
        receita_realizada: numOrNull(fin.receita_realizada),
        custos_realizados: numOrNull(fin.custos_realizados),
        prazo_desembolso: fin.prazo_desembolso,
        prazo_recebimento: fin.prazo_recebimento,
        premissas: fin.premissas,
        escopo_parcial: fin.escopo_parcial,
      };
      if (cenarios[0]) await updateCenario(numero, cenarios[0].id, body);
      else await createCenario(numero, body);
      setMsg('Cenário financeiro guardado.');
      await reload();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha financeira');
    }
  }

  async function doBackup() {
    try {
      const r = await createBackup();
      setMsg(`Backup criado: ${r.nome}`);
      await reload();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha no backup');
    }
  }

  async function doRestore(nome: string) {
    try {
      const r = await restoreBackupCopy(nome);
      setMsg(r.aviso);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha na restauração');
    }
  }

  return (
    <div className="docs-analise">
      <section className="drawer__block">
        <h3>Preparação, participação e resultados</h3>
        <p className="drawer__hint">{fluxo?.aviso}</p>
        {fluxo && (
          <>
            <label className="acomp__label">
              Estado no fluxo
              <select
                value={fluxo.estado_fluxo}
                onChange={(e) =>
                  void patchFluxo({
                    estado_fluxo: e.target.value as FluxoOportunidade['estado_fluxo'],
                  })
                }
              >
                {ESTADOS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            {(
              [
                ['resultado_disputa', 'Resultado da disputa'],
                ['resultado_contratacao', 'Contratação'],
                ['resultado_execucao', 'Execução'],
                ['resultado_recebimento', 'Recebimento'],
              ] as const
            ).map(([key, label]) => (
              <label key={key} className="acomp__label">
                {label}
                <select
                  value={fluxo[key]}
                  onChange={(e) => void patchFluxo({ [key]: e.target.value })}
                >
                  {RESULTADOS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
            ))}
            <label className="acomp__label">
              Notas de resultado
              <textarea
                rows={2}
                value={fluxo.notas_resultado}
                onChange={(e) => setFluxo({ ...fluxo, notas_resultado: e.target.value })}
                onBlur={() => void patchFluxo({ notas_resultado: fluxo.notas_resultado })}
              />
            </label>
            <label className="acomp__label">
              Tempo de preparação (horas)
              <input
                value={fluxo.tempo_preparacao_horas ?? ''}
                onChange={(e) => {
                  const n = e.target.value.trim() === '' ? null : Number(e.target.value.replace(',', '.'));
                  setFluxo({
                    ...fluxo,
                    tempo_preparacao_horas: n != null && Number.isFinite(n) ? n : null,
                  });
                }}
                onBlur={() =>
                  void patchFluxo({
                    tempo_preparacao_horas: fluxo.tempo_preparacao_horas ?? null,
                  })
                }
                placeholder="Ex.: 12"
              />
            </label>
            <label className="acomp__label">
              Custo de preparação (R$)
              <input
                value={fluxo.custo_preparacao ?? ''}
                onChange={(e) => {
                  const n = e.target.value.trim() === '' ? null : Number(e.target.value.replace(',', '.'));
                  setFluxo({
                    ...fluxo,
                    custo_preparacao: n != null && Number.isFinite(n) ? n : null,
                  });
                }}
                onBlur={() => void patchFluxo({ custo_preparacao: fluxo.custo_preparacao ?? null })}
                placeholder="Ex.: 1500"
              />
            </label>
          </>
        )}
      </section>

      <section className="drawer__block">
        <h3>Cenário financeiro (estimado)</h3>
        <p className="drawer__hint">
          Campo vazio = desconhecido (não é zero). Estimativa incompleta não é lucro líquido.
        </p>
        <label className="acomp__label">
          Nome
          <input value={fin.nome} onChange={(e) => setFin({ ...fin, nome: e.target.value })} />
        </label>
        <label className="acomp__label">
          Receita estimada
          <input
            value={fin.receita_estimada}
            onChange={(e) => setFin({ ...fin, receita_estimada: e.target.value })}
            placeholder="Deixe vazio se não souber"
          />
        </label>
        <label className="acomp__label">
          Quantidade
          <input
            value={fin.quantidade}
            onChange={(e) => setFin({ ...fin, quantidade: e.target.value })}
          />
        </label>
        <label className="acomp__label">
          Custo unitário
          <input
            value={fin.custo_unitario}
            onChange={(e) => setFin({ ...fin, custo_unitario: e.target.value })}
          />
        </label>
        <label className="acomp__label">
          Frete
          <input value={fin.frete} onChange={(e) => setFin({ ...fin, frete: e.target.value })} />
        </label>
        <label className="acomp__label">
          Deslocamento
          <input
            value={fin.deslocamento}
            onChange={(e) => setFin({ ...fin, deslocamento: e.target.value })}
          />
        </label>
        <label className="acomp__label">
          Mão de obra
          <input value={fin.mao_obra} onChange={(e) => setFin({ ...fin, mao_obra: e.target.value })} />
        </label>
        <label className="acomp__label">
          Despesas operacionais
          <input
            value={fin.despesas_operacionais}
            onChange={(e) => setFin({ ...fin, despesas_operacionais: e.target.value })}
          />
        </label>
        <label className="acomp__label">
          Tributos / encargos (informados)
          <input value={fin.tributos} onChange={(e) => setFin({ ...fin, tributos: e.target.value })} />
        </label>
        <label className="acomp__label">
          Outros custos
          <input
            value={fin.outros_custos}
            onChange={(e) => setFin({ ...fin, outros_custos: e.target.value })}
          />
        </label>
        <label className="acomp__label">
          Contingência
          <input
            value={fin.contingencia}
            onChange={(e) => setFin({ ...fin, contingencia: e.target.value })}
          />
        </label>
        <label className="acomp__label">
          Premissas (obrigatório para cenário completo)
          <textarea
            rows={2}
            value={fin.premissas}
            onChange={(e) => setFin({ ...fin, premissas: e.target.value })}
          />
        </label>
        <label className="acomp__label">
          <input
            type="checkbox"
            checked={fin.escopo_parcial}
            onChange={(e) => setFin({ ...fin, escopo_parcial: e.target.checked })}
          />{' '}
          Pretendo atender só parte do objeto
        </label>
        <h4>Resultados realizados (separados do estimado)</h4>
        <p className="drawer__hint">
          Só preencha o que já aconteceu. Vazio = desconhecido. Não substitui o cenário estimado.
        </p>
        <label className="acomp__label">
          Receita realizada
          <input
            value={fin.receita_realizada}
            onChange={(e) => setFin({ ...fin, receita_realizada: e.target.value })}
          />
        </label>
        <label className="acomp__label">
          Custos realizados
          <input
            value={fin.custos_realizados}
            onChange={(e) => setFin({ ...fin, custos_realizados: e.target.value })}
          />
        </label>
        <label className="acomp__label">
          Prazo de desembolso (texto livre)
          <input
            value={fin.prazo_desembolso}
            onChange={(e) => setFin({ ...fin, prazo_desembolso: e.target.value })}
            placeholder="Ex.: até 15 dias após empenho"
          />
        </label>
        <label className="acomp__label">
          Prazo de recebimento (texto livre)
          <input
            value={fin.prazo_recebimento}
            onChange={(e) => setFin({ ...fin, prazo_recebimento: e.target.value })}
            placeholder="Ex.: 30 dias após entrega"
          />
        </label>
        <button type="button" className="btn btn--primary" onClick={() => void salvarCenario()}>
          Guardar cenário
        </button>
        {cenarios.map((c) => (
          <div key={c.id} className="docs-analise__campo">
            <strong>{c.nome}</strong>
            {c.incompleto && <span className="pill">Incompleto</span>}
            <p className="muted">
              Estimado — custos:{' '}
              {c.custos_registrados != null ? c.custos_registrados.toLocaleString('pt-BR') : '—'}
              {' · '}
              saldo s/ custos:{' '}
              {c.saldo_sobre_custos_registrados != null
                ? c.saldo_sobre_custos_registrados.toLocaleString('pt-BR')
                : '—'}
              {' · '}
              necessidade de caixa:{' '}
              {c.necessidade_caixa_estimada != null
                ? c.necessidade_caixa_estimada.toLocaleString('pt-BR')
                : '—'}
            </p>
            <p className="muted">
              Realizado — receita:{' '}
              {c.receita_realizada != null ? c.receita_realizada.toLocaleString('pt-BR') : '—'}
              {' · '}
              custos:{' '}
              {c.custos_realizados != null ? c.custos_realizados.toLocaleString('pt-BR') : '—'}
              {' · '}
              saldo:{' '}
              {c.saldo_realizado != null ? c.saldo_realizado.toLocaleString('pt-BR') : '—'}
            </p>
            <ul className="muted">
              {c.avisos.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </div>
        ))}
        <h4>Linha do tempo de caixa (prazos dos cenários)</h4>
        <p className="drawer__hint">
          Agregação simples pelos prazos informados. Tributos são valores que você informa —
          o sistema não inventa regimes, alíquotas nem enquadramentos.
        </p>
        {fluxoCaixa.length === 0 ? (
          <p className="muted">Informe prazo de desembolso/recebimento nos cenários.</p>
        ) : (
          <ul className="docs-analise__list">
            {fluxoCaixa.map((e, i) => (
              <li key={`${e.data}-${e.tipo}-${i}`}>
                <span>
                  {e.data || '—'} · {e.tipo} · {e.cenario}
                  {e.valor != null ? ` · ${e.valor.toLocaleString('pt-BR')}` : ''}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="drawer__block">
        <h3>Cópia de segurança (local)</h3>
        <p className="drawer__hint">
          Backup grava banco + documentos. Não inclui perfil/preferências do navegador
          (localStorage). Aqui: restauração em cópia isolada. Para substituir o banco
          operacional (com confirmação), use Configurações.
        </p>
        <button type="button" className="btn btn--primary" onClick={() => void doBackup()}>
          Criar backup agora
        </button>
        <ul className="docs-analise__list">
          {backups.map((b) => (
            <li key={b.nome}>
              <span>
                {b.nome} · {(b.bytes / 1024).toFixed(0)} KB
              </span>
              <button type="button" className="btn btn--ghost" onClick={() => void doRestore(b.nome)}>
                Restaurar em cópia isolada
              </button>
            </li>
          ))}
        </ul>
      </section>

      {msg && <p className="acomp__ok">{msg}</p>}
      {erro && <p className="acomp__err">{erro}</p>}
    </div>
  );
}
