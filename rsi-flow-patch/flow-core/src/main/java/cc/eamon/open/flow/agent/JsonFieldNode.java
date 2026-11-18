package cc.eamon.open.flow.agent;

import cc.eamon.open.flow.core.FlowEngine;
import cc.eamon.open.flow.core.stereotype.Flow;
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;

/**
 * Extracts a top-level (or dot-path) field from a JSON string.
 */
public class JsonFieldNode {

    @Flow(value = "JSON_FIELD", retrieve = "jsonField")
    public void extract(String json, String path, String resultName) {
        Object current;
        try {
            current = JSON.parse(Template.renderText(json == null ? "{}" : json));
        } catch (Exception e) {
            current = null;
        }
        if (path != null && !path.trim().isEmpty()) {
            for (String part : path.split("\\.")) {
                if (current instanceof JSONObject) {
                    current = ((JSONObject) current).get(part);
                } else if (current instanceof JSONArray) {
                    try {
                        current = ((JSONArray) current).get(Integer.parseInt(part));
                    } catch (Exception e) {
                        current = null;
                    }
                } else {
                    current = null;
                    break;
                }
            }
        }
        String value;
        if (current == null) {
            value = "";
        } else if (current instanceof String) {
            value = (String) current;
        } else {
            value = JSON.toJSONString(current);
        }
        String name = (resultName == null || resultName.trim().isEmpty())
                ? "jsonField" : resultName;
        FlowEngine.instance().register(name, value);
    }

}
