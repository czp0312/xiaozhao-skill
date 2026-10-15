# 常见问题与规避方法

记录实际检索中反复踩到的坑，以及对应的处理协议。写脚本或做批量检索前先看这一页。

## 一、状态码 200 不等于入口可用

招聘站最常见的三种"看起来正常、其实没用"的情况：

| 现象 | 判定 | 原因 | 处理 |
| --- | --- | --- | --- |
| 标题正常，正文几乎为空（< 200 字） | `SHELL` | 页面由前端渲染，静态请求只能拿到外壳 | 用浏览器打开；或改从高校就业网取 JD 正文 |
| 标题是"xxx Resources and Information." | `PARKED` | 域名已停放 / 待售 | 入口作废，重新查找官方招聘站 |
| 落地地址是图片 / 文件（如 `404-graphic_es.png`） | `NONHTML` | 域名过期后被托管商接管，跳转到一张占位图，状态码仍是 200 | 入口作废，重新查找官方招聘站 |
| 打开后跳转到完全不相干的页面 | `PARKED` / `NONHTML` 或人工确认 | 域名过期被抢注 | 同上 |

用 `scripts/check_portals.py` 批量判定，用 `scripts/fetch_jd.py` 判定单个页面并取正文。

判定口径：

- `OK`：能读到正文，可直接使用。
- `SHELL`：页面可打开但读不到正文。**属于正常现象**，不算入口失效，但**不能据此写 JD 结论**。
- `PARKED`：入口失效，需要替换。
- `NONHTML`：落地地址不是网页（图片 / PDF / 压缩包等），通常是域名过期被托管商接管，入口失效，需要替换。
- `BLOCKED`：401/403/405/429/468，反爬或权限拦截，需人工确认。
- `NETERR`：网络不可达、TLS 失败或超时，通常需在国内网络环境重试。

## 二、官方 ATS 静态读不到正文，但可以用无头浏览器读出来

以下招聘系统几乎全部是前端渲染，静态请求只能拿到外壳：

- 飞书招聘：`*.jobs.feishu.cn`、`*.jobs.feishu.cn/campusrecruitment`
- 北森：`*.zhiye.com`
- Moka：`app.mokahr.com`、`app-tc.mokahr.com`

**结论：不要把它们标成「读不到正文」就收工。** 岗位数据就在浏览器渲染出来的 DOM 里，
用无头浏览器打开同一地址即可读到正文。`scripts/_browser.py` 就是干这个的，
`scripts/fetch_jd.py` 遇到 `SHELL` 会自动调用它。

实测（2026-10-15，Chromium 无头渲染）：

| 站点 | 静态请求 | 无头浏览器渲染 |
| --- | --- | --- |
| 智元机器人（飞书招聘） | 0 字 | 约 5 000 字，含岗位职责与职位 ID |
| 宇树科技（北森） | 0 字 | 约 780 字，含各城市在招职位数 |
| 银河通用（Moka 岗位列表页） | 0 字 | 约 39 000 字，含「具身大模型算法工程师-27届」完整职位描述与职位要求 |

用法：

```bash
python scripts/fetch_jd.py <url>              # 静态优先，SHELL 时自动渲染
python scripts/fetch_jd.py <url> --render     # 强制渲染
python scripts/fetch_jd.py <url> --no-render  # 只看静态结果
python scripts/check_portals.py --render      # 批量把可渲染的 SHELL 入口升级为 OK
```

依赖：`pip install playwright && python -m playwright install chromium`。
没装时脚本会降级为静态抓取并给出提示，不会报错退出。

### 为什么不直接逆向它们的接口

Moka 的岗位列表接口返回的是加密串（`{"data":"...","necromancer":"..."}`），
飞书招聘的 `/api/v1/search/job/posts` 对 POST 返回 405。跟着各家的私有接口做解密，
会随前端发版随时失效；渲染 DOM 对所有 ATS 一视同仁，维护成本最低。

### 渲染之后仍要注意

渲染只解决「页面读得到」，不解决「这一页是不是某条 JD 的原文」：

