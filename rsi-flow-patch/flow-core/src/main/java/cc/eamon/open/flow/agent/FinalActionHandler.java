package cc.eamon.open.flow.agent;

/**
 * A required final action (write-back, notify, create record, ...).
 * A flow that needs M4 enforcement registers one handler per action and uses a
 * {@link FinalActionNode}; a missing handler fails the flow instead of silently
 * ending before the last step.
 */
public interface FinalActionHandler {

    String execute(String payloadJson) throws Exception;

}
