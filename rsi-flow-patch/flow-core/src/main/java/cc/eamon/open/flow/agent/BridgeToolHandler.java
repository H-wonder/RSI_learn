package cc.eamon.open.flow.agent;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

import java.util.concurrent.TimeUnit;

/**
 * ToolHandler that forwards a tool call to the local AutomationBench
 * WorldState bridge (scripts/world_bridge.py).
 */
public class BridgeToolHandler implements ToolHandler {

    private static final MediaType JSON_TYPE = MediaType.parse("application/json; charset=utf-8");
    private static final OkHttpClient CLIENT = new OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(120, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build();

    private final String baseUrl;
    private final String toolName;

    public BridgeToolHandler(String baseUrl, String toolName) {
        this.baseUrl = trimTrailingSlash(baseUrl);
        this.toolName = toolName;
    }

    @Override
    public String execute(String argumentsJson) throws Exception {
        JSONObject payload = new JSONObject();
        payload.put("name", toolName);
        JSONObject arguments = argumentsJson == null || argumentsJson.trim().isEmpty()
                ? new JSONObject()
                : JSON.parseObject(argumentsJson);
        payload.put("arguments", arguments == null ? new JSONObject() : arguments);

        Request request = new Request.Builder()
                .url(baseUrl + "/tool")
                .post(RequestBody.create(JSON_TYPE, payload.toJSONString()))
                .build();
        Response response = CLIENT.newCall(request).execute();
        String body;
        try {
            body = response.body() == null ? "" : response.body().string();
        } finally {
            response.close();
        }
        if (!response.isSuccessful()) {
            throw new IllegalStateException("bridge tool HTTP " + response.code() + ": " + body);
        }
        JSONObject json = JSON.parseObject(body);
        if (json == null) {
            throw new IllegalStateException("bridge tool returned non-JSON: " + body);
        }
        if (json.containsKey("error")) {
            throw new IllegalStateException("bridge tool error: " + json.getString("error"));
        }
        return json.getString("result");
    }

    private static String trimTrailingSlash(String value) {
        String result = value;
        while (result.endsWith("/")) {
            result = result.substring(0, result.length() - 1);
        }
        return result;
    }

}
