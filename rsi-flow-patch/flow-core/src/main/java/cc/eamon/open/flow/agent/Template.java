package cc.eamon.open.flow.agent;

import cc.eamon.open.flow.core.context.FlowContextHolder;
import com.alibaba.fastjson.JSON;

import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Replaces {{variable}} placeholders from the current flow context.
 * Values inside JSON templates are JSON-escaped (without the surrounding
 * quotes) so a plan/evidence string can be embedded safely.
 */
public final class Template {

    private static final Pattern PLACEHOLDER =
            Pattern.compile("\\{\\{\\s*([A-Za-z0-9_]+)\\s*\\}\\}");

    private Template() {
    }

    public static String renderText(String template) {
        return render(template, false);
    }

    public static String renderJson(String template) {
        return render(template, true);
    }

    private static String render(String template, boolean jsonEscape) {
        if (template == null || !template.contains("{{")) {
            return template;
        }
        Map<String, Object> variables = FlowContextHolder.get().retrieveVariables();
        Matcher matcher = PLACEHOLDER.matcher(template);
        StringBuffer out = new StringBuffer();
        while (matcher.find()) {
            Object value = variables.get(matcher.group(1));
            String replacement = value == null ? "" : String.valueOf(value);
            if (jsonEscape) {
                replacement = JSON.toJSONString(replacement);
                replacement = replacement.substring(1, replacement.length() - 1);
            }
            matcher.appendReplacement(out, Matcher.quoteReplacement(replacement));
        }
        matcher.appendTail(out);
        return out.toString();
    }

}
