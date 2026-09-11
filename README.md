# pytest-myplugin

一个用于 pytest 二次开发的项目模板，支持通过配置文件管理多个 SDK 服务，并以内置 PyGithub 服务作为示例。

## 项目能力

- `pytest11` 插件入口点，安装后由 pytest 自动加载
- 支持SDK集成，调用API测试
- 集成playwright，支持UI测试
- 测试配置统一管理与加载
- SDK 客户端懒加载、缓存和 session 结束统一关闭
- 使用 pytest 自带 `pytester` 的插件集成测试
- Ruff、coverage 和 wheel/sdist 构建配置

## 初始化开发环境

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## 服务配置

项目配置位于 `config/services.toml`

```toml
[services.github]
base_url = "https://api.github.com"
token = "${GITHUB_TOKEN}"
timeout = 15

# 后续可以继续增加其他 SDK
# [services.gitlab]
# base_url = "https://gitlab.example.com/api/v4"
# token = "${GITLAB_TOKEN}"
# timeout = 30
```

配置文件支持以下环境变量语法：

```text
${GITHUB_TOKEN}          # 必须提供变量，否则加载失败
${GITHUB_TOKEN:-}        # 未设置时替换为空字符串
${GITHUB_TOKEN:-anonymous}
```

真实 token 不应写入仓库。推荐：
```bash
export GITHUB_TOKEN=github_pat_xxx
export GITLAB_TOKEN=glpat_xxx

# 使用额外的本地配置时设置
export TEST_SERVICE_CONFIG=/absolute/path/to/services.local.toml
```

`config/services.local.toml` 已加入 `.gitignore`，适合保存本地非敏感覆盖项。配置加载优先级为：

```text
包内默认配置
-> config/services.toml
-> config/services.local.toml
```

显式传入的配置文件或 `TEST_SERVICE_CONFIG` 会替代上述项目文件继续按顺序合并。

## 在测试中使用

pytest 插件已经注册 `github_client` fixture，测试函数直接声明参数即可：

```python
def test_get_repository(github_client):
    repository = github_client.get_repo("PyGithub/PyGithub")

    assert repository.name == "PyGithub"
```

GitHub 服务已经封装以下常用接口：

- `get_authenticated_user()`
- `get_user(login)`
- `get_repo(full_name_or_id)`
- `get_organization(org)`
- `get_rate_limit()`
- `search_repositories(query, **qualifiers)`
- `close()`

其他 PyGithub 方法会通过 `__getattr__` 自动转发：

```python
def test_emojis(github_client):
    emojis = github_client.get_emojis()

    assert "smile" in emojis
```

需要原生 PyGithub 客户端时使用 `github_client.raw_client`。这些示例会访问真实 GitHub API；



## Playwright UI 测试

项目使用 `pytest-playwright`，测试代码可以直接使用 `page`、`context` 和 `browser` fixture。

首次安装 Playwright 浏览器：

```bash
python -m playwright install chromium
```

运行 UI 测试：

```bash
# 只运行 UI 测试
pytest tests/ui -m ui

# 在已安装的 Google Chrome 中运行
pytest tests/ui -m ui --browser-channel=chrome

# 有界面模式，便于本地调试
pytest tests/ui -m ui --browser-channel=chrome --headed

# 使用其他 Playwright 浏览器前需要先安装对应 browser
pytest tests/ui -m ui --browser firefox
```

[test_github_login.py](tests/ui/test_github_login.py) 会访问真实 GitHub 页面。登录动作封装在 [github_ui.py](src/pytest_myplugin/fixtures/github_ui.py) 的 `github_logged_in_page` fixture 中。

测试假定账号和密码已经配置在运行环境中：

```bash
export GITHUB_UI_USERNAME=your-test-account
export GITHUB_UI_PASSWORD=your-test-password

pytest tests/ui/test_github_login.py -m ui --browser-channel=chrome
```

fixture 完成登录，并校验页面中的 `user-login` 与配置账号一致。凭据不应写入仓库。

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
│       ├── plugin.py
│       ├── bootstrap.py
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
│           ├── registry.py
│           └── github.py
└── tests/
    ├── api/
    │   └── test_github_search_live.py
    └── ui/
        └── test_github_login.py
```

## 新增其他 SDK

以新增 GitLab 为例：

1. 在 `config/services.toml` 和包内默认配置中增加 `[services.gitlab]`。
2. 新建 `src/pytest_myplugin/services/gitlab.py`。
3. 定义 `GitlabSettings`、`GitlabClient` 和 `build_gitlab_client(config)`。
4. 在 `src/pytest_myplugin/bootstrap.py` 中注册：

```python
registry.register("gitlab", build_gitlab_client)
```

5. 新建 `src/pytest_myplugin/fixtures/gitlab.py`：

```python
@pytest.fixture(scope="session")
def gitlab_client(service_manager):
    return service_manager.get("gitlab")
```

6. 在 `src/pytest_myplugin/plugin.py` 中导入该 fixture。

完成后测试代码可以直接使用：

```python
def test_gitlab_project(gitlab_client):
    project = gitlab_client.get_project("group/project")
    assert project.name == "project"
```

## 常用命令

```bash
# 运行测试
pytest

# 显示覆盖率
pytest --cov --cov-report=term-missing

# 代码检查
ruff check .

# 自动修复
ruff check . --fix

# 构建 wheel 和 sdist（默认使用隔离环境）
python -m build

# 本地已经安装构建依赖时，可跳过隔离环境
python -m build --no-isolation
```

## pytest 插件验证

```bash
pytest --myplugin
pytest --myplugin --trace-config
```

`--trace-config` 输出中应包含 `myplugin`。基础配置也可以通过 fixture 获取：

```python
def test_example(myplugin_config):
    assert myplugin_config.version == "0.1.0"
```
