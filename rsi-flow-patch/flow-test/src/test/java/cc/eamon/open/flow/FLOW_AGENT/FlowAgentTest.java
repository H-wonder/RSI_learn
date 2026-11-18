package cc.eamon.open.flow.FLOW_AGENT;

import cc.eamon.open.flow.agent.FinalActionNode;
import cc.eamon.open.flow.agent.FinalActionRegistry;
import cc.eamon.open.flow.agent.ToolRegistry;
import cc.eamon.open.flow.agent.VerifierNode;
import cc.eamon.open.flow.config.constants.FlowConstants;
import cc.eamon.open.flow.core.FlowEngine;
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

public class FlowAgentTest {

    @Test
    public void toolNodeFlow() throws Exception {
        ToolRegistry.register("demo.echo", new cc.eamon.open.flow.agent.ToolHandler() {
            @Override
            public String execute(String argumentsJson) {
                return "echo:" + argumentsJson;
            }
        });
        try {
            String result = (String) FlowEngine.instance()
                    .register("toolName", "demo.echo")
                    .register("argumentsJson", "{\"x\":1}")
                    .register("resultName", "toolResult")
                    .run("FLOW_AGENT_TOOL")
                    .retrieve(FlowConstants.SCOPE_DEFAULT, "toolResult");
            Assert.assertEquals(result, "echo:{\"x\":1}");
        } finally {
            FlowEngine.instance().release();
            ToolRegistry.clear();
        }
    }

