package cc.eamon.open.flow.agent;

import cc.eamon.open.flow.core.FlowEngine;
import cc.eamon.open.flow.core.stereotype.Flow;
import cc.eamon.open.flow.route.util.JexlUtils;
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;

import java.util.HashMap;
import java.util.Map;

/**
 * Row-wise JEXL filter over a JSON array (the deterministic "where" of a
 * structured flow).
 *
 * <p>Each row must be a JSON object. Column names are exposed to the
 * expression with non-alphanumeric characters replaced by {@code _}
 * ({@code "Last Load Test"} becomes {@code Last_Load_Test}). An optional
 * {@code varsJson} object adds constants such as reference dates or joined
 * lookup values.</p>
 *
 * <p>Example expression:
 * {@code Status != 'Under Repair' && Last_Load_Test <= '2026-01-24'}.</p>
 */
public class WhereNode {

    @Flow(value = "WHERE_JSON", retrieve = "whereJson")
    public void filter(String itemsJson, String expression, String varsJson, String resultName) {
        if (expression == null || expression.trim().isEmpty()) {
            throw new cc.eamon.open.flow.core.error.FlowNodeRuntimeException(
                    "WHERE_JSON", "expression is required");
        }
        expression = Template.renderText(expression);
        JSONArray items;
        try {
            items = JSON.parseArray(Template.renderText(itemsJson == null ? "[]" : itemsJson));
        } catch (Exception e) {
            items = new JSONArray();
        }
        Map<String, Object> constants = new HashMap<String, Object>();
        String varsText = varsJson == null ? "" : Template.renderText(varsJson).trim();
        if (!varsText.isEmpty()) {
            try {
                JSONObject vars = JSON.parseObject(varsText);
                if (vars != null) {
                    for (String key : vars.keySet()) {
                        constants.put(normalize(key), vars.get(key));
                    }
                }
            } catch (Exception e) {
                // Ignore malformed extra variables; the expression still runs
                // against row fields and fails visibly if a variable is missing.
            }
        }

        JSONArray result = new JSONArray();
        for (int i = 0; i < items.size(); i++) {
            Object item = items.get(i);
            if (!(item instanceof JSONObject)) {
                continue;
            }
            Map<String, Object> variables = new HashMap<String, Object>(constants);
            JSONObject row = (JSONObject) item;
            for (String key : row.keySet()) {
                variables.put(normalize(key), row.get(key));
            }
            Object value;
            try {
                value = JexlUtils.invokeMethod(expression, variables);
            } catch (Exception e) {
                throw new cc.eamon.open.flow.core.error.FlowNodeRuntimeException(
                        "WHERE_JSON", "failed to evaluate: " + expression, e);
            }
            if (value instanceof Boolean && (Boolean) value) {
                result.add(item);
            } else if (value != null && !(value instanceof Boolean)
                    && Boolean.parseBoolean(String.valueOf(value))) {
                result.add(item);
            }
        }
        String name = (resultName == null || resultName.trim().isEmpty())
                ? "whereJson" : resultName;
        FlowEngine.instance().register(name, result.toJSONString());
    }

    static String normalize(String key) {
        return key == null ? "" : key.replaceAll("[^A-Za-z0-9_]", "_");
    }

}
