import json
import re
from groq import Groq
from app.core.config import settings
from app.core.logger import get_logger
from app.tools.calculator import calculate_working_days
from app.tools.web_search_tool import web_search
from app.tools.llm_tool import (
    get_employee_info,
    get_employee_name,
    get_leave_balance,
    get_leave_requests,
    submit_leave_request,
)
from app.tools.rag_tool import search_hr_policy
from app.utils.prompt_builder import build_system_prompt

logger = get_logger(__name__)

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_hr_policy",
            "description": "Search company HR policy documents.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee_info",
            "description": "Get employee profile info.",
            "parameters": {
                "type": "object",
                "properties": {"employee_id": {"type": "string"}},
                "required": ["employee_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_leave_balance",
            "description": "Get leave balance for an employee.",
            "parameters": {
                "type": "object",
                "properties": {"employee_id": {"type": "string"}},
                "required": ["employee_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_leave_request",
            "description": "Submit a leave request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string"},
                    "leave_type": {"type": "string", "enum": ["annual", "sick", "casual"]},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["employee_id", "leave_type", "start_date", "end_date", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_leave_requests",
            "description": "Get leave request history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string"},
                    "status": {"type": "string", "enum": ["pending", "approved", "rejected", "all"]},
                },
                "required": ["employee_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_working_days",
            "description": "Calculate working days between two dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
                "required": ["start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search internet for latest, current, real-time information not in HR documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query. Example: latest AI news 2026"
                    }
                },
                "required": ["query"],
            },
        },
    },
]

_TOOL_REGISTRY = {
    "search_hr_policy": search_hr_policy,
    "get_employee_info": get_employee_info,
    "get_leave_balance": get_leave_balance,
    "submit_leave_request": submit_leave_request,
    "get_leave_requests": get_leave_requests,
    "calculate_working_days": calculate_working_days,
    "web_search": web_search,
}


def _execute_tool(name: str, tool_input: dict) -> str:
    fn = _TOOL_REGISTRY.get(name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        return json.dumps(fn(**tool_input), default=str)
    except Exception as exc:
        logger.error(f"Tool '{name}' raised: {exc}")
        return json.dumps({"error": str(exc)})


def _parse_failed_tool_call(failed_text: str):
    """
    Groq गलत format देता है जैसे:
    <function=web_search[]{"query": "..."}</function>
    इसे manually parse करो
    """
    try:
        # ✅ [] भी handle करता है
        match = re.search(
            r'<function=(\w+)[\[\]]*\(?({.*?})\)?<?\/?>?<\/function>',
            failed_text,
            re.DOTALL
        )
        if match:
            tool_name = match.group(1)
            tool_args = json.loads(match.group(2))
            logger.info(f"Parsed tool: {tool_name}({tool_args})")
            return tool_name, tool_args
        else:
            logger.warning(f"No match found in: {failed_text}")
    except Exception as e:
        logger.error(f"Parse error: {e}")
    return None, None


class HRAgent:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)

    def chat(self, employee_id: str, message: str, history: list) -> str:
        name = get_employee_name(employee_id) if employee_id else "Guest"
        system = build_system_prompt(employee_id, name)

        messages = [{"role": "system", "content": system}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        emp_prefix = f"Employee ID: {employee_id}\n" if employee_id else ""
        messages.append({"role": "user", "content": f"{emp_prefix}{message}"})

        for iteration in range(settings.max_iterations):
            logger.info(f"[{employee_id}] Agent iteration {iteration + 1}")

            try:
                response = self.client.chat.completions.create(
                    model=settings.model_name,
                    max_tokens=settings.max_tokens,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    temperature=0.1,
                    messages=messages,
                )
                msg = response.choices[0].message

                if not msg.tool_calls:
                    return msg.content

                messages.append(msg)
                for tool_call in msg.tool_calls:
                    tool_input = json.loads(tool_call.function.arguments)
                    logger.info(f"Tool call: {tool_call.function.name}({tool_input})")
                    result = _execute_tool(tool_call.function.name, tool_input)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })

            except Exception as e:
                error_str = str(e)
                logger.error(f"Groq error: {error_str}")

                if "tool_use_failed" in error_str:
                    # ✅ Direct regex से failed_generation निकालो
                    failed_match = re.search(
                        r"'failed_generation':\s*'([^']+)'", error_str
                    )
                    failed_text = failed_match.group(1) if failed_match else error_str
                    logger.info(f"Parsing failed text: {failed_text}")

                    tool_name, tool_args = _parse_failed_tool_call(failed_text)

                    if tool_name and tool_args:
                        logger.info(f"Fallback: {tool_name}({tool_args})")
                        result = _execute_tool(tool_name, tool_args)
                        messages.append({
                            "role": "user",
                            "content": f"Tool result for {tool_name}: {result}\n\nNow answer the original question based on this result."
                        })
                        continue

                # ✅ Last resort — direct web search
                if any(w in message.lower() for w in
                       ["latest", "news", "today", "current", "2026", "recent"]):
                    logger.info("Direct web search fallback triggered")
                    return web_search(message)

                return "Something went wrong. Please try again."

        return "I'm unable to process your request right now. Please try again."