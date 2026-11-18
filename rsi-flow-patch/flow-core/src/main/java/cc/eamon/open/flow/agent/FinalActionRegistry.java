package cc.eamon.open.flow.agent;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public final class FinalActionRegistry {

    private static final Map<String, FinalActionHandler> HANDLERS = new ConcurrentHashMap<String, FinalActionHandler>();

    private FinalActionRegistry() {
    }

    public static void register(String name, FinalActionHandler handler) {
        if (name == null || name.trim().isEmpty()) {
            throw new IllegalArgumentException("final action name is required");
        }
        if (handler == null) {
            throw new IllegalArgumentException("final action handler is required");
        }
        HANDLERS.put(name, handler);
    }

    public static FinalActionHandler get(String name) {
        return name == null ? null : HANDLERS.get(name);
    }

    public static void unregister(String name) {
        HANDLERS.remove(name);
    }

    public static void clear() {
        HANDLERS.clear();
    }

}
