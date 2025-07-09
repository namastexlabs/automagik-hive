# Scripts de Demonstração - Sistema Multiagente PagBank

## Visão Geral da Demonstração

A demonstração consiste em 6 casos distintos, cada um em um chat separado, mostrando diferentes capacidades do sistema. Total: 20-25 minutos.

---

## Case 1: Cliente Educado com Dúvida Simples (3 min)
**Demonstra: Roteamento eficiente, knowledge base, resposta precisa**

### Perfil: Dra. Marina Oliveira
- Médica, 35 anos, alta escolaridade
- Comunicação clara e objetiva

**Marina:**
> "Boa tarde! Gostaria de informações sobre os tipos de cartão de crédito disponíveis e suas vantagens."

**Sistema (Time Principal):**
> "Boa tarde, Dra. Marina! Prazer em atendê-la. Vou direcioná-la para nosso especialista em cartões que poderá detalhar todas as opções e benefícios disponíveis."

**Sistema (Time de Cartões):**
> *[Busca Knowledge Base: area="cartoes", tipo_informacao="beneficios"]*
> 
> "Olá, Dra. Marina! No PagBank oferecemos cartões de crédito totalmente gratuitos com excelentes benefícios:
> 
> **1. Cartão de Crédito Internacional**
> - Sem anuidade
> - Aceito mundialmente (bandeira Visa)
> - Programa de benefícios Vai de Visa
> - Compatível com Apple Pay, Google Pay e Samsung Wallet
> 
> **2. Limite Flexível**
> - Via Reserva de Saldo: cada real reservado = 1 real de limite
> - Via CDB: invista e use o valor como limite (até R$ 300 mil)
> 
> **3. Benefícios Adicionais**
> - Parcelamento de faturas em até 24x
> - Cartão virtual para compras online
> - Gestão completa pelo app
> 
> Gostaria de saber como solicitar ou tem alguma dúvida específica?"

**Marina:**
> "Perfeito! E quanto ao prazo de entrega?"

**Sistema (Time de Cartões):**
> "O prazo de entrega é de até 15 dias úteis para qualquer endereço no Brasil. Assim que aprovarmos seu pedido, você já terá acesso ao cartão virtual no app para começar a usar em compras online imediatamente. 
> 
> Posso ajudá-la a solicitar seu cartão agora mesmo?"

---

## Case 2: Idoso com Dificuldade Tecnológica (4 min)
**Demonstra: Clarificação, linguagem adaptativa, paciência**

### Perfil: Sr. José Santos
- Aposentado, 72 anos, pouca familiaridade com tecnologia
- Escreve devagar, confunde termos

**José:**
> "ola moça eu quero saber desse negocio de guardar dinheiro que rende mais que a poupança mas nao entendo nada disso de cdb"

**Sistema (Time Principal - Clarifica):**
> *[Detecta: idade avançada pelo contexto, necessidade de simplificação]*
> 
> "Olá, Sr. José! Que bom falar com o senhor. O senhor quer guardar seu dinheiro para ele render mais, é isso? Me conta: o senhor prefere poder pegar esse dinheiro a qualquer hora ou pode deixar guardado por um tempo?"

**José:**
> "eu quero poder pegar quando precisar ne mas que renda mais que essa poupança que nao rende nada"

**Sistema (Time Principal - Roteia):**
> "Entendi perfeitamente! O senhor quer seu dinheiro rendendo mais, mas com a liberdade de pegar quando precisar. Vou passar o senhor para nosso especialista que vai explicar tudinho de forma bem simples."

**Sistema (Time de Investimentos):**
> *[Busca Knowledge Base: nivel_complexidade="basico", publico_alvo="aposentado"]*
> 
> "Sr. José, vou explicar de um jeito bem fácil!
> 
> No PagBank, seu dinheiro parado na conta já rende automaticamente mais que a poupança - o senhor não precisa fazer nada! Isso se chama **Conta Rendeira**.
> 
> Agora, se quiser guardar uma parte separada, temos o **Cofrinho**:
> - É como uma poupança, mas rende mais
> - O senhor pode tirar o dinheiro quando quiser (depois de 1 dia)
> - Não tem taxa nenhuma
> 
> Por exemplo: se o senhor colocar R$ 1.000 no Cofrinho, em um ano terá aproximadamente R$ 1.120, enquanto na poupança teria só R$ 1.080.
> 
> O senhor gostaria que eu explicasse como colocar dinheiro no Cofrinho?"

