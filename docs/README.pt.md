<div align="center">

<img src="../assets/logo.svg" alt="Rewind Bulk Creator" width="150" />

# Rewind Bulk Creator

**Crie contas do Rewind.ai em massa, verifique automaticamente e gere uma chave de API para cada uma — com um único comando.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Licença: MIT](https://img.shields.io/badge/Licen%C3%A7a-MIT-3DA639?style=flat-square)](../LICENSE)
[![Plataforma](https://img.shields.io/badge/Plataforma-Rewind.ai-6366F1?style=flat-square)](https://rewind.ai/)
[![Caixas](https://img.shields.io/badge/Caixas-mail.tm-06B6D4?style=flat-square)](https://mail.tm/)
[![Status](https://img.shields.io/badge/Status-Ativo-22C55E?style=flat-square)]()

[English](../README.md) · [Español](README.es.md) · [Português](README.pt.md) · [Deutsch](README.de.md) · [日本語](README.ja.md)

</div>

---

## Visão geral

O Rewind Bulk Creator é uma CLI leve em Python que automatiza todo o fluxo de
cadastro do Rewind.ai: cria caixas descartáveis no [mail.tm](https://mail.tm/),
registra uma conta do Rewind.ai para cada uma, aguarda o e-mail de verificação,
aciona o link de verificação e, por fim, cria uma chave de API com nome
aleatório. Cada conta e chave é salva em JSON, CSV e uma lista simples
`email:chave`.

Ele fala direto com os endpoints HTTP, então não precisa de navegador, driver
headless nem Selenium.

## Recursos

- Um comando para criar quantas contas quiser.
- Caixas descartáveis via mail.tm — sem configuração.
- Verificação de e-mail automática (lê o token da caixa de entrada).
- Nomes de chave de API aleatórios e legíveis (`key-cobalt-falcon-4f2a`).
- Senhas fortes aleatórias ou fixas com `--password`.
- Tratamento elegante de limite de requisições com modo de espera e repetição.
- Saídas JSON, CSV e texto `email:chave`.
- Modo de simulação (`--dry-run`) sem chamadas de rede.

## Início rápido

```bash
git clone https://github.com/<seu-usuario>/rewind-bulk-creator.git
cd rewind-bulk-creator
pip install -r requirements.txt

# Cria 5 contas verificadas, cada uma com sua chave de API
python rewind_bulk.py --count 5
```

Os resultados são salvos em `accounts/`:

```
accounts/
├── accounts.json
├── accounts.csv
└── keys.txt
```

## Uso

```bash
# Dez contas com caixas aleatórias do mail.tm
python rewind_bulk.py -n 10

# Três contas com senha fixa
python rewind_bulk.py -n 3 --password "MinhaSenhaForte123!"

# Prefixo personalizado para os nomes das chaves
python rewind_bulk.py -n 5 --label-prefix worker

# Planejar sem chamadas de rede
python rewind_bulk.py -n 3 --dry-run

# Continuar automaticamente quando o Rewind.ai limitar seu IP
python rewind_bulk.py -n 20 --wait-on-rate-limit
```

## Como funciona

1. **Cria uma caixa** no mail.tm.
2. **Cadastra-se** com `POST /v1/auth/signup`.
3. **Aguarda o e-mail** de verificação e extrai o `token` do link.
4. **Verifica** com `POST /v1/auth/verify-email`.
5. **Cria uma chave de API** com `POST /v1/api-keys`.

## Requisitos

- Python 3.10 ou superior
- `requests`
- Acesso de rede a `api.mail.tm` e `api.rewind.ai`

## Notas e limitações

- O Rewind.ai limita cadastros por IP (por exemplo, 10 por hora). A ferramenta
  detecta o limite e para de forma limpa ou aguarda.
- A entrega do e-mail depende do mail.tm; aumente `--verify-timeout` se demorar.
- Use com responsabilidade e respeite os termos de serviço de cada plataforma.

## Licença

Distribuído sob a [Licença MIT](../LICENSE).
