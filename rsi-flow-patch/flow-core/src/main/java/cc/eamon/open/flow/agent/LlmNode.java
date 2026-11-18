package cc.eamon.open.flow.agent;

import cc.eamon.open.flow.core.FlowEngine;
import cc.eamon.open.flow.core.error.FlowNodeRuntimeException;
import cc.eamon.open.flow.core.stereotype.Flow;
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

import java.util.concurrent.TimeUnit;

/**
 * Minimal LLM node for rsi-flow.
 *
 * <p>Request JSON fields: {@code prompt} (required), {@code system},
 * {@code model}, {@code temperature}, {@code maxTokens},
 * {@code reasoningEffort}. The result is the assistant text, registered under
 * {@code resultName} (default {@code llmResult}).</p>
 *
 * <p>Configuration: {@code OPENAI_BASE_URL} / {@code OPENAI_API_KEY} /
 * {@code OPENAI_MODEL}, or the matching {@code flow.llm.*} system properties
 * (the latter are mainly for tests).</p>
 */
public class LlmNode {

    private static final MediaType JSON_TYPE = MediaType.parse("application/json; charset=utf-8");
    private static final OkHttpClient CLIENT = new OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(180, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build();

    @Flow(value = "LLM_CALL", retrieve = "llmResult")
    public void call(String requestJson, String resultName) throws Exception {
        JSONObject request = JSON.parseObject(Template.renderJson(requestJson));
        if (request == null) {
            throw new FlowNodeRuntimeException("LLM_CALL", "requestJson is required");
        }
        String prompt = request.getString("prompt");
        if (prompt == null || prompt.trim().isEmpty()) {
            throw new FlowNodeRuntimeException("LLM_CALL", "prompt is required");
        }

        String baseUrl = firstNonBlank(
                System.getProperty("flow.llm.baseUrl"),
                System.getenv("OPENAI_BASE_URL"),
                "https://api.openai.com/v1");
        String apiKey = firstNonBlank(
                System.getProperty("flow.llm.apiKey"),
                System.getenv("OPENAI_API_KEY"),
                null);
        if (apiKey == null) {
            throw new FlowNodeRuntimeException("LLM_CALL", "OPENAI_API_KEY is not set");
        }
        String model = firstNonBlank(
                request.getString("model"),
                System.getProperty("flow.llm.model"),
                System.getenv("OPENAI_MODEL"),
                "gpt-5.6-sol");

        JSONArray messages = new JSONArray();
        String system = request.getString("system");
        if (system != null && !system.trim().isEmpty()) {
            JSONObject systemMessage = new JSONObject();
            systemMessage.put("role", "system");
            systemMessage.put("content", system);
            messages.add(systemMessage);
        }
        JSONObject userMessage = new JSONObject();
        userMessage.put("role", "user");
        userMessage.put("content", prompt);
        messages.add(userMessage);

        JSONObject body = new JSONObject();
        body.put("model", model);
        body.put("messages", messages);
        if (request.get("temperature") != null) {
            body.put("temperature", request.get("temperature"));
        }
        if (request.get("maxTokens") != null) {
            body.put("max_completion_tokens", request.get("maxTokens"));
        }
        if (request.get("reasoningEffort") != null) {
            body.put("reasoning_effort", request.get("reasoningEffort"));
        }

        String url = trimTrailingSlash(baseUrl) + "/chat/completions";
        Request httpRequest = new Request.Builder()
                .url(url)
                .header("Authorization", "Bearer " + apiKey)
                .header("Content-Type", "application/json")
                .post(RequestBody.create(JSON_TYPE, body.toJSONString()))
                .build();

        Response response = CLIENT.newCall(httpRequest).execute();
        String responseBody;
        try {
            responseBody = response.body() == null ? "" : response.body().string();
        } finally {
            response.close();
        }
        if (!response.isSuccessful()) {
            throw new FlowNodeRuntimeException(
                    "LLM_CALL",
                    "LLM HTTP " + response.code() + ": " + shorten(responseBody));
        }

        JSONObject json = JSON.parseObject(responseBody);
        JSONArray choices = json == null ? null : json.getJSONArray("choices");
        if (choices == null || choices.isEmpty()) {
            throw new FlowNodeRuntimeException("LLM_CALL", "no choices in response: " + shorten(responseBody));
        }
        JSONObject message = choices.getJSONObject(0).getJSONObject("message");
        String content = message == null ? null : message.getString("content");
        if (content == null || content.trim().isEmpty()) {
            content = message == null ? null : message.getString("reasoning_content");
        }
        if (content == null) {
            throw new FlowNodeRuntimeException("LLM_CALL", "no assistant content in response");
        }
        content = stripCodeFence(content);

        String name = (resultName == null || resultName.trim().isEmpty()) ? "llmResult" : resultName;
        FlowEngine.instance().register(name, content);
    }

    private static String firstNonBlank(String... values) {
        for (String value : values) {
            if (value != null && !value.trim().isEmpty()) {
                return value;
            }
        }
        return null;
    }

    private static String trimTrailingSlash(String value) {
        String result = value;
        while (result.endsWith("/")) {
            result = result.substring(0, result.length() - 1);
        }
        return result;
    }

    private static String stripCodeFence(String value) {
        String text = value.trim();
        if (!text.startsWith("```")) {
            return value;
        }
        int firstNewline = text.indexOf('\n');
        int lastFence = text.lastIndexOf("```");
        if (firstNewline < 0 || lastFence <= firstNewline) {
            return value;
        }
        return text.substring(firstNewline + 1, lastFence).trim();
    }

    private static String shorten(String value) {
        if (value == null) {
            return "";
        }
        return value.length() <= 500 ? value : value.substring(0, 500) + "...";
    }

}
