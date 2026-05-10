# Peer Review Manipulation Score
# --------------------------------
# Peer review is the last defense before bad science
# enters the literature. When that defense is gamed,
# the consequences propagate for decades.
#
# Manipulation takes several forms:
# Authors suggest reviewers who are actually collaborators.
# Papers get accepted in days when months is the norm.
# Editors handle papers from their own institution.
# Authors cite the editor excessively before submission.
# Review reports are suspiciously short or praise-only.
#
# Most of these signals live in metadata — journal names,
# dates, acknowledgments, conflict statements.
# This module reads what is available in the paper text
# and scores the manipulation risk from those signals.

import re
from dataclasses import dataclass
from datetime import datetime


# ── constants ──────────────────────────────────────────────────────────────────

CURRENT_YEAR = datetime.now().year

# phrases that signal a potentially compromised review process
FAST_ACCEPTANCE_MARKERS = [
    r'received[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
    r'accepted[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
    r'submitted[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
    r'revised[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
]

MONTH_ORDER = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9,
    "oct": 10, "nov": 11, "dec": 12,
}

# phrases that reveal undisclosed relationships
CONFLICT_RED_FLAGS = [
    "no conflict", "no competing interest", "no financial interest",
    "authors declare no", "declare no conflict",
]

# phrases suggesting reviewer suggestions were made
REVIEWER_SUGGESTION_MARKERS = [
    "suggested reviewer", "recommended reviewer",
    "proposed reviewer", "reviewer suggestion",
]

# special issue markers — these have lighter review
SPECIAL_ISSUE_MARKERS = [
    "special issue", "invited paper", "invited article",
    "guest editor", "symposium paper", "conference paper",
    "extended version", "workshop paper",
]

# predatory journal signals in acknowledgment or journal name context
PREDATORY_SIGNALS = [
    "article processing charge", "apc waiver", "rapid publication",
    "fast track", "open access fee", "publication fee waived",
    "guaranteed acceptance", "no peer review", "editorial board member",
]


# ── data structures ────────────────────────────────────────────────────────────

@dataclass
class ReviewFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class PeerReviewResult:
    days_to_acceptance:      int
    has_conflict_statement:  bool
    conflict_credible:       bool
    reviewer_suggestions:    bool
    special_issue:           bool
    predatory_signals:       int
    self_citation_of_editor: float
    manipulation_score:      float
    risk_level:              str
    summary:                 str
    flags:                   list
    flags_count:             int


# ── main class ────────────────────────────────────────────────────────────────

