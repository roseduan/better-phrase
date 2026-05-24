<div align="center">

# Better Phrase

**润色你的英文措辞,装进 Claude Code。**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

[English](README.md) · **中文**

</div>

---

## 演示效果

写英文时:

> ✏️ **English tip:**
> - "I very like" → "I really like" — *very* 不能直接修饰动词。
> - "open the light" → "turn on the light" — 开灯用 *turn on*。
>
> ✍️ **Better version:** "I really like coding with Claude — turn on the lights, start typing, and it just works."

写中文时:

> 🌐 **English:**
> "I'd like to schedule a meeting with the client next Tuesday to go over the contract details."

写代码、敲命令、或者不需要翻译的中文 — **完全静默**,0 token,0 干扰。

## 这是什么

**Better Phrase** 是一个 Claude Code 插件,做的事很简单:
- 写英文时,挑出语法 / 用词 / 地道说法的问题
- 写中文时,顺便给你一段地道的英文版(可关)
- 其他场景(写代码、敲命令、不需要翻译的中文)**完全静默**

## 跟在 CLAUDE.md 里写规则有什么区别

| | CLAUDE.md 规则 | Better Phrase |
|---|---|---|
| Token 成本 | **每条**消息都加载完整规则(~400 token) | 只在**真正触发时**才注入 |
| 触发判定 | 模型自己判断(易遗忘 / 误触发) | 确定性判断,100% 一致 |
| 纯中文 / 代码 | 仍占用 token | **0 token**,完全静默 |

**结果:全天用下来 token 成本降低 5–10 倍,触发可靠性更高。**

核心 thesis:**布尔决策属于代码,不属于 LLM**。LLM 该用在生成上(写 tip / 翻译),不该用在判断"是不是英文"这种简单分类上。

## 特性

- ✏️ **英文润色** — 语法 / 词汇 / 表达地道度修正 + native rewrite
- 🌐 **中文 → 英文翻译** — 地道英文版(可开关)
- 🎯 **零干扰** — 代码 / 命令 / 不相关输入完全不触发
- 🇨🇳 **中文讲解** — tip 用中文解释,聚焦常见**中式英语**模式
- 🚀 **启动开销可忽略** — 相对 Claude 自身的响应延迟完全感知不到
- 🔒 **100% 本地** — 无 API 调用,无遥测,数据永不出本机

## 系统要求

