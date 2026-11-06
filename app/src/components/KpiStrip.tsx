type Props = {
  total: number;
  altaConfianca: number;
  scoreMedio: number;
  orgaosAtivos: number;
  vencendo7: number;
  mudancasRecentes: number;
  modo?: 'geral' | 'ti';
};

export function KpiStrip({
  total,
  altaConfianca,
  scoreMedio,
  orgaosAtivos,
  vencendo7,
  mudancasRecentes,
  modo = 'geral',
}: Props) {
  const items =
    modo === 'ti'
      ? [
          { label: 'Oportunidades TI', value: String(total), sub: 'no escopo (UF coleta)' },
          { label: 'Alta confiança', value: String(altaConfianca), sub: 'na lista carregada', accent: true },
          { label: 'Score médio', value: scoreMedio.toFixed(1), sub: 'na lista carregada' },
          { label: 'Órgãos ativos', value: String(orgaosAtivos), sub: 'na lista carregada' },
          { label: 'Vence em 7 dias', value: String(vencendo7), sub: 'na lista carregada', warn: vencendo7 > 0 },
          { label: 'Mudanças recentes', value: String(mudancasRecentes), sub: '7 dias', pulse: mudancasRecentes > 0 },
        ]
      : [
          { label: 'Oportunidades', value: String(total), sub: 'no escopo (UF coleta)' },
          { label: 'Classif. TI alta', value: String(altaConfianca), sub: 'na lista carregada' },
          { label: 'Órgãos', value: String(orgaosAtivos), sub: 'na lista carregada' },
          { label: 'Prazo ≤ 7 dias', value: String(vencendo7), sub: 'na lista carregada', warn: vencendo7 > 0 },
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
