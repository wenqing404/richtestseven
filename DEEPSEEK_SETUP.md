# DeepSeek API 配置指南

本文档将指导您如何配置此应用以使用 DeepSeek 大语言模型进行财报分析。

## 1. 获取 DeepSeek API 密钥

1. 访问 [DeepSeek 官网](https://platform.deepseek.com/)
2. 注册账号并登录
3. 在控制台中创建 API 密钥
4. 复制您的 API 密钥

## 2. 配置环境变量

### 方法一：使用 .env 文件

1. 复制 `.env.example` 文件为 `.env`：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，设置您的 DeepSeek API 密钥：
   ```
   DEEPSEEK_API_KEY=您的实际API密钥
   DEFAULT_LLM_MODEL=deepseek-chat
   ```

### 方法二：直接设置环境变量

在命令行中设置环境变量：

**Windows (CMD/PowerShell):**
```cmd
set DEEPSEEK_API_KEY=您的实际API密钥
set DEFAULT_LLM_MODEL=deepseek-chat
```

**Linux/macOS:**
```bash
export DEEPSEEK_API_KEY=您的实际API密钥
export DEFAULT_LLM_MODEL=deepseek-chat
```

## 3. 支持的 DeepSeek 模型

应用目前支持以下 DeepSeek 模型：

- `deepseek-chat` - DeepSeek 通用聊天模型（默认）
- `deepseek-coder` - DeepSeek 代码专用模型
- `deepseek-llm` - DeepSeek 基础大语言模型

您可以通过修改 `DEFAULT_LLM_MODEL` 环境变量来更改默认模型。

## 4. 验证配置

运行应用后，您可以通过以下方式验证 DeepSeek API 是否配置正确：

1. 访问应用的 LLM 分析页面
2. 尝试分析一份财报
3. 查看日志确认使用的是 DeepSeek 模型

## 5. 故障排除

### 常见问题

1. **API 密钥无效**
   - 检查 API 密钥是否正确
   - 确认 DeepSeek 账户是否有足够的额度

2. **连接超时**
   - 检查网络连接
   - 确认 DeepSeek API 服务状态

3. **模型不可用**
   - 确认模型名称拼写正确
   - 检查 DeepSeek 是否支持该模型

### 日志查看

应用会在 `financial_analysis.log` 文件中记录详细的日志信息，可用于调试。

## 6. 性能优化建议

1. **调整最大 token 数**
   - 对于长财报，可能需要增加 `max_tokens` 参数
   - 可在 `app/services/llm_analysis_service.py` 中调整

2. **缓存结果**
   - 应用会自动缓存已分析的财报结果
   - 重复分析相同财报时会使用缓存结果

## 7. 安全注意事项

1. **保护 API 密钥**
   - 不要将 `.env` 文件提交到版本控制系统
   - 确保 `.env` 文件权限设置正确

2. **API 使用限制**
   - 注意 DeepSeek 的 API 调用频率限制
   - 监控 API 使用情况以避免超额费用

## 8. 技术支持

如果遇到问题，请参考：
- [DeepSeek 官方文档](https://platform.deepseek.com/docs)
- 应用日志文件 `financial_analysis.log`
- 检查网络连接和防火墙设置

## 9. 版本更新

当 DeepSeek 发布新模型时，您可以：

1. 更新 `DEFAULT_LLM_MODEL` 环境变量
2. 或在 `app/routers/llm_analysis.py` 中的模型列表添加新模型

---
*最后更新: 2024年*