class PeerReviewScorer:
    """
    Scores the risk that a paper's peer review process was manipulated.

    Six detection layers:
    1. Unusually fast acceptance timeline
    2. Missing or boilerplate conflict of interest statement
    3. Reviewer suggestion language in the text
    4. Special issue / invited paper bypass signals
    5. Predatory journal process markers
    6. Excessive self-citation patterns suggesting editor citation farming
    """

    def analyze(self, text: str) -> PeerReviewResult:
        flags = []

        days          = self._measure_acceptance_speed(text, flags)
        has_conflict  = self._check_conflict_statement(text)
        credible_conf = self._check_conflict_credibility(text, has_conflict, flags)
        reviewer_sugg = self._check_reviewer_suggestions(text, flags)
        special       = self._check_special_issue(text, flags)
        predatory     = self._check_predatory_signals(text, flags)
        editor_cite   = self._check_editor_self_citation(text, flags)

        score     = self._compute_score(
            days, has_conflict, credible_conf,
            reviewer_sugg, special, predatory, editor_cite
        )
        risk      = self._get_risk_level(score)

        return PeerReviewResult(
            days_to_acceptance      = days,
            has_conflict_statement  = has_conflict,
            conflict_credible       = credible_conf,
            reviewer_suggestions    = reviewer_sugg,
            special_issue           = special,
            predatory_signals       = predatory,
            self_citation_of_editor = round(editor_cite, 3),
            manipulation_score      = round(score, 3),
            risk_level              = risk,
            summary                 = self._write_summary(flags, risk, days),
            flags                   = flags,
            flags_count             = len(flags),
        )

    # ── timeline analysis ──────────────────────────────────────────────────────

    def _measure_acceptance_speed(self, text: str, flags: list) -> int:
        """
        Extract submission and acceptance dates and compute the gap in days.
        Legitimate peer review takes 30-180 days on average.
        Under 14 days is a strong manipulation signal.
        Under 7 days is near-certain manipulation or editorial bypass.
        """
        dates = {}
        text_lo = text.lower()

        for marker_type in ["received", "accepted", "submitted", "revised"]:
            pattern = rf'{marker_type}[:\s]+([a-z]+\s+\d{{1,2}},?\s+\d{{4}}|\d{{1,2}}\s+[a-z]+\s+\d{{4}})'
            match   = re.search(pattern, text_lo)
            if match:
                parsed = self._parse_date_string(match.group(1))
                if parsed:
                    dates[marker_type] = parsed

        submit_key = "received" if "received" in dates else "submitted"
        accept_key = "accepted"

        if submit_key not in dates or accept_key not in dates:
            return -1

        delta = (dates[accept_key] - dates[submit_key]).days

        if delta < 0:
            return -1

        if delta <= 7:
            flags.append(ReviewFlag(
                flag_type   = "instant_acceptance",
                severity    = "high",
                description = (
                    f"Paper accepted in {delta} day(s) — "
                    f"faster than any legitimate peer review process. "
                    f"Standard review takes 30-180 days. "
                    f"This timeline indicates editorial bypass or "
                    f"pre-arranged acceptance."
                ),
                evidence    = (
                    f"Submission to acceptance gap: {delta} days. "
                    f"Dates extracted from paper header."
                ),
                suggestion  = (
                    "Verify the review timeline against the journal's "
                    "published average review duration. Report to the "
                    "editorial board if discrepancy is confirmed."
                ),
            ))
        elif delta <= 14:
            flags.append(ReviewFlag(
                flag_type   = "unusually_fast_acceptance",
                severity    = "medium",
                description = (
                    f"Paper accepted in {delta} days — "
                    f"significantly below the typical 30-180 day range. "
                    f"This speed is consistent with compromised review."
                ),
                evidence    = f"Submission to acceptance gap: {delta} days.",
                suggestion  = (
                    "Cross-check with the journal's stated review timeline."
                ),
            ))

        return max(delta, 0)

    def _parse_date_string(self, raw: str):
        """Parse common academic date formats into a datetime object."""
        raw = raw.strip().lower().replace(",", "")
        parts = raw.split()

        if len(parts) < 3:
            return None

        try:
            # format: "january 15 2023" or "15 january 2023"
            if parts[0].isdigit():
                day   = int(parts[0])
                month = MONTH_ORDER.get(parts[1], 0)
                year  = int(parts[2])
            else:
                month = MONTH_ORDER.get(parts[0], 0)
                day   = int(parts[1])
                year  = int(parts[2])

            if not month or not (1 <= day <= 31) or not (2000 <= year <= 2030):
                return None

            return datetime(year, month, day)
        except (ValueError, IndexError):
            return None

    # ── conflict of interest ───────────────────────────────────────────────────

    def _check_conflict_statement(self, text: str) -> bool:
        """Check whether any conflict of interest statement exists."""
        text_lo = text.lower()
        return any(phrase in text_lo for phrase in CONFLICT_RED_FLAGS + [
            "conflict of interest", "competing interest",
            "financial disclosure", "funding source",
        ])

    def _check_conflict_credibility(
        self, text: str, has_conflict: bool, flags: list
    ) -> bool:
        """
        A boilerplate 'no conflicts' statement with no specific details
        is less credible than a detailed disclosure.
        Missing conflict statement is always a flag in funded research.
        """
        text_lo = text.lower()

        has_funding = any(w in text_lo for w in [
            "funded by", "supported by", "grant", "foundation",
            "ministry", "national science", "european research",
        ])

        if not has_conflict and has_funding:
            flags.append(ReviewFlag(
                flag_type   = "missing_conflict_statement",
                severity    = "medium",
                description = (
                    "Funding acknowledgment detected but no conflict of "
                    "interest statement found. Most journals require authors "
                    "to declare potential conflicts when external funding exists."
                ),
                evidence    = "Funding mention present; conflict statement absent.",
                suggestion  = (
                    "Add a conflict of interest section disclosing all "
                    "funding sources and potential financial relationships."
                ),
            ))
            return False

        boilerplate_only = has_conflict and not any(w in text_lo for w in [
            "received funding", "consultant", "honorarium", "stock",
            "employee of", "board member", "owns shares",
        ])

        return not boilerplate_only

    # ── reviewer manipulation ──────────────────────────────────────────────────

    def _check_reviewer_suggestions(self, text: str, flags: list) -> bool:
        """
        Some journals allow authors to suggest reviewers.
        When this language appears in the paper itself, it may indicate
        that the suggestion process was leveraged inappropriately.
        """
        text_lo = text.lower()
        found   = any(m in text_lo for m in REVIEWER_SUGGESTION_MARKERS)

        if found:
            flags.append(ReviewFlag(
                flag_type   = "reviewer_suggestion_language",
                severity    = "low",
                description = (
                    "The paper contains language related to reviewer suggestions. "
                    "While suggesting reviewers is legitimate, it becomes "
                    "problematic when suggested reviewers are undisclosed "
                    "collaborators or colleagues."
                ),
                evidence    = "Reviewer suggestion language detected in paper text.",
                suggestion  = (
                    "Verify that suggested reviewers had no prior relationship "
                    "with the authors within the past 5 years."
                ),
            ))

        return found

    # ── special issue bypass ───────────────────────────────────────────────────

    def _check_special_issue(self, text: str, flags: list) -> bool:
        """
        Special issues and invited papers often undergo lighter review.
        This is not inherently fraudulent but reduces scrutiny significantly.
        """
        text_lo = text.lower()
        found   = any(m in text_lo for m in SPECIAL_ISSUE_MARKERS)

        if found:
            flags.append(ReviewFlag(
                flag_type   = "special_issue_bypass",
                severity    = "low",
                description = (
                    "Paper appears to be a special issue or invited submission. "
                    "These papers often receive expedited or reduced peer review, "
                    "lowering the scrutiny applied to methodology and data."
                ),
                evidence    = "Special issue or invited paper language detected.",
                suggestion  = (
                    "Apply the same rigor to special issue papers as to "
                    "regular submissions when evaluating integrity."
                ),
            ))

        return found

    # ── predatory signals ──────────────────────────────────────────────────────

    def _check_predatory_signals(self, text: str, flags: list) -> int:
        """
        Predatory journals guarantee acceptance, charge fees without
        providing genuine review, and compromise the integrity of the
        entire publication. Their language patterns are distinctive.
        """
        text_lo = text.lower()
        found   = [s for s in PREDATORY_SIGNALS if s in text_lo]

        if len(found) >= 2:
            flags.append(ReviewFlag(
                flag_type   = "predatory_journal_signals",
                severity    = "high",
                description = (
                    f"{len(found)} predatory journal marker(s) detected. "
                    f"These signals suggest the paper may have been published "
                    f"in a venue that does not conduct genuine peer review."
                ),
                evidence    = f"Markers found: {found[:4]}.",
                suggestion  = (
                    "Verify the journal's legitimacy using Beall's list, "
                    "DOAJ whitelist, or Cabell's Journalytics before "
                    "citing or building on this work."
                ),
            ))
        elif len(found) == 1:
            flags.append(ReviewFlag(
                flag_type   = "possible_predatory_signal",
                severity    = "low",
                description = (
                    f"One predatory journal marker detected: '{found[0]}'. "
                    f"Alone this is not conclusive, but warrants verification."
                ),
                evidence    = f"Marker: {found[0]}.",
                suggestion  = "Verify journal legitimacy.",
            ))

        return len(found)

    # ── editor self-citation ───────────────────────────────────────────────────

    def _check_editor_self_citation(self, text: str, flags: list) -> float:
        """
        Some authors identify the handling editor and then cite them
        heavily — a known strategy to guarantee favorable review.
        We measure citation density around editor-identification language.
        """
        text_lo      = text.lower()
        editor_markers = ["editor", "handling editor", "associate editor", "guest editor"]
        has_editor   = any(m in text_lo for m in editor_markers)

        if not has_editor:
            return 0.0

        # count citations in a window around editor mentions
        total_citations = len(re.findall(
            r'[A-Z][a-z]+\s+\(\d{4}\)', text
        ))

        if total_citations == 0:
            return 0.0

        # citations within 500 chars of an editor mention
        editor_adjacent = 0
        for marker in editor_markers:
            idx = text_lo.find(marker)
            while idx != -1:
                window = text[max(0, idx - 250): idx + 250]
                editor_adjacent += len(re.findall(
                    r'[A-Z][a-z]+\s+\(\d{4}\)', window
                ))
                idx = text_lo.find(marker, idx + 1)

        ratio = min(editor_adjacent / max(total_citations, 1), 1.0)

        if ratio >= 0.30:
            flags.append(ReviewFlag(
                flag_type   = "editor_citation_concentration",
                severity    = "medium",
                description = (
                    f"{round(ratio * 100, 1)}% of citations cluster "
                    f"near editor-identification language. "
                    f"Concentrating citations around the editor is a "
                    f"known strategy to incentivize favorable review."
                ),
                evidence    = (
                    f"Editor mentions: present. "
                    f"Citations near editor language: {editor_adjacent} "
                    f"of {total_citations} total."
                ),
                suggestion  = (
                    "Ensure citations reflect genuine intellectual debt "
                    "rather than reviewer management strategy."
                ),
            ))

        return ratio

    # ── scoring ────────────────────────────────────────────────────────────────

    def _compute_score(
        self,
        days:          int,
        has_conflict:  bool,
        credible_conf: bool,
        reviewer_sugg: bool,
        special:       bool,
        predatory:     int,
        editor_cite:   float,
    ) -> float:
        score = 0.0

        if days >= 0:
            if days <= 7:
                score += 0.40
            elif days <= 14:
                score += 0.25
            elif days <= 21:
                score += 0.10

        if not has_conflict:
            score += 0.15
        elif not credible_conf:
            score += 0.08

        if reviewer_sugg:
            score += 0.08
        if special:
            score += 0.05
        if predatory >= 2:
            score += 0.30
        elif predatory == 1:
            score += 0.10

        score += editor_cite * 0.15

        return min(score, 1.0)

    def _get_risk_level(self, score: float) -> str:
        if score >= 0.70:   return "critical"
        if score >= 0.45:   return "high"
        if score >= 0.20:   return "medium"
        return "low"

    def _write_summary(
        self, flags: list, risk_level: str, days: int
    ) -> str:
        timeline = ""
        if days >= 0:
            timeline = f" Acceptance timeline: {days} days."

        if not flags:
            return (
                f"Peer Review Analysis: No manipulation signals detected."
                f"{timeline} Review process appears standard. "
                f"Risk level: {risk_level.upper()}."
            )

        high   = sum(1 for f in flags if f.severity == "high")
        medium = sum(1 for f in flags if f.severity == "medium")
        low    = sum(1 for f in flags if f.severity == "low")
        parts  = []
        if high:
            parts.append(f"{high} high-severity signal{'s' if high > 1 else ''}")
        if medium:
            parts.append(f"{medium} medium concern{'s' if medium > 1 else ''}")
        if low:
            parts.append(f"{low} low-severity indicator{'s' if low > 1 else ''}")

        return (
            f"Peer Review Analysis: {', '.join(parts)} detected."
            f"{timeline} Risk level: {risk_level.upper()}."
        )