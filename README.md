# Shadowrocket AI 规则（源自 v2fly category-ai-!cn）

每天自动把 [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) 的
`data/category-ai-!cn`（连同它 `include:` 的全部子列表）编译成 Shadowrocket 可用的远程规则集，
由 GitHub Actions 定时更新并提交回本仓库。

- 生成物：`dist/category-ai-!cn.list` —— 纯规则行（`DOMAIN-SUFFIX,xxx` / `DOMAIN,xxx` / `DOMAIN-KEYWORD,xxx`），
  不写策略，策略在 Shadowrocket 里添加 RULE-SET 时指定
- 更新频率：每天一次（UTC 22:00 ≈ 北京时间 06:00），也可在 Actions 页手动触发
- 上游无变化时不产生提交，diff 干净

## 仓库结构

```
.
├── .github/workflows/update.yml   # 每天定时抓上游、重新生成并提交
├── scripts/generate_rules.py      # 生成器（仅标准库，无需 pip install）
├── dist/category-ai-!cn.list      # 生成产物（Actions 自动更新）
└── README.md
```

## 部署（三步）

1. 在 GitHub 新建一个**空仓库**（不要勾选初始化 README）。
2. 在本目录执行：

   ```bash
   git init -b main
   git add .
   git commit -m "init: shadowrocket ai rules"
   git remote add origin https://github.com/<你的用户名>/<仓库名>.git
   git push -u origin main
   ```

   （也可以在 GitHub 网页上传全部文件，注意要包含 `.github`、`scripts`、`dist`）
3. 打开仓库 **Actions** 页启用 Workflows，进入 `Update Shadowrocket rules` 点 **Run workflow**
   跑一次，确认 `dist/` 里出现当天生成的文件。

## 规则链接（部署后）

把 `<你的用户名>/<仓库名>` 换成实际值，两条任选：

| 用途 | URL |
| --- | --- |
| GitHub 原始地址（最及时） | `https://raw.githubusercontent.com/<你的用户名>/<仓库名>/main/dist/category-ai-!cn.list` |
| jsDelivr 镜像（raw 直连不通时用，有缓存延迟） | `https://cdn.jsdelivr.net/gh/<你的用户名>/<仓库名>@main/dist/category-ai-!cn.list` |

## 在 Shadowrocket 里添加

1. 底部「配置」→ 点当前配置右侧的 ⓘ → 「规则」
2. 右上角 ＋ → **规则类型**选 `RULE-SET` → **规则策略**选 `PROXY`（或你的代理分组/订阅）
3. 输入框粘贴上面的规则集 URL → 保存
4. 回到「配置」点一次「使用配置」触发编译；可在「编辑配置 → 规则集 URL」查看下载状态（✅/❎）
5. 规则从上到下逐条匹配，遇到即停。需要 AI 流量强制走代理时，把这条 RULE-SET 拖到
   `GEOIP,CN,DIRECT`、`IP-CIDR` 等规则之前
6. 手动更新：再次点「使用配置 / 编译配置」（或「规则集 URL」里点该链接）即可拉取最新版

## 本地生成 / 自定义

```bash
python3 scripts/generate_rules.py                    # 默认 category-ai-!cn
python3 scripts/generate_rules.py --keep-cn          # 保留 @cn 条目
python3 scripts/generate_rules.py --root openai      # 换成任意上游列表（data/ 下的文件名）
# 在交互式 shell 中直接写带 ! 的名称时，建议加引号：
python3 scripts/generate_rules.py --root 'category-ai-!cn'
```

编译规则：

- `include:` 递归展开并去重（多文件同名条目只保留一条）
- 普通域名 → `DOMAIN-SUFFIX`；`full:` → `DOMAIN`；`keyword:` → `DOMAIN-KEYWORD`
- 带 `@cn` 属性的条目默认排除（这类域名国内可直连，应交给直连规则），`--keep-cn` 可保留
- `regexp:` 在 Shadowrocket 中没有对应规则类型，跳过并在日志中告警（数量很少）

## 注意

- GitHub 定时任务 cron 按 **UTC** 计；仓库连续 60 天无提交时 schedule 会被自动停用，
  手动 Run workflow 一次或任何一次 push 即可恢复
- `raw.githubusercontent.com` 在国内部分网络直连不通：小火箭下载规则集前需先有可用节点，
  或换用上面的 jsDelivr 链接
- 规则集只声明「域名 + 类型」、不含策略，换节点/策略组不影响规则集本身
