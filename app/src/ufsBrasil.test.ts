import { describe, expect, it } from 'vitest';
import { UFS_BRASIL, isUfBrasil } from './ufsBrasil';

describe('UFS_BRASIL', () => {
  it('lista as 27 unidades federativas sem duplicata', () => {
    expect(UFS_BRASIL).toHaveLength(27);
    expect(new Set(UFS_BRASIL).size).toBe(27);
  });

  it('reconhece siglas válidas', () => {
    expect(isUfBrasil('pi')).toBe(true);
    expect(isUfBrasil('DF')).toBe(true);
    expect(isUfBrasil('XX')).toBe(false);
  });
});
