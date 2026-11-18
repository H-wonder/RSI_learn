package cc.eamon.open.flow.core.context;

import cc.eamon.open.flow.route.util.JexlUtils;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Author: eamon
 * Email: eamon@eamon.cc
 * Time: 2021-05-25 23:37:18
 */
public class FlowScopeContext {

    private String name;

    /**
     * 线程参数
     */
    private Map<String, Object> variableMap = new ConcurrentHashMap<>();

    FlowScopeContext(String name) {
        this.name = name;
    }

    void registerVariable(String variableName, Object variableValue) {
        variableMap.put(variableName, variableValue);
    }

    Object retrieveVariable(String variableName) {
        return JexlUtils.getVariable(variableName, variableMap);
//        return variableMap.get(variableName);
    }

    void releaseVariables(String... variableNames) {
        for (String variableName : variableNames) {
            variableMap.remove(variableName);
        }
    }

    public Map<String, Object> getVariableMap() {
        return variableMap;
    }

    public String getName() {
        return name;
    }


}
