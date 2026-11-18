package cc.eamon.open.flow.agent;

import cc.eamon.open.flow.core.FlowEngine;
import cc.eamon.open.flow.core.error.FlowNodeRuntimeException;
import cc.eamon.open.flow.core.stereotype.Flow;

/**
 * Deterministic tool node: the app/action is fixed by the flow, not chosen by
 * the model. This is the M1 intervention described in the report.
 */
public class ToolNode {

    @Flow(value = "TOOL_CALL", retrieve = "toolResult")
    public void call(String toolName, String argumentsJson, String resultName) throws Exception {
        ToolHandler handler = ToolRegistry.get(toolName);
        if (handler == null) {
            throw new FlowNodeRuntimeException("TOOL_CALL", "tool is not registered: " + toolName);
        }
        String result = handler.execute(
                argumentsJson == null ? "{}" : Template.renderText(argumentsJson));
        String name = (resultName == null || resultName.trim().isEmpty()) ? "toolResult" : resultName;
        FlowEngine.instance().register(name, result);
    }

}