1. 列表页渲染出来的是**多条岗位的合集**，不能直接当某一条 JD 引用；
2. 要拿单条 JD，需再进入岗位详情页（如飞书 `.../position/<id>/detail`、
   Moka `#/job/<id>`）单独渲染；
3. 仍拿不到正文时，按下面的顺序换来源，并标为 `未核验线索`。

## 三、可静态读取正文的 JD 来源（2026-10-15 核验）

高校就业网的岗位详情页大多服务端渲染，能直接读到完整 JD 正文，是校招 JD 最可靠的公开来源。

| 学校 | 站点 | 详情页形态 |
| --- | --- | --- |
| 南开大学 | https://career.nankai.edu.cn/ | `/correcruit/content/id/<数字>.html` |
| 西安电子科技大学 | https://job.xidian.edu.cn/ | `/job/view/id/<数字>` |
| 吉林大学 | https://jdjyw.jlu.edu.cn/ | `/portal/jyzp/job/details?id=<uuid>` |
| 天津工业大学 | https://job.tiangong.edu.cn/ | `/correcruit/content/id/<数字>.html` |
| 河北工业大学 | https://career.hebut.edu.cn/ | `/correcruit/content/id/<数字>.html` |
| 清华大学 | https://career.tsinghua.edu.cn/ | 首页与列表页可读 |
| 上海交通大学 | https://www.job.sjtu.edu.cn/ | 首页与列表页可读 |
| 华中科技大学 | https://job.hust.edu.cn/ | 首页与列表页可读 |
| 山东大学 | https://job.sdu.edu.cn/ | 首页与列表页可读 |

检索建议：用「公司名 + 岗位名 + 年份 + 校园招聘」在搜索引擎中限定站点，命中高校就业网详情页的概率较高。

聚合平台（如各类求职站）可以快速找到 JD 线索，但**必须**回到官方入口或高校就业网复核后再写入主表。

## 四、入口核验与写入流程

1. 抓取候选入口，用 `scripts/fetch_jd.py` 或 `scripts/check_portals.py` 判定。
2. 静态判定为 `SHELL` 的入口，先加 `--render` 用无头浏览器复核一次；能读到正文的按 `OK` 处理。
3. 复核后仍是 `SHELL` 的可以收录为投递入口，但要在说明列注明"需浏览器打开"。
4. 无法核验的放进 `### 待人工确认` 分区，该分区不计入失败统计。
5. 合并入口时用 `scripts/update_portals.py`，它会自动重算「覆盖情况」并做防误删校验。

## 五、Windows / PowerShell 环境注意事项

这些坑在本次调研中都实际发生过，写脚本或做批量改写时务必注意。

- **控制台编码**：Windows 默认不是 UTF-8，Python 直接打印中文会乱码或被截断。脚本统一调用 `_common.configure_utf8_stdio()`；命令行可临时设 `PYTHONIOENCODING=utf-8` 与 `PYTHONUTF8=1`。
- **PowerShell 的反引号是转义字符**：在双引号字符串里，`` `n ``、`` `r `` 会被解释成换行和回车。做文本替换时必须用单引号字符串，否则匹配串会静默变形、替换失败甚至写坏文件。
- **.NET 文件 API 使用进程工作目录**：`[System.IO.File]::ReadAllText("相对路径")` 不跟随 PowerShell 的当前目录，务必传绝对路径。
- **不要用管道把枚举结果传给删除命令**：会触发安全策略拦截。删除请使用明确的字面路径。
- **写文件前先校验**：任何"读全文 → 改 → 写回"的脚本都要先确认新内容仍然完整（入口数量、必需小节），参考 `scripts/update_portals.py` 的 `validate()`。本次调研中曾因一次失败的替换把索引文件写空，这类事故必须靠校验兜住。
- **HTTP 抓取要带 Cookie 容器**：部分招聘站先下发 Cookie 再 302，没有 Cookie 容器会停在跳转页并误判为失效。

## 六、结论书写纪律

- 只有读到 JD 正文的内容才能写成 `事实`；从入口标题、公司官网宣传页推断的内容标为 `推断`。
- 抓不到正文时，不要用模型记忆补全岗位要求。
- 截止时间、内推码、面试轮次这类高时效信息，必须以当次官方页面为准。
