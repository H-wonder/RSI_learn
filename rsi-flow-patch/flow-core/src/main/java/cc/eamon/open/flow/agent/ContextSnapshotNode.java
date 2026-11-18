package cc.eamon.open.flow.agent;

import cc.eamon.open.flow.core.FlowEngine;
import cc.eamon.open.flow.core.context.FlowContextHolder;
import cc.eamon.open.flow.core.stereotype.Flow;
import com.alibaba.fastjson.JSON;

/**
 * Registers a snapshot of all current flow variables as JSON. Useful for
 * passing evidence/facts into an LLM prompt via {@link Template}.
 */
public class ContextSnapshotNode {

    @Flow(value = "CONTEXT_JSON", retrieve = "contextJson")
    public void snapshot(String resultName) {
        String name = (resultName == null || resultName.trim().isEmpty())
                ? "contextJson" : resultName;
        FlowEngine.instance().register(
                name,
                JSON.toJSONString(FlowContextHolder.get().retrieveVariables()));
    }

}
