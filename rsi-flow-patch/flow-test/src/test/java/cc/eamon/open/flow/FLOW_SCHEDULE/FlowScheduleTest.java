package cc.eamon.open.flow.FLOW_SCHEDULE;

import cc.eamon.open.flow.config.constants.FlowConstants;
import cc.eamon.open.flow.core.FlowEngine;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Author: eamon
 * Email: eamon@eamon.cc
 * Time: 2021-05-31 13:19:07
 */
public class FlowScheduleTest {

    // Disabled: the scheduler beans (SchedulerTask.schedulerTemplate / schedulerDAO /
    // scheduleDBUtil) are injected by Spring. A plain TestNG run has no application
    // context, so ScheduleTaskRegistrar.register() throws NullPointerException.
    // Re-enable this test once a Spring test context is set up for the scheduler.
    @Test(enabled = false)
    public void caseScheduleTest() throws Exception {
        FlowEngine flowEngine = FlowEngine.instance()
                .register(FlowConstants.SCOPE_DEFAULT, "id", "B207BE79230C4ABBBAE7BA4AAD8AD4F3")
                .run("FLOW_SCHEDULE_EVENT_DELAY");

        String name = (String) flowEngine.retrieve(FlowConstants.SCOPE_DEFAULT, "name");
        Assert.assertEquals(name, "FLOW_SCHEDULE_EVENT_DELAY SUCCESS");
        FlowEngine.instance().release();
    }

}
