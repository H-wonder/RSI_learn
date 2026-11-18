package cc.eamon.open.flow.agent;

import cc.eamon.open.flow.core.FlowEngine;
import cc.eamon.open.flow.core.error.FlowNodeRuntimeException;
import cc.eamon.open.flow.core.stereotype.Flow;

/**
 * Explicit final-action node (M4). The flow has to pass through it; if the
 * handler is not registered or the action fails, the node throws instead of
 * letting the flow end with a dangling partial result.
 */
public class FinalActionNode {

    @Flow(value = "FINAL_ACTION", retrieve = "finalActionResult")
    public void execute(String actionName, String payloadJson, String resultName) throws Exception {
        FinalActionHandler handler = FinalActionRegistry.get(actionName);
        if (handler == null) {
            throw new FlowNodeRuntimeException("FINAL_ACTION", "final action is not registered: " + actionName);
        }
        String result = handler.execute(
                payloadJson == null ? "{}" : Template.renderText(payloadJson));
        String name = (resultName == null || resultName.trim().isEmpty())
                ? "finalActionResult" : resultName;
        FlowEngine.instance().register(name, result);
    }

}
