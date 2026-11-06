/** 26 estados + DF — seletor de localidade do painel (não depende do que há no SQLite). */
export const UFS_BRASIL = [
  'AC',
  'AL',
  'AP',
  'AM',
  'BA',
  'CE',
  'DF',
  'ES',
  'GO',
  'MA',
  'MT',
  'MS',
  'MG',
  'PA',
  'PB',
  'PR',
  'PE',
  'PI',
  'RJ',
  'RN',
  'RS',
  'RO',
  'RR',
  'SC',
  'SP',
  'SE',
  'TO',
] as const;

export type UfBrasil = (typeof UFS_BRASIL)[number];

export function isUfBrasil(value: string): value is UfBrasil {
  const u = value.trim().toUpperCase();
  return (UFS_BRASIL as readonly string[]).includes(u);
}
