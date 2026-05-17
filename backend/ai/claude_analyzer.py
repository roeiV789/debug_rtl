"""
ClaudeAnalyzer — three-turn stateful conversation that produces AI debug insights
from an RTL analysis context (violations, FSM issues, full signal history).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from anthropic import Anthropic

from ..models.analysis_models import (
    AnalysisContext,
    AnalysisResult,
    FSMIssueOut,
    RecommendationOut,
    ViolationOut,
)


class ClaudeAnalyzer:
    """
    Uses the Anthropic Messages API in a three-turn conversation to generate
    root-cause analysis and fix recommendations for RTL protocol violations.

    Turn 1 — establish context (prompt-cached large block)
    Turn 2 — root cause analysis per violation / invalid FSM transition
    Turn 3 — actionable fix recommendations
    """

    MODEL = "claude-sonnet-4-6"
    MAX_TOKENS = 4096

    SYSTEM_PROMPT = (
        "You are an expert RTL/hardware verification engineer specializing in "
        "AXI protocol debugging. You analyze signal traces and protocol "
        "specifications to identify bugs and recommend fixes."
    )

    def __init__(self) -> None:
        # ANTHROPIC_API_KEY is read automatically from the environment.
        self.client = Anthropic()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, context: AnalysisContext) -> AnalysisResult:
        """
        Run a three-turn conversation against Claude and return a fully
        populated AnalysisResult.

        Raises:
            RuntimeError: if the Anthropic API call fails or the response
                          cannot be parsed into the expected structure.
        """
        conversation: List[Dict[str, Any]] = []

        # --- Turn 1: establish context, ask for acknowledgement ----------
        context_text = context.to_prompt_context()
        turn1_user_content = [
            {
                "type": "text",
                "text": context_text,
                # Cache the large static block — saves cost on turns 2 & 3.
                "cache_control": {"type": "ephemeral"},
            },
            {
                "type": "text",
                "text": (
                    "Please confirm you have understood the RTL debug context "
                    "above. Briefly list all rule violations and invalid FSM "
                    "transitions you can see, by ID and cycle number."
                ),
            },
        ]

        turn1_response = self._chat(conversation, turn1_user_content)
        conversation.append({"role": "assistant", "content": turn1_response})

        # --- Turn 2: root cause analysis ---------------------------------
        turn2_user_content = (
            "For each rule violation and each invalid FSM transition listed "
            "above, provide a detailed root cause analysis. Explain why the "
            "violation occurred based on the signal trace provided in the "
            "context. Be specific about which signal values at which cycles "
            "led to each problem."
        )
        turn2_response = self._chat(conversation, turn2_user_content)
        conversation.append({"role": "assistant", "content": turn2_response})

        # --- Turn 3: fix recommendations ---------------------------------
        turn3_user_content = (
            "Now provide specific, actionable fix recommendations for each "
            "issue identified. Format each recommendation with a clear title "
            "on a line starting with '## ' followed by a detailed description. "
            "Focus on RTL design changes, timing fixes, or FSM corrections. "
            "Use markdown formatting throughout."
        )
        turn3_response = self._chat(conversation, turn3_user_content)

        # --- Build AnalysisResult from responses -------------------------
        violations = self._build_violations(context)
        fsm_issues = self._build_fsm_issues(context)
        ai_summary = turn2_response
        ai_recommendations = self._parse_recommendations(turn3_response)

        return AnalysisResult(
            violations=violations,
            fsm_issues=fsm_issues,
            ai_summary=ai_summary,
            ai_recommendations=ai_recommendations,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _chat(
        self,
        conversation: List[Dict[str, Any]],
        user_content: Any,
    ) -> str:
        """
        Append *user_content* to the conversation, call the API, extract the
        assistant text, and append the new user message to *conversation* in
        place so subsequent turns accumulate history correctly.

        Returns the assistant's text response.

        Raises:
            RuntimeError: wraps any Anthropic API exception with context.
        """
        user_message: Dict[str, Any] = {"role": "user", "content": user_content}
        conversation.append(user_message)

        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                system=self.SYSTEM_PROMPT,
                messages=conversation,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Anthropic API call failed: {exc}"
            ) from exc

        # Extract text from the first content block.
        assistant_text: str = ""
        for block in response.content:
            if hasattr(block, "text"):
                assistant_text = block.text
                break

        if not assistant_text:
            raise RuntimeError(
                "Anthropic API returned an empty response for the current turn."
            )

        return assistant_text

    # ------------------------------------------------------------------

    @staticmethod
    def _build_violations(context: AnalysisContext) -> List[ViolationOut]:
        """Mirror context.rule_violations into ViolationOut objects."""
        return [
            ViolationOut(
                rule_id=v.rule_id,
                rule_name=v.rule_name,
                severity=v.severity,
                trigger_cycle=v.trigger_cycle,
                details=v.details,
                relevant_cycles=v.relevant_cycles,
            )
            for v in context.rule_violations
        ]

    @staticmethod
    def _build_fsm_issues(context: AnalysisContext) -> List[FSMIssueOut]:
        """Mirror invalid FSMTransition entries into FSMIssueOut objects."""
        return [
            FSMIssueOut(
                from_state=t.from_state,
                to_state=t.to_state,
                cycle=t.cycle,
                allowed_next=t.allowed_next,
            )
            for t in context.fsm_transitions
            if not t.valid
        ]

    @staticmethod
    def _parse_recommendations(text: str) -> List[RecommendationOut]:
        """
        Split Claude's turn-3 response into RecommendationOut objects.

        Expected format (requested in the prompt):
            ## <Title>
            <body text — may be multiple paragraphs>

        If the text does not contain any '## ' headings, the entire response
        is returned as a single recommendation with title "Analysis".
        """
        # Split on lines that start with '## '
        sections = re.split(r"(?m)^##\s+", text)

        recommendations: List[RecommendationOut] = []

        # sections[0] is everything before the first '## ' heading (preamble).
        # We skip it if it's blank, otherwise treat it as a lead-in note and
        # attach it to the first real section (handled naturally by the loop).
        preamble = sections[0].strip()

        remaining = sections[1:]  # each element: "Title\nbody..."

        for section in remaining:
            # The first line is the title, the rest is the body.
            newline_pos = section.find("\n")
            if newline_pos == -1:
                title = section.strip()
                body = ""
            else:
                title = section[:newline_pos].strip()
                body = section[newline_pos + 1:].strip()

            if title:
                recommendations.append(RecommendationOut(title=title, body=body))

        # If nothing was parsed (Claude didn't use headings), fall back to a
        # single catch-all recommendation.
        if not recommendations:
            fallback_body = text.strip() if text.strip() else "(no recommendations generated)"
            recommendations.append(
                RecommendationOut(title="Analysis", body=fallback_body)
            )
        elif preamble:
            # Prepend preamble content to the first recommendation's body.
            recommendations[0] = RecommendationOut(
                title=recommendations[0].title,
                body=f"{preamble}\n\n{recommendations[0].body}".strip(),
            )

        return recommendations