- [Claude Code](https://docs.claude.com/en/docs/claude-code) 已经装好并能正常使用
- **Python 3.9+**(macOS / 多数 Linux 默认自带)
- **jq** — 仅"方式 B"安装脚本需要(用来安全编辑 `~/.claude/settings.json`)
  - macOS: `brew install jq`
  - Linux: `sudo apt install jq`(或对应发行版)

## 安装

两种方式任选其一,结果一样:都是给 Claude Code 注册一个 `UserPromptSubmit` hook。

### 方式 A:通过 skills.sh(推荐)

```bash
npx skills add roseduan/better-phrase
```

把这个 skill 加入 Claude Code 的 skill 注册表,hook 自动接好。如果你本来就在用 `skills.sh` 管理 skill,选这个。

### 方式 B:仓库自带安装脚本

把仓库克隆到一个**长期保留**的目录(安装脚本会让 Claude Code 指向本地脚本,删掉文件夹 hook 就坏了)。

```bash
git clone https://github.com/roseduan/better-phrase.git ~/.claude/skills/better-phrase
cd ~/.claude/skills/better-phrase
./install.sh
```

安装脚本做的事:

1. 检查 `~/.claude/` 存在,以及 `python3` / `jq` 都可用
2. 备份你现有的 `~/.claude/settings.json`(带时间戳)
3. 往 `hooks.UserPromptSubmit` 加一条指向 `better-phrase.sh` 的入口
4. 清理掉之前装过的旧版本 hook 入口(如有)

### 验证安装

1. **重启 Claude Code**(或开新 session),让它重新加载 settings
2. 输入任意一句英文,例如 `how are you today`
3. 应该会在正常回答之前看到 `✏️ English tip` 块

如果没出现,检查 `~/.claude/settings.json` 里 `hooks.UserPromptSubmit` 下面是否有指向 `better-phrase.sh` 的入口。

### 卸载

- 用 `npx skills add` 装的 → `npx skills remove better-phrase`
- 用 `./install.sh` 装的 → 在仓库目录跑 `./uninstall.sh`

卸载脚本会移除 `~/.claude/settings.json` 里的 hook 入口(需要时从备份还原)。仓库文件夹本身**不会被删**,如果不再需要可以手动删除。

## 配置

只有**一个**用户开关:中文 → 英文翻译是否开启(默认开)。

英文润色是产品核心价值,**始终在线**。如果想全部禁用,跑 `./uninstall.sh`。

```bash
# 从仓库根目录执行:
PYTHONPATH=. python3 -m better_phrase translate           # 查看
PYTHONPATH=. python3 -m better_phrase translate off       # 关闭中文翻译
PYTHONPATH=. python3 -m better_phrase translate on        # 重新开启
```

### 耗时显示

每个 BP 块结尾会附一行 footer,显示这次 hook 步骤的耗时:

```
*(⏱ Better Phrase: 21ms hook)*
```

可以随时切换:

```bash
PYTHONPATH=. python3 -m better_phrase timing              # 查看状态
PYTHONPATH=. python3 -m better_phrase timing off          # 隐藏 footer
PYTHONPATH=. python3 -m better_phrase timing on           # 重新开启
```

### 行为对照表

| 输入 | `translate=on`(默认) | `translate=off` |
|------|-----------------------|-----------------|
| 英文 | ✏️ English tip | ✏️ English tip |
| 中文 | 🌐 English version | (静默) |
| 中英混合(中文为主) | 🌐 English version | 有足够英文 → 润色,否则静默 |
| 中英混合(英文为主) | ✏️ English tip | ✏️ English tip |
| 代码 / 命令 | (静默) | (静默) |

## 已知局限

Better Phrase 看到的是 prompt 离开键盘之后的最终文本——Claude Code 不会把粘贴元信息透传过来,所以**无法区分"键入"和"粘贴"**。

为了缓解:

- **Tail-only 启发式**:当输入末尾一段明显比正文短时(末尾 ≤ 50 字、正文 ≥ 100 字),Better Phrase 只分析末尾那段。覆盖了"粘贴一大坨 + 自己写一句"的常见 case。
- **完全跳过机制**:用 ``` ``` 三重反引号包裹的内容,会被**完全剥离**,不进入语言检测:

      ```
      <你粘贴的、不想被分析的内容放在这里>
      ```

      你真正的问题

  fenced block 在所有 detection 之前就剥掉了。

两条加起来覆盖大约 90% 的场景。完美的粘贴感知需要 IDE 集成(V1.0 规划中)。

## 隐私

- **100% 本地执行**,无外部 API,无遥测,无分析
- 你的 prompt / 修改建议永不出本机
- 未来的错误档案存在 `~/.better-phrase/`,归你所有(V0.3 规划)

## 路线图

- [x] **V0.1** — 初版发布
- [x] **V0.2** — 中文翻译开关
- [ ] **V0.3** — 本地错误档案 + `better-phrase stats` 子命令
- [ ] **V0.4** — SRS 间隔复习(复盘历史错误)
- [ ] **V0.5** — 中式英语 pattern 库(中式英语专项检测)
- [ ] **V1.0** — 跨工具支持(Cursor / VS Code / Chrome 扩展共享错误档案)

## License

Apache License 2.0 — 详见 [LICENSE](LICENSE)。

---

<div align="center">

**如果 Better Phrase 帮你写出更地道的英文,欢迎给个 Star ⭐。**

</div>
