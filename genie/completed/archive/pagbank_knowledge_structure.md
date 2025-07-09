# Estrutura Completa do Knowledge Base PagBank

## Schema do CSV

### Colunas Obrigatórias

| Coluna | Tipo | Descrição | Valores Possíveis |
|--------|------|-----------|-------------------|
| conteudo | TEXT | Informação completa | Texto livre |
| area | STRING | Área do conhecimento | cartoes, conta_digital, investimentos, credito, seguros |
| tipo_produto | STRING | Produto específico | Ver tabela abaixo |
| tipo_informacao | STRING | Categoria da info | como_solicitar, taxas, beneficios, requisitos, prazos, limites, problemas_comuns |
| nivel_complexidade | STRING | Complexidade | basico, intermediario, avancado |
| publico_alvo | STRING | Público | pessoa_fisica, pessoa_juridica, aposentado, menor_idade, trabalhador_clt, todos |
| palavras_chave | TEXT | Tags de busca | Palavras separadas por espaço |
| atualizado_em | DATE | Data atualização | YYYY-MM |

### Valores de tipo_produto por Área

```yaml
cartoes:
  - cartao_credito
  - cartao_debito  
  - cartao_prepago
  - cartao_virtual
  - limite_credito
  
conta_digital:
  - conta_rendeira
  - pix
  - ted
  - doc
  - pagamento_contas
  - recarga_celular
  - recarga_servicos
  - portabilidade
  
investimentos:
  - cdb
  - lci
  - lca
  - renda_variavel
  - tesouro_direto
  - cofrinho
  - fundos
  
credito:
  - fgts
  - consignado_inss
  - consignado_publico
  - emprestimo_pessoal
  
seguros:
  - seguro_vida
  - seguro_residencia
  - seguro_conta
  - saude
  - seguro_cartao
```

## Exemplos de Registros CSV

### Área: Cartões

```csv
"O Cartão de Crédito PagBank é totalmente gratuito, sem anuidade. Para solicitar, acesse o app PagBank, toque em 'Cartões' na tela inicial e selecione 'Pedir cartão grátis'. O cartão chega em até 15 dias úteis.",cartoes,cartao_credito,como_solicitar,basico,pessoa_fisica,"pedir cartao credito gratis solicitar",2024-01

"Para aumentar o limite do cartão de crédito, você tem duas opções: 1) Reserva de Saldo: cada R$1 reservado vira R$1 de limite. Acesse Cartões > Gerenciar Limite > Aumentar Reserva. 2) Investir em CDB: o valor investido vira limite automaticamente.",cartoes,limite_credito,como_solicitar,intermediario,pessoa_fisica,"aumentar limite reserva saldo cdb investimento",2024-01

"Problema: 'Não consigo ver a opção Gerenciar Limite'. Solução: Tente atualizar o app. Se persistir, procure o menu três pontos (⋮) no canto superior da tela do cartão. Casos específicos podem necessitar atendimento.",cartoes,cartao_credito,problemas_comuns,intermediario,todos,"erro problema gerenciar limite nao aparece",2024-01

"Cartão Pré-Pago PagBank: Taxa única de R$ 12,90 para emissão, sem mensalidade. Ideal para controle de gastos e mesada dos filhos. Funciona na função crédito em compras online.",cartoes,cartao_prepago,taxas,basico,menor_idade,"prepago valor custo mesada filhos crianca",2024-01
```

### Área: Conta Digital

```csv
"A Conta Rendeira PagBank rende 100% do CDI automaticamente. Isso significa que seu dinheiro rende mais que a poupança todos os dias, sem você precisar fazer nada. O rendimento é creditado mensalmente.",conta_digital,conta_rendeira,beneficios,basico,pessoa_fisica,"render cdi 100 porcento automatico poupanca",2024-01

"PIX no PagBank: Transferências gratuitas e ilimitadas, 24 horas por dia, 7 dias por semana. Para fazer um PIX: App > PIX > Transferir. Você pode usar CPF, telefone, e-mail ou chave aleatória.",conta_digital,pix,como_solicitar,basico,todos,"pix transferencia gratis ilimitado como fazer",2024-01

"Recargas de celular com cashback: Ganhe dinheiro de volta em todas as recargas. Operadoras: Claro, Vivo, TIM, Oi. Como fazer: App > Recargas > Escolha operadora > Digite número > Confirme.",conta_digital,recarga_celular,beneficios,basico,pessoa_fisica,"recarga celular cashback volta dinheiro claro vivo tim oi",2024-01
```

### Área: Investimentos

