# Nichos — classificador multi-setor

Classificador **determinístico** (sem LLM): regras sobre **objeto + órgão**.  
Implementação: `packages/otto-core/src/otto_core/niche.py`

**Atualizado:** 2026-11-06 — setores além de TI; TI permanece `ti_software` (v2.2).

---

## Setores (IDs)

| ID | Rótulo |
|----|--------|
| `passagens_viagens` | Passagens / viagens |
| `saude_medicamentos` | Saúde / medicamentos |
| `obras_engenharia` | Obras / engenharia |
| `alimentos_merenda` | Alimentos / merenda |
| `material_escritorio_papelaria` | Material de escritório |
| `limpeza_conservacao` | Limpeza / conservação |
| `veiculos_combustiveis` | Veículos / combustíveis |
| `ti_software` | TI / software |
| `outros` | Residual |

Ordem: setores específicos → TI → `outros`.

---

## TI (v2.2, preservado)

```
SE bloqueio residual (hotelaria, mobiliário, iluminação pública, …) → outros
SENÃO SE ≥1 termo/frase forte → ti_software · alta
SENÃO SE ≥2 fracos → ti_software · baixa
SENÃO → outros
```

Matching por fronteira de palavra; `servidor(es)` + municipal/público ≠ hardware; hospedagem contextual.

---

## Reclassificação

```bat
otto reclassify-nicho
```

Idempotente. **Não** altera registros com `origem=usuario` / `revisado_pelo_usuario` na tabela de classificações, nem `origem_registro` manual/usuario.

---

## Especializações §14 (Saúde / Viagens)

Quando o nicho for `saude_medicamentos` ou `passagens_viagens`, o detalhe da
oportunidade mostra subtipos e condições **só se o texto do objeto** trouxer
sinais (`otto_core.especializacao`). Não inventa exigências pela categoria.
API: `GET /api/oportunidades/{numero}/especializacao`.

---

## Painel

- Filtro **UF**: coleta (padrão) · as 27 UFs (sem dados no SQLite aparece marcado) · Todas (no banco)  
- Filtro **Nicho**: Todos + setores com contagem (respeita UF + prazo ativos)  
- Regiões / Categorias: clique aplica filtro e volta à Lista geral  

