# 常见问题与规避方法

记录实际检索中反复踩到的坑，以及对应的处理协议。写脚本或做批量检索前先看这一页。

## 一、状态码 200 不等于入口可用

招聘站最常见的三种"看起来正常、其实没用"的情况：

| 现象 | 判定 | 原因 | 处理 |
| --- | --- | --- | --- |
| 标题正常，正文几乎为空（< 200 字） | `SHELL` | 页面由前端渲染，静态请求只能拿到外壳 | 用浏览器打开；或改从高校就业网取 JD 正文 |
| 标题是"xxx Resources and Information." | `PARKED` | 域名已停放 / 待售 | 入口作废，重新查找官方招聘站 |
| 打开后跳转到完全不相干的页面 | `PARKED` 或人工确认 | 域名过期被抢注 | 同上 |

用 `scripts/check_portals.py` 批量判定，用 `scripts/fetch_jd.py` 判定单个页面并取正文。

判定口径：

- `OK`：能读到正文，可直接使用。
- `SHELL`：页面可打开但读不到正文。**属于正常现象**，不算入口失效，但**不能据此写 JD 结论**。
- `PARKED`：入口失效，需要替换。
- `BLOCKED`：401/403/405/429/468，反爬或权限拦截，需人工确认。
- `NETERR`：网络不可达、TLS 失败或超时，通常需在国内网络环境重试。

## 二、官方 ATS 基本读不到岗位正文

以下招聘系统几乎全部是前端渲染，静态请求只能拿到外壳，**不要**把它们当 JD 来源：

- 飞书招聘：`*.jobs.feishu.cn`、`*.jobs.feishu.cn/campusrecruitment`
- 北森：`*.zhiye.com`
- Moka：`app.mokahr.com`、`app-tc.mokahr.com`

它们的价值是**投递入口**（收录在 `references/company-portals.md`），不是**JD 正文来源**。

正确做法：

1. 从入口索引拿到官方投递链接；
2. 到高校就业网或聚合平台取 JD 正文；
3. 用公司名 + 岗位名回到官方入口交叉确认岗位确实在招；
4. 无法确认时标为 `未核验线索`。

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
2. 只把 `OK` 的入口写进索引主体；`SHELL` 可收录为投递入口，但要在说明列注明"需浏览器打开"。
3. 无法核验的放进 `### 待人工确认` 分区，该分区不计入失败统计。
4. 合并入口时用 `scripts/update_portals.py`，它会自动重算「覆盖情况」并做防误删校验。

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