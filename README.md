# Themis
## Engenharia Jurídica

Themis é uma plataforma de engenharia jurídica local-first desenvolvida como plugin oficial para o **Hermes**. Permite organizar, sincronizar e pesquisar autos judiciais com armazenamento e recuperação (retrieval) estritamente locais, integrando-se aos modelos de linguagem (LLM) e provedores configurados no Hermes para análises e sínteses.

### Requisitos Atuais
- **Sistema Operacional**: Windows 10/11 (x64)
- **Plataforma**: Hermes (CLI e Desktop)
- **Navegador**: Google Chrome ou Microsoft Edge

---

## Instalação

A instalação é realizada pelo gerenciador de plugins do Hermes:

```bash
hermes plugins install LogicDump/themis
hermes plugins enable themis
hermes themis setup
```

O comando `hermes themis setup` é idempotente e realiza a preparação completa do ambiente:
- Inicializa a persistência em `<HERMES_HOME>\plugin-data\themis`;
- Cria o catálogo global de processos (`catalog.db`) e arquivos de configuração padrão;
- Baixa e valida via hash SHA-256 os modelos locais de embedding (`EmbeddingGemma 300M ONNX`);
- Gera o token seguro de pareamento (`config/bridge_token.json`);
- Registra o Native Messaging Host no Chrome e Edge para pareamento automático com o navegador.

### Permissões de IA (Capabilities)

Para habilitar sínteses e análises avançadas pelo modelo LLM configurado no Hermes, conceda as capabilities oficiais:

```bash
hermes plugins grant themis llm.provider_override
hermes plugins grant themis llm.model_override
```

---

## Browser Bridge (Extensão do Navegador)

O Themis Browser Bridge conecta a Pasta Digital do e-SAJ/TJSP ao Themis. A extensão já vem distribuída dentro do pacote do plugin.

O único passo necessário no navegador é carregá-la:

1. Acesse `edge://extensions` ou `chrome://extensions` no navegador;
2. Ative o **Modo do desenvolvedor** (Developer mode);
3. Clique em **Carregar sem compactação** (Load unpacked);
4. Selecione a pasta:
   ```text
   <HERMES_HOME>\plugins\themis\browser-bridge
   ```

O pareamento com o Hermes Desktop em execução é automático via Native Messaging.

---

## Primeiro Uso

1. Abra o **Hermes Desktop** e acesse a rota **Themis** na barra lateral;
2. No seu navegador, abra normalmente um processo na Pasta Digital do **e-SAJ / TJSP**;
3. O painel do Themis Bridge aparecerá na página com o botão **“Sincronizar este processo”**;
4. Clique para sincronizar os autos e metadados diretamente para o seu ambiente local.

> **Privacidade e Soberania**: A autenticação, certificados digitais, cookies de sessão e senhas permanecem exclusivamente no seu navegador. Nenhuma credencial é enviada ou armazenada pelo Themis.

---

## Estrutura de Dados

Todos os dados operacionais residem em `<HERMES_HOME>\plugin-data\themis\`:

```text
<HERMES_HOME>\plugin-data\themis\
├── catalog.db                             # Catálogo e descoberta global de processos
├── config\
│   ├── bridge_token.json                  # Token de autenticação do Browser Bridge
│   └── fontes.json                        # Configuração de fontes públicas
├── models\
│   └── embeddinggemma-300m-onnx\          # Modelos neurais locais para busca semântica
│       ├── model_int8.onnx
│       └── tokenizer.json
└── processos\
    └── <CNJ>\                             # Pacote isolado e autocontido de cada processo
        ├── process.db                     # Banco SQLite com peças, páginas e movimentações
        └── markdown\                      # Conteúdo textual e tabelas reconstruídas
```

---

## Tema Visual (Themis Theme)

O pacote inclui o **Themis Theme** para o Hermes Desktop, construído com tipografia baseada nas fontes variáveis **Inter** (interface) e **Roboto Mono** (código e monospace).

O tema é registrado automaticamente no Hermes e pode ser selecionado no painel de aparência. Sua ativação é opcional.
