package cc.eamon.open.flow.agent;

import cc.eamon.open.flow.core.FlowEngine;
import cc.eamon.open.flow.core.stereotype.Flow;

/**
 * Records a stage entry into the per-run audit trail and registers the
 * accumulated trail as a JSON array string.
 */
public class AuditNode {

    @Flow(value = "AUDIT", retrieve = "auditJson")
    public void record(String stage, String payloadJson, String resultName) {
        AuditStore.record(stage, payloadJson);
        String name = (resultName == null || resultName.trim().isEmpty())
                ? "auditJson" : resultName;
        FlowEngine.instance().register(name, AuditStore.snapshot().toJSONString());
    }

}
