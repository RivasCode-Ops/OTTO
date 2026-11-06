import { describe, expect, it } from 'vitest';
import type { Oportunidade } from './types';
import {
  countPrazoAte,
  daysUntil,
  filterOportunidades,
  isRegistroTeste,
  labelCategoria,
  passaFiltroPrazo,
} from './utils';

function opp(partial: Partial<Oportunidade> & { numero_controle_pncp: string }): Oportunidade {
  return {
    orgao_razao_social: 'ORG',
    uf: 'PI',
    objeto_compra: 'Objeto',
    situacao: 'Publicada',
    nicho: 'outros',
    confianca_classificacao: 'nenhuma',
    score_total: 0,
    score_detalhe: { valor: 0, urgencia: 0, nicho: 0, recorrencia: 0, labels: {} },
    ...partial,
  };
}

function isoOffset(days: number): string {
  const d = new Date();
  d.setHours(12, 0, 0, 0);
  d.setDate(d.getDate() + days);
  // Data local YYYY-MM-DD (evita fuso UTC do toISOString).
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

describe('daysUntil', () => {
  it('retorna null sem data', () => {
    expect(daysUntil(null)).toBeNull();
    expect(daysUntil(undefined)).toBeNull();
    expect(daysUntil('')).toBeNull();
  });

  it('conta dias até o prazo', () => {
    expect(daysUntil(isoOffset(0))).toBe(0);
    expect(daysUntil(isoOffset(7))).toBe(7);
    expect(daysUntil(isoOffset(-3))).toBe(-3);
  });
});

describe('passaFiltroPrazo / filterOportunidades', () => {
  const futura = opp({
    numero_controle_pncp: 'A',
    data_encerramento: isoOffset(5),
  });
  const vencida = opp({
    numero_controle_pncp: 'B',
    data_encerramento: isoOffset(-2),
  });
  const semPrazo = opp({
    numero_controle_pncp: 'C',
    data_encerramento: null,
  });
  const longe = opp({
    numero_controle_pncp: 'D',
    data_encerramento: isoOffset(40),
  });

  it('abertas exclui vencidas e mantém sem data', () => {
    expect(passaFiltroPrazo(futura, 'abertas')).toBe(true);
    expect(passaFiltroPrazo(vencida, 'abertas')).toBe(false);
    expect(passaFiltroPrazo(semPrazo, 'abertas')).toBe(true);
  });

  it('dias < 3650 exclui vencidas e sem data', () => {
    expect(passaFiltroPrazo(futura, 7)).toBe(true);
    expect(passaFiltroPrazo(longe, 7)).toBe(false);
    expect(passaFiltroPrazo(vencida, 7)).toBe(false);
    expect(passaFiltroPrazo(semPrazo, 7)).toBe(false);
  });

  it('qualquer prazo (3650) exclui só vencidas', () => {
    expect(passaFiltroPrazo(longe, 3650)).toBe(true);
    expect(passaFiltroPrazo(semPrazo, 3650)).toBe(true);
    expect(passaFiltroPrazo(vencida, 3650)).toBe(false);
  });

  it('filterOportunidades aplica prazo + busca + oculta testes', () => {
    const teste = opp({
      numero_controle_pncp: 'T',
      origem_registro: 'manual',
      objeto_compra: 'TESTE ruido',
      data_encerramento: isoOffset(3),
    });
    const out = filterOportunidades([futura, vencida, semPrazo, teste], {
      q: '',
      dias: 'abertas',
      somenteAlta: false,
    });
    expect(out.map((o) => o.numero_controle_pncp).sort()).toEqual(['A', 'C']);
  });

  it('countPrazoAte alinha ao KPI de 7 dias', () => {
    expect(countPrazoAte([futura, longe, vencida, semPrazo], 7)).toBe(1);
  });
});

describe('isRegistroTeste / labelCategoria', () => {
  it('detecta manuais de teste', () => {
    expect(
      isRegistroTeste(
        opp({
          numero_controle_pncp: '1',
          origem_registro: 'manual',
          objeto_compra: 'TESTE IA',
        }),
      ),
    ).toBe(true);
    expect(
      isRegistroTeste(
        opp({
          numero_controle_pncp: '2',
          origem_registro: 'manual',
          objeto_compra: 'Import JSON teste X',
        }),
      ),
    ).toBe(true);
    expect(
      isRegistroTeste(
        opp({
          numero_controle_pncp: '3',
          origem_registro: 'pncp',
          objeto_compra: 'TESTE real pncp',
        }),
      ),
    ).toBe(false);
  });

  it('mapeia nao_classificado para Outros', () => {
    expect(
      labelCategoria(
        opp({ numero_controle_pncp: '1', nicho: 'nao_classificado' }),
      ),
    ).toBe('Outros');
    expect(
      labelCategoria(opp({ numero_controle_pncp: '2', nicho: 'ti_software', categoria_principal: 'TI' })),
    ).toBe('TI');
  });
});
