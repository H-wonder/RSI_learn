package cc.eamon.open.flow.agent;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

import java.util.concurrent.TimeUnit;

/**
 * Reads the current AutomationBench score from the local world bridge.
 * This is an experiment/verification handler, not a benchmark tool.
 */
public class BridgeScoreHandler implements ToolHandler {

    private static final OkHttpClient CLIENT = new OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .build();

    private final String baseUrl;

    public BridgeScoreHandler(String baseUrl) {
        String value = baseUrl;
        while (value.endsWith("/")) {
            value = value.substring(0, value.length() - 1);
        }
        this.baseUrl = value;
    }

    @Override
    public String execute(String argumentsJson) throws Exception {
        Request request = new Request.Builder().url(baseUrl + "/score").get().build();
        Response response = CLIENT.newCall(request).execute();
        try {
            String body = response.body() == null ? "" : response.body().string();
            if (!response.isSuccessful()) {
                throw new IllegalStateException("bridge score HTTP " + response.code() + ": " + body);
            }
            return body;
        } finally {
            response.close();
        }
    }

}
