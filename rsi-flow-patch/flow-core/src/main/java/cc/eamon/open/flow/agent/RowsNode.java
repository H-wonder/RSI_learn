package cc.eamon.open.flow.agent;

import cc.eamon.open.flow.core.FlowEngine;
import cc.eamon.open.flow.core.stereotype.Flow;
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;

/**
 * Converts a tabular payload into an array of JSON objects.
 *
 * <p>Accepts either a Google Sheets v4 values response
 * ({@code {"values": [[header...], [row...]]}}) or a bare array of arrays.
 * The first row is used as the header; missing cells become empty strings, so
 * downstream {@link WhereNode} expressions never see nulls.</p>
 *
 * <p>Example: {@code [["Unit ID","Status"],["GEN-01","Active"]]} becomes
 * {@code [{"Unit ID":"GEN-01","Status":"Active"}]}.</p>
 */
public class RowsNode {

    @Flow(value = "ROWS_JSON", retrieve = "rowsJson")
    public void toRows(String valuesJson, String resultName) {
        JSONArray rows = new JSONArray();
        String text = valuesJson == null ? "" : Template.renderText(valuesJson).trim();
        if (!text.isEmpty()) {
            try {
                Object parsed = JSON.parse(text);
                JSONArray table = null;
                if (parsed instanceof JSONObject) {
                    Object values = ((JSONObject) parsed).get("values");
                    if (values instanceof JSONArray) {
                        table = (JSONArray) values;
                    }
                } else if (parsed instanceof JSONArray) {
                    table = (JSONArray) parsed;
                }
                if (table != null && !table.isEmpty()) {
                    JSONArray header = asArray(table.get(0));
                    for (int i = 1; i < table.size(); i++) {
                        JSONArray row = asArray(table.get(i));
                        JSONObject object = new JSONObject(true);
                        for (int c = 0; c < header.size(); c++) {
                            String key = header.get(c) == null ? "" : String.valueOf(header.get(c));
                            if (key.isEmpty()) {
                                continue;
                            }
                            Object value = c < row.size() ? row.get(c) : "";
                            object.put(key, value == null ? "" : value);
                        }
                        rows.add(object);
                    }
                }
            } catch (Exception e) {
                // A malformed payload yields an empty table; the flow's rule
                // gate will fail visibly instead of acting on garbage.
                rows = new JSONArray();
            }
        }
        String name = (resultName == null || resultName.trim().isEmpty())
                ? "rowsJson" : resultName;
        FlowEngine.instance().register(name, rows.toJSONString());
    }

    private static JSONArray asArray(Object value) {
        if (value instanceof JSONArray) {
            return (JSONArray) value;
        }
        JSONArray wrapped = new JSONArray();
        if (value != null) {
            wrapped.add(value);
        }
        return wrapped;
    }

}