    @Test
    public void llmNodeFlow() throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/v1/chat/completions", new HttpHandler() {
            @Override
            public void handle(HttpExchange exchange) throws IOException {
                consume(exchange.getRequestBody());
                byte[] body = "{\"choices\":[{\"message\":{\"content\":\"hello from mock\"}}]}"
                        .getBytes(StandardCharsets.UTF_8);
                exchange.getResponseHeaders().add("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, body.length);
                OutputStream out = exchange.getResponseBody();
                out.write(body);
                out.close();
            }
        });
        server.start();
        System.setProperty("flow.llm.baseUrl", "http://127.0.0.1:" + server.getAddress().getPort() + "/v1");
        System.setProperty("flow.llm.apiKey", "test-key");
        try {
            String result = (String) FlowEngine.instance()
                    .register("requestJson", "{\"prompt\":\"hi\",\"model\":\"mock\"}")
                    .register("resultName", "llmResult")
                    .run("FLOW_AGENT_LLM")
                    .retrieve(FlowConstants.SCOPE_DEFAULT, "llmResult");
            Assert.assertEquals(result, "hello from mock");
        } finally {
            System.clearProperty("flow.llm.baseUrl");
            System.clearProperty("flow.llm.apiKey");
            server.stop(0);
            FlowEngine.instance().release();
        }
    }

    @Test
    public void finalActionAndVerifier() throws Exception {
        FinalActionRegistry.register("notify", new cc.eamon.open.flow.agent.FinalActionHandler() {
            @Override
            public String execute(String payloadJson) {
                return "sent:" + payloadJson;
            }
        });
        try {
            new FinalActionNode().execute("notify", "{\"to\":\"ops\"}", "finalResult");
            String sent = (String) FlowEngine.instance().retrieve("finalResult");
            Assert.assertEquals(sent, "sent:{\"to\":\"ops\"}");

            new VerifierNode().verify("alpha beta gamma", "[\"alpha\",\"gamma\"]", "verifyResult");
            JSONObject ok = JSON.parseObject((String) FlowEngine.instance().retrieve("verifyResult"));
            Assert.assertTrue(ok.getBooleanValue("passed"));
            Assert.assertTrue(ok.getJSONArray("missing").isEmpty());

            new VerifierNode().verify("alpha", "[\"alpha\",\"delta\"]", "verifyResult");
            JSONObject bad = JSON.parseObject((String) FlowEngine.instance().retrieve("verifyResult"));
            Assert.assertFalse(bad.getBooleanValue("passed"));
            Assert.assertEquals(bad.getJSONArray("missing").getString(0), "delta");
        } finally {
            FinalActionRegistry.clear();
            FlowEngine.instance().release();
        }
    }

    @Test
    public void ruleFilterAudit() throws Exception {
        try {
            new cc.eamon.open.flow.agent.RuleNode().eval(
                    "{\"tier\":\"Enterprise\",\"amount\":156000}",
                    "tier == 'Enterprise' && amount > 100000",
                    "ruleResult");
            Assert.assertEquals(String.valueOf(FlowEngine.instance().retrieve("ruleResult")), "true");

            new cc.eamon.open.flow.agent.FilterNode().filter(
                    "[{\"status\":\"Active\",\"amount\":100},{\"status\":\"Closed\",\"amount\":200}]",
                    "status", "equals", "Active", "filterResult");
            String filtered = (String) FlowEngine.instance().retrieve("filterResult");
            Assert.assertTrue(filtered.contains("Active"));
            Assert.assertFalse(filtered.contains("Closed"));

            cc.eamon.open.flow.agent.AuditStore.clear();
            new cc.eamon.open.flow.agent.AuditNode().record("S0", "{\"ok\":true}", "auditJson");
            new cc.eamon.open.flow.agent.AuditNode().record("S1", "{\"ok\":true}", "auditJson");
            String audit = (String) FlowEngine.instance().retrieve("auditJson");
            Assert.assertTrue(audit.contains("\"S0\""));
            Assert.assertTrue(audit.contains("\"S1\""));
        } finally {
            cc.eamon.open.flow.agent.AuditStore.clear();
            FlowEngine.instance().release();
        }
    }

    @Test
    public void rowsAndWhereNodes() throws Exception {
        try {
            String table = "{\"values\":[[\"Unit ID\",\"Status\",\"Last Load Test\","
                    + "\"Test Frequency\"],"
                    + "[\"GEN-01\",\"Active\",\"2026-01-08\",\"Monthly\"],"
                    + "[\"GEN-03\",\"Under Repair\",\"2025-12-15\",\"Monthly\"],"
                    + "[\"GEN-07\",\"Active\",\"2025-10-20\",\"Quarterly\"],"
                    + "[\"GEN-08\",\"Active\",\"2026-01-02\",\"Monthly\"]]}";
            new cc.eamon.open.flow.agent.RowsNode().toRows(table, "rowsJson");
            String rows = (String) FlowEngine.instance().retrieve("rowsJson");
            JSONObject first = JSON.parseArray(rows).getJSONObject(0);
            Assert.assertEquals(first.getString("Unit ID"), "GEN-01");
            Assert.assertEquals(first.getString("Status"), "Active");

            String expression =
                    "Status != 'Under Repair' && Last_Load_Test <= cutoff"
                            + " && ((Test_Frequency == 'Monthly' && cutoff == '2026-01-24')"
                            + " || (Test_Frequency == 'Quarterly' && cutoff == '2025-11-24'))";
            new cc.eamon.open.flow.agent.WhereNode().filter(
                    rows, expression, "{\"cutoff\":\"2026-01-24\"}", "whereJson");
            String monthly = (String) FlowEngine.instance().retrieve("whereJson");
            Assert.assertTrue(monthly.contains("GEN-01"));
            Assert.assertTrue(monthly.contains("GEN-08"));
            Assert.assertFalse(monthly.contains("GEN-03"));
            Assert.assertFalse(monthly.contains("GEN-07"));

            new cc.eamon.open.flow.agent.WhereNode().filter(
                    rows, expression, "{\"cutoff\":\"2025-11-24\"}", "whereJson");
            String quarterly = (String) FlowEngine.instance().retrieve("whereJson");
            Assert.assertFalse(quarterly.contains("GEN-01"));
            Assert.assertTrue(quarterly.contains("GEN-07"));
            Assert.assertFalse(quarterly.contains("GEN-03"));
        } finally {
            FlowEngine.instance().release();
        }
    }

    private static void consume(InputStream input) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buffer = new byte[1024];
        int read;
        while ((read = input.read(buffer)) != -1) {
            out.write(buffer, 0, read);
        }
    }

}
