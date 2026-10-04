<div align="center">

<img src="../assets/logo.svg" alt="Rewind Bulk Creator" width="150" />

# Rewind Bulk Creator（批量账号创建器）

**一条命令即可批量创建 Rewind.ai 账号、自动完成邮箱验证，并为每个账号生成一个随机命名的 API 密钥。**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![许可证: MIT](https://img.shields.io/badge/%E8%AE%B8%E5%8F%AF%E8%AF%81-MIT-3DA639?style=flat-square)](../LICENSE)
[![平台](https://img.shields.io/badge/%E5%B9%B3%E5%8F%B0-Rewind.ai-6366F1?style=flat-square)](https://rewind.ai/)
[![邮箱](https://img.shields.io/badge/%E9%82%AE%E7%AE%B1-mail.tm-06B6D4?style=flat-square)](https://mail.tm/)
[![状态](https://img.shields.io/badge/%E7%8A%B6%E6%80%81-%E6%B4%BB%E8%B7%83-22C55E?style=flat-square)]()

[English](../README.md) · [Español](README.es.md) · [Português](README.pt.md) · [Deutsch](README.de.md) · [日本語](README.ja.md) · [中文](README.zh.md)

</div>

---

## 概述

Rewind Bulk Creator 是一个轻量级 Python 命令行工具，可自动完成 Rewind.ai 的整个注册流程：在 [mail.tm](https://mail.tm/) 上创建一次性邮箱，为每个邮箱注册一个 Rewind.ai 账号，等待验证邮件，打开验证链接，最后创建一个随机命名的 API 密钥。每个账号和密钥都会以 JSON、CSV 以及简单的 `email:key` 文本形式保存到磁盘。

它直接调用 HTTP 接口，因此无需浏览器、无头驱动或 Selenium。

## 功能特性

- 一条命令创建任意数量的账号。
- 通过 mail.tm 创建一次性邮箱 — 无需任何配置。
- 自动邮箱验证（从收件箱中提取令牌）。
- 随机且易读的 API 密钥名称（`key-cobalt-falcon-4f2a`）。
- 随机强密码，或使用 `--password` 固定密码。
- 优雅处理速率限制，支持等待并重试模式。
- 输出 JSON、CSV 和 `email:key` 文本，便于管道处理。
- 演练模式（`--dry-run`），不发起任何网络请求。

## 快速开始

```bash
git clone https://github.com/<你的用户名>/rewind-bulk-creator.git
cd rewind-bulk-creator
pip install -r requirements.txt

# 创建 5 个已验证账号，每个账号都有自己的 API 密钥
python rewind_bulk.py --count 5
```

结果会保存到 `accounts/`：

```
accounts/
├── accounts.json
├── accounts.csv
└── keys.txt
```

## 使用方法

```bash
# 使用随机 mail.tm 邮箱创建十个账号
python rewind_bulk.py -n 10

# 使用固定密码创建三个账号
python rewind_bulk.py -n 3 --password "MyFixedPassw0rd!"

# 自定义 API 密钥名称前缀
python rewind_bulk.py -n 5 --label-prefix worker

# 仅规划，不发起网络请求
python rewind_bulk.py -n 3 --dry-run

# 当 Rewind.ai 限制你的 IP 时自动等待并继续
python rewind_bulk.py -n 20 --wait-on-rate-limit
```

## 工作原理

1. 在 mail.tm 上**创建邮箱**。
2. 通过 `POST /v1/auth/signup` **注册账号**。
3. **等待验证邮件**并从链接中提取 `token`。
4. 通过 `POST /v1/auth/verify-email` **完成验证**。
5. 通过 `POST /v1/api-keys` **创建 API 密钥**。

## 环境要求

- Python 3.10 或更高版本
- `requests`
- 可访问 `api.mail.tm` 和 `api.rewind.ai` 的网络

## 说明与限制

- Rewind.ai 会按 IP 限制注册数量（例如每小时 10 个）。本工具会检测该限制，并根据参数选择干净停止或等待。
- 邮件投递取决于 mail.tm；若较慢，请增大 `--verify-timeout`。
- 请负责任地使用，并遵守你所自动化操作的任何平台的服务条款。

## 许可证

基于 [MIT 许可证](../LICENSE) 发布。
