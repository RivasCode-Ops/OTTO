import { describe, expect, it } from 'vitest';
import type { Oportunidade } from './types';
import {
  countPrazoAte,
  daysUntil,
  filterOportunidades,
  isRegistroTeste,
  labelCategoria,
  passaFiltroPrazo,
  resolveKpiTotalBanco,
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

describe('resolveKpiTotalBanco', () => {
  it('prioriza total de /api/kpis e nunca usa length da lista', () => {
    expect(
      resolveKpiTotalBanco({
        kpisTotal: 243,
        coberturaEscopoTotal: 243,
        coberturaBancoTotal: 1025,
        escopoUf: 'config',
      }),
    ).toBe(243);
    expect(resolveKpiTotalBanco({ kpisTotal: 888 })).not.toBe(500);
    expect(resolveKpiTotalBanco({})).toBe(0);
  });

  it('com escopo config não cai no banco inteiro; corrige KPI global vs escopo menor', () => {
    expect(
      resolveKpiTotalBanco({
        kpisTotal: 1025,
        coberturaEscopoTotal: 243,
        coberturaBancoTotal: 1025,
        escopoUf: 'config',
      }),
    ).toBe(243);
    expect(
      resolveKpiTotalBanco({
        kpisTotal: null,
        coberturaEscopoTotal: 243,
        coberturaBancoTotal: 1025,
        escopoUf: 'config',
      }),
    ).toBe(243);
    expect(
      resolveKpiTotalBanco({
        kpisTotal: null,
        coberturaBancoTotal: 1025,
        escopoUf: 'config',
      }),
    ).toBe(0);
  });

  it('escopo todas usa total do banco', () => {
    expect(
      resolveKpiTotalBanco({
        kpisTotal: 1025,
        coberturaEscopoTotal: 243,
        coberturaBancoTotal: 1025,
        escopoUf: 'todas',
      }),
    ).toBe(1025);
    expect(
      resolveKpiTotalBanco({
        kpisTotal: null,
        coberturaBancoTotal: 1025,
        escopoUf: 'todas',
      }),
    ).toBe(1025);
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

  it('qualquer prazo (3650) inclui vencidas e sem prazo', () => {
    expect(passaFiltroPrazo(longe, 3650)).toBe(true);
    expect(passaFiltroPrazo(semPrazo, 3650)).toBe(true);
    expect(passaFiltroPrazo(vencida, 3650)).toBe(true);
    expect(passaFiltroPrazo(futura, 3650)).toBe(true);
  });

  it('filterOportunidades oculta testes (objeto e MANUAL-) por padrão', () => {
    const testeObj = opp({
      numero_controle_pncp: 'T',
      origem_registro: 'manual',
      objeto_compra: 'TESTE ruido',
      data_encerramento: isoOffset(3),
    });
    const testeManual = opp({
      numero_controle_pncp: 'MANUAL-ABC',
      origem_registro: 'manual',
      objeto_compra: 'Cadastro realista',
      data_encerramento: isoOffset(3),
    });
    const out = filterOportunidades([futura, vencida, semPrazo, testeObj, testeManual], {
      q: '',
      dias: 'abertas',
      somenteAlta: false,
    });
    expect(out.map((o) => o.numero_controle_pncp).sort()).toEqual(['A', 'C']);
  });

  it('filterOportunidades pode mostrar testes com ocultarTestes=false', () => {
    const testeManual = opp({
      numero_controle_pncp: 'MANUAL-XYZ',
      origem_registro: 'manual',
      objeto_compra: 'Qualquer',
      data_encerramento: isoOffset(2),
    });
    const out = filterOportunidades([futura, testeManual], {
      q: '',
      dias: 'abertas',
      somenteAlta: false,
      ocultarTestes: false,
    });
    expect(out.map((o) => o.numero_controle_pncp).sort()).toEqual(['A', 'MANUAL-XYZ']);
  });

  it('countPrazoAte alinha ao KPI de 7 dias', () => {
    expect(countPrazoAte([futura, longe, vencida, semPrazo], 7)).toBe(1);
  });
});

describe('isRegistroTeste / labelCategoria', () => {
  it('detecta MANUAL- e manuais de teste por objeto', () => {
    expect(
      isRegistroTeste(
        opp({
          numero_controle_pncp: 'MANUAL-1',
          origem_registro: 'manual',
          objeto_compra: 'Sem palavra teste',
        }),
      ),
    ).toBe(true);
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
