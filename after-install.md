# Themis — Instruções Pós-Instalação

O plugin Themis foi instalado com sucesso.

Para concluir a configuração e inicializar os modelos locais e esquemas de dados, execute os passos a seguir:

### 1. Habilitar o Plugin

```bash
hermes plugins enable themis
```

### 2. Inicializar o Ambiente e Baixar Modelos Locais

```bash
hermes themis setup
```

Este comando:
- Inicializa a persistência em `<HERMES_HOME>/plugin-data/themis`;
- Cria o catálogo SQLite global (`catalog.db`);
- Gera os arquivos de configuração locais (`config/fontes.json`, `config/bridge_token.json`);
- Registra o Native Messaging Host no Chrome e Edge para pareamento automático com a extensão;
- Baixa e valida com integridade SHA-256 os modelos locais de embedding (`EmbeddingGemma 300M ONNX`).

### 3. Instalar a Extensão Themis Browser Bridge no Navegador

A extensão do Browser Bridge está localizada na pasta do próprio plugin:
`<HERMES_HOME>/plugins/themis/browser-bridge`

Para instalá-la no Google Chrome ou Microsoft Edge:
1. Abra `chrome://extensions` ou `edge://extensions` no navegador;
2. Ative o **Modo do desenvolvedor** (Developer mode);
3. Clique em **Carregar sem compactação** (Load unpacked);
4. Selecione a pasta `browser-bridge` dentro da instalação do plugin Themis;
5. Ao abrir a Pasta Digital do e-SAJ/TJSP, o ícone da extensão indicará `🟢 Conectado ao Themis` automaticamente. Se necessário pareamento manual, o token gerado está em `<HERMES_HOME>/plugin-data/themis/config/bridge_token.json`.

### 4. Capabilities de IA (Consentimento do Usuário)

O Themis utiliza operações de IA com override explícito de provedor/modelo. Conceda as seguintes permissões através do fluxo de consentimento do Hermes:

```bash
hermes plugins grant themis llm.provider_override
hermes plugins grant themis llm.model_override
```

---
*Para verificar a integridade da instalação a qualquer momento, execute `hermes plugins doctor <caminho-do-plugin> --ci`.*
