type Props = {
  /** Contagem alinhada ao filtro de prazo ativo (ex.: Abertas). */
  total: number;
  /** Contagem no recorte UF+nicho sem filtro de prazo (banco do recorte). */
  totalBanco?: number;
  /** Ex.: "abertas", "prazo ≤7d" — usado no subtítulo dual. */
  prazoRotulo?: string;
  /** Testes ocultos no recorte — explica diferença vs banner bruto. */
  nTestesOcultos?: number;
  altaConfianca: number;
  scoreMedio: number;
  orgaosAtivos: number;
  vencendo7: number;
  mudancasRecentes: number;
  modo?: 'geral' | 'ti';
};

export function KpiStrip({
  total,
  totalBanco,
  prazoRotulo = 'abertas',
  nTestesOcultos = 0,
  altaConfianca,
  scoreMedio,
  orgaosAtivos,
  vencendo7,
  mudancasRecentes,
  modo = 'geral',
}: Props) {
  const notaTestes = nTestesOcultos > 0 ? ' (sem testes)' : '';
  const mostraDual =
    typeof totalBanco === 'number' && totalBanco !== total && prazoRotulo !== 'qualquer prazo';
  const subOportunidades = mostraDual
    ? `${totalBanco} no banco${notaTestes} · ${total} ${prazoRotulo}`
    : typeof totalBanco === 'number'
      ? `${totalBanco} no banco${notaTestes}`
      : modo === 'ti'
        ? 'nicho TI · filtro ativo'
        : 'UF + nicho · filtro ativo';

  const items =
    modo === 'ti'
      ? [
          { label: 'Oportunidades TI', value: String(total), sub: subOportunidades },
          {
            label: 'TI · alta confiança',
            value: String(altaConfianca),
            sub: 'nicho ti_software + confiança alta',
            accent: true,
          },
          { label: 'Score médio', value: scoreMedio.toFixed(1), sub: 'no recorte filtrado' },
          { label: 'Órgãos ativos', value: String(orgaosAtivos), sub: 'no recorte (sem prazo)' },
          { label: 'Vence em 7 dias', value: String(vencendo7), sub: 'no recorte (sem prazo)', warn: vencendo7 > 0 },
          { label: 'Mudanças recentes', value: String(mudancasRecentes), sub: '7 dias', pulse: mudancasRecentes > 0 },
        ]
      : [
          { label: 'Oportunidades', value: String(total), sub: subOportunidades },
          {
            label: 'TI · alta confiança',
            value: String(altaConfianca),
            sub: 'só nicho TI + confiança alta',
          },
          { label: 'Órgãos', value: String(orgaosAtivos), sub: 'no recorte (sem prazo)' },
          { label: 'Prazo ≤ 7 dias', value: String(vencendo7), sub: 'no recorte (sem prazo)', warn: vencendo7 > 0 },
          { label: 'Mudanças recentes', value: String(mudancasRecentes), sub: '7 dias', pulse: mudancasRecentes > 0 },
        ];

  return (
    <section className="kpi-strip" aria-label="Indicadores executivos">
      {items.map((k) => (
        <article
          key={k.label}
          className={`kpi-card ${k.accent ? 'kpi-card--accent' : ''} ${k.warn ? 'kpi-card--warn' : ''} ${k.pulse ? 'kpi-card--pulse' : ''}`}
        >
          <span className="kpi-card__label">{k.label}</span>
          <strong className="kpi-card__value">{k.value}</strong>
          <span className="kpi-card__sub">{k.sub}</span>
        </article>
      ))}
    </section>
  );
}
