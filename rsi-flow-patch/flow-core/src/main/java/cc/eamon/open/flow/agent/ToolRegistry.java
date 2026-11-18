package cc.eamon.open.flow.agent;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Registry of tool handlers. The flow engine deliberately does not hard-code
 * any application; callers register the tools they need before running a flow.
 */
public final class ToolRegistry {

    private static final Map<String, ToolHandler> HANDLERS = new ConcurrentHashMap<String, ToolHandler>();

    private ToolRegistry() {
    }

    public static void register(String name, ToolHandler handler) {
        if (name == null || name.trim().isEmpty()) {
            throw new IllegalArgumentException("tool name is required");
        }
        if (handler == null) {
            throw new IllegalArgumentException("tool handler is required");
        }
        HANDLERS.put(name, handler);
    }

    public static ToolHandler get(String name) {
        return name == null ? null : HANDLERS.get(name);
    }

    public static void unregister(String name) {
        HANDLERS.remove(name);
    }

    public static void clear() {
        HANDLERS.clear();
    }

}
