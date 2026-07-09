# Auto-Research Plugin · 自动研究插件

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-blue)](https://claude.ai/code)

> **让 Claude Code 遇到不确定问题时，自动问 ChatGPT / 搜索网页，整理方案后等你拍板再动手。**
>
> Automatically research via ChatGPT (Playwright) or web search when uncertain — present options, wait for your approval, then code.

---

## 🎬 效果演示

```
用户: ? PyTorch 中自定义 ADMM 优化器怎么设计
Claude: [自动打开 ChatGPT → 输入问题 → 抓取回答 → 整理方案]
Claude: GPT 建议方案 A，原因是 X Y Z。要继续实现吗？
用户: 行
Claude: [开始写代码]
```

---

## 🔧 触发词 / Triggers

| 输入 | 行为 |
|------|------|
| `?` | **确认去问 ChatGPT** — 把当前问题用 Playwright 打开 GPT 去问 |
| `??` | **搜索引擎调研** — WebSearch/WebFetch 查资料 |

---

## 📦 安装 / Installation

### Prerequisites

**1. 安装 Playwright 浏览器扩展（一次性）**

在 Edge 中打开，点击 "添加到 Edge" / "Add to Edge"：

> https://chromewebstore.google.com/detail/playwright-extension/mmlmfjhmonkocbjadbfplnigmagldckm

Chrome 用户同理，点击 "添加至 Chrome"。

**2. 安装本插件**

```bash
# GitHub 克隆安装
git clone https://github.com/zyu51847-maker/Diooo.git auto-research-plugin
claude plugins install ./auto-research-plugin
```

**3. 批准 MCP Server**

首次使用 Claude Code 会提示批准 Playwright MCP — 点 Allow 即可，一次批准全局生效。

---

## 🛠️ 工作原理 / How It Works

| 组件 | 说明 |
|------|------|
| **Playwright MCP** | 通过浏览器扩展直连 Edge/Chrome，自动携带登录态和 Cookie |
| **ChatGPT** | ProseMirror 编辑器交互，`keyboard.type()` 输入，`data-testid="send-button"` 提交 |
| **WebSearch** | 搜索引擎查博客、论文、开源项目 |
| **WebFetch** | 抓取具体网页提炼关键信息 |

全程在浏览器窗口可见，用户监控每一步操作。

---

## 📁 插件结构 / Structure

```
auto-research-plugin/
├── .claude-plugin/
│   └── plugin.json          # 插件元数据 + MCP 声明
├── skills/
│   └── auto-research/
│       └── SKILL.md         # 核心行为规则
├── .mcp.json                # Playwright MCP 参考配置
├── package.json             # npm 打包信息
└── README.md                # 本文件
```

---

## 🚀 进阶安装 / Advanced

从 GitHub 直接安装到全局：

```bash
claude plugins install https://github.com/zyu51847-maker/Diooo.git
```

或手动配置 MCP（不装插件，只配 MCP server）：

```bash
claude mcp add playwright -s user -- npx -y @playwright/mcp@latest --extension --browser msedge
```

---

## 🌐 让别人发现 / Discovery

- [Claude Code Plugin Marketplace](https://claude.ai/code)
- [MCP Server Directory](https://glama.ai/mcp)
- [MCP Server Directory 2](https://mcpserver.so)

---

## 📄 License

MIT
