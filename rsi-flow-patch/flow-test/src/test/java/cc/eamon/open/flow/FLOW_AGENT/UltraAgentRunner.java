package cc.eamon.open.flow.FLOW_AGENT;

import cc.eamon.open.flow.agent.AuditStore;
import cc.eamon.open.flow.agent.BridgeScoreHandler;
import cc.eamon.open.flow.agent.BridgeToolHandler;
import cc.eamon.open.flow.agent.FinalActionRegistry;
import cc.eamon.open.flow.agent.ToolRegistry;
import cc.eamon.open.flow.core.FlowEngine;
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.concurrent.TimeUnit;

/**
 * Runs FLOW_AGENT_ULTRA against a running world_bridge.py.
 *
 * Usage:
 *   java -Dbridge.url=http://127.0.0.1:8765 \
 *        -Dtask.name=sales.multi_hop_lookup \
 *        -Dresult.path=/tmp/ultra-result.json \
 *        -cp ... UltraAgentRunner
 */
public class UltraAgentRunner {

    private static final OkHttpClient CLIENT = new OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(120, TimeUnit.SECONDS)
            .build();

    public static void main(String[] args) throws Exception {
        String bridge = System.getProperty("bridge.url", "http://127.0.0.1:8765");
        String taskName = System.getProperty("task.name", "sales.multi_hop_lookup");
        String flowId = System.getProperty("flow.id", "FLOW_AGENT_ULTRA");
        String resultPath = System.getProperty("result.path", "/tmp/ultra-result.json");

        JSONObject task = getJson(bridge + "/task");
        String prompt = task.getString("prompt");

        ToolRegistry.register("api_search", new BridgeToolHandler(bridge, "api_search"));
        ToolRegistry.register("api_fetch", new BridgeToolHandler(bridge, "api_fetch"));
        ToolRegistry.register("base64_encode", new BridgeToolHandler(bridge, "base64_encode"));
        ToolRegistry.register("bridge_score", new BridgeScoreHandler(bridge));
        FinalActionRegistry.register("finalize", payload -> "finalized");

        AuditStore.clear();
        try {
            FlowEngine.instance()
                    .register("taskPrompt", prompt)
                    .register("taskName", taskName)
                    .run(flowId);

            Object audit = FlowEngine.instance().retrieve("auditJson");
            String score = getText(bridge + "/score");
            JSONObject output = new JSONObject();
            output.put("task", taskName);
            output.put("audit", audit == null ? "" : String.valueOf(audit));
            output.put("score", JSON.parseObject(score));
            Files.write(
                    Paths.get(resultPath),
                    output.toJSONString().getBytes(StandardCharsets.UTF_8));
            System.out.println("RESULT " + output.toJSONString());
        } finally {
            FlowEngine.instance().release();
            ToolRegistry.clear();
            FinalActionRegistry.clear();
            AuditStore.clear();
        }
    }

    private static JSONObject getJson(String url) throws Exception {
        return JSON.parseObject(getText(url));
    }

    private static String getText(String url) throws Exception {
        Request request = new Request.Builder().url(url).get().build();
        Response response = CLIENT.newCall(request).execute();
        try {
            String body = response.body() == null ? "" : response.body().string();
            if (!response.isSuccessful()) {
                throw new IllegalStateException("HTTP " + response.code() + ": " + body);
            }
            return body;
        } finally {
            response.close();
        }
    }

}
