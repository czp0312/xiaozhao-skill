# 信息源与核验系统

用于当前岗位、投递链接、截止时间、公司招聘流程和招聘状态查询。

## 信息源分级

### S 级：官方直接来源

可作为最终依据：

- 公司招聘官网；
- 公司校园招聘或实习招聘站；
- 官方岗位详情页；
- 官方招聘公众号文章或官方招聘社媒账号；
- 官方公开 FAQ、小程序、招聘机器人。

### A 级：官方授权或近官方来源

确认公司归属后可作为最终依据：

- Moka 企业招聘页；
- 北森 / Hotjob 企业招聘页；
- 猎聘、智联等官方校招项目页；
- 公司自有 `career`、`jobs`、`campus`、`talent` 域名。

页面必须展示公司、岗位详情和直接投递路径。

### B 级：线索来源

只用于发现线索，不能直接作为主表依据：

- 牛客、实习僧、BOSS 直聘、拉勾、应届生求职网；
- 小红书、知乎、脉脉；
- 微信搜索结果；
- 社区表格、语雀、飞书文档。

如果找不到官方或近官方来源，将该条单独标为 `未核验线索`。

### C 级：不直接采用

默认不使用：

- 没有可追溯来源的截图；
- 没有投递链接的个人整理；
- 旧招聘季文章；
- 付费群、引流帖、营销漏斗。

## 时效性核验

遇到以下问题必须核验时效：

- “现在”“最新”“还在招吗”“截止了吗”；
- 岗位清单；
- 投递链接；
- 公司或岗位是否开放；
- 当前机会对比。

状态规则：

- `active`：官方页面开放、有可投递入口，或截止时间未过。
- `expired`：截止时间已过、页面显示关闭、岗位下线或投递按钮不可用。
- `unknown`：当前官方页面存在，但未公开截止时间或状态。
- `unverified_lead`：只有线索来源，或官方来源无法访问。

## 岗位记录字段

将每个岗位整理为以下字段：

```text
company_name
role_title
role_family
recruiting_type
target_graduation
locations
deadline
apply_url
source_url
source_level
source_name
posted_at
verified_at
job_description
requirements
status
confidence_note
```

日期能确定时使用 `YYYY-MM-DD`；没有公开截止时间时填空或 `null`，不要猜。

## 岗位族

```text
frontend
backend
client
fullstack
ai_app
llm_app
algorithm
machine_learning
data_engineering
data_analysis
test_development
sre
security
game_development
graphics
embedded
hardware_software
other_technical
non_technical
```

## 招聘类型

```text
campus
internship
daily_internship
summer_internship
spring_recruitment
fall_recruitment
early_batch
off_cycle
unknown
```

## 搜索顺序

1. 公司招聘官网。
2. 公司校园招聘或实习招聘页。
3. 官方招聘账号和官方公告。
4. 官方 ATS 页面。
5. 搜索引擎定向查询。
6. 聚合平台和社区线索。
7. 回到官方或近官方来源复核。

常用查询：

```text
公司名 校招 官网
公司名 实习生招聘 官网
公司名 2026 校招 技术岗
公司名 2027 实习 前端
公司名 AI 应用开发 实习
site:app.mokahr.com/campus-recruitment 公司名 前端 实习
site:hotjob.cn 公司名 校招
```

## 去重规则

比较前先标准化：

- 移除 `utm_*`、`spm`、`from`、`source`、`token` 等链接追踪参数；
- 统一公司别名；
- 将城市分隔符统一为 `、`；
- 按岗位族比较，不只看岗位标题原文；
- 统一招聘对象，如 `26届`、`27届`、`日常实习`、`暑期实习`。

判定为重复：

- 同公司、同岗位族、同招聘对象且城市重叠；
- 同一个岗位详情链接；
- 同一个官方项目下的同一岗位。

不判定为重复：

- 不同招聘批次；
- 不同岗位族；
- 同公司同岗位但明确为不同城市的独立岗位。

## 来源状态标签

输出时使用：

```text
官方已核验
近官方已核验
状态不明
未核验线索
已过期
```

正式岗位表通常只放 `官方已核验`、`近官方已核验` 和已解释的 `状态不明`。