---

## Case 3: Manoel Silva - Urgência Familiar (5 min)
**Demonstra: Detecção de frustração, escalonamento humano, memória**

### Perfil: Manoel Silva
- Comerciante, 47 anos, ensino fundamental
- Desesperado, família dependendo dele

**[Já documentado no artifact anterior - mantém o caso completo do Manoel com problema de limite do cartão]**

*[Sistema aprende: Problema recorrente com interface "Gerenciar Limite"]*

---

## Case 4: Empresária com Múltiplas Necessidades (4 min)
**Demonstra: Múltiplos roteamentos, contexto mantido, eficiência**

### Perfil: Amanda Chen
- Dona de loja online, 28 anos, tech-savvy
- Várias perguntas em sequência

**Amanda:**
> "Oi! Preciso de 3 coisas: 1) maquininha com taxa competitiva 2) conta PJ com API para integração 3) cartão corporativo pros funcionários"

**Sistema (Time Principal):**
> *[Detecta: múltiplas necessidades, perfil empresarial]*
> 
> "Olá Amanda! Vi que você tem necessidades empresariais específicas. Como são três áreas diferentes, vou conectar você com especialistas para cada uma. Começando pela maquininha - vou direcioná-la ao time comercial."

**Sistema (Time Comercial - não especificado anteriormente mas mencionado aqui):**
> "Amanda, para seu e-commerce temos condições especiais:
> - Taxa zero para novos clientes nos primeiros 3 meses
> - Depois, taxas a partir de 0,99% no débito e 2,39% no crédito
> - Link de pagamento e QR Code inclusos
> 
> Agora sobre a conta PJ..."

**Sistema (Time de Conta Digital):**
> *[Busca: publico_alvo="pessoa_juridica", tipo_informacao="beneficios"]*
> 
> "Para sua conta PJ:
> - API completa para integração com seu e-commerce
> - Webhooks para notificações de pagamento
> - Conciliação automática
> - Split de pagamento disponível
> 
> E sobre os cartões corporativos..."

**Sistema (Time de Cartões):**
> "Oferecemos cartões corporativos pré-pagos:
> - Emissão: R$ 12,90 por cartão
> - Controle total de gastos por funcionário
> - Recarga instantânea pelo app
> - Relatórios detalhados de despesas
> 
> Posso ajudar a calcular uma proposta completa?"

---

## Case 5: Cliente Vítima de Tentativa de Golpe (4 min)
**Demonstra: Detecção de fraude, proteção ao cliente, escalonamento urgente**

### Perfil: Dona Maria Silva
- Pensionista, 65 anos, vulnerável
- Mencionando pagamento suspeito

**Maria:**
> "moça o rapaz do pagbank me ligou dizendo que eu tenho que pagar 500 reais pra liberar meu emprestimo consignado é assim mesmo"

**Sistema (Time Principal - ALERTA VERMELHO):**
> *[Detecta: palavras-chave "pagar para liberar empréstimo" = GOLPE]*
> *[Ação imediata: Proteção ao cliente]*
> 
> "Dona Maria, ATENÇÃO! Isso é GOLPE! O PagBank NUNCA pede pagamento antecipado. NÃO faça nenhum pagamento! Vou transferir a senhora AGORA para nossa equipe de segurança."

**Sistema (Agente de Segurança - Mock):**
> *[Cria protocolo urgente: FRAUDE-20240117-1847]*
> 
> "Dona Maria, aqui é a equipe de segurança do PagBank. A senhora fez muito bem em perguntar antes de pagar!
> 
> **IMPORTANTE:**
> - NÃO pague nada
> - NÃO passe seus dados
> - Se ligarem de novo, desligue
> 
> **Protocolo de Segurança: FRAUDE-20240117-1847**
> 
> A senhora já fez algum pagamento ou passou dados pessoais para essa pessoa?"

