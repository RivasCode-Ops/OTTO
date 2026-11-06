// Gerado por sync-dados.py — NÃO editar à mão.
// Fonte canônica: dados.json
window.LICITAR_ACOMPANHAMENTO = {
  "meta": {
    "titulo": "Acompanhar a construção do LICITAR",
    "subtitulo": "Painel de desenvolvimento — não é o aplicativo de oportunidades",
    "atualizado_em": "2026-11-06T12:05:00-03:00",
    "aviso_atualizacao": "Este painel NÃO atualiza sozinho. Ele só muda quando o assistente (ou você) registra uma nova atualização. Se a conversa estiver parada, o trabalho também está parado.",
    "sessao_agente": "encerrada",
    "como_abrir": "Abra painel.html nesta pasta (duplo clique). App: INICIAR-OTTO.bat → http://127.0.0.1:5194. DOCX: docs/DOCX.md. OCR: docs/OCR.md.",
    "onde_esta_o_projeto": "DOCX autorizado (python-docx; pagina opcional). OCR local ja entregue. Download automatico ainda nao.",
    "proxima_entrega_proposta": {
      "nome": "Download automatico (autorizacao) · §12.4 se houver fonte",
      "id_interno": "download-ou-concorrencia",
      "status": "DOCX+OCR entregues",
      "nao_iniciar_sem_autorizacao": true
    },
    "como_abrir_app": "INICIAR-OTTO.bat → oportunidade → Adicionar arquivo (.docx)"
  },
  "resumo_topo": {
    "ja_foi_feito": [
      "DOCX: upload + extracao paragrafos/tabelas; pagina opcional; docs/DOCX.md; .doc legado rejeitado.",
      "OCR local; doc instalacao; Vite 127.0.0.1; orgaos; ingest UI; aprendizado→prompt."
    ],
    "esta_sendo_feito": [],
    "mensagem_sem_execucao": "Fatia DOCX encerrada.",
    "falta_fazer": [
      "Instalar Tesseract (dono) se PDF digitalizado for prioridade (opcional).",
      "§12.4 concorrencia — bloqueada ate fonte.",
      "AGUARDANDO AUTORIZACAO: IMPORT-JSON na UI.",
      "ADIADOS DE PROPOSITO: validacao humana da IA local; teste rede fisicamente off."
    ],
    "precisa_de_mim": [
      {
        "pergunta_curta": "Download automatico de anexos do edital?",
        "impede": "So captura automatica de arquivos da fonte."
      }
    ]
  },
  "como_iniciar_encerrar": {
    "iniciar": [
      "Duplo clique em INICIAR-OTTO.bat (abre API :8791 e painel :5194)",
      "App: http://127.0.0.1:5194",
      "Este acompanhamento: abra painel.html nesta pasta"
    ],
    "encerrar": [
      "Feche a janela OTTO-API (ou Ctrl+C)",
      "Feche a janela do Vite/npm (ou Ctrl+C no INICIAR-OTTO)"
    ],
    "limitacoes_visiveis": [
      "IA local lenta neste equipamento (i3) — aguarde o job",
      "PDF so-imagem: depende de Tesseract no PC (opcional)",
      "Validacao humana da IA local e teste rede fisicamente off: adiados de proposito"
    ],
    "oportunidades_teste": [
      {
        "numero": "MANUAL-IA-PDF-E2E-05NOV-B",
        "objeto": "Cadeiras — documento de teste IA PDF",
        "doc": "edital-teste-ia-multipagina.pdf (v1/v2)"
      },
      {
        "numero": "MANUAL-FBFF06D94C0E",
        "objeto": "TESTE IA LOCAL / INPROCESS",
        "doc": "edital-teste-ia-local.txt"
      }
    ]
  },
  "ia_local_validacao": {
    "o_que_funciona_e_foi_testado": [
      "Campo origem usuario nunca sobrescrito pela IA (inclusive forcar=True ignorado)",
      "Integracao Ollama loopback + qwen2.5:3b; gate de evidencia; apply/rejeitar",
      "Aprendizado→prompt local (≥3 decisoes apply/reject; preferir/evitar; pytest)",
      "pytest regressao anterior + teste de preservacao usuario",
      "Fluxo analise→tarefa→evidencia; IA down; cobertura parcial",
      "PDF multipagina ACEITAVEL_COM_RESSALVAS"
    ],
    "limitacoes_conhecidas": [
      "CPU i3: analise lenta (~90s PDF curto; editais longos bem mais)",
      "OCR nao implementado (PDF so-imagem fora da IA)",
      "consumo_modelo = nao_medido (RSS llama-server ~2GB e observacao, nao prova)",
      "Campo origem usuario nunca sobrescrito pela IA — so edicao manual",
      "Citacoes as vezes curtas — revisao humana obrigatoria"
    ],
    "testes_pendentes": [],
    "adiados_proposito": [
      "Validacao humana da IA local (revisao de qualidade em uso real pelo dono)",
      "Teste com rede fisicamente desligada (endpoint local != esse teste)"
    ],
    "aguardando_autorizacao": [
      "IMPORT-JSON na UI"
    ],
    "integracao": {
      "status": "ok",
      "detalhe": "Regressao + fluxo completo + falhas/cobertura. Sem nuvem."
    },
    "qualidade_extracao": {
      "status": "aceitavel_com_ressalvas",
      "detalhe": "PDF teste alinhado; revisao humana obrigatoria."
    },
    "evidencias_verificadas": {
      "status": "ok_com_gate",
      "detalhe": "Apply bloqueado sem evidencia; browser Localizar referencia ok."
    },
    "desempenho": {
      "status": "limitado_hardware",
      "carregamento_s": 12.9,
      "analise_pdf_4pags_s": 91.2,
      "consumo_modelo": "nao_medido",
      "rss_llama_server_mb_observado": 2128.5
    }
  },
  "roteiro_teste_usuario": {
    "titulo": "Testar uma oportunidade com o seu edital (PDF/TXT com texto)",
    "passos": [
      "1. Abra INICIAR-OTTO.bat e va em http://127.0.0.1:5194",
      "2. Abra a oportunidade (ou cadastre manual) → detalhe",
      "3. Em Documentos locais, anexe o edital (PDF com texto ou TXT). Confira status_extracao=ok",
      "4. Em Analise local por IA: marque o documento → Analisar. Aguarde o job (pode demorar minutos)",
      "5. Em Confirmadas: leia valor + doc/versao/pagina/trecho → Aplicar apos revisao (ou Rejeitar)",
      "6. Nao confirmadas: nao aplique pela IA; se quiser o valor, edite a ficha/requisito no fluxo manual",
      "7. Em Verificacao de requisitos: Criar tarefa → confira a tarefa no checklist com a evidencia",
      "8. Use Localizar referencia / Abrir documento e confira o trecho na pagina",
      "9. Reinicie o app/API se quiser: dados devem permanecer; rejeitadas nao voltam como pendentes"
    ],
    "o_que_conferir": [
      "Sugestao so aplica se a evidencia estiver Confirmada",
      "Campo com origem usuario NUNCA e sobrescrito pela IA — edite a ficha manualmente se quiser mudar",
      "Cobertura do job lista o que foi processado (nao declare completo se houver Falha na parte)",
      "Sem OCR: PDF so-imagem nao entra na IA; analise pode demorar neste PC"
    ]
  },
  "caminho_etapas": [
    {
      "numero": 1,
      "nome": "Preparação e diagnóstico",
      "tipo": "preparacao",
      "o_que_sera_feito": "Entender o documento do LICITAR, inspecionar o OTTO que já existe e montar este painel para você acompanhar o trabalho.",
      "para_que_serve": "Evitar recomeçar do zero, marcar o que já existe e o que falta, e registrar decisões importantes antes de mexer no aplicativo.",
      "o_que_poderei_fazer": "Acompanhar o andamento neste painel. O aplicativo de oportunidades do OTTO continua como estava — diagnóstico pronto não significa LICITAR pronto.",
      "como_verificar": "Abrir este painel e conferir a data de atualização, o resumo no topo e o histórico. Ver também a seção “Como conferir”.",
      "situacao_atual": "Concluída e registrada. Teste interno do núcleo OTTO executado (13 ok). Aplicativo na tela e coleta de dados pela internet não foram revalidados nesta etapa."
    },
    {
      "numero": 2,
      "nome": "Lista de oportunidades no jeito LICITAR",
      "tipo": "concluida",
      "o_que_sera_feito": "Ajustar como a lista abre: se mostra vários setores ou só TI, e como as oportunidades são ordenadas — sem apagar o radar de TI que já existe.",
      "para_que_serve": "Você poder descobrir oportunidades sem cadastrar empresa e sem ser obrigado a escolher um nicho antes.",
      "o_que_poderei_fazer": "Abrir a lista sem perfil, ver todos os setores presentes nos dados coletados, ordenar por publicacao ou prazo de proposta, usar Radar TI como opcao e ler a cobertura real da coleta.",
      "como_verificar": "INICIAR-OTTO.bat → http://127.0.0.1:5194 → conferir banner de cobertura, modo Todos os setores, ordenacao, e opcao Radar TI.",
      "situacao_atual": "Concluida. Testes automaticos ok. Validacao visual no navegador nesta sessao: cobertura, lista geral, ordenacao por prazo, Radar TI."
    },
    {
      "numero": 3,
      "nome": "Interesse e acompanhamento pessoal",
      "tipo": "implementada_testada",
      "o_que_sera_feito": "Permitir salvar, analisar, rejeitar e registrar se você quer ou não seguir com cada oportunidade.",
      "para_que_serve": "Organizar o que você está avaliando, sem se inscrever automaticamente em nenhuma licitação.",
      "o_que_poderei_fazer": "Salvar para depois, marcar interesse em analisar, registrar decisao (prosseguir / nao prosseguir), anotar observacoes e justificativa; consultar nas vistas do menu. Tudo so no computador — sem perfil e sem participar de licitacao.",
      "como_verificar": "Escolher uma oportunidade de teste, usar os botões de ação e reabrir o app para ver se o status permaneceu.",
      "situacao_atual": "Concluida nesta sessao. Persistencia no SQLite local (tabela oportunidade_acompanhamento). Backup do banco antes da migracao: data/otto.db.bak-pre-l2-20261104. Validado no navegador e apos reinicio da API."
    },
    {
      "numero": 4,
      "nome": "Leitura e explicação dos documentos",
      "tipo": "implementada_parcial",
      "o_que_sera_feito": "Guardar editais/anexos e montar uma ficha clara do que está sendo contratado, com avisos do que ainda não deu para confirmar.",
      "para_que_serve": "Entender o edital em linguagem simples, sem inventar informação que não está no documento.",
      "o_que_poderei_fazer": "Anexar edital/anexos locais, ler texto por pagina, completar a ficha e organizar checklist de participacao — sem perfil e sem envio externo.",
      "como_verificar": "Anexar ou abrir um documento de exemplo e conferir a ficha; testar o caso em que falta anexo (deve aparecer como parcial).",
      "situacao_atual": "Documentos + ficha + checklist + evidencias. IA local FECHADA no escopo: regressao 43; fluxo ate tarefa/evidencia; cobertura parcial; IA down. Sem OCR/DOCX/download. Rede fisicamente off pendente."
    },
    {
      "numero": 5,
      "nome": "Checklist de preparação",
      "tipo": "implementada_testada",
      "o_que_sera_feito": "Lista de tarefas práticas (documentos, cotação, prazos) ligada à oportunidade.",
      "para_que_serve": "Não esquecer o que falta para decidir se participa.",
      "o_que_poderei_fazer": "Marcar tarefas como pendente, em andamento, concluída ou não aplicável, com observações.",
      "como_verificar": "Criar tarefas em uma oportunidade de teste e ver se os estados e o histórico se mantêm ao reabrir.",
      "situacao_atual": "Checklist com estados, rastreio, prazo conhecido e responsavel. Validado em testes."
    },
    {
      "numero": 6,
      "nome": "Cópia de segurança dos dados",
      "tipo": "implementada_parcial",
      "o_que_sera_feito": "Forma clara de guardar e recuperar os dados do aplicativo no seu computador.",
      "para_que_serve": "Não perder oportunidades salvas, análises e decisões se algo der errado.",
      "o_que_poderei_fazer": "Fazer backup e restaurar em um teste controlado.",
      "como_verificar": "Gerar backup, restaurar em cópia de teste e confirmar que os dados voltaram — nunca testar apagando a única cópia.",
      "situacao_atual": "Backup zip em data/backups/ e restauracao em data/restore-test-* (nao sobrescreve otto.db automaticamente). Validado."
    },
    {
      "numero": 7,
      "nome": "Custos, riscos e resultados",
      "tipo": "implementada_testada",
      "o_que_sera_feito": "Registrar custos estimados, acompanhar participação e resultados financeiros quando você informar os números.",
      "para_que_serve": "Ajudar a decidir com números, sem chamar de lucro o que ainda está incompleto.",
      "o_que_poderei_fazer": "Montar cenários, ver o que falta preencher e registrar o que aconteceu depois.",
      "como_verificar": "Cenário incompleto deve mostrar aviso de incompletude; não deve aparecer como lucro confirmado.",
      "situacao_atual": "Cenarios estimados + campos de custo; resultados realizados separados com comparacao e avisos. Sem chamar lucro liquido."
    }
  ],
  "entregas": [
    {
      "id": "E0",
      "nome": "Diagnóstico e painel de acompanhamento",
      "o_que_significa": "Foi feito um inventário do que o OTTO já faz e do que o LICITAR pede, e foi criado este painel para você acompanhar o trabalho em linguagem clara.",
      "o_que_muda_para_mim": "Você passa a ter um lugar fixo para ver o que foi feito, o que falta e o que precisa da sua decisão. O aplicativo de oportunidades em si não ganhou funções novas do LICITAR nesta entrega.",
      "situacao": "Concluída (preparação). Não confundir com “aplicativo LICITAR pronto”.",
      "como_conferir": "Abra este painel.html. Veja data/hora no topo, as quatro caixas de resumo e o histórico. O app de oportunidades (OTTO) não precisa estar aberto para ver este painel.",
      "o_que_falta": "Validar visualmente o painel no seu navegador. Smoke do aplicativo OTTO na tela e da coleta pela internet não foram refeitos nesta etapa.",
      "depende_de_decisao_minha": false,
      "tipo": "preparacao",
      "comprovacao": "Arquivos em docs/licitar-acompanhamento/; teste interno 13 passed; nenhum arquivo de negócio do radar alterado para “fechar” o LICITAR.",
      "testavel_na_interface_do_app": false
    },
    {
      "id": "E-OTTO-BASE",
      "nome": "Base já existente (OTTO) — o que o computador já tem",
      "o_que_significa": "Antes do LICITAR, já existia um radar local de licitações: busca dados públicos, guarda no computador, classifica TI, pontua e mostra uma tela de oportunidades.",
      "o_que_muda_para_mim": "Se o OTTO estiver instalado e ligado, você já pode ver oportunidades (hoje com foco em TI no Piauí). Isso é base aproveitável, não o produto LICITAR completo.",
      "situacao": "Funcionalidade existente no código. Parte testada por testes internos; abertura da tela e coleta real pela internet não foram revalidadas nesta etapa de acompanhamento.",
      "como_conferir": "Se quiser conferir o app antigo: use INSTALAR-OTTO.bat / INICIAR-OTTO.bat e abra http://127.0.0.1:5194 — isso é o radar OTTO, não este painel de acompanhamento.",
      "o_que_falta": "Transformar essa base no fluxo completo do LICITAR (interesse, documentos, checklist, custos etc.).",
      "depende_de_decisao_minha": false,
      "tipo": "existente_parcialmente_verificada",
      "comprovacao": "Código e documentação OTTO; pytest 13 passed em 2026-11-04.",
      "testavel_na_interface_do_app": true
    },
    {
      "id": "E1",
      "nome": "Ajustar a lista inicial de oportunidades",
      "o_que_significa": "Mudar o comportamento da lista para combinar com a regra do LICITAR: descobrir oportunidades sem perfil obrigatório e com ordenação clara.",
      "o_que_muda_para_mim": "Ao abrir o app, a lista geral mostra os setores que ja estao nos dados coletados, ordenado pela publicacao mais recente; voce pode mudar para prazo de proposta; Radar TI continua disponivel como opcao; um aviso explica que isso nao e o Brasil inteiro.",
      "situacao": "Concluida. Testes automaticos e validacao visual no navegador nesta sessao.",
      "como_conferir": "Abra o app em http://127.0.0.1:5194 apos INICIAR-OTTO.bat. No topo: aviso de cobertura. Seletor de modo (Todos os setores / Radar TI). Seletor de ordenacao (Publicacao mais recente / Prazo de proposta). Na lista geral nao deve ordenar nem ocultar por pontuacao TI.",
      "o_que_falta": "Coleta PNCP real e Task Scheduler nao foram rodados (fora do escopo).",
      "depende_de_decisao_minha": false,
      "tipo": "concluida",
      "comprovacao": "Browser: cobertura 878 regs; lista 200; prazo e Radar TI. pytest lista + typecheck.",
      "testavel_na_interface_do_app": true
    },
    {
      "id": "E2",
      "nome": "Interesse e decisão sobre cada oportunidade",
      "o_que_significa": "Salvar, marcar interesse, decidir prosseguir ou nao, com observacoes — tudo local, sem perfil e sem envio a plataformas.",
      "o_que_muda_para_mim": "Voce organiza o que quer olhar depois, o que quer analisar e a decisao local. Interesse nao e participacao; prosseguir nao e envio de proposta; salvar nao e analise concluida.",
      "situacao": "Concluida. Implementacao + testes + validacao no navegador e persistencia apos reinicio da API.",
      "como_conferir": "Abrir oportunidade → Salvar / Interesse / Decisao / textos → conferir no menu lateral → fechar e reabrir (ou reiniciar INICIAR-OTTO) e ver se permanece. Desfazer Salvar deve tirar da vista Salvas.",
      "o_que_falta": "Nada deste escopo. Proxima etapa (documentos/IA) nao iniciada.",
      "depende_de_decisao_minha": false,
      "tipo": "concluida",
      "comprovacao": "Migracao 001_oportunidade_acompanhamento; API PUT/GET; DetailDrawer; vistas; pytest test_acompanhamento + suite 20 passed; typecheck ok; browser: salvar/desfazer, interesse, nao_prosseguir, detalhe; contagens apos restart API.",
      "testavel_na_interface_do_app": true
    },
    {
      "id": "E3",
      "nome": "Análise dos documentos do edital",
      "o_que_significa": "Ficha explicativa a partir dos documentos, com avisos do que não foi possível confirmar.",
      "o_que_muda_para_mim": "Entender o edital sem precisar ser especialista; ver limitações com honestidade.",
      "situacao": "Parte manual concluida e comprovada (ficha, evidencias versao/pagina/trecho, revisao por versao). Parte automatica (IA) continua dependente de decisao.",
      "como_conferir": "Detalhe → anexar TXT/PDF → preencher campo/requisito com documento+trecho → criar tarefa → nova versao → ver sinal de revisao e evidencia antiga intacta.",
      "o_que_falta": "So a parte automatica (IA). OCR e DOCX tambem fora (decisoes separadas).",
      "depende_de_decisao_minha": true,
      "tipo": "implementada_parcial",
      "comprovacao": "Migracao 011; pytest 34; API E2E MANUAL-767CA28DEC1C; browser referencia v1 + sem pagina TXT; backup bak-pre-evidencias-011.",
      "testavel_na_interface_do_app": true
    },
    {
      "id": "E4",
      "nome": "Checklist de preparação",
      "o_que_significa": "Lista de tarefas práticas por oportunidade.",
      "o_que_muda_para_mim": "Saber o que falta fazer antes de participar.",
      "situacao": "Concluida no essencial (§10): estados, rastreio, prazo, responsavel.",
      "como_conferir": "Depois de pronta: criar e marcar tarefas; reabrir e conferir.",
      "o_que_falta": "Nada critico deste escopo. Evidencias de anexo opcional ja suportadas.",
      "depende_de_decisao_minha": false,
      "tipo": "concluida",
      "comprovacao": "Migracao 005; analise_store prazo/responsavel; DocsAnalisePanel; pytest.",
      "testavel_na_interface_do_app": true
    },
    {
      "id": "E5",
      "nome": "Backup e restauração",
      "o_que_significa": "Cópia de segurança e forma de recuperar dados.",
      "o_que_muda_para_mim": "Menos risco de perder o histórico guardado no computador.",
      "situacao": "Implementada: criar backup e restaurar em copia isolada. Sem botao de substituir o banco operacional.",
      "como_conferir": "No detalhe da oportunidade → Copia de seguranca → Criar backup → Restaurar em copia isolada. Conferir pasta data/restore-test-*.",
      "o_que_falta": "Fluxo guiado de substituicao do operacional (se desejado).",
      "depende_de_decisao_minha": true,
      "tipo": "implementada_testada",
      "comprovacao": "otto_core.backup + API /api/backup*; teste test_continuidade_l4.",
      "testavel_na_interface_do_app": false
    },
    {
      "id": "E6",
      "nome": "Custos e resultados",
      "o_que_significa": "Registrar números, ver cenários incompletos com aviso, acompanhar resultados reais.",
      "o_que_muda_para_mim": "Apoio financeiro à decisão, sem fingir certeza onde falta dado.",
      "situacao": "Estimado + realizado separados; comparacao com avisos; custos da §11 na UI.",
      "como_conferir": "Depois de pronta: cenário incompleto deve avisar; não chamar de lucro líquido confirmado.",
      "o_que_falta": "Prazos de desembolso/recebimento (se desejar) e regras tributarias (exigem decisao).",
      "depende_de_decisao_minha": false,
      "tipo": "implementada_testada",
      "comprovacao": "financeiro_store saldo_realizado; ContinuidadePanel; teste continuidade.",
      "testavel_na_interface_do_app": true
    },
    {
      "id": "E7",
      "nome": "Orgaos, categorias, indicadores e concorrencia (§12)",
      "o_que_significa": "Explorar dados locais por orgao, setor/categoria e regiao, com indicadores honestos e concorrencia so se houver participantes/resultados.",
      "o_que_muda_para_mim": "Menu Explorar: Orgaos (lista/detalhe/historico/anotacoes), Categorias, Regioes, Indicadores (base/periodo/limitacoes), Concorrencia (Dados insuficientes ate haver integracao).",
      "situacao": "Concluida com dados locais. Concorrencia sem analise inventada.",
      "como_conferir": "http://127.0.0.1:5194 → Explorar → Orgaos (abrir detalhe) → Categorias → Indicadores → Concorrencia (deve dizer Dados insuficientes).",
      "o_que_falta": "Integracao de resultados/participantes PNCP para concorrencia real; priorizacao avancada de orgaos com resultados do usuario.",
      "depende_de_decisao_minha": false,
      "tipo": "concluida",
      "comprovacao": "orgaos_store + migracao 004; API /api/orgaos|/visoes|/indicadores/explorar|/concorrencia; ExplorarPanel/ClassificacaoPanel; pytest test_orgaos_visoes; browser 352 orgaos; concorrencia Dados insuficientes.",
      "testavel_na_interface_do_app": true
    }
  ],
  "decisoes_para_mim": [
    {
      "id": "D-ia",
      "momento": "necessaria_para_proxima_entrega",
      "pergunta": "Como tratar análise automática por IA nos editais?",
      "por_que": "É a capacidade que mais reduz trabalho na ficha. Não inclui OCR, Word nem download.",
      "opcoes": [
        "Adiar IA (continuar ficha + extração de texto manual/PDF texto).",
        "IA só local no computador (privacidade alta; hardware/modelo).",
        "Serviço externo pago — só com autorização explícita por documento (privacidade: texto sai da máquina).",
        "Híbrido (local primeiro; externo sob demanda)."
      ],
      "recomendacao": "Adiar IA até ter 2–3 editais reais anexados para medir qualidade.",
      "motivo_recomendacao": "Evita custo e risco de privacidade cedo; ficha humana já funciona.",
      "o_que_fica_impedido": "Preenchimento automático inteligente da ficha. Não impede checklist, financeiro, órgãos, backup, perguntas §9.1.",
      "custo_potencial": "Local: tempo/CPU. Externo: assinatura + tokens. Híbrido: ambos.",
      "impacto_privacidade": "Externo envia trechos/documentos para fora. Local mantém no PC.",
      "dependencias": "Nenhuma outra decisão obrigatória; OCR/DOCX são caminhos separados."
    },
    {
      "id": "D-ocr",
      "momento": "pode_ficar_para_depois",
      "pergunta": "Ativar OCR para PDF que é só imagem?",
      "por_que": "Sem OCR, PDF escaneado gera aviso e texto vazio — não inventa exigências.",
      "opcoes": [
        "Manter só aviso (sem OCR).",
        "OCR local (ex.: Tesseract) — sem enviar arquivo.",
        "OCR em serviço externo — só com autorização."
      ],
      "recomendacao": "Manter aviso até precisar de um edital escaneado concreto.",
      "motivo_recomendacao": "A maioria dos editais PNCP vem com texto; OCR adiciona dependência.",
      "o_que_fica_impedido": "Leitura automática de PDFs imagem. Upload e ficha manual continuam.",
      "custo_potencial": "Local: instalação/manutenção. Externo: custo por página + envio.",
      "impacto_privacidade": "Externo envia páginas. Local permanece no PC.",
      "dependencias": "Independente de IA (pode OCR sem IA e vice-versa)."
    },
    {
      "id": "D-docx",
      "momento": "pode_ficar_para_depois",
      "pergunta": "Aceitar e extrair texto de arquivos Word (.docx)?",
      "por_que": "Alguns anexos vêm em Word; hoje o fluxo forte é PDF/TXT.",
      "opcoes": [
        "Não aceitar DOCX por enquanto (pedir PDF).",
        "Aceitar DOCX com extração local."
      ],
      "recomendacao": "Não aceitar ainda; pedir PDF quando possível.",
      "motivo_recomendacao": "Menos parsers; PDF cobre a maior parte.",
      "o_que_fica_impedido": "Anexos .docx. Não afeta PDF/TXT nem o restante do app.",
      "custo_potencial": "Baixo (biblioteca local).",
      "impacto_privacidade": "Processamento local se escolhido.",
      "dependencias": "Independente de IA/OCR."
    },
    {
      "id": "D-download",
      "momento": "pode_ficar_para_depois",
      "pergunta": "Baixar automaticamente anexos a partir do link da fonte?",
      "por_que": "Hoje você abre o link e anexa manualmente — evita rede/autorização de sites e malware.",
      "opcoes": [
        "Manter só upload manual + link.",
        "Download automático controlado (lista de URLs, com confirmação)."
      ],
      "recomendacao": "Manter upload manual nesta fase.",
      "motivo_recomendacao": "Menos superfície de ataque e de falha de rede; controle explícito do que entra no PC.",
      "o_que_fica_impedido": "Coleta automática de anexos. Não impede análise com arquivos que você anexar.",
      "custo_potencial": "Tempo de implementação + possíveis bloqueios de portais.",
      "impacto_privacidade": "Tráfego de rede; arquivos passam a residir em data/documentos.",
      "dependencias": "Independente de IA/OCR/DOCX."
    },
    {
      "id": "D-abrangencia",
      "momento": "pode_ficar_para_depois",
      "pergunta": "O foco geográfico inicial continua só no Piauí, ou já várias UFs?",
      "por_que": "Volume de dados e configuração da coleta.",
      "opcoes": [
        "Manter Piauí como padrão.",
        "Várias UFs configuráveis.",
        "Brasil inteiro."
      ],
      "recomendacao": "Manter Piauí como padrão.",
      "motivo_recomendacao": "Já funciona; amplia depois.",
      "o_que_fica_impedido": "Nada no desenvolvimento local atual (já há PI+SP no banco de teste).",
      "custo_potencial": "Mais disco/tempo de ingest.",
      "impacto_privacidade": "Nenhum extra relevante (dados públicos).",
      "dependencias": "—"
    }
  ],
  "decisoes_ja_respondidas": [
    {
      "pergunta": "O LICITAR comeca do zero ou aproveita o OTTO?",
      "resposta": "Aproveita o OTTO como base.",
      "quando": "2026-11-04"
    },
    {
      "pergunta": "Lista padrao: todos os setores ou so TI?",
      "resposta": "Todos os setores presentes nos dados coletados; Radar TI opcional.",
      "quando": "2026-11-04"
    },
    {
      "pergunta": "Ordenacao da lista?",
      "resposta": "Padrao: publicacao mais recente. Opcao: prazo de encerramento da proposta (mais proximo); sem prazo no final. Sem pontuacao TI na lista geral.",
      "quando": "2026-11-04"
    },
    {
      "id": "D-backup-ui",
      "quando": "2026-11-04T21:40:00-03:00",
      "pergunta": "Backup na tela?",
      "resposta": "Botão de backup + restauração em cópia isolada implementados (Configurações e detalhe). Restauração operacional permanece procedimento restrito, não bloqueio de desenvolvimento."
    }
  ],
  "como_conferir": [
    {
      "entrega": "Marca LICITAR",
      "onde_abrir": "http://127.0.0.1:5194",
      "o_que_fazer": "Ver aba e menu lateral: so LICITAR, sem subtítulo.",
      "resultado_esperado": "Sem OTTO/Radar/PI na marca; sem tagline.",
      "ainda_nao_disponivel": "—"
    },
    {
      "entrega": "Documentos e ficha",
      "onde_abrir": "http://127.0.0.1:5194 → detalhe da oportunidade",
      "o_que_fazer": "Adicionar PDF/TXT; Ver texto; editar campo da ficha; incluir item no checklist; reiniciar e conferir.",
      "resultado_esperado": "Arquivo versionado; PDF sem texto avisa OCR; ficha distingue coleta/usuario; aviso de que nao ha IA.",
      "ainda_nao_disponivel": "IA, OCR, DOCX, download automatico de URL."
    },
    {
      "entrega": "Painel",
      "onde_abrir": "docs\\licitar-acompanhamento\\painel.html",
      "o_que_fazer": "Ver sessao parada e L3 registrado.",
      "resultado_esperado": "Nenhuma tarefa em execucao.",
      "ainda_nao_disponivel": "Tempo real."
    }
  ],
  "evidencias_tecnicas": [
    {
      "quando": "2026-11-04T22:00:00-03:00",
      "o_que": "Manual + fluxo + itens/lotes",
      "comando": "python -m pytest packages/otto-core/tests/ -q; npm run typecheck --prefix app",
      "resultado": "28 passed; typecheck ok; mig 008",
      "nao_executado": [
        "commit/push/deploy",
        "IA/OCR/DOCX/download"
      ],
      "como_conferir": "App → Cadastro manual → criar → detalhe (origem manual, itens/lotes) → Fluxo Arquivadas apos Arquivar; lista geral nao deve listar arquivada."
    },
    {
      "quando": "2026-11-04T21:50:00-03:00",
      "o_que": "§9.2 + recontagem requisitos",
      "comando": "python -m pytest packages/otto-core/tests/ -q; npm run typecheck --prefix app",
      "resultado": "27 passed; typecheck ok",
      "nao_executado": [
        "commit/push/deploy"
      ],
      "nota_comando_tail": "Falha isolada: pipe com tail no PowerShell (comando inexistente). Nao indica falha da suite pytest."
    },
    {
      "quando": "2026-11-04T21:40:00-03:00",
      "o_que": "Auditoria + migração 006 + Configurações/orientação/caixa",
      "comando": "pytest packages/otto-core/tests/; npm run typecheck --prefix app",
      "resultado": "26 passed; typecheck ok; migrações até 006",
      "nao_executado": [
        "commit/push/deploy",
        "IA/OCR/DOCX/download",
        "restore operacional"
      ]
    },
    {
      "quando": "2026-11-05T00:35:00-03:00",
      "o_que": "Bloco §12 + checklist/financeiro realizado",
      "comando": "pytest packages/otto-core/tests/; npm run typecheck --prefix app; browser Explorar; API /api/orgaos /api/concorrencia",
      "resultado": "25 passed; typecheck ok; 352 orgaos; Concorrencia Dados insuficientes; migracao 005 aplicada",
      "nao_executado": [
        "IA/OCR/DOCX/download",
        "restore operacional",
        "commit/push/deploy",
        "ingest rede"
      ]
    }
  ],
  "historico_usuario": [
    {
      "quando": "2026-11-04T22:00:00-03:00",
      "o_que_mudou": "Cadastro manual, vistas de fluxo, itens/lotes; reclassificacao §12.2/§14/restore como previstas aguardando autorizacao.",
      "o_que_foi_concluido": "Migracao 008; pytest 28; typecheck; painel atualizado.",
      "problemas_encontrados": "—",
      "proxima_entrega_proposta": "Continuar gaps parciais autorizados ou decidir IA."
    },
    {
      "quando": "2026-11-04T21:50:00-03:00",
      "o_que_mudou": "Implementacao §9.2 requisitos_verificacao + painel; contagens README informadas ao usuario.",
      "o_que_foi_concluido": "pytest 27; typecheck; estados de verificacao sem declarar habilitacao.",
      "problemas_encontrados": "Comando com tail no PowerShell falhou (ferramenta); suíte valida: 26 depois 27 passed.",
      "proxima_entrega_proposta": "Cadastro manual ou vistas por fluxo; decisao IA se quiser ficha automatica."
    },
    {
      "quando": "2026-11-04T21:40:00-03:00",
      "o_que_mudou": "Auditoria README×código; bloqueios reclassificados; data caderno 05.11→04.11 (4); Continuou Configurações, §9.1, caixa, ações.",
      "o_que_foi_concluido": "Matriz requisitos_readme no painel; decisões IA/OCR/DOCX/download separadas; pytest 26.",
      "problemas_encontrados": "Concorrência real continua sem dados de participantes (esperado).",
      "proxima_entrega_proposta": "Decisão de IA para destravar ficha automática, ou §9.2/cadastro manual sem decisão."
    },
    {
      "quando": "2026-11-05T00:35:00-03:00",
      "o_que_mudou": "§12 orgaos/categorias/indicadores/concorrencia entregues; checklist prazo/responsavel; financeiro realizado vs estimado.",
      "o_que_foi_concluido": "Explorar no painel; concorrencia honesta; migracoes 004/005; pytest 25; typecheck; browser.",
      "problemas_encontrados": "Base PNCP local sem participantes — concorrencia marcada como Dados insuficientes (correto).",
      "proxima_entrega_proposta": "Parar em bloqueios reais (IA/OCR/DOCX/download; restore operacional; nova fonte de resultados)."
    },
    {
      "quando": "2026-11-05T00:20:00-03:00",
      "o_que_mudou": "Inicio do bloco README §12 (orgaos, categorias, historico).",
      "o_que_foi_concluido": "Registro de inicio.",
      "problemas_encontrados": "—",
      "proxima_entrega_proposta": "Concluir bloco e seguir requisitos seguros do README."
    },
    {
      "quando": "2026-11-05T00:15:00-03:00",
      "o_que_mudou": "Continuidade L4-cont concluida nesta sessao. Pergunta de IA registrada sem bloquear o restante.",
      "o_que_foi_concluido": "Rastreio, desatualizacao por versao, fluxo/resultados, financeiro estimado, backup/restore isolado. Sessao parada.",
      "problemas_encontrados": "—",
      "proxima_entrega_proposta": "Retomar com OCR/formatos/IA apos decisao, ou §12 orgaos — conforme prioridade."
    },
    {
      "quando": "2026-11-05T00:10:00-03:00",
      "o_que_mudou": "Retomada autorizada apos L3. Continuidade local iniciada.",
      "o_que_foi_concluido": "Registro de inicio.",
      "problemas_encontrados": "—",
      "proxima_entrega_proposta": "Concluir fatias desta continuidade."
    },
    {
      "quando": "2026-11-05T00:05:00-03:00",
      "o_que_mudou": "L3 concluido + tagline removida. Documentos locais, extracao, ficha e checklist. IA registrada como decisao separada (nao implementada).",
      "o_que_foi_concluido": "Criterios do lote atendidos sem fingir IA. Sessao encerrada.",
      "problemas_encontrados": "Upload exigiu python-multipart. Arquivo de teste edital-teste-l3.txt foi anexado a uma oportunidade real do banco local para validacao (nome deixa claro que e teste).",
      "proxima_entrega_proposta": "L4+ so com autorizacao."
    },
    {
      "quando": "2026-11-04T20:55:00-03:00",
      "o_que_mudou": "Inicio do lote L3 (documentos e analise). Tagline 'no seu computador' removida da marca.",
      "o_que_foi_concluido": "Registro de inicio.",
      "problemas_encontrados": "—",
      "proxima_entrega_proposta": "Concluir L3; nao iniciar L4 sem autorizacao."
    },
    {
      "quando": "2026-11-04T20:50:00-03:00",
      "o_que_mudou": "Nome visivel do aplicativo padronizado para LICITAR, sem OTTO/Radar/PI como marca. Titulo da aba, menu lateral e textos de identidade alinhados. Filtro TI e cobertura geografica (ex.: PI) preservados como funcao, nao como nome.",
      "o_que_foi_concluido": "Padronizacao de marca na UI + sync deste painel.",
      "problemas_encontrados": "—",
      "proxima_entrega_proposta": "Documentos e analise (L3) — nao iniciar sem autorizacao. Push do caderno scripts ainda pendente se desejar."
    },
    {
      "quando": "2026-11-04T20:45:00-03:00",
      "o_que_mudou": "Lote L2 concluido: validacao da lista no navegador; fluxo local de salvar/interesse/decisao/observacoes; detalhe da oportunidade; vistas de acompanhamento; migracao SQLite nao destrutiva com backup previo.",
      "o_que_foi_concluido": "Criterios do lote atendidos. Sessao do agente encerrada. Nenhum outro lote iniciado.",
      "problemas_encontrados": "Corrida ao trocar vistas de acompanhamento deixava lista vazia ate Atualizar — corrigida. Anexos do edital ainda nao sao baixados (so link da fonte).",
      "proxima_entrega_proposta": "Documentos e analise (L3) — nao iniciar sem autorizacao."
    },
    {
      "quando": "2026-11-04T20:16:12-03:00",
      "o_que_mudou": "Inicio do lote completo autorizado: validacao da lista + fluxo de interesse/decisao.",
      "o_que_foi_concluido": "Registro de inicio no painel.",
      "problemas_encontrados": "—",
      "proxima_entrega_proposta": "Concluir este lote; nao iniciar outro."
    },
    {
      "quando": "2026-11-04T20:13:57-03:00",
      "o_que_mudou": "Entrega da lista inicial implementada: API/defaults, ordenacao publicacao/prazo, modo geral vs Radar TI, banner de cobertura. Painel atualizado. Sessao do agente encerrada.",
      "o_que_foi_concluido": "Codigo da lista + pytest 17 + typecheck. Definicoes 1–5 atendidas no escopo da entrega.",
      "problemas_encontrados": "Tela nao foi aberta pelo assistente nesta sessao. Coleta real nao reexecutada. Se o banco local so tiver editais de TI/PI, a lista geral refletira so isso — cobertura informa o limite.",
      "proxima_entrega_proposta": "Interesse e decisao sobre cada oportunidade — nao iniciar sem autorizacao."
    },
    {
      "quando": "2026-11-04T20:09:19-03:00",
      "o_que_mudou": "Inicio autorizado da entrega Ajustar a lista inicial de oportunidades, com as cinco definicoes registradas. Painel marcado como em andamento antes das alteracoes no aplicativo.",
      "o_que_foi_concluido": "Nada desta entrega ainda — so o registro de inicio.",
      "problemas_encontrados": "—",
      "proxima_entrega_proposta": "Concluir a lista inicial (em andamento). Nao iniciar outras entregas."
    },
    {
      "quando": "2026-11-04T20:05:00-03:00",
      "o_que_mudou": "O painel foi reorganizado para linguagem comum: caminho numerado, quatro destaques no topo, entregas explicadas, decisões traduzidas e roteiros de conferência. Nada do aplicativo de oportunidades foi alterado.",
      "o_que_foi_concluido": "Ajuste do acompanhamento (esta etapa). Diagnóstico L0 já estava concluído.",
      "problemas_encontrados": "Nenhum defeito novo no app. Continua válido: tela do OTTO e coleta pela internet não foram retestadas nesta etapa.",
      "proxima_entrega_proposta": "Ajustar a lista inicial de oportunidades — somente após sua autorização e respostas sobre lista padrão e ordenação."
    },
    {
      "quando": "2026-11-04T19:57:00-03:00",
      "o_que_mudou": "Registrada a decisão de usar o OTTO como base; decisões reclassificadas (nem todas travam a próxima entrega).",
      "o_que_foi_concluido": "Registro da decisão de base.",
      "problemas_encontrados": "O texto antigo do README do LICITAR ainda fala do OTTO como integração futura — ficou desatualizado; o README não foi editado.",
      "proxima_entrega_proposta": "Lista inicial (não autorizada)."
    },
    {
      "quando": "2026-11-04T19:50:00-03:00",
      "o_que_mudou": "Primeiro diagnóstico e criação deste acompanhamento.",
      "o_que_foi_concluido": "Diagnóstico + pasta do painel. Teste interno 13 passed.",
      "problemas_encontrados": "Nenhuma falha nos testes internos rodados. Vários itens do LICITAR ainda inexistentes no app.",
      "proxima_entrega_proposta": "Lista inicial (não autorizada)."
    }
  ],
  "tecnico": {
    "nota": "Seção para quem for mexer no código. O resumo acima não depende desta seção.",
    "readme_licitar": "README.txt",
    "readme_otto": "README.md",
    "fonte_canonica": "dados.json",
    "espelho_painel": "dados.js",
    "sync": "python sync-dados.py",
    "lote_interno_atual": "auditoria-readme + fatias independentes",
    "tarefas_estado": {
      "em_andamento": 0,
      "pendente": 0,
      "bloqueada": 0,
      "aguardando_decisao": 1,
      "concluida": 9
    },
    "ids_decisoes_abertas_bloqueiam_l1": [],
    "ids_decisoes_resolvidas": [
      "D-base-otto",
      "D-stack"
    ],
    "mapa_lotes": [
      {
        "id": "L0",
        "nome_usuario": "Diagnóstico e painel",
        "estado": "concluida"
      },
      {
        "id": "L1",
        "nome_usuario": "Ajustar lista inicial",
        "estado": "concluida"
      },
      {
        "id": "L2",
        "nome_usuario": "Interesse e decisão",
        "estado": "concluida"
      },
      {
        "id": "L3",
        "nome_usuario": "Documentos e análise",
        "estado": "concluida_parcial_sem_ia"
      },
      {
        "id": "L4",
        "nome_usuario": "Continuidade (rastreio/financeiro/backup)",
        "estado": "concluida_parcial_continuidade"
      },
      {
        "id": "L5",
        "nome_usuario": "Backup",
        "estado": "proposta"
      },
      {
        "id": "L6",
        "nome_usuario": "Custos e resultados",
        "estado": "proposta"
      },
      {
        "id": "L-ORG",
        "nome_usuario": "Orgaos/categorias/concorrencia (§12)",
        "estado": "concluida"
      },
      {
        "id": "L-CHK-FIN",
        "nome_usuario": "Checklist prazo/responsavel + financeiro realizado",
        "estado": "concluida_parcial"
      }
    ],
    "arquivos_alterados_e1": [
      "packages/otto-core/src/otto_core/db.py",
      "packages/otto-core/tests/test_lista_ordenacao.py",
      "api/src/otto_api/main.py",
      "app/src/api.ts",
      "app/src/App.tsx",
      "app/src/types.ts",
      "app/src/utils.ts",
      "app/src/components/TopBar.tsx",
      "app/src/components/CoverageBanner.tsx",
      "app/src/components/OportunidadesTable.tsx",
      "app/src/components/PriorityCards.tsx",
      "app/src/styles.css",
      "docs/licitar-acompanhamento/*"
    ],
    "arquivos_alterados_e2": [
      "packages/otto-core/src/otto_core/migrations.py",
      "packages/otto-core/src/otto_core/models.py",
      "packages/otto-core/src/otto_core/db.py",
      "packages/otto-core/tests/test_acompanhamento.py",
      "api/src/otto_api/main.py",
      "app/src/App.tsx",
      "app/src/api.ts",
      "app/src/types.ts",
      "app/src/components/DetailDrawer.tsx",
      "app/src/components/Sidebar.tsx",
      "app/src/components/AcompanhamentoPanel.tsx",
      "app/src/components/KpiStrip.tsx",
      "data/otto.db.bak-pre-l2-20261104",
      "docs/licitar-acompanhamento/*"
    ],
    "arquivos_marca_licitar": [
      "app/index.html",
      "app/src/components/Sidebar.tsx",
      "app/src/App.tsx",
      "app/src/components/PriorityCards.tsx",
      "app/src/components/AlertsBanner.tsx",
      "app/src/styles.css",
      "docs/licitar-acompanhamento/*"
    ],
    "data_efetiva_execucao": "2026-11-04"
  },
  "validacoes_executadas": [
    {
      "quando": "2026-11-04T22:00:00-03:00",
      "o_que": "Manual + fluxo + itens/lotes",
      "comando": "python -m pytest packages/otto-core/tests/ -q; npm run typecheck --prefix app",
      "resultado": "28 passed; typecheck ok; mig 008",
      "nao_executado": [
        "commit/push/deploy",
        "IA/OCR/DOCX/download"
      ],
      "como_conferir": "App → Cadastro manual → criar → detalhe (origem manual, itens/lotes) → Fluxo Arquivadas apos Arquivar; lista geral nao deve listar arquivada."
    },
    {
      "quando": "2026-11-04T21:50:00-03:00",
      "o_que": "§9.2 + recontagem requisitos",
      "comando": "python -m pytest packages/otto-core/tests/ -q; npm run typecheck --prefix app",
      "resultado": "27 passed; typecheck ok",
      "nao_executado": [
        "commit/push/deploy"
      ],
      "nota_comando_tail": "Falha isolada: pipe com tail no PowerShell (comando inexistente). Nao indica falha da suite pytest."
    },
    {
      "quando": "2026-11-04T21:40:00-03:00",
      "o_que": "Auditoria + migração 006 + Configurações/orientação/caixa",
      "comando": "pytest packages/otto-core/tests/; npm run typecheck --prefix app",
      "resultado": "26 passed; typecheck ok; migrações até 006",
      "nao_executado": [
        "commit/push/deploy",
        "IA/OCR/DOCX/download",
        "restore operacional"
      ]
    },
    {
      "quando": "2026-11-05T00:35:00-03:00",
      "o_que": "Bloco §12 + checklist/financeiro realizado",
      "comando": "pytest packages/otto-core/tests/; npm run typecheck --prefix app; browser Explorar; API /api/orgaos /api/concorrencia",
      "resultado": "25 passed; typecheck ok; 352 orgaos; Concorrencia Dados insuficientes; migracao 005 aplicada",
      "nao_executado": [
        "IA/OCR/DOCX/download",
        "restore operacional",
        "commit/push/deploy",
        "ingest rede"
      ]
    }
  ],
  "requisitos_readme": [
    {
      "id": "§3",
      "titulo": "Descoberta sem perfil",
      "status": "implementado_validado",
      "evidencia": "Lista geral sem login; Sidebar sem perfil obrigatório; Radar TI opcional; testes lista.",
      "falta": "—",
      "bloqueio": "Nenhum"
    },
    {
      "id": "§3.5",
      "titulo": "Perfil opcional",
      "status": "implementado_validado",
      "evidencia": "ConfiguracoesPanel: nome/CNPJ/contato em localStorage; aviso de que nao filtra lista; browser.",
      "falta": "Persistencia multi-dispositivo / multiuser (se desejado).",
      "bloqueio": "Multiuser = decisao; perfil local feito"
    },
    {
      "id": "§5.1",
      "titulo": "Estados do fluxo do usuário",
      "status": "implementado_validado",
      "evidencia": "Menu Fluxo com salva, em_analise, aguardando_informacoes, em_preparacao, participacao_registrada, em_acompanhamento, encerrada, arquivada; contagens; API /api/fluxo; browser.",
      "falta": "—",
      "bloqueio": "Nenhum"
    },
    {
      "id": "§5.4",
      "titulo": "Ações independentes",
      "status": "implementado_validado",
      "evidencia": "Salvar/interesse/analisar/nao interesse/arquivar; arquivadas fora da lista geral; salvar→estado_fluxo=salva (sem rebaixar analise+).",
      "falta": "—",
      "bloqueio": "Nenhum"
    },
    {
      "id": "§6.1",
      "titulo": "Entrada de dados / cadastro manual",
      "status": "implementado_validado",
      "evidencia": "Cadastro unitario manual (POST /api/oportunidades/manual + CadastroManualPanel); origem_registro=manual vs pncp. Import JSON removido da UI nesta correcao.",
      "falta": "— (cadastro unitario). Import JSON: ver item IMPORT-JSON (fora do escopo autorizado).",
      "bloqueio": "Nenhum para cadastro unitario"
    },
    {
      "id": "§6.3",
      "titulo": "Ordenação objetiva",
      "status": "implementado_validado",
      "evidencia": "publicacao/prazo; modo geral sem score; testes.",
      "falta": "Ordenar por documentos disponiveis (opcional).",
      "bloqueio": "Nenhum"
    },
    {
      "id": "§6.4",
      "titulo": "Deduplicação",
      "status": "implementado_validado",
      "evidencia": "PK numero_controle_pncp + upsert.",
      "falta": "Multi-fonte.",
      "bloqueio": "Decisão de outras fontes"
    },
    {
      "id": "§7",
      "titulo": "Cartão / valores / datas",
      "status": "implementado_validado",
      "evidencia": "Lista: categoria/docs/origem/esclarecimento/impugnacao; prazos manuais no detalhe; migração 009.",
      "falta": "Preenchimento automatico desses prazos a partir do edital.",
      "bloqueio": "Extracao automatica → decisao IA/OCR (campos manuais feitos)"
    },
    {
      "id": "§8.1-8.3-manual",
      "titulo": "Ficha documental — parte manual",
      "status": "implementado_validado",
      "evidencia": "Ficha revisavel com naturezas; evidencia em campo e requisito (documento_id/versao + pagina opcional + trecho); TXT sem pagina; localizar/abrir referencia; geracao de requisitos a partir da ficha; itens/lotes. Comprovado em MANUAL-767CA28DEC1C (API+navegador) e pytest evidencias.",
      "falta": "—",
      "bloqueio": "Nenhum (parte manual concluida; ausencia de IA nao torna esta parte pendente)"
    },
    {
      "id": "§8.1-8.3-automatico",
      "titulo": "Ficha documental — parte automatica (IA local)",
      "status": "implementado_validado_com_ressalvas",
      "evidencia": "Fechamento: pytest 43; fluxo e2e-ia-fluxo-completo (aplicar/rejeitar/tarefa/evidencia/reinicio); browser Localizar referencia; cobertura parcial + lista Processados; IA down falha job. PDF MANUAL-IA-PDF-E2E-05NOV-B. Gate de evidencia ativo.",
      "falta": "Rede fisicamente off pendente. OCR/DOCX/download fora do escopo.",
      "bloqueio": "Nenhum no escopo autorizado; desempenho limitado pelo hardware"
    },
    {
      "id": "§8.4",
      "titulo": "OCR / digitalizados",
      "status": "implementado_validado_com_ressalvas",
      "evidencia": "OCR local Tesseract+pypdfium2; upload tenta OCR; Reprocessar OCR; docs/OCR.md; pytest test_ocr_local. Motor depende do Tesseract instalado no SO.",
      "falta": "Instalacao do Tesseract (por) no PC do operador para ocr_disponivel=true.",
      "bloqueio": "Nenhum de produto; hardware/motor local"
    },
    {
      "id": "§8.5",
      "titulo": "Versões / desatualização",
      "status": "implementado_validado",
      "evidencia": "Nova versao: ficha desatualizada + requisitos com evidencia na versao antiga marcados precisa_revisao; vinculo antigo preservado; confirmar revisao marca revisao_origem=usuario (nunca automatico). Browser + pytest 34.",
      "falta": "Snapshot completo de análise (melhoria opcional — nao e requisito obrigatorio deste bloco).",
      "bloqueio": "Nenhum"
    },
    {
      "id": "§9.1",
      "titulo": "Perguntas progressivas",
      "status": "implementado_validado",
      "evidencia": "OrientacaoPanel; respostas Nao/Preciso verificar geram requisito §9.2 (origem orientacao:<id>); pytest.",
      "falta": "—",
      "bloqueio": "Nenhum"
    },
    {
      "id": "§9.2",
      "titulo": "Verificação por requisito",
      "status": "implementado_validado",
      "evidencia": "RequisitosPanel: estado; evidencia com versao/pagina opcional/trecho; Localizar referencia; Criar tarefa; revisao por nova versao; pytest + browser MANUAL-767CA28DEC1C.",
      "falta": "—",
      "bloqueio": "Nenhum"
    },
    {
      "id": "§10",
      "titulo": "Checklist preparação",
      "status": "implementado_validado",
      "evidencia": "Checklist com estados, prazo, responsavel, categoria; tarefa gerada a partir do requisito com evidencia copiada; testes + browser.",
      "falta": "—",
      "bloqueio": "Nenhum"
    },
    {
      "id": "§11",
      "titulo": "Financeiro",
      "status": "implementado_validado",
      "evidencia": "Cenarios estimados vs realizados separados; necessidade de caixa; prazos; tributos como valor informado pelo usuario (sem regimes/aliquotas inventados); linha do tempo pelos prazos.",
      "falta": "—",
      "bloqueio": "Nenhum no escopo aprovado (tributos fixos nao sao criterio de aceite)"
    },
    {
      "id": "§12.1",
      "titulo": "Órgãos",
      "status": "implementado_validado",
      "evidencia": "Lista/detalhe/anotacoes + normalizacao CNPJ (mascara/digitos; orgaoEntidade/unidadeOrgao); merge nome→CNPJ no recorte; alias de anotacao; pytest test_orgaos_normalizacao.",
      "falta": "— (fuzzy de nomes distintos continua fora de escopo de proposito).",
      "bloqueio": "Nenhum"
    },
    {
      "id": "§12.2",
      "titulo": "Priorização de órgãos",
      "status": "implementado_validado",
      "evidencia": "calcular_prioridade_orgao + list_orgaos ordena por score; motivos_prioridade na lista/detalhe; sinais: frequencia, categorias, valor/periodo, prazos abertos, interesse/salva, fluxo/resultado do usuario, anotacao. Sem reputacao. pytest test_orgaos_visoes; UI Explorar Órgãos.",
      "falta": "—",
      "bloqueio": "Nenhum"
    },
    {
      "id": "§12.3",
      "titulo": "Nichos/categorias",
      "status": "implementado_parcial",
      "evidencia": "Classificacao multissetorial da oportunidade; itens/lotes com edicao manual de setor/categoria; sugestao deterministica identificada (nao aplica sozinha). Migração 010 marca autoaplicacoes anteriores.",
      "falta": "Melhoria opcional (nao obrigatoria): classificacao manual em lote/itens legados em massa pela UI (hoje item a item).",
      "bloqueio": "Nenhum — opcional, nao bloqueia fluxo documental"
    },
    {
      "id": "§12.4",
      "titulo": "Concorrência (análise real)",
      "status": "implementado_parcial",
      "evidencia": "Stub honesto Dados insuficientes.",
      "falta": "Criterio restante: participantes/vencedores/valores de disputa persistidos da fonte.",
      "bloqueio": "So bloqueia analise real de concorrencia"
    },
    {
      "id": "§13",
      "titulo": "Resultados",
      "status": "implementado_validado",
      "evidencia": "GET /api/resultados + menu Resultados; tempo_preparacao_horas e custo_preparacao no fluxo; browser.",
      "falta": "—",
      "bloqueio": "Nenhum"
    },
    {
      "id": "§14",
      "titulo": "Especializações Saúde/Viagens",
      "status": "implementado_validado",
      "evidencia": "otto_core.especializacao (subtipos/condicoes so com sinal no objeto); GET /especializacao; EspecializacaoPanel no detalhe; docs/NICHOS.md; pytest test_especializacao. Sem LX Saude / app viagens.",
      "falta": "— (leitura de anexos PDF/DOCX para requisitos setoriais continua fora deste lote).",
      "bloqueio": "Nenhum para o escopo autorizado"
    },
    {
      "id": "§15",
      "titulo": "Execução local / persistência",
      "status": "implementado_validado",
      "evidencia": "SQLite + data/; backup zip; restore isolado; docs/INSTALACAO.md + INSTALAR-OTTO.bat corrigido; bind Vite 127.0.0.1.",
      "falta": "—",
      "bloqueio": "Nenhum"
    },
    {
      "id": "§15-restore-op",
      "titulo": "Restauração operacional do banco",
      "status": "implementado_validado",
      "evidencia": "restaurar_operacional + POST /api/backup/restaurar-operacional; confirmacao SUBSTITUIR-BANCO-OPERACIONAL; backup de seguranca automatico; UI Configuracoes; pytest test_backup_restore_op.",
      "falta": "—",
      "bloqueio": "Nenhum"
    },
    {
      "id": "§16",
      "titulo": "IA",
      "status": "implementado_validado_com_ressalvas",
      "evidencia": "Mecanismo local: Ollama loopback + qwen2.5:3b. Sem nuvem. Status UI 'modelo local disponivel'. Inferencia real comprovada (nao mock).",
      "falta": "Melhoria opcional de citacoes em campos; modelos maiores exigem hardware melhor (nao trocado sem nova autorizacao).",
      "bloqueio": "Nenhum para o escopo autorizado"
    },
    {
      "id": "§18-config",
      "titulo": "Tela Configurações",
      "status": "implementado_validado",
      "evidencia": "Config: paths, capacidades, backup/restore isolado, perfil, preferencias, auditoria, aprendizado, disparo coleta PNCP (POST /api/ingest + poll status). pytest test_ingest_store; typecheck.",
      "falta": "—",
      "bloqueio": "Nenhum"
    },
    {
      "id": "§19",
      "titulo": "Segurança/integrações",
      "status": "implementado_validado",
      "evidencia": "Tabela auditoria_acoes + GET /api/auditoria + lista em Configuracoes; registro em acompanhamento/fluxo/import/prazos.",
      "falta": "Identidade de usuario de rede (multiuser).",
      "bloqueio": "Multiuser = decisao; auditoria local feita"
    },
    {
      "id": "§21",
      "titulo": "Aceite essenciais MVP",
      "status": "implementado_validado",
      "evidencia": "MVP essenciais + ErrorBanner com aviso offline/API local; cadastro manual e persistencia.",
      "falta": "—",
      "bloqueio": "Nenhum"
    },
    {
      "id": "DOCX",
      "titulo": "Arquivos Word/DOCX",
      "status": "implementado_validado",
      "evidencia": "Upload .docx; python-docx (paragrafos+tabelas); pagina opcional; .doc rejeitado; docs/DOCX.md; pytest test_docx_extracao.",
      "falta": "— (imagens dentro do DOCX sem OCR nesta fatia)",
      "bloqueio": "Nenhum"
    },
    {
      "id": "DOWNLOAD",
      "titulo": "Download automático de anexos",
      "status": "implementado_validado",
      "evidencia": "otto_core.download_anexos_store; GET/POST anexos-remotos; whitelist pncp.gov.br; PDF/DOCX/TXT ≤25MB; origem download_pncp; UI Buscar/Baixar; docs/DOWNLOAD-ANEXOS.md; pytest test_download_anexos.",
      "falta": "— (ZIP e outros formatos: listados, extração manual)",
      "bloqueio": "Nenhum"
    },
    {
      "id": "§4/§17-itens",
      "titulo": "Itens e lotes estruturados",
      "status": "implementado_validado",
      "evidencia": "Tabelas oportunidade_lotes/itens; API; ItensLotesPanel; aviso disputa separada; pytest; browser.",
      "falta": "Importacao automatica do edital (capacidade separada → decisao IA/OCR).",
      "bloqueio": "Preenchimento automatico → decisao IA/OCR; cadastro manual estruturado feito"
    },
    {
      "id": "IMPORT-JSON",
      "titulo": "Importacao JSON em lote (manual)",
      "status": "implementada_fora_escopo_aguardando_avaliacao",
      "evidencia": "Codigo/API POST /api/oportunidades/manual/import permanece. UI removida. Registro MANUAL-595A3D764039 preservado. Auditoria import_manual_json.",
      "falta": "Avaliacao/autorizacao para expor de novo na interface (ou decidir o destino da API).",
      "bloqueio": "Fora do escopo do bloco autorizado; nao e requisito aprovado"
    }
  ],
  "evidencias": [],
  "historico_sessoes": [
    {
      "quando": "2026-11-06T01:35:00-03:00",
      "o_que_mudou": "Download PNCP autorizado: listar/baixar anexos (whitelist pncp.gov.br); PDF/DOCX/TXT; UI Buscar/Baixar; docs/DOWNLOAD-ANEXOS.md.",
      "o_que_foi_concluido": "Fatia download seletivo fechada. ZIP permanece manual.",
      "comprovacao": "pytest test_download_anexos; typecheck; painel DOWNLOAD.",
      "estado": "encerrada"
    },
    {
      "quando": "2026-11-06T01:25:00-03:00",
      "o_que_mudou": "DOCX autorizado: upload .docx; extracao python-docx; pagina opcional na evidencia; docs/DOCX.md; .doc legado rejeitado.",
      "o_que_foi_concluido": "Formato Word moderno no fluxo documental local.",
      "comprovacao": "pytest test_docx_extracao; typecheck; painel DOCX.",
      "estado": "encerrada"
    },
    {
      "quando": "2026-11-06T01:20:00-03:00",
      "o_que_mudou": "OCR local autorizado: otto_core.ocr_local; PDF sem texto → Tesseract; UI Reprocessar OCR; POST /documentos/{id}/ocr; docs/OCR.md.",
      "o_que_foi_concluido": "§8.4 OCR no produto; motor real exige Tesseract no Windows.",
      "comprovacao": "pytest test_ocr_local; typecheck; painel §8.4.",
      "estado": "encerrada"
    },
    {
      "quando": "2026-11-06T01:10:00-03:00",
      "o_que_mudou": "Doc instalacao consolidada (docs/INSTALACAO.md); INSTALAR-OTTO.bat corrigido; Vite host 127.0.0.1 (link app); README/TECH_STACK apontam o guia.",
      "o_que_foi_concluido": "§15 doc instalacao LICITAR fechada. Fatias pequenas sem autorizacao esgotadas.",
      "comprovacao": "docs/INSTALACAO.md; curl/app 127.0.0.1:5194; painel atualizado.",
      "estado": "encerrada"
    },
    {
      "quando": "2026-11-06T01:00:00-03:00",
      "o_que_mudou": "§12.1 orgaos: CNPJ normalizado; fontes amplas no JSON; merge mesma razao social→CNPJ; anotacoes por alias; sem fuzzy.",
      "o_que_foi_concluido": "Criterio restante de entidade orgao ampliada fechado.",
      "comprovacao": "pytest test_orgaos_normalizacao + test_orgaos_visoes; typecheck; painel §12.1.",
      "estado": "encerrada"
    },
    {
      "quando": "2026-11-06T00:55:00-03:00",
      "o_que_mudou": "Coleta PNCP pela UI (Configuracoes): otto_core.ingest_store; GET/POST /api/ingest; um job por vez; CLI otto ingest reusa o core; auditoria ingest_disparado_ui.",
      "o_que_foi_concluido": "Criterio restante de §18-config (disparo ingest) fechado. Testes humanos adiados.",
      "comprovacao": "pytest test_ingest_store 4; suíte otto-core; typecheck; ARCHITECTURE.md.",
      "estado": "encerrada"
    },
    {
      "quando": "2026-11-06T00:45:00-03:00",
      "o_que_mudou": "Autorizado: historico passa a influenciar o prompt da proxima analise IA local (bloco APRENDIZADO_LOCAL; ≥3 decisoes; preferir/evitar). Sem fine-tune/nuvem. UI Configuracoes + nota na cobertura do job.",
      "o_que_foi_concluido": "Salto de 'entender' para 'ajustar foco' via prompt local, mantendo evidencia e campo usuario.",
      "comprovacao": "pytest test_aprendizado_historico; typecheck; docs/IA-LOCAL.md; injecao em ia_analise_store._executar_job.",
      "estado": "encerrada"
    },
    {
      "quando": "2026-11-06T00:25:00-03:00",
      "o_que_mudou": "Aprendizado do historico (MVP): agrega auditoria + sugestoes IA + resultados em Configuracoes; API /api/aprendizado; auditoria em apply/rejeitar IA. Sem alterar modelo/nuvem.",
      "o_que_foi_concluido": "Usuario consegue entender padroes das proprias acoes neste PC.",
      "comprovacao": "pytest test_aprendizado_historico 2; typecheck; painel atualizado.",
      "estado": "encerrada"
    },
    {
      "quando": "2026-11-05T06:30:00-03:00",
      "o_que_mudou": "Correcao: removeu sobrescrita de campo usuario via IA (caixa forcar). Preserve sempre; edicao so manual. Painel com iniciar/encerrar, limitacoes e IDs de teste.",
      "o_que_foi_concluido": "Comportamento alinhado a preservacao de origem usuario. Pronto para validacao humana.",
      "comprovacao": "pytest test_job_falha_sem_runtime_e_preserva_usuario (forcar=True tambem bloqueia); UI sem checkbox; aviso API atualizado.",
      "estado": "encerrada"
    },
    {
      "quando": "2026-11-05T05:15:00-03:00",
      "o_que_mudou": "Fechamento IA local: regressao pytest 43; fluxo analise→preparacao (API+browser); cobertura parcial com Processados; IA indisponivel; painel com funciona/limitacoes/pendentes/autorizacao + roteiro usuario.",
      "o_que_foi_concluido": "Escopo autorizado da IA documental local encerrado. Rede fisicamente off continua pendente. Sem OCR/DOCX/download/commit.",
      "comprovacao": "data/e2e-ia-fluxo-completo-resultado.json; pytest 43; typecheck; browser MANUAL-IA-PDF-E2E-05NOV-B.",
      "estado": "encerrada"
    },
    {
      "quando": "2026-11-05T04:45:00-03:00",
      "o_que_mudou": "Corrigiu lacuna de evidencias: apply so com trecho confirmado; UI Nao confirmadas; localiza citacao no doc sem inventar; PDF multipagina E2E; metricas load vs analise; memoria modelo=nao_medido (RSS llama-server ~2,1GB observado).",
      "o_que_foi_concluido": "Validacao IA com gate de evidencia + PDF representativo. Rede fisicamente off permanece pendente.",
      "comprovacao": "data/e2e-ia-pdf-evidencias-resultado.json; pytest test_ia_local_analise 8; typecheck app; docs/IA-LOCAL.md.",
      "estado": "encerrada"
    },
    {
      "quando": "2026-11-05T00:30:00-03:00",
      "o_que_mudou": "Instalou Ollama 0.40.14 + pull qwen2.5:3b (~1,9 GB, ~511s) em D:\\…\\ia-models; OLLAMA_HOST=127.0.0.1. Teste E2E real MANUAL-FBFF06D94C0E (~109s); aplicar/rejeitar; preservacao usuario; browser OK. Avaliacao ACEITAVEL_COM_RESSALVAS.",
      "o_que_foi_concluido": "Bloco autorizado IA local com inferencia real comprovada (sem mock). OCR/DOCX/download continuam fora.",
      "comprovacao": "data/e2e-ia-real-resultado.json; docs/IA-LOCAL.md; UI detalhe MANUAL-FBFF06D94C0E (Analise local disponivel + sugestoes pendentes).",
      "estado": "encerrada"
    },
    {
      "quando": "2026-11-04T23:15:00-03:00",
      "o_que_mudou": "IA local: integracao no fluxo documental (migracao 012, API, UI). Sem download ainda. docs/IA-LOCAL.md com hardware e pedido de autorizacao Ollama+qwen2.5:3b.",
      "o_que_foi_concluido": "Codigo e testes sem runtime; fluxo manual preservado. Inferencia real pendente de instalacao.",
      "comprovacao": "Backup bak-pre-ia-local-012; pytest ia_local; UI painel Analise local; sem mock de modelo.",
      "estado": "encerrada"
    },
    {
      "quando": "2026-11-04T23:00:00-03:00",
      "o_que_mudou": "Fechou evidencias documentais: migracao 011 (pagina/revisao); vinculo a versao; revisao por nova versao sem apagar; UI localizar; §8.1–8.3 manual vs automatico no painel.",
      "o_que_foi_concluido": "Fluxo documental autorizado comprovado ponta a ponta (API+navegador+pytest 34).",
      "comprovacao": "Backup otto.db.bak-pre-evidencias-011-20261104-224723; MANUAL-767CA28DEC1C; typecheck ok; aviso backup/localStorage intacto; IMPORT-JSON continua fora da UI.",
      "estado": "encerrada"
    },
    {
      "quando": "2026-11-04T22:45:00-03:00",
      "o_que_mudou": "Correcao de desvios sem apagar dados: UI JSON fora; classificacao item manual+sugestao; §11; aviso backup; evidencias validacao.",
      "o_que_foi_concluido": "Desvios pedidos corrigidos e registrados no painel.",
      "comprovacao": "Manuais preservados; migração 010; UI sem import; painel status IMPORT-JSON.",
      "estado": "encerrada"
    },
    {
      "quando": "2026-11-04T22:35:00-03:00",
      "o_que_mudou": "Migração 009 + fechamento de parciais: import JSON, prazos manuais, Resultados, §9, auditoria, preferencias, UX offline, setor item, timeline caixa.",
      "o_que_foi_concluido": "Varios requisitos passaram a implementado_validado; faltas precisas nos restantes.",
      "comprovacao": "pytest 32; typecheck; API import/auditoria/resultados; browser lista+Resultados+Config.",
      "estado": "encerrada"
    },
    {
      "quando": "2026-11-04T22:15:00-03:00",
      "o_que_mudou": "Fechou gaps: atalhos fluxo, sync salvar→salva, cartao categoria/docs/origem, perfil opcional. Atualizou faltas precisas dos parciais.",
      "o_que_foi_concluido": "§5.1 §5.4 §3.5 §4/§17-itens validados; bloco manual/fluxo/itens mantido.",
      "comprovacao": "pytest 30; typecheck; API smoke sync; browser lista+Fluxo Salvas+Config perfil.",
      "estado": "encerrada"
    }
  ],
  "validacao_entrega": {
    "atualizado_em": "2026-11-05T04:45:00-03:00",
    "aviso": "Distinguir: integracao OK ≠ qualidade perfeita. Consumo_modelo=nao_medido. Rede fisicamente off = pendente (endpoint local nao substitui esse teste).",
    "itens": [
      {
        "fluxo": "Gate de evidencia (nao aplicar sem trecho)",
        "evidencia": "aplicar_sugestao levanta ValueError sem referencia_confirmada; UI desabilita Aplicar e rotula Nao confirmada. pytest test_bloquear_aplicar_sem_evidencia.",
        "como_conferir": "Sugestao sem trecho → botao Aplicar desabilitado; mensagem aponta fluxo manual."
      },
      {
        "fluxo": "PDF multipagina representativo",
        "evidencia": "MANUAL-IA-PDF-E2E-05NOV-B / edital-teste-ia-multipagina.pdf (4 pags); 5 sugestoes confirmadas com pagina+trecho; quantidades=200 e valores~180k; nao inventou visita tecnica; nova versao preservou objeto usuario. data/e2e-ia-pdf-evidencias-resultado.json.",
        "como_conferir": "Detalhe MANUAL-IA-PDF-E2E-05NOV-B → Analise local → ver Confirmadas com doc/versao/pagina/trecho."
      },
      {
        "fluxo": "Desempenho (load vs analise)",
        "evidencia": "Carregamento ~12,9s; analise PDF ~91,2s. Processos: ollama.exe + llama-server.exe (~2,1 GB RSS). consumo_modelo=nao_medido.",
        "como_conferir": "Relatorio e2e-ia-pdf-evidencias-resultado.json → desempenho."
      },
      {
        "fluxo": "Operacao somente local",
        "evidencia": "base_url http://127.0.0.1:11434; nuvem=false; sem fallback externo no codigo. Rede fisicamente desligada = pendente.",
        "como_conferir": "Status no painel IA; docs/IA-LOCAL.md; pytest test_somente_loopback."
      },
      {
        "fluxo": "Preservacao de campo confirmado pelo usuario",
        "evidencia": "objeto usuario preservado apos analise e apos upload v2 do PDF.",
        "como_conferir": "Ficha do MANUAL-IA-PDF-E2E-05NOV-B → objeto permanece VALOR CONFIRMADO…"
      },
      {
        "fluxo": "TXT anterior (referencia)",
        "evidencia": "MANUAL-FBFF06D94C0E ~109s; lacuna de campos sem trecho motivou este bloco. data/e2e-ia-real-resultado.json.",
        "como_conferir": "Historico / relatorio TXT."
      },
      {
        "fluxo": "IA local indisponivel nao quebra manual",
        "evidencia": "POST /ia-analise com Ollama ausente cria job status=falhou e mensagem clara; ficha/requisitos manuais intactos. pytest test_job_falha_sem_runtime_e_preserva_usuario.",
        "como_conferir": "Detalhe → Analise local → analisar sem Ollama → ver falha; editar ficha manualmente."
      },
      {
        "fluxo": "Recusa de URL de nuvem",
        "evidencia": "_assert_loopback rejeita hosts nao-loopback; status.nuvem=false.",
        "como_conferir": "pytest test_somente_loopback."
      },
      {
        "fluxo": "Evidencia completa (versao + pagina opcional + trecho)",
        "evidencia": "Migracao 011; campo e requisito gravam documento_id (versao), evidencia_pagina (NULL em TXT / nao inventada em legado), trecho. UI mostra Referencia doc # / v / pagina ou sem pagina (TXT). Caso MANUAL-767CA28DEC1C.",
        "como_conferir": "Detalhe → requisitos/ficha → vincular doc v1 + trecho; em TXT nao exige pagina; recarregar e ver referencia persistida."
      },
      {
        "fluxo": "Nova versao sinaliza revisao sem apagar evidencia",
        "evidencia": "Upload v2 marca ficha desatualizada e requisitos com evidencia na versao antiga (precisa_revisao=1); documento_id permanece no id antigo; revisao_origem='' ate o usuario confirmar (usuario).",
        "como_conferir": "Com evidencia em v1, adicionar mesmo arquivo de novo → ver aviso de revisao e referencia ainda em v1; Confirmei a revisao."
      },
      {
        "fluxo": "Tarefa a partir do requisito",
        "evidencia": "POST /requisitos/{id}/checklist cria item com requisito_chave=requisito:{id} e copia evidencia; visivel no checklist do detalhe.",
        "como_conferir": "Requisito → Criar tarefa → ver item no checklist."
      },
      {
        "fluxo": "Datas manuais (esclarecimento/impugnacao)",
        "evidencia": "Campos data_esclarecimento/data_impugnacao na oportunidade; UI no detalhe grava via PATCH /prazos-manuais; lista mostra Esclar./Impug.; origem = usuario (manual), nao extracao automatica.",
        "como_conferir": "Abrir detalhe → Prazos manuais → guardar datas → recarregar lista e detalhe."
      },
      {
        "fluxo": "Requisitos vinculados a documentos/trechos/pagina",
        "evidencia": "evidencia_documento_id + evidencia_pagina + evidencia_trecho persistidos; UI seleciona versao, pagina opcional, trecho; Localizar referencia / Abrir documento.",
        "como_conferir": "Anexar PDF ou TXT → requisitos → vincular → Guardar evidencia → Localizar referencia."
      },
      {
        "fluxo": "Resultados estimados vs realizados",
        "evidencia": "ContinuidadePanel separa cenario estimado de receita/custos realizados; avisos de incompleto; vista Resultados agrega etapas distintas.",
        "como_conferir": "Detalhe → Preparacao/Financeiro: preencher estimado e realizado em campos separados; abrir menu Resultados."
      },
      {
        "fluxo": "Historico de alteracoes sem conteudo sensivel",
        "evidencia": "auditoria_acoes registra acao, numero, detalhe curto (ex. salva=true; estado=...); sem senhas, perfil localStorage ou documentos. Configuracoes → Auditoria local.",
        "como_conferir": "Salvar acompanhamento / mudar fluxo → Configuracoes → lista de auditoria."
      },
      {
        "fluxo": "Offline vs API local indisponivel",
        "evidencia": "ErrorBanner distingue navigator.onLine=false (falta de internet) de rede ok com API local parada.",
        "como_conferir": "Parar API e recarregar (mensagem de API local); ou DevTools offline (mensagem de falta de internet)."
      },
      {
        "fluxo": "Preservacao apos reiniciar",
        "evidencia": "SQLite data/otto.db; manuais MANUAL-3BA117E25456 e MANUAL-595A3D764039 presentes apos reinicio da API nesta sessao; backup pre-correcao otto.db.bak-pre-correcao-desvios-20261104.",
        "como_conferir": "Reiniciar API/app → lista geral ainda mostra os manuais e contagens de fluxo."
      },
      {
        "fluxo": "Backup vs perfil",
        "evidencia": "criar_backup copia otto.db + documentos/; meta.nao_incluido lista localStorage. Aviso na UI de Configuracoes e Continuidade.",
        "como_conferir": "Criar backup → ler backup-meta no zip; confirmar que perfil em Configuracoes nao esta no zip."
      }
    ]
  }
};
