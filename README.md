# Markdown 链接检查器

一个使用多线程检查 Markdown 文件中链接的 Python 脚本。该脚本将验证所有 Markdown 文件中的链接是否可访问，并生成详细报告。

> ⚠️ **重要提示**：
>
> - 本工具仅作为辅助检查手段，检测结果可能不完全准确
> - 某些网站可能会限制访问或返回错误状态码，但实际链接是可用的
> - 建议在使用时开启代理，以提高检测准确性和成功率
> - 对于重要链接，建议手动验证其可访问性

## 功能特点

- 多线程链接检查（默认：16线程）
- 详细的操作日志记录（可选择性开启/关闭）
- 进度条显示
- 支持单个文件和目录
- 生成全面的报告
- 处理重定向和超时
- 支持 UTF-8 编码
- 模拟真实浏览器行为
- 自动重试失败的请求

## 系统要求

- Python 3.6+
- 所需包（使用 `pip install -r requirements.txt` 安装）：
  - requests
  - beautifulsoup4
  - markdown
  - tqdm

## 安装步骤

1. 克隆此仓库或下载文件
2. 安装所需的包：

```bash
pip install -r requirements.txt
```

## 使用方法

基本用法：

```bash
python link_checker.py 路径/到/markdown文件.md
```

检查目录中的所有 markdown 文件：

```bash
python link_checker.py 路径/到/目录
```

自定义线程数和超时时间：

```bash
python link_checker.py 路径/到/文件.md --threads 32 --timeout 30
```

禁用日志记录：

```bash
python link_checker.py 路径/到/文件.md --no-log
```

### 命令行参数

- `path`：Markdown 文件或目录的路径（必需）
- `--threads`：使用的线程数（默认：16）
- `--timeout`：请求超时时间（秒）（默认：20）
- `--no-log`：禁用日志记录（可选）

## 输出文件

1. 日志文件（`link_check_YYYYMMDD_HHMMSS.log`）：
   - 包含所有操作的详细日志
   - 包括成功、失败和错误信息
   - 可通过 `--no-log` 参数禁用

2. 结果文件（`link_check_results_YYYYMMDD_HHMMSS.txt`）：
   - 列出所有检查过的链接
   - 将链接分类为成功、失败或跳过
   - 包含状态码和错误信息
   - 始终生成，不受日志设置影响

## 使用示例

1. 基本检查：

```bash
python link_checker.py ./docs
```

2. 高性能检查（更多线程，更长超时）：

```bash
python link_checker.py ./docs --threads 32 --timeout 30
```

3. 静默模式（无日志）：

```bash
python link_checker.py ./docs --no-log
```

4. 完整参数示例：

```bash
python link_checker.py ./docs --threads 32 --timeout 30 --no-log
```

## 注意事项

- 脚本使用 GET 请求而不是 HEAD 请求，以更好地模拟浏览器行为
- 对于失败的请求会自动重试一次
- 即使返回 403 状态码的链接也可能被标记为成功（因为有些网站会返回 403 但实际可访问）
- 禁用日志后仍然会显示进度条和生成结果文件

## 提高检测准确性的建议

1. **使用代理**：
   - 建议配置代理服务器，特别是对于国外网站
   - 可以通过设置环境变量 `HTTP_PROXY` 和 `HTTPS_PROXY` 来使用代理

2. **调整超时时间**：
   - 对于响应较慢的网站，可以适当增加超时时间
   - 默认 20 秒可能不足以处理某些网站

3. **手动验证**：
   - 对于标记为失败的链接，建议手动验证
   - 某些网站可能有特殊的访问限制或验证机制

4. **分批检查**：
   - 如果链接数量很多，建议分批检查
   - 可以避免触发目标网站的反爬虫机制

5. **定期更新**：
   - 网站状态可能随时变化
   - 建议定期重新检查重要链接