**Maria:**
> "nao ainda nao mas ele disse que era urgente"

**Sistema:**
> "A senhora agiu corretamente! Esse é um golpe comum. O verdadeiro empréstimo consignado do PagBank:
> - Desconta direto do seu benefício
> - Não precisa pagar nada antecipado
> - É aprovado apenas pelo app oficial
> 
> Vou registrar essa tentativa de golpe. A senhora tem o número que te ligou?"

*[Memória: Registra padrão de golpe, número do golpista, perfil vulnerável]*

---

## Case 6: Investidor Sofisticado com Dúvidas Técnicas (3 min)
**Demonstra: Conhecimento avançado, compliance, linguagem técnica adaptada**

### Perfil: Roberto Nakamura
- Analista financeiro, 40 anos, CPA-20
- Questões complexas sobre investimentos

**Roberto:**
> "Boa tarde. Gostaria de informações sobre a estrutura de FIDCs ou FIMs disponíveis na plataforma, especificamente sobre liquidez D+N, taxa de administração e performance, e se há produtos com estratégias de hedge cambial."

**Sistema (Time Principal):**
> *[Detecta: alto nível técnico, conhecimento especializado]*
> 
> "Boa tarde, Sr. Roberto. Vejo que o senhor busca informações detalhadas sobre nossos produtos de investimento mais sofisticados. Vou direcioná-lo para nossa assessoria de investimentos especializada."

**Sistema (Time de Investimentos):**
> *[Busca Knowledge Base: nivel_complexidade="avancado", tipo_produto="fundos"]*
> 
> "Sr. Roberto, prazer em atendê-lo. Sobre sua consulta:
> 
> **Fundos Disponíveis:**
> - FI Renda Fixa: Liquidez D+1, taxa de administração 0,5% a.a.
> - FI Multimercado: Liquidez D+30, taxa de administração 2% a.a. + performance 20% sobre CDI
> 
> **Estratégias com Proteção Cambial:**
> - Ainda não oferecemos FIDCs próprios
> - Temos BDRs para exposição internacional
> - Fundos com hedge cambial estão em nosso pipeline para Q2/2024
> 
> **Importante:** Esta não é uma recomendação de investimento. Os produtos apresentados podem não ser adequados aos seus objetivos.
> 
> Para investidores qualificados como o senhor, sugiro agendar uma conversa com nosso time de wealth management. Posso verificar a disponibilidade?"

*[Memória: Cliente qualificado, interesse em produtos sofisticados]*

---

## Resumo das Capacidades Demonstradas

| Capacidade | Case 1 | Case 2 | Case 3 | Case 4 | Case 5 | Case 6 |
|------------|--------|--------|--------|--------|--------|--------|
| Knowledge Base com Filtros | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Clarificação | | ✓ | ✓ | | | |
| Adaptação de Linguagem | | ✓ | ✓ | | ✓ | ✓ |
| Detecção de Frustração | | | ✓ | | ✓ | |
| Escalonamento Humano | | | ✓ | | ✓ | |
| Memória/Aprendizado | | | ✓ | | ✓ | ✓ |
| Multi-roteamento | | | | ✓ | | |
| Detecção de Fraude | | | | | ✓ | |
| Compliance | ✓ | | | | | ✓ |
| Contexto Empresarial | | | | ✓ | | |

## Insights para Apresentação

1. **Inclusão Digital**: Sistema atende desde idosos com dificuldade até analistas financeiros
2. **Proteção ao Cliente**: Detecção proativa de golpes e fraudes
3. **Inteligência Contextual**: Adapta linguagem e profundidade conforme o cliente
4. **Eficiência Operacional**: Resolve múltiplas necessidades em uma única interação
5. **Aprendizado Contínuo**: Cada interação melhora o sistema para os próximos clientes