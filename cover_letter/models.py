"""자소서 서비스 공유 도메인 모델."""

from dataclasses import dataclass, field


@dataclass
class Experience:
    """프로필에서 추출한 개별 경험."""

    key: str
    title: str
    description: str
    period: str = ""
    competencies: list[str] = field(default_factory=list)


@dataclass
class WritingStyle:
    """프로필에서 추출한 문체 스타일."""

    sentence_length: str = "medium"
    tone: str = "formal"
    expression_patterns: list[str] = field(default_factory=list)
    avoid_patterns: list[str] = field(default_factory=list)


@dataclass
class MappingEntry:
    """경험-질문 매핑 엔티티."""

    experience_key: str
    usage_type: str
    relevance_score: int
    rationale: str


@dataclass
class DiagnosisIssue:
    """자가 진단 이슈."""

    issue: str
    text: str
    suggestion: str


@dataclass
class JD:
    """직무기술서(JD) 엔티티."""

    job_analysis_id: int
    raw_text: str
    source_type: str  # 'firecrawl' | 'pdf' | 'manual'
    source_url: str = ""
    required_competencies: list[str] = field(default_factory=list)
