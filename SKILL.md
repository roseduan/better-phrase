---
name: better-phrase
description: Better Phrase — English phrasing polish for Claude Code users. A UserPromptSubmit hook detects English in the user's prompt and prepends a Chinese-explained polish block (grammar + word choice + idiomatic rewrite) before the main response. Zero token cost on Chinese-only or code-only inputs.
---

# Better Phrase

把英语老师装进 Claude Code。每次你输入英文,自动在响应前面给你一段语法 / 用词 / 地道说法的小 tip,中文讲解,然后才回答你原本的问题。

> ✏️ **English tip:**
> - "I very like" → "I really like" — *very* 不能直接修饰动词。
> - "open the light" → "turn on the light" — 开灯用 *turn on*,不用 *open*。
>
> ✍️ **Better version:** "I really like coding with Claude — turn on the lights, start typing, and it just works."

## 它是怎么工作的

```
你输入 prompt
     ↓
Claude Code 触发 UserPromptSubmit hook
     ↓
better-phrase.sh (bash 启动器)
     ↓
python3 -m better_phrase hook
     ├─ 剥掉 fenced code block / inline backticks / slash-bang 命令行
     ├─ 数 2+ 字母的英文词数(< 3 个直接跳过)
     ├─ 检查是否含英文功能词(过滤纯标识符)
     ↓
若判定为英文 → 输出 additionalContext 指令
     ↓
主模型同时拿到:
  - 你原本的 prompt
  - "先给一段英语 tip,再正常回答"的指令
     ↓
返回:tip block + 正常回答
```

非英文 / 代码 / 纯命令 → 静默退出 0,**零 token 成本**。

## 为什么用 hook 而不是 CLAUDE.md 指令

| | 把规则写进 CLAUDE.md | 用 Better Phrase hook |
|---|---|---|
| Token 成本 | **每条**消息都加载完整规则 | 只在**检测到英文**时才注入 |
| 触发判定 | 模型自己判断(易误触发 / 漏触发) | Python 预先过滤,确定性 |
| 中文消息 | 仍占用 token | 0 token,完全跳过 |
| 代码 / 命令 | 容易误判 | 提前剥掉 |

## 技术要求

- Claude Code
- Python 3.9+(macOS / 多数 Linux 自带,纯 stdlib 不需要额外依赖)

## 隐私

完全本地运行。脚本不向任何外部服务发送数据。源码就在 `better_phrase/` 下,100 多行 Python 直接读自查。

## 安装(两种方式都能用)

**A. 通过 skills.sh:**
```bash
npx skills add roseduan/better-phrase
```

**B. 仓库自带的安装脚本(不走 skills.sh):**
```bash
git clone https://github.com/roseduan/better-phrase.git
cd better-phrase
./install.sh
```

两种方式效果完全一样,只是注册 hook 的方式不同。

## 卸载

- `npx skills` 安装的 → `npx skills remove better-phrase`
- `./install.sh` 安装的 → `./uninstall.sh`

## 配置

**唯一用户开关:中文翻译是否开启**(默认开)。英文润色是产品核心功能,**始终在线**——要全关请 `./uninstall.sh`。

```bash
# 从仓库根目录执行:
PYTHONPATH=. python3 -m better_phrase translate          # 查看当前状态
PYTHONPATH=. python3 -m better_phrase translate off      # 关闭中文翻译
PYTHONPATH=. python3 -m better_phrase translate on       # 重新开启
```

配置存在 `~/.better-phrase/config.json`。

### 行为对照

| 输入类型 | translate=on(默认) | translate=off |
|---------|---------------------|---------------|
| 英文 | ✏️ English tip + Better version | ✏️ English tip + Better version |
| 中文 | 🌐 English: "..." | 静默 |
| 中英混合(中文为主) | 🌐 翻译块 | 看是否有足够英文,有就润色,没有就静默 |
| 中英混合(英文为主) | ✏️ tip 模板 | ✏️ tip 模板 |
| 代码 / 命令 | 静默 | 静默 |

### 高级:模板和阈值
如果你想自己调:
- 触发阈值(默认英文词数 ≥ 3、中文字符 ≥ 5)→ 编辑 `better_phrase/detector.py`
- 润色 / 翻译模板 → 编辑 `better_phrase/prompts.py`

## 路线图

- [x] V0.2:Python 重写 + 单测覆盖 + skills.sh 兼容
- [ ] V0.3:本地 SQLite 错误档案 + `better-phrase stats` 子命令
- [ ] V0.4:SRS 间隔复习 + 周报
- [ ] V0.5:中式英语 pattern 库(中式英语专项检测)
- [ ] V1.0:跨工具支持(Cursor / VSCode / Chrome 扩展共享错误档案)

## License

Apache License 2.0
