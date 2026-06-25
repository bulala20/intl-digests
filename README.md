# 每日国际要闻 · 仪表盘

每日北京时间 8:00 自动抓取数据、生成三联仪表盘并部署为公开静态站点。

**三联仪表盘：**
- **AI 行业晨报** — 调用 [AI HOT](https://aihot.virxact.com) API，汇总近 7 日 AI 圈模型 / 产品 / 行业 / 论文 / 观点五大版块要闻
- **国际金融日报** — 通过 RSS 订阅源抓取全球股市、央行政策、大宗商品、汇率债市与机构观点
- **国际要闻日报** — 聚焦非政治类国际事件：世界杯赛况、科技与太空、自然与气候、国际会议与展会、商业与产业

---

## 项目结构

```
intl-digests/
├── .github/workflows/
│   └── daily.yml              # GitHub Actions 定时任务（每日 8:00 北京时间）
├── scripts/
│   ├── common.py              # 通用模块：RSS 抓取、时间格式化、HTML 模板
│   ├── fetch_ai.py            # AI 日报数据抓取 + 渲染
│   ├── fetch_finance.py       # 国际金融 RSS 抓取 + 分类 + 渲染
│   ├── fetch_affairs.py       # 国际要闻 RSS 抓取 + 分类 + 过滤 + 渲染
│   └── build_index.py         # 首页生成器（三张入口卡片 + 历史归档表）
└── site/                      # 构建产物（自动生成，部署目标）
    ├── index.html             # 首页
    ├── ai/index.html          # AI 仪表盘（当前期）
    ├── finance/index.html     # 金融仪表盘（当前期）
    ├── affairs/index.html     # 要闻仪表盘（当前期）
    ├── data/                  # 各仪表盘 meta.json
    └── archive/
        └── YYYY-MM-DD/        # 按日归档的历史快照
            ├── ai.html
            ├── finance.html
            └── affairs.html
```

---

## 本地运行

依赖：Python 3.10+（仅用标准库，无需安装第三方包）

```bash
cd scripts

# 1. 抓取并生成三个仪表盘
python fetch_ai.py
python fetch_finance.py
python fetch_affairs.py

# 2. 生成首页
python build_index.py
```

打开 `site/index.html` 即可预览整站。

> 说明：脚本统一使用 `common.py` 里的相对路径（`PROJECT_ROOT` 自动定位），所以可以在任意目录执行。

---

## 部署到 Cloudflare Pages（推荐）

### 第 1 步：推送到 GitHub

```bash
cd intl-digests
git init
git add .
git commit -m "init: daily digests site"
git branch -M main
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

### 第 2 步：开启 GitHub Actions

仓库 **Settings → Actions → General**：
- Workflow permissions 选 **Read and write permissions**（自动构建需要写权限提交 `site/` 目录）
- 勾选 Allow GitHub Actions to create and approve pull requests

`.github/workflows/daily.yml` 已配置：
- 触发时机：`cron: '0 0 * * *'`（UTC 0:00 = 北京时间 8:00）+ 手动触发
- 执行：依次跑三个抓取脚本 → 生成首页 → `git commit & push` 回主分支

### 第 3 步：连接 Cloudflare Pages

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com) → Workers & Pages → Create application → Pages → Connect to Git
2. 选择刚推送的 GitHub 仓库
3. 构建配置：
   - **Framework preset**: `None`
   - **Build command**: `cd scripts && python fetch_ai.py && python fetch_finance.py && python fetch_affairs.py && python build_index.py`
   - **Build output directory**: `site`
   - **Root directory**: `/`（留空）
   - **Environment variables**: `PYTHON_VERSION` = `3.12`
4. Save and Deploy

部署成功后会得到一个 `https://<project>.pages.dev` 的公开域名，可自定义域名。

### 第 4 步（可选）：双保险

GitHub Actions 每天定时把数据 commit 到仓库；Cloudflare Pages 检测到 push 会自动重新部署。两边都不依赖对方即可工作：
- Actions 负责"定时抓数据 + 写回仓库"
- Cloudflare 负责"仓库一变就重新发布"

即使 Actions 偶发失败，Cloudflare 仍会发布仓库里最新的 `site/` 内容，不会让线上挂掉。

---

## RSS 源说明

金融和要闻仪表盘使用 RSS 订阅源，部分通过 [RSSHub](https://docs.rsshub.app) 公共实例 `rsshub.app` 聚合。

**公共 RSSHub 实例可能不稳定**（限流、超时）。如遇大面积抓取失败：

1. **自建 RSSHub**（推荐长期方案）：
   ```bash
   docker run -d --name rsshub -p 1200:1200 diygod/rsshub
   ```
   然后把脚本里 `RSSHUB = "https://rsshub.app"` 改成 `http://你的服务器:1200`

2. **替换为官方 RSS**：脚本里已混入 CNBC、Investing.com、NASA、Space.com、FourFourTwo 等官方源，可逐步把 RSSHub 路径替换为各站官方 RSS

3. **添加更多源**：在 `fetch_finance.py` / `fetch_affairs.py` 的 `FEEDS` 列表里追加 `(url, source_name)` 元组即可

---

## 自定义

### 改版块分类关键词

- 金融：`fetch_finance.py` 的 `CLASSIFY_RULES`
- 要闻：`fetch_affairs.py` 的 `CLASSIFY_RULES`

每条规则是 `(分类名, [关键词列表])`，按顺序匹配，第一个命中即归类；都不命中则进 `default` 分类。

### 改配色 / 渐变

每个仪表盘的 Hero 渐变在对应 fetch 脚本的 `render_dashboard(..., gradient=...)` 调用里，meta.json 也存了一份给首页卡片用。

### 改更新频率

编辑 `.github/workflows/daily.yml` 的 `cron` 字段。例如改成每天 4 次：
```yaml
schedule:
  - cron: '0 0,6,12,18 * * *'
```

### 改保留天数

`build_index.py` 的 `render_archive_list()` 里 `[:14]` 控制首页展示多少期归档；实际历史文件不会自动清理（保留越久仓库越大，可按需加清理脚本）。

---

## 常见问题

**Q: GitHub Actions 跑了但没 commit？**
A: 检查 Workflow permissions 是否给了 write 权限；或当日数据无变化（`git diff --staged --quiet` 跳过提交）。

**Q: 某个 RSS 源返回 0 条？**
A: 公共 RSSHub 实例偶发限流。脚本会打印 `[RSS WARN]` 警告但不中断流程，其他源仍正常工作。

**Q: 想加新的仪表盘？**
A: 复制 `fetch_finance.py` 改名，改 `FEEDS` / `SECTION_ORDER` / `SECTION_META` / `CLASSIFY_RULES`，然后在 `build_index.py` 的 `DASHBOARDS` 列表追加一项即可。

---

由 WorkBuddy 自动生成 · 数据源见各仪表盘页脚
