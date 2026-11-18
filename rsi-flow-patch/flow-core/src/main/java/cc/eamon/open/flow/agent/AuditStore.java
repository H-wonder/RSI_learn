package cc.eamon.open.flow.agent;

import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;

import java.util.ArrayList;
import java.util.List;

/**
 * Per-thread audit trail for a flow run. A flow runs on one thread; async
 * branches have their own thread and are intentionally not merged here.
 */
public final class AuditStore {

    private static final ThreadLocal<List<JSONObject>> ENTRIES =
            ThreadLocal.withInitial(ArrayList::new);

    private AuditStore() {
    }

    public static void record(String stage, String payloadJson) {
        JSONObject entry = new JSONObject();
        entry.put("stage", stage);
        entry.put("payload", payloadJson);
        entry.put("ts", System.currentTimeMillis());
        ENTRIES.get().add(entry);
    }

    public static JSONArray snapshot() {
        JSONArray array = new JSONArray();
        array.addAll(ENTRIES.get());
        return array;
    }

    public static void clear() {
        ENTRIES.get().clear();
    }

}
