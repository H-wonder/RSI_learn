package cc.eamon.open.flow.agent;

import cc.eamon.open.flow.core.FlowEngine;
import cc.eamon.open.flow.core.error.FlowNodeRuntimeException;
import cc.eamon.open.flow.core.stereotype.Flow;
import cc.eamon.open.flow.route.util.JexlUtils;
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;

import java.util.HashMap;
import java.util.Map;

/**
 * Deterministic rule evaluation (M2). The context is a JSON object; the
 * expression is JEXL (the same engine used by rsi-flow route conditions).
 */
public class RuleNode {

    @Flow(value = "RULE_EVAL", retrieve = "ruleResult")
    public void eval(String contextJson, String expression, String resultName) {
        if (expression == null || expression.trim().isEmpty()) {
            throw new FlowNodeRuntimeException("RULE_EVAL", "expression is required");
        }
        JSONObject context = JSON.parseObject(
                Template.renderText(contextJson == null ? "{}" : contextJson));
        Map<String, Object> variables = new HashMap<String, Object>();
        if (context != null) {
            for (String key : context.keySet()) {
                variables.put(key, context.get(key));
            }
        }
        Object value;
        try {
            value = JexlUtils.invokeMethod(expression, variables);
        } catch (Exception e) {
            throw new FlowNodeRuntimeException("RULE_EVAL", "failed to evaluate: " + expression, e);
        }
        String name = (resultName == null || resultName.trim().isEmpty())
                ? "ruleResult" : resultName;
        FlowEngine.instance().register(name, value == null ? "null" : String.valueOf(value));
    }

}
