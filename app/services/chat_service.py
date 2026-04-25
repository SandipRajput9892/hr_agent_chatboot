from app.agents.hr_agent import HRAgent
from app.core.logger import get_logger

logger = get_logger(__name__)

_agent: HRAgent | None = None
_sessions: dict[str, list] = {}

_MAX_HISTORY = 20  # keep last 10 turns (20 messages)


def _get_agent() -> HRAgent:
    global _agent
    if _agent is None:
        _agent = HRAgent()
    return _agent


def process_message(employee_id: str, message: str, session_id: str) -> str:
    agent = _get_agent()
    history = _sessions.get(session_id, [])

    response = agent.chat(
        employee_id=employee_id,
        message=message,
        history=history,
    )

    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": response},
    ]
    _sessions[session_id] = history[-_MAX_HISTORY:]
    logger.info(f"Session {session_id}: responded to {employee_id}")
    return response
