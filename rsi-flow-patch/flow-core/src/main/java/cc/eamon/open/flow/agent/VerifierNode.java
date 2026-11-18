package cc.eamon.open.flow.agent;

import cc.eamon.open.flow.core.FlowEngine;
import cc.eamon.open.flow.core.stereotype.Flow;
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;

import java.util.ArrayList;
import java.util.List;

/**
 * Post-condition verifier (M6). It checks that every expected fragment is
 * present in the actual output and registers a JSON result:
 * {@code {"passed":true/false,"missing":["..."]}}.
 */
public class VerifierNode {

    @Flow(value = "VERIFY_CONTAINS", retrieve = "verifyResult")
    public void verify(String actual, String expectedJson, String resultName) {
        List<String> expected = parseExpected(expectedJson);
        List<String> missing = new ArrayList<String>();
        String value = actual == null ? "" : actual;
        for (String item : expected) {
            if (!value.contains(item)) {
                missing.add(item);
            }
        }
        JSONObject result = new JSONObject();
        result.put("passed", missing.isEmpty());
        result.put("missing", missing);
        String name = (resultName == null || resultName.trim().isEmpty())
                ? "verifyResult" : resultName;
        FlowEngine.instance().register(name, result.toJSONString());
    }

    private static List<String> parseExpected(String expectedJson) {
        List<String> result = new ArrayList<String>();
        if (expectedJson == null || expectedJson.trim().isEmpty()) {
            return result;
        }
        try {
            JSONArray array = JSON.parseArray(expectedJson);
            if (array != null) {
                for (int i = 0; i < array.size(); i++) {
                    Object item = array.get(i);
                    if (item != null) {
                        result.add(String.valueOf(item));
                    }
                }
                return result;
            }
        } catch (Exception ignored) {
            // fall through to single-string mode
        }
        result.add(expectedJson);
        return result;
    }

}
