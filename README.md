# pytest-myplugin

一个用于 pytest 二次开发的测试框架模板，支持多 SDK 服务配置、Data-driven API 测试、PyGithub 集成和 Playwright UI 测试。

## 核心能力

- `pytest11` 插件入口点，安装后由 pytest 自动加载
- 多 SDK 配置加载、环境变量替换和本地覆盖
- SDK 客户端懒加载、缓存和 session 结束统一关闭
- JSON 驱动的 Data-driven API 测试
- PyGithub SDK 服务和 `github_client` fixture
- Playwright UI 测试和 GitHub 登录 fixture
- Allure 测试步骤、附件和 HTML 报告
- Ruff、Coverage、wheel/sdist 构建配置

## 初始化开发环境

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## 服务配置

包内默认配置位于：

```text
src/pytest_myplugin/config/default.toml
```

项目配置位于：

```text
config/services.toml
```

示例：

```toml
[services.github]
base_url = "https://api.github.com"
token = "${GITHUB_TOKEN}"
timeout = 15

# 后续可以增加其他 SDK
# [services.gitlab]
# base_url = "https://gitlab.example.com/api/v4"
# token = "${GITLAB_TOKEN}"
# timeout = 30
```

支持的环境变量语法：

```text
${GITHUB_TOKEN}              # 必须设置，否则配置加载失败
${GITHUB_TOKEN:-}            # 未设置时使用空字符串
${GITHUB_TOKEN:-anonymous}   # 未设置时使用默认值
```

配置加载顺序：

```text
包内默认配置
-> config/services.toml
-> config/services.local.toml
```

也可以通过环境变量指定额外配置：

```bash
export TEST_SERVICE_CONFIG=/absolute/path/to/services.local.toml
```

`config/services.local.toml` 和 `.env` 已加入 `.gitignore`，不要将真实 token 提交到仓库。

## 测试分层

```text
tests/
├── api/                 # JSON 定义的 Data-driven API 用例
├── sdk/                 # SDK 直调用例和框架单元测试
└── ui/                  # Playwright UI 用例
```

三种测试需要的凭据不同：

| 测试类型 | 所需环境变量 |
|---|---|
| API 测试 | `GITHUB_TOKEN` |
| SDK 测试 | `GITHUB_TOKEN` |
| UI 测试 | `GITHUB_UI_USERNAME`、`GITHUB_UI_PASSWORD` |
| Data-driven 加载器单元测试 | 无 |

## Data-driven API 测试

API 用例位于：

```text
tests/api/github/cases/
```

加载器会递归扫描该目录下的所有 JSON 文件。每个 JSON 文件会被转换成一个独立 pytest 用例，文件名作为 case ID。

示例：

```json
{
  "request_name": "search_repositories",
  "parameters": {
    "query": "pytest",
    "sort": "stars",
    "order": "desc"
  },
  "expectation": {
    "code": 200
  }
}
```

字段说明：

| 字段 | 说明 |
|---|---|
| `request_name` | 要调用的 `GithubClient` 方法名 |
| `parameters` | 传给方法的 Python 关键字参数 |
| `expectation.code` | 期望的 HTTP 状态码 |

加载器使用严格 schema：

- 只允许 `request_name`、`parameters`、`expectation`
- `expectation` 只允许 `code`
- 错误拼写会直接导致加载失败
- 重复 case ID 会直接导致加载失败

执行流程：

1. pytest 收集阶段加载所有 JSON。
2. 每个 JSON 被转换成 `ApiCase`。
3. `pytest.mark.parametrize` 为每个 `ApiCase` 创建独立测试。
4. `github_client.invoke()` 根据 `request_name` 动态调用 SDK 方法。
5. `parameters` 通过关键字参数传给 SDK。
6. 框架触发 PyGithub 懒加载对象，确保请求真实发生。
7. 正常响应统一得到 200，HTTP 异常从 `GithubException.status` 获取状态码。
8. pytest 断言实际状态码等于 `expectation.code`。

运行：

```bash
export GITHUB_TOKEN=github_pat_xxx
pytest tests/api -m api
```

当前包含：

```text
search_repositories_200.json
search_repositories_empty_query_422.json
```

空查询负向用例会直接构造 GitHub Search 请求，让 GitHub 服务端返回真实的 422，而不是由 PyGithub 在本地提前拒绝。

新增 API 用例时只需要增加 JSON 文件，不需要修改测试代码。

## SDK 测试

SDK 直调用例位于：

