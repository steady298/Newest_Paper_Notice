# GitHub Actions 配置说明

本项目已配置 GitHub Actions，每天自动运行更新论文列表。

## 配置步骤

### 1. 设置 GitHub Secrets

在 GitHub 仓库中设置以下 Secrets（Settings → Secrets and variables → Actions → New repository secret）：

1. **GEMINI_API_KEY**
   - 名称：`GEMINI_API_KEY`
   - 值：您的 Gemini API 密钥

2. **PUSHDEER_KEY**
   - 名称：`PUSHDEER_KEY`
   - 值：您的 PushDeer 推送密钥

### 2. 启用 GitHub Actions

1. 确保 `.github/workflows/daily-update.yml` 文件已提交到仓库
2. 在仓库的 Settings → Actions → General 中，确保 Actions 已启用

### 3. 验证配置

- 可以手动触发 workflow：在 Actions 标签页中，选择 "Daily Paper Update"，点击 "Run workflow"
- 或者等待定时任务自动运行（每天早上8点北京时间）

## 工作流程

1. **定时触发**：每天 UTC 0:00（北京时间 8:00）自动运行
2. **手动触发**：可以在 Actions 页面手动触发
3. **执行步骤**：
   - 检出代码
   - 设置 Python 环境
   - 安装依赖
   - 运行主程序
   - 自动提交更新后的文件（README.md, index.html, cv-arxiv-daily.json）

## 注意事项

- 确保仓库有写入权限（通常默认就有）
- 如果推送失败，检查 GitHub Token 权限
- 定时任务可能因为 GitHub Actions 的负载而略有延迟

## 修改运行时间

如需修改运行时间，编辑 `.github/workflows/daily-update.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 0 * * *'  # UTC 时间，北京时间需要减去8小时
```

例如：
- 北京时间 8:00 = UTC 0:00 → `'0 0 * * *'`
- 北京时间 9:00 = UTC 1:00 → `'0 1 * * *'`
- 北京时间 10:00 = UTC 2:00 → `'0 2 * * *'`

