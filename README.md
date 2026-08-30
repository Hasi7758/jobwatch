# 慕尼黑 · IG Metall 雇主新职位监控(全托管版)

**跑在 GitHub 的免费服务器上,你的电脑不用开机、不用装任何东西。**
每天早上它自动:抓联邦劳动局 + 你配置的公司招聘接口 → 和数据库比对,
找出**首次出现**的职位(所以 StepStone 标错发布日期无所谓)→ 用
IG Metall 雇主名单过滤 → 更新一个固定网址的页面。你每天点开看就行。

---

## 一次性设置(约 15 分钟,全程点鼠标)

### ① 建仓库

github.com 注册/登录 → 右上角 **+** → **New repository** →
名字填 `jobwatch` → 选 **Private**(私有) → **Create repository**。

### ② 传文件

仓库页面 → **Add file → Upload files** → 把这 6 个文件拖进去:

> `jobwatch.py` `import_igm.py` `names.py` `config.yaml`
> `companies.yaml` `README.md`

→ 底部 **Commit changes**。

### ③ 建定时任务

**Add file → Create new file** → 文件名一字不差地输入:

```
.github/workflows/daily.yml
```

→ 把 `GITHUB-WORKFLOW-daily.yml` 里的内容整个复制粘贴进去 →
**Commit changes**。
(为什么要这样:网页拖拽上传经常会丢掉 `.github` 这种隐藏文件夹,
所以单独建。)

### ④ 手动触发第一次

仓库顶部 **Actions** 标签 → 左边点 **daily-jobwatch** →
右边 **Run workflow** → 绿色按钮确认。

等两三分钟,任务变绿勾就成了。这一次它会:自动去
arbeitgeberliste.netlify.app 把 IG Metall 名单导下来(存成
`igmetall.yaml`)、把当前所有在线职位收作**基线**。

### ⑤ 开结果页

**Settings → Pages** → Source 选 **Deploy from a branch** →
Branch 选 `main`、文件夹选 **/docs** → **Save**。

一两分钟后你的页面就在:

```
https://你的用户名.github.io/jobwatch/
```

手机浏览器收藏它。**从明天起,这个页面每天自动更新,只显示最近
7 天内新发布的职位**,按天分组,IG Metall 雇主带绿标。完事。

---

## 之后唯一要做的事

**改关键词。** `config.yaml` 里现在是一套示例关键词(软件/数据/工程/
实习),多半不是你的方向。在 GitHub 网页上就能改:打开 `config.yaml` →
右上角铅笔图标 → 编辑 `keywords.include` → Commit。下次运行自动生效。

写德语词根即可:`ingenieur` 能命中 `Wirtschaftsingenieur (m/w/d)`。
IG Metall 是金属电气行业,`mechatronik` `konstruktion` `fertigung`
`elektrotechnik` `qualität` 这类词会很有用。

前几天建议顺手做两件小事(都在网页上点几下):

- 抽查绿标:鼠标悬停能看到它匹配到名单上哪家公司,确认没乱认。
- 该出现却没出现的公司,补进 `config.yaml` 的 `employers.aliases`
  (常见于缩写,比如名单写 BMW AG、劳动局写 Bayerische Motoren Werke——
  这条我已预置)。

---

## 可选增强

**手机推送(Telegram,5 分钟)**:Telegram 里找 `@BotFather` 发
`/newbot` 拿到 token;找 `@userinfobot` 拿到你的数字 id。然后仓库
**Settings → Secrets and variables → Actions → New repository secret**,
建两条:`TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID`。下次起有新职位
就直接推到你手机,页面照常更新。

**公司直连(这才是"最早")**:公司在自家官网发布通常比任何平台早
3~14 天。在自己电脑上(装 Python 的前提下)跑:

```bash
python jobwatch.py discover knorrbremse webasto brainlab ...
```

探到的粘进 `companies.yaml` 提交即可。IG Metall 名单里的大厂很多用
Workday,探测器测不到,需要手工拿接口:公司招聘页 → F12 → Network →
翻一页 → 找名为 `jobs` 的 POST 请求 → 复制 URL,按 `companies.yaml`
里的 workday 格式填。没有电脑也可以跳过这步,劳动局源照样每天工作。

**跑得更勤**:编辑 `daily.yml` 里的 cron,比如 `"20 5,11,17 * * *"`
一天三次。重复职位自动去重,不会重复打扰。

---

## 出问题看哪里

Actions 标签页能看到每次运行的完整日志。常见情况:

| 日志里出现 | 含义 / 处理 |
|---|---|
| `IG Metall 名单自动导入失败` | 那个站的结构猜不出来。手动:浏览器打开该站 → F12 → Network → 刷新 → 最大的 `.json` → Copy response → 在仓库里新建 `igm_raw.json` 粘贴进去,然后把 daily.yml 中导入命令改为 `python import_igm.py file igm_raw.json --region bayern`。或者把那个 json 的前几条发给 Claude 帮你改解析。 |
| 劳动局 HTTP 404 | 官方接口路径变了。查 api.bund.dev 上 Jobsuche 文档,改 `jobwatch.py` 里的 `AA_URL`。 |
| 白名单开着但命中 0 条 | 导入时 `--region bayern` 可能过滤过头(名单字段里没写地区)。把 daily.yml 里的 `--region bayern` 去掉,删除仓库里的 `igmetall.yaml`,重新 Run workflow。 |
| 页面好几天不变 | 看 Actions 是否红叉;另外 GitHub 定时任务延迟一小时内属正常。 |
| 想清零重来 | 删除仓库里的 `jobs.db`,下次运行重建基线。 |

---

## 两点务必知道

**名单上有 ≠ 岗位一定是 Tarif 岗。** 德国常见母公司有 Tarifbindung、
子公司/服务公司没有,或者 OT-Mitgliedschaft(入会但不受约束)。白名单
是高质量筛子,不是保证;面试时问清楚岗位挂在哪个法律实体、适用哪份
Tarifvertrag。

**接口细节以 2026 年 5 月为准。** 之后劳动局或那个名单站如果改版,
看上面的排查表处理;代码所有字段读取都做了容错,不会整个崩掉。