```text
tests/sdk/test_github_search_live.py
```

运行：

```bash
export GITHUB_TOKEN=github_pat_xxx
pytest tests/sdk/test_github_search_live.py -m integration
```

Data-driven 加载器的单元测试不需要 token：

```bash
pytest tests/sdk/test_data_driven_loader.py
```

## Playwright UI 测试

安装 Playwright 浏览器：

```bash
python -m playwright install chromium
```

也可以使用本机 Google Chrome：

```bash
pytest tests/ui -m ui --browser-channel=chrome
```

有界面调试：

```bash
pytest tests/ui -m ui --browser-channel=chrome --headed
```

GitHub 登录测试位于：

```text
tests/ui/test_github_login.py
```

登录动作封装在：

```text
src/pytest_myplugin/fixtures/github_ui.py
```

配置账号：

```bash
export GITHUB_UI_USERNAME=your-test-account
export GITHUB_UI_PASSWORD=your-test-password

pytest tests/ui/test_github_login.py -m ui --browser-channel=chrome
```

fixture 会打开 GitHub 登录页、提交账号密码，并校验页面中的 `user-login` 与配置账号一致。

## Allure 报告

Allure Python 插件已经包含在 `dev` 依赖中。安装 Allure CLI：

```bash
brew install allure
```

生成 API 和 SDK 测试结果：

```bash
export GITHUB_TOKEN=github_pat_xxx

pytest tests/api tests/sdk \
  -m "api or integration" \
  --alluredir=allure-results \
  --clean-alluredir
```

生成 UI 测试结果：

```bash
pytest tests/ui \
  -m ui \
  --browser-channel=chrome \
  --alluredir=allure-results
```

直接打开临时报告：

```bash
allure serve allure-results
```

生成静态 HTML 报告：

```bash
allure generate allure-results -o allure-report --clean
allure open allure-report
```

`allure-results/` 和 `allure-report/` 已加入 `.gitignore`。

## 目录结构

```text
.
├── config/
│   └── services.toml
├── pyproject.toml
├── README.md
├── src/
│   └── pytest_myplugin/
│       ├── __init__.py
│       ├── bootstrap.py
│       ├── data_driven.py
│       ├── plugin.py
│       ├── py.typed
│       ├── config/
│       │   ├── __init__.py
│       │   ├── default.toml
│       │   ├── errors.py
│       │   ├── loader.py
│       │   └── resolver.py
│       ├── fixtures/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── github.py
│       │   └── github_ui.py
│       └── services/
│           ├── __init__.py
│           ├── base.py
│           ├── github.py
│           └── registry.py
└── tests/
    ├── api/
    │   └── github/
    │       ├── cases/
    │       │   ├── search_repositories_200.json
    │       │   └── search_repositories_empty_query_422.json
    │       └── test_github_api_cases.py
    ├── sdk/
    │   ├── test_data_driven_loader.py
    │   └── test_github_search_live.py
    └── ui/
        └── test_github_login.py
```

## 新增其他 SDK

以 GitLab 为例：

1. 在 `config/services.toml` 和包内默认配置中增加 `[services.gitlab]`。
2. 新建 `src/pytest_myplugin/services/gitlab.py`。
3. 定义 `GitlabSettings`、`GitlabClient` 和 `build_gitlab_client(config)`。
4. 在 `src/pytest_myplugin/bootstrap.py` 中注册：

```python
registry.register("gitlab", build_gitlab_client)
```

5. 新建 `src/pytest_myplugin/fixtures/gitlab.py`。
6. 在 `src/pytest_myplugin/plugin.py` 中导入对应 fixture。

调用示例：

```python
def test_gitlab_project(gitlab_client):
    project = gitlab_client.get_project("group/project")
    assert project.name == "project"
```

## 常用命令

```bash
# 无外部依赖的框架单元测试
pytest tests/sdk/test_data_driven_loader.py

# API 用例
pytest tests/api -m api

# SDK 用例
pytest tests/sdk/test_github_search_live.py -m integration

# UI 用例
pytest tests/ui -m ui --browser-channel=chrome

# 覆盖率
pytest --cov --cov-report=term-missing

# 代码检查
ruff check .

# 自动修复
ruff check . --fix

# 构建 wheel 和 sdist
python -m build

# 本地已有构建依赖时
python -m build --no-isolation
```

## pytest 插件验证

```bash
pytest --myplugin
pytest --myplugin --trace-config
```

`--trace-config` 输出中应包含 `myplugin`。
