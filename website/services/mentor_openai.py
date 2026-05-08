"""OpenAI-backed mentor chat service."""

import logging
import os

from openai import OpenAI

from website.onboarding_config import (
    CAREER_GOAL_LABELS,
    CAREER_STAGE_LABELS,
    MAJOR_LABELS,
)

log = logging.getLogger(__name__)

_MAX_REPLY_TOKENS = 700
_DEFAULT_MODEL = "gpt-4o-mini"


def _mentor_system_prompt() -> str:
    return (
        "You are Blueprint AI Mentor, a concise and practical college career mentor.\n"
        "Primary scope: academics, career exploration, internships, projects, networking, and recruiting prep.\n"
        "Rules:\n"
        "1) Keep answers actionable, supportive, and specific to a student's situation.\n"
        "2) Prefer short paragraphs, simple numbered or dashed lists, and clear next steps.\n"
        "3) OUTPUT FORMAT: plain text only for a simple chat UI. Do NOT use Markdown or markup: "
        "no # headings, no ###, no **bold**, no __underline__, no ``` fences, no --- rules, no [links](url). "
        "Use blank lines between paragraphs. For emphasis, use plain words or capitalization sparingly.\n"
        "4) If a question is dangerous, illegal, or unrelated to student mentoring, refuse briefly and redirect.\n"
        "5) Do not provide legal, medical, or financial advice.\n"
        "6) If missing context, ask one clarifying question at the end.\n"
        "7) Aim for under ~280 words unless the user asks for more detail; finish complete sentences "
        "and do not trail off mid-thought."
    )


def _profile_context(profile: dict) -> str:
    major = MAJOR_LABELS.get(profile.get("major", ""), profile.get("major", "Not set"))
    class_year = profile.get("class_year", "Not set")
    goal = CAREER_GOAL_LABELS.get(
        profile.get("career_goal", ""), profile.get("career_goal", "Not set")
    )
    stage = CAREER_STAGE_LABELS.get(
        profile.get("career_stage", ""), profile.get("career_stage", "Not set")
    )

    return (
        "Student profile:\n"
        f"- Major: {major}\n"
        f"- Class year: {class_year}\n"
        f"- Career goal: {goal}\n"
        f"- Career stage: {stage}\n"
    )


def _fallback_reply(user_message: str) -> str:
    return (
        "I can still help even though the AI service is temporarily unavailable. "
        "Based on your question, try this: define one clear goal for this week, "
        "pick one action (apply, project milestone, networking message, or resume update), "
        "and schedule a 30-minute block to do it today. "
        "If you share your major/year and target role, I can suggest a tailored next-step plan."
    )


def get_mentor_reply(*, user_message: str, profile: dict, history: list | None = None) -> dict:
    """Return mentor chat response payload."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        log.info("No OPENAI_API_KEY for mentor chat; returning fallback response.")
        return {"reply": _fallback_reply(user_message), "source": "fallback"}

    model = os.getenv("OPENAI_MODEL", _DEFAULT_MODEL)
    client = OpenAI(api_key=api_key)

    messages = [
        {"role": "system", "content": _mentor_system_prompt()},
        {"role": "system", "content": _profile_context(profile)},
    ]

    # Optional: include trimmed history to keep context and token cost predictable.
    if history:
        for turn in history[-6:]:
            role = turn.get("role")
            content = (turn.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content[:1500]})

    messages.append({"role": "user", "content": user_message})

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.4,
            max_tokens=_MAX_REPLY_TOKENS,
            messages=messages,
        )
        reply = (resp.choices[0].message.content or "").strip()
        if not reply:
            raise ValueError("Empty mentor response from model.")
        return {"reply": reply, "source": "llm"}
    except Exception:
        log.exception("Mentor OpenAI call failed; returning fallback response.")
        return {"reply": _fallback_reply(user_message), "source": "fallback"}