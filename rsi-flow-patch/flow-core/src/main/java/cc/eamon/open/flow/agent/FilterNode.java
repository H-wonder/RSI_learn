package cc.eamon.open.flow.agent;

import cc.eamon.open.flow.core.FlowEngine;
import cc.eamon.open.flow.core.stereotype.Flow;
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;

import java.math.BigDecimal;

/**
 * Deterministic JSON-array filter (M2/M5). Supported ops:
 * equals, not_equals, contains, not_contains, exists, not_exists,
 * gt, gte, lt, lte.
 *
 * <p>{@code field} supports dot paths (e.g. {@code owner.email}).</p>
 */
public class FilterNode {

    @Flow(value = "FILTER_JSON", retrieve = "filterResult")
    public void filter(String itemsJson, String field, String op, String value, String resultName) {
        JSONArray items;
        try {
            items = JSON.parseArray(itemsJson == null ? "[]" : itemsJson);
        } catch (Exception e) {
            items = new JSONArray();
        }
        JSONArray result = new JSONArray();
        String operation = op == null ? "equals" : op;
        for (int i = 0; i < items.size(); i++) {
            Object item = items.get(i);
            Object actual = readField(item, field);
            if (matches(actual, operation, value)) {
                result.add(item);
            }
        }
        String name = (resultName == null || resultName.trim().isEmpty())
                ? "filterResult" : resultName;
        FlowEngine.instance().register(name, result.toJSONString());
    }

    private static Object readField(Object item, String field) {
        if (!(item instanceof JSONObject) || field == null || field.isEmpty()) {
            return item;
        }
        Object current = item;
        String[] parts = field.split("\\.");
        for (String part : parts) {
            if (!(current instanceof JSONObject)) {
                return null;
            }
            current = ((JSONObject) current).get(part);
        }
        return current;
    }

    private static boolean matches(Object actual, String op, String expected) {
        if ("exists".equals(op)) {
            return actual != null;
        }
        if ("not_exists".equals(op)) {
            return actual == null;
        }
        if (actual == null) {
            return false;
        }
        String actualText = String.valueOf(actual);
        if ("equals".equals(op)) {
            return actualText.equals(expected);
        }
        if ("not_equals".equals(op)) {
            return !actualText.equals(expected);
        }
        if ("contains".equals(op)) {
            return expected != null && actualText.contains(expected);
        }
        if ("not_contains".equals(op)) {
            return expected == null || !actualText.contains(expected);
        }
        BigDecimal left = toDecimal(actualText);
        BigDecimal right = toDecimal(expected);
        if (left == null || right == null) {
            return false;
        }
        int cmp = left.compareTo(right);
        if ("gt".equals(op)) {
            return cmp > 0;
        }
        if ("gte".equals(op)) {
            return cmp >= 0;
        }
        if ("lt".equals(op)) {
            return cmp < 0;
        }
        if ("lte".equals(op)) {
            return cmp <= 0;
        }
        return false;
    }

    private static BigDecimal toDecimal(String value) {
        try {
            return new BigDecimal(value);
        } catch (Exception e) {
            return null;
        }
    }

}
