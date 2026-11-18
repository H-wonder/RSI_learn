package cc.eamon.open.flow.agent;

/**
 * A tool implementation used by {@link ToolNode}.
 *
 * <p>The handler receives the node's arguments as a JSON string and returns a
 * JSON/text result. AutomationBench integration can register handlers that
 * bridge to its in-process WorldState; unit tests can register simple mocks.</p>
 */
public interface ToolHandler {

    String execute(String argumentsJson) throws Exception;

}
