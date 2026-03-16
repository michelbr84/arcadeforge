"""Static code scanner for game source code.

Scans generated/user-submitted code for dangerous patterns before
execution in sandbox. Starts with a denylist approach, designed to
evolve toward an allowlist model.

Strategy pattern: ScanStrategy base with DenylistStrategy (current)
and future AllowlistStrategy.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ScanFinding:
    """A single finding from the code scanner."""

    line: int
    pattern: str
    severity: str  # "critical", "high", "medium", "low"
    message: str


@dataclass
class ScanResult:
    """Result of scanning game source code."""

    passed: bool
    findings: list[ScanFinding] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "critical")

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "high")


class ScanStrategy(ABC):
    """Base class for code scanning strategies."""

    @abstractmethod
    def scan(self, code: str) -> ScanResult:
        ...


# --- Denylist patterns ---

DENY_PATTERNS: list[tuple[str, str, str]] = [
    # (regex, severity, message)
    # Critical: direct code execution / system access
    (r"\bimport\s+os\b", "critical", "Imports os module — filesystem/process access"),
    (r"\bfrom\s+os\b", "critical", "Imports from os module"),
    (r"\bimport\s+subprocess\b", "critical", "Imports subprocess — command execution"),
    (r"\bfrom\s+subprocess\b", "critical", "Imports from subprocess"),
    (r"\bimport\s+shutil\b", "critical", "Imports shutil — filesystem manipulation"),
    (r"\bimport\s+socket\b", "critical", "Imports socket — network access"),
    (r"\bfrom\s+socket\b", "critical", "Imports from socket"),
    (r"\bimport\s+ctypes\b", "critical", "Imports ctypes — native code execution"),
    (r"\bimport\s+importlib\b", "critical", "Imports importlib — dynamic module loading"),
    (r"\b__import__\s*\(", "critical", "Uses __import__() — dynamic import"),
    (r"\bexec\s*\(", "critical", "Uses exec() — arbitrary code execution"),
    (r"\beval\s*\(", "critical", "Uses eval() — arbitrary expression evaluation"),
    (r"\bcompile\s*\(", "high", "Uses compile() — code compilation"),
    # High: file system access
    (r"\bopen\s*\(", "high", "Uses open() — file access"),
    (r"\bimport\s+pathlib\b", "high", "Imports pathlib — filesystem access"),
    (r"\bimport\s+glob\b", "high", "Imports glob — filesystem traversal"),
    (r"\bimport\s+tempfile\b", "high", "Imports tempfile — temp file creation"),
    # High: network
    (r"\bimport\s+http\b", "high", "Imports http module"),
    (r"\bimport\s+urllib\b", "high", "Imports urllib — network requests"),
    (r"\bimport\s+requests\b", "high", "Imports requests library"),
    # Medium: potentially dangerous
    (r"\bimport\s+pickle\b", "medium", "Imports pickle — deserialization risk"),
    (r"\bimport\s+marshal\b", "medium", "Imports marshal — deserialization risk"),
    (r"\bimport\s+multiprocessing\b", "medium", "Imports multiprocessing"),
    (r"\bimport\s+threading\b", "medium", "Imports threading"),
    (r"\bimport\s+signal\b", "medium", "Imports signal — process signals"),
]

# Allowed imports (for informational purposes — future allowlist)
ALLOWED_IMPORTS = {
    "pygame", "random", "math", "time", "sys", "json",
    "collections", "itertools", "functools", "enum",
    "dataclasses", "typing", "abc",
}


class DenylistStrategy(ScanStrategy):
    """Scan using a denylist of dangerous patterns.

    Any match against a critical pattern fails the scan.
    High patterns also fail. Medium patterns are warnings.
    """

    def scan(self, code: str) -> ScanResult:
        findings: list[ScanFinding] = []
        lines = code.split("\n")

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Skip comments
            if stripped.startswith("#"):
                continue

            for pattern, severity, message in DENY_PATTERNS:
                if re.search(pattern, line):
                    findings.append(
                        ScanFinding(
                            line=line_num,
                            pattern=pattern,
                            severity=severity,
                            message=message,
                        )
                    )

        # Fail if any critical or high findings
        passed = all(f.severity not in ("critical", "high") for f in findings)

        return ScanResult(passed=passed, findings=findings)


# Default scanner instance
_scanner = DenylistStrategy()


def scan_code(code: str) -> ScanResult:
    """Scan game source code for dangerous patterns.

    Returns ScanResult with passed=True/False and findings list.
    """
    return _scanner.scan(code)
