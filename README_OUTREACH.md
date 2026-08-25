# Local Outreach Studio

面向本地餐厅和小商家的单店销售辅助工具。

## 功能

- 输入国家和区域，按公开、透明的评分体系给商家排序。
- 内置 Thailand / Chiang Mai 示例，可扩展其他国家和城市。
- 为选中的商家生成个性化网站示意图，输出到 `campaign_output/demo-*`。
- 生成包含 Demo 链接、菜单、价格、营业时间和退订说明的英文邮件草稿。
- 默认 Preview / dry-run；关闭后每次发送仍需要人工确认。
- 从 `mailbox/inbox/*.eml` 读取回信，匹配固定问题答案。
- 可选使用 `OPENAI_API_KEY` 生成 AI 回复草稿，AI 回复同样不会自动发送。
- 支持 SMTP；只适用于你拥有并获授权使用的邮箱。

## 运行

```powershell
& "C:\Users\15657\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" outreach_app.py
```

## 打包 EXE

```powershell
.\build_exe.ps1
```

生成 `dist\LocalOutreachStudio.exe`。

## 邮件安全

复制 `smtp_config.example.json` 为 `smtp_config.json`，填入邮箱配置。建议先使用 Mailpit/MailHog 等本地虚拟邮箱验证邮件内容，再发送真实邮件。程序不提供批量发送和自动群发；目标邮箱、内容和退订处理必须由人工确认，并遵守目标国家的反垃圾邮件法规。

## 数据来源

内置示例使用公开餐厅目录信息，仅用于演示。实际外联前应人工核对营业状态、菜单、价格、联系方式和图片使用权。
