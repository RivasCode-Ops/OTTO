# Nichos — TI v2.1 (congelado)

Classificador **defensivo** para radar operacional PI.  
Implementação: `packages/otto-core/src/otto_core/niche.py`

---

## Regra em pseudocódigo

```
SE qualquer bloqueio no objeto → outros
SENÃO SE ≥1 termo_forte OU frase_forte_hospedagem → ti_software · alta
SENÃO SE ≥2 termos_fracos → ti_software · baixa
SENÃO → outros

# v2.1 — hospedagem contextual
SE "hospedagem" no objeto
  E NÃO (frase "hospedagem de …" OU termo técnico adjacente)
  → ignorar como sinal TI (neutro)
```

---

## Alta confiança

≥ **1 termo forte**, sem bloqueio.

| Grupo | Termos / frases |
|-------|-----------------|
| Software | software, licença, licenciamento, SaaS, ERP, aplicativo |
| TI explícita | informática, tecnologia da informação, TIC, TI |
| Hardware | computador, notebook, desktop, servidor, impressora, scanner |
| Rede / segurança | firewall, switch, roteador, link de internet, infraestrutura de rede |
| Infra / cloud | hosting, cloud, nuvem, datacenter, backup, domínio |
| Hospedagem TI | **hospedagem de sistemas**, hospedagem de sites, hospedagem em nuvem |
| Sistemas | desenvolvimento de software, sistema de gestão, equipamento de informática |

### Hospedagem (v2.1)

| Contexto | Classificação |
|----------|---------------|
| `hospedagem` + hotelaria / diária / café da manhã | **bloqueio** → outros |
| `hospedagem` + hosting / cloud / servidor / domínio / sistemas | **forte** → alta |
| `hospedagem` isolada | **neutro** → não sobe para TI |

---

## Baixa confiança

≥ **2 termos fracos**, sem bloqueio e sem forte:

`sistema`, `digital`, `eletrônico`, `manutenção`, `serviço técnico`, `API`, `app`…

**Um fraco isolado → `outros`.**

---

## Bloqueios → `outros`

Anulam TI mesmo com termo fraco ou ambíguo.

| Categoria | Exemplos |
|-----------|----------|
| Institucional PNCP | portal de compras públicas |
| Saúde / hospital | medicamento, hospitalar, fisioterapia |
| Obras / frota | engenharia civil, veículo, frota, transporte escolar |
| Hotelaria | **hotel**, **hotelaria**, **pousada**, **diária**, apartamento |
| Alimentação | alimentação, merenda, cozinheiro, café da manhã, almoço, jantar |
| Outros | mobiliário, material de limpeza, combustível, rede pública (escolar) |

Frases bloqueadoras: `hospedagem com café da manhã`, `evento presencial`.

---

## Referência YAML (espelho da regra)

```yaml
nicho: ti_software
versao: "2.1"

fortes:
  frases:
    - tecnologia da informacao
    - infraestrutura de ti
    - hospedagem de sistemas
    - hospedagem de sites
    - hospedagem em nuvem
  termos:
    - software
    - notebook
    - servidor
    - hosting
    - cloud
    - nuvem
    - dominio

fracos:
  - sistema
  - digital
  - eletronico
  - manutencao

bloqueios:
  frases:
    - portal de compras publicas
    - hospedagem com cafe da manha
  termos:
    - hotelaria
    - hotel
    - pousada
    - medicamento
    - mobiliario

hospedagem:
  neutro_se_isolado: true
  contexto_ti:
    - hosting
    - cloud
    - nuvem
    - servidor
    - dominio
    - sistemas
```

---

## Critério V1 fechada (nicho)

- Top 10 sem falso positivo grosseiro
- PGE / infra / notebooks com **alta confiança**
- Painel default: filtro `somente alta confiança`

## Evolução pós-V1

- Carregar regras de `config/nichos.yaml`
- Segunda camada: CATSER/CATMAT quando PNCP expuser item catalogado
- CNAE/CNPJ do órgão como sinal secundário