```csv
"CDB PagBank com até 130% do CDI. Aplicação mínima: R$ 300. O valor investido vira limite no cartão de crédito automaticamente. Proteção FGC até R$ 250 mil. Aviso: Esta não é recomendação de investimento.",investimentos,cdb,beneficios,intermediario,pessoa_fisica,"cdb 130 cdi render limite cartao investir",2024-01

"LCI e LCA: Investimentos isentos de Imposto de Renda para pessoa física. LCI financia o setor imobiliário, LCA financia o agronegócio. Rendimento competitivo e proteção FGC.",investimentos,lci,beneficios,intermediario,pessoa_fisica,"lci lca isento imposto renda ir investimento",2024-01

"Cofrinho PagBank: Guarde dinheiro rendendo 100% do CDI. Resgate quando quiser após 1 dia. Ideal para reserva de emergência. Configure aportes automáticos: diários, semanais ou mensais.",investimentos,cofrinho,como_solicitar,basico,todos,"cofrinho guardar dinheiro reserva emergencia render",2024-01
```

### Área: Crédito

```csv
"Antecipação Saque-Aniversário FGTS: Receba até 10 anos do seu FGTS em 2 minutos. Taxas a partir de 1,24% ao mês. Requisitos: ter saldo FGTS, optar pelo saque-aniversário, autorizar BancoSeguro.",credito,fgts,como_solicitar,basico,trabalhador_clt,"fgts antecipacao saque aniversario taxa requisito",2024-01

"ALERTA GOLPE: PagBank NUNCA solicita pagamento antecipado para liberar empréstimos. Se pedirem depósito, boleto ou PIX antes de liberar o crédito, é GOLPE. Denuncie imediatamente.",credito,todos,requisitos,basico,todos,"golpe fraude pagamento antecipado emprestimo alerta",2024-01

"Consignado INSS: Para aposentados e pensionistas. Parcelas descontadas direto do benefício. Até 40% de comprometimento da renda. Prazo até 96 meses. Contratação 100% pelo app.",credito,consignado_inss,requisitos,basico,aposentado,"consignado inss aposentado pensionista desconto beneficio",2024-01
```

### Área: Seguros

```csv
"PagBank Saúde: R$ 24,90/mês para titular + até 4 dependentes grátis. Sem carência, uso imediato. Consultas médicas e odontológicas com desconto. Rede com mais de 40 mil profissionais.",seguros,saude,precos,basico,pessoa_fisica,"saude plano medico dentista desconto consulta preco",2024-01

"Seguro Residência: Planos a partir de R$ 5,90/mês. Cobertura: incêndio, roubo, danos elétricos, vendaval. Assistência 24h: chaveiro, encanador, eletricista. Sorteio mensal R$ 20 mil.",seguros,seguro_residencia,beneficios,basico,pessoa_fisica,"seguro casa residencia chaveiro encanador assistencia",2024-01

"Seguro de Vida: A partir de R$ 8,90/mês. Cobertura por morte de qualquer causa, invalidez por acidente. Assistência funeral individual ou familiar. Orientação psicológica incluída.",seguros,seguro_vida,beneficios,basico,pessoa_fisica,"seguro vida morte invalidez funeral psicologico",2024-01
```

## Script de Importação Sugerido

```python
# Pseudocódigo para importação
def import_knowledge_base():
    # Ler CSV
    df = read_csv("pagbank_knowledge.csv")
    
    # Criar knowledge base
    knowledge_base = CSVKnowledgeBase(
        path="pagbank_knowledge.csv",
        vector_db=PgVector(
            table_name="pagbank_documents",
            db_url="postgresql://..."
        ),
        columns_to_embed=["conteudo", "palavras_chave"],
        metadata_columns=[
            "area", "tipo_produto", "tipo_informacao",
            "nivel_complexidade", "publico_alvo", "atualizado_em"
        ]
    )
    
    # Carregar e indexar
    knowledge_base.load(recreate=True)
    
    return knowledge_base
```

## Queries de Exemplo com Filtros

```python
# Time de Cartões buscando sobre limite
agent.search_knowledge(
    "como aumentar limite cartão",
    filters={
        "area": "cartoes",
        "tipo_produto": ["cartao_credito", "limite_credito"]
    }
)

# Time de Crédito verificando alertas de golpe
agent.search_knowledge(
    "pagamento antecipado",
    filters={
        "area": "credito",
        "tipo_informacao": "requisitos",
        "palavras_chave": "golpe"
    }
)

# Busca por complexidade para cliente iniciante
agent.search_knowledge(
    "investir dinheiro",
    filters={
        "area": "investimentos",
        "nivel_complexidade": "basico"
    }
)
```