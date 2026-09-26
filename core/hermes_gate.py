"""Hermes Update Gate Engine.

Manages safe, commit-exact updates for Hermes Agent.
Tracks approved commit SHAs, analyzes risk of candidate commits, detects
sensitive changes in Desktop/SDK/Plugins, issues GO/NO-GO decisions, and provides rollback.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple

try:
    from core.runtime_paths import get_default_hermes_home
except ModuleNotFoundError:
    from runtime_paths import get_default_hermes_home

DEFAULT_HERMES_REPO = Path(
    os.environ.get("HERMES_AGENT_PATH") or get_default_hermes_home() / "hermes-agent"
).resolve()
DEFAULT_GATE_CONFIG = Path(__file__).resolve().parents[1] / "config" / "hermes_gate.json"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GateDecision(str, Enum):
    GO = "GO"
    NO_GO = "NO-GO"
    OVERRIDE = "OVERRIDE"


@dataclass
class CommitInfo:
    sha: str
    short_sha: str
    version: str
    author: str
    date: str
    summary: str
    body: str = ""


@dataclass
class ChangedFile:
    path: str
    status: str  # M, A, D, R, etc.
    category: str
    risk_level: RiskLevel
    risk_reasons: List[str] = field(default_factory=list)


@dataclass
class KnownIssue:
    id: str
    url: str
    description: str
    blocked_patterns: List[str]
    status: str = "OPEN"  # OPEN, RESOLVED, MITIGATED

    def matches(self, files: List[str], commit_messages: List[str]) -> List[str]:
        if self.status != "OPEN":
            return []
        matches = []
        for pattern in self.blocked_patterns:
            pat_lower = pattern.lower()
            for f in files:
                if pat_lower in f.lower():
                    matches.append(f"Arquivo '{f}' corresponde ao padrão sensível '{pattern}' da Issue #{self.id}")
            for msg in commit_messages:
                if pat_lower in msg.lower():
                    matches.append(f"Mensagem de commit contém '{pattern}' vinculada à Issue #{self.id}")
        return list(dict.fromkeys(matches))


@dataclass
class ApprovedCommitState:
    sha: str
    short_sha: str
    version: str
    approved_at: str
    approved_by: str = "system"
    notes: str = ""
    commit_summary: str = ""


@dataclass
class GateState:
    approved: ApprovedCommitState
    history: List[ApprovedCommitState] = field(default_factory=list)
    known_issues: List[KnownIssue] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GateState":
        approved_data = data.get("approved", {})
        approved = ApprovedCommitState(
            sha=approved_data.get("sha", ""),
            short_sha=approved_data.get("short_sha", approved_data.get("sha", "")[:7]),
            version=approved_data.get("version", "0.0.0"),
            approved_at=approved_data.get("approved_at", datetime.now(timezone.utc).isoformat()),
            approved_by=approved_data.get("approved_by", "system"),
            notes=approved_data.get("notes", ""),
            commit_summary=approved_data.get("commit_summary", ""),
        )
        history = [
            ApprovedCommitState(
                sha=h.get("sha", ""),
                short_sha=h.get("short_sha", h.get("sha", "")[:7]),
                version=h.get("version", "0.0.0"),
                approved_at=h.get("approved_at", ""),
                approved_by=h.get("approved_by", "system"),
                notes=h.get("notes", ""),
                commit_summary=h.get("commit_summary", ""),
            )
            for h in data.get("history", [])
        ]
        known_issues = [
            KnownIssue(
                id=str(iss.get("id", "")),
                url=iss.get("url", ""),
                description=iss.get("description", ""),
                blocked_patterns=iss.get("blocked_patterns", []),
                status=iss.get("status", "OPEN"),
            )
            for iss in data.get("known_issues", [])
        ]
        return cls(approved=approved, history=history, known_issues=known_issues)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approved": dataclasses.asdict(self.approved),
            "history": [dataclasses.asdict(h) for h in self.history],
            "known_issues": [dataclasses.asdict(iss) for iss in self.known_issues],
        }


@dataclass
class DiffReport:
    current_sha: str
    current_short_sha: str
    current_version: str
    approved_sha: str
    approved_short_sha: str
    approved_version: str
    candidate_sha: str
    candidate_short_sha: str
    candidate_version: str
    commits: List[CommitInfo]
    changed_files: List[ChangedFile]
    raw_diff_stat: str
    risk_level: RiskLevel
    decision: GateDecision
    reasons: List[str]
    warnings: List[str]
    is_behind_approved: bool = False
    is_same_as_approved: bool = False
    is_same_as_current: bool = False


KNOWN_GOOD_BASELINE_SHA = "ead7e91dabf1e963796ec834b196984a2fa44ff4"


class HermesUpdateGate:
    """Gatekeeper controller for Hermes Agent updates."""

    def __init__(
        self,
        repo_path: Optional[Path | str] = None,
        config_path: Optional[Path | str] = None,
    ) -> None:
        self.repo_path = Path(repo_path or os.environ.get("HERMES_AGENT_PATH") or DEFAULT_HERMES_REPO).resolve()
        self.config_path = Path(config_path or os.environ.get("HERMES_GATE_CONFIG") or DEFAULT_GATE_CONFIG).resolve()
        self._ensure_config_initialized()

    def _run_git(self, args: List[str], check: bool = True) -> str:
        """Executes a git command in the Hermes repo."""
        if not self.repo_path.is_dir() or not (self.repo_path / ".git").exists():
            raise FileNotFoundError(f"Repositório git do Hermes não encontrado em: {self.repo_path}")
        cmd = ["git"] + args
        res = subprocess.run(
            cmd,
            cwd=str(self.repo_path),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if check and res.returncode != 0:
            raise RuntimeError(f"Git command failed ({' '.join(cmd)}): {res.stderr.strip()}")
        return res.stdout.strip()

    def _ensure_config_initialized(self) -> None:
        """Initializes gate config file with the canonical known-good baseline if not present."""
        if not self.config_path.exists():
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            approved_sha = KNOWN_GOOD_BASELINE_SHA
            version = "0.21.1"
            summary = "refactor(recovery): stream the salvaged population; table the shape rules"
            if self.repo_path.exists() and (self.repo_path / ".git").exists():
                try:
                    version = self.extract_version_at_ref(approved_sha)
                    summary = self._run_git(["log", "-1", "--pretty=format:%s", approved_sha])
                except Exception:
                    pass

            initial_state = GateState(
                approved=ApprovedCommitState(
                    sha=approved_sha,
                    short_sha=approved_sha[:7],
                    version=version,
                    approved_at="2026-09-09T18:28:57+05:30",
                    approved_by="canonical_baseline",
                    notes="Último commit known-good validado antes da regressão de injeção de plugin no runtime loader (Issue #107312).",
                    commit_summary=summary,
                ),
                history=[],
                known_issues=[
                    KnownIssue(
                        id="107312",
                        url="https://github.com/NousResearch/hermes-agent/issues/107312",
                        description="Desktop plugin SDK runtime injection TypeError: Cannot convert undefined or null to object devido a chunk hoisting / avaliação circular.",
                        blocked_patterns=[
                            "apps/desktop/src/sdk/runtime.ts",
                            "apps/desktop/src/contrib/runtime-loader.ts",
                            "GLOBALS.__HERMES_PLUGIN_SDK__",
                            "@hermes/plugin-sdk",
                        ],
                        status="OPEN",
                    )
                ],
            )
            self.save_state(initial_state)

    def load_state(self) -> GateState:
        """Loads state from config json."""
        if not self.config_path.exists():
            self._ensure_config_initialized()
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return GateState.from_dict(data)

    def save_state(self, state: GateState) -> None:
        """Saves state to config json atomically."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.config_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)
        tmp_path.replace(self.config_path)

    def extract_version_at_ref(self, ref: str) -> str:
        """Extracts __version__ from hermes_cli/__init__.py at a specific git ref."""
        try:
            content = self._run_git(["show", f"{ref}:hermes_cli/__init__.py"], check=False)
            match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
        except Exception:
            pass
        return "0.0.0"

    def get_commit_info(self, ref: str) -> CommitInfo:
        """Returns metadata for a specific commit ref."""
        sha = self._run_git(["rev-parse", ref])
        short_sha = sha[:7]
        version = self.extract_version_at_ref(sha)
        log_line = self._run_git(["log", "-1", "--pretty=format:%an|%ad|%s|%b", "--date=iso-strict", sha])
        parts = log_line.split("|", 3)
        author = parts[0] if len(parts) > 0 else "unknown"
        date = parts[1] if len(parts) > 1 else ""
        summary = parts[2] if len(parts) > 2 else ""
        body = parts[3] if len(parts) > 3 else ""
        return CommitInfo(
            sha=sha,
            short_sha=short_sha,
            version=version,
            author=author,
            date=date,
            summary=summary,
            body=body.strip(),
        )

    def get_current_commit(self) -> CommitInfo:
        """Returns metadata for current working HEAD."""
        return self.get_commit_info("HEAD")

    def fetch_remote(self, remote: str = "origin") -> None:
        """Fetches updates from remote."""
        self._run_git(["fetch", remote])

    def categorize_file(self, filepath: str) -> Tuple[str, RiskLevel, List[str]]:
        """Categorizes a file path and determines its inherent risk level."""
        fp = filepath.replace("\\", "/").strip()
        reasons = []

        # 1. Desktop Plugin SDK / Runtime Loader (CRITICAL)
        if fp.startswith("apps/desktop/src/sdk/") or fp in (
            "apps/desktop/src/contrib/runtime-loader.ts",
            "apps/desktop/src/contrib/plugin.ts",
        ):
            reasons.append("Modifica runtime loader ou SDK de plugins do Desktop (risco de quebra de contrato/importação)")
            return ("DESKTOP_SDK", RiskLevel.CRITICAL, reasons)

        # 2. Desktop UI App (HIGH - Rebuild required)
        if fp.startswith("apps/desktop/"):
            reasons.append("Modifica componentes do Hermes Desktop (requer rebuild de release/assets)")
            return ("DESKTOP_APP", RiskLevel.HIGH, reasons)

        # 3. Plugin Backend / Subcommands (HIGH)
        if fp.startswith("hermes_cli/plugins/") or "plugin" in fp.lower():
            reasons.append("Modifica infraestrutura ou CLI de plugins do backend")
            return ("PLUGIN_BACKEND", RiskLevel.HIGH, reasons)

        # 4. Gateway / Platforms / Agent lifecycle (MEDIUM/HIGH)
        if fp.startswith("gateway/") or fp.startswith("agent/"):
            reasons.append("Modifica subsistemas de gateway ou ciclo de vida do agente")
            return ("GATEWAY_CORE", RiskLevel.MEDIUM, reasons)

        # 5. CLI commands / Tools (MEDIUM)
        if fp.startswith("hermes_cli/") or fp.startswith("tools/") or fp == "cli.py":
            reasons.append("Modifica comandos da CLI ou ferramentas nativas")
            return ("CLI_TOOLS", RiskLevel.MEDIUM, reasons)

        # 6. Docs, tests, evals, website (LOW)
        if any(fp.startswith(p) for p in ("docs/", "website/", "tests/", "evals/", "benchmarks/")):
            return ("DOCS_TESTS", RiskLevel.LOW, ["Documentação ou testes automatizados"])

        return ("GENERAL", RiskLevel.LOW, ["Outras alterações"])

    def analyze_diff(
        self,
        from_sha: str,
        to_sha: str,
        state: Optional[GateState] = None,
    ) -> DiffReport:
        """Analyzes all changes between from_sha and to_sha and determines GO/NO-GO decision."""
        if state is None:
            state = self.load_state()

        current = self.get_current_commit()
        approved = state.approved

        from_commit = self.get_commit_info(from_sha)
        to_commit = self.get_commit_info(to_sha)

        if from_commit.sha == to_commit.sha:
            return DiffReport(
                current_sha=current.sha,
                current_short_sha=current.short_sha,
                current_version=current.version,
                approved_sha=approved.sha,
                approved_short_sha=approved.short_sha,
                approved_version=approved.version,
                candidate_sha=to_commit.sha,
                candidate_short_sha=to_commit.short_sha,
                candidate_version=to_commit.version,
                commits=[],
                changed_files=[],
                raw_diff_stat="",
                risk_level=RiskLevel.LOW,
                decision=GateDecision.GO,
                reasons=["Nenhuma diferença entre os commits especificados."],
                warnings=[],
                is_same_as_approved=(to_commit.sha == approved.sha),
                is_same_as_current=(to_commit.sha == current.sha),
            )

        # Retrieve commit list
        raw_log = self._run_git([
            "log",
            "--pretty=format:%H|%h|%an|%ad|%s",
            "--date=iso-strict",
            f"{from_commit.sha}..{to_commit.sha}",
        ])
        commits: List[CommitInfo] = []
        if raw_log:
            for line in raw_log.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split("|", 4)
                if len(parts) >= 5:
                    c_sha, c_short, c_author, c_date, c_sum = parts
                    c_ver = self.extract_version_at_ref(c_sha)
                    commits.append(
                        CommitInfo(
                            sha=c_sha,
                            short_sha=c_short,
                            version=c_ver,
                            author=c_author,
                            date=c_date,
                            summary=c_sum,
                        )
                    )

        # Retrieve diff stat
        raw_diff_stat = self._run_git(["diff", "--stat", f"{from_commit.sha}..{to_commit.sha}"])

        # Retrieve name-status files
        raw_files = self._run_git(["diff", "--name-status", f"{from_commit.sha}..{to_commit.sha}"])
        changed_files: List[ChangedFile] = []
        file_paths: List[str] = []
        if raw_files:
            for line in raw_files.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    status, path = parts
                    file_paths.append(path)
                    category, risk, reasons = self.categorize_file(path)
                    changed_files.append(
                        ChangedFile(
                            path=path,
                            status=status,
                            category=category,
                            risk_level=risk,
                            risk_reasons=reasons,
                        )
                    )

        # Evaluate risk level & reasons
        highest_risk = RiskLevel.LOW
        reasons: List[str] = []
        warnings: List[str] = []

        # 1. Check known issues (e.g. #107312)
        commit_summaries = [c.summary for c in commits]
        for issue in state.known_issues:
            matches = issue.matches(file_paths, commit_summaries)
            if matches:
                highest_risk = RiskLevel.CRITICAL
                reasons.append(
                    f"[BLOQUEIO] Alerta de Issue Ativa #{issue.id} ({issue.url}): "
                    + "; ".join(matches)
                )

        # 2. Check file-level risks
        for cf in changed_files:
            if cf.risk_level == RiskLevel.CRITICAL:
                highest_risk = RiskLevel.CRITICAL
                reasons.extend(cf.risk_reasons)
            elif cf.risk_level == RiskLevel.HIGH and highest_risk != RiskLevel.CRITICAL:
                highest_risk = RiskLevel.HIGH
                warnings.extend(cf.risk_reasons)
            elif cf.risk_level == RiskLevel.MEDIUM and highest_risk not in (RiskLevel.CRITICAL, RiskLevel.HIGH):
                highest_risk = RiskLevel.MEDIUM

        # 3. Check commit message keywords
        for c in commits:
            sum_lower = c.summary.lower()
            if any(k in sum_lower for k in ("breaking", "breaking change", "drop legacy", "revert")):
                if highest_risk != RiskLevel.CRITICAL:
                    highest_risk = RiskLevel.HIGH
                warnings.append(f"Commit '{c.short_sha}' contém termo sensível: '{c.summary}'")

        # Deduplicate reasons and warnings
        reasons = list(dict.fromkeys(reasons))
        warnings = list(dict.fromkeys(warnings))

        # Determine Decision
        if highest_risk == RiskLevel.CRITICAL:
            decision = GateDecision.NO_GO
            if not reasons:
                reasons.append("Alterações críticas detectadas em componentes sensíveis (Desktop SDK / Plugin Loader).")
        elif highest_risk == RiskLevel.HIGH:
            decision = GateDecision.NO_GO
            reasons.append("Alterações estruturais em Desktop / Backend de plugins detectadas. Validação prévia requerida.")
        else:
            decision = GateDecision.GO
            if not reasons:
                reasons.append("Todas as alterações estão classificadas como seguras (LOW/MEDIUM risk).")

        return DiffReport(
            current_sha=current.sha,
            current_short_sha=current.short_sha,
            current_version=current.version,
            approved_sha=approved.sha,
            approved_short_sha=approved.short_sha,
            approved_version=approved.version,
            candidate_sha=to_commit.sha,
            candidate_short_sha=to_commit.short_sha,
            candidate_version=to_commit.version,
            commits=commits,
            changed_files=changed_files,
            raw_diff_stat=raw_diff_stat,
            risk_level=highest_risk,
            decision=decision,
            reasons=reasons,
            warnings=warnings,
            is_same_as_approved=(to_commit.sha == approved.sha),
            is_same_as_current=(to_commit.sha == current.sha),
        )

    def check_update(self, target_ref: str = "origin/main", fetch: bool = True) -> DiffReport:
        """Fetches remote and analyzes candidate vs approved SHA."""
        if fetch:
            try:
                self.fetch_remote()
            except Exception:
                pass
        state = self.load_state()
        return self.analyze_diff(from_sha=state.approved.sha, to_sha=target_ref, state=state)

    def approve_commit(
        self,
        ref: Optional[str] = None,
        notes: str = "",
        author: str = "user",
    ) -> ApprovedCommitState:
        """Records a new approved commit SHA in state."""
        target_ref = ref or "HEAD"
        info = self.get_commit_info(target_ref)
        state = self.load_state()

        new_approved = ApprovedCommitState(
            sha=info.sha,
            short_sha=info.short_sha,
            version=info.version,
            approved_at=datetime.now(timezone.utc).isoformat(),
            approved_by=author,
            notes=notes or f"Aprovação manual do commit {info.short_sha}",
            commit_summary=info.summary,
        )

        if state.approved.sha and state.approved.sha != new_approved.sha:
            state.history.insert(0, state.approved)

        state.approved = new_approved
        self.save_state(state)
        return new_approved

    def rebuild_desktop(self) -> Tuple[bool, str]:
        """Rebuilds and packages the Hermes Electron Desktop app executable from the current commit."""
        desktop_dir = self.repo_path / "apps" / "desktop"
        if not desktop_dir.exists():
            return (True, "Diretório apps/desktop não encontrado; rebuild do Desktop dispensado.")

        python_exe = self.repo_path / "venv" / "Scripts" / "python.exe"
        if not python_exe.exists():
            python_exe = Path(sys.executable)

        cmd = [str(python_exe), "-m", "hermes_cli.main", "desktop", "--build-only", "--force-build"]
        try:
            res = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if res.returncode != 0:
                err_msg = (res.stderr or res.stdout or f"exit code {res.returncode}").strip()
                return (False, f"Falha na reconstrução do Desktop: {err_msg}")
            return (True, "Desktop reconstruído e empacotado com sucesso a partir do commit atual.")
        except Exception as e:
            return (False, f"Erro ao executar rebuild do Desktop: {e}")

    def apply_update(
        self,
        target_ref: str = "origin/main",
        force: bool = False,
        dry_run: bool = False,
        rebuild_desktop: bool = True,
        author: str = "user",
        notes: str = "",
    ) -> Tuple[bool, str, Optional[DiffReport]]:
        """Applies update if GO (or force). Rebuilds desktop and updates approved SHA on success."""
        report = self.check_update(target_ref=target_ref, fetch=True)

        if report.is_same_as_current:
            return (True, f"Hermes já está exatamente no commit candidato {report.candidate_short_sha} (v{report.candidate_version}).", report)

        if report.decision == GateDecision.NO_GO and not force:
            reasons_str = "\n  - " + "\n  - ".join(report.reasons)
            return (
                False,
                f"UPDATE BLOQUEADO PELO GATE (NO-GO).\nMotivos:{reasons_str}\n\nPara forçar explicitamente assumindo o risco, use --force.",
                report,
            )

        if dry_run:
            msg = f"[DRY-RUN] Update para {report.candidate_short_sha} aprovado (Decisão: {report.decision.value}). Nenhuma alteração aplicada."
            if rebuild_desktop:
                msg += " Reconstrução do Desktop executável planejada."
            return (True, msg, report)

        # Apply checkout / fast-forward
        try:
            self._run_git(["checkout", report.candidate_sha])
        except Exception as e:
            return (False, f"Falha ao executar git checkout {report.candidate_short_sha}: {e}", report)

        rebuild_msg = ""
        if rebuild_desktop:
            success_build, b_msg = self.rebuild_desktop()
            if not success_build:
                return (False, f"Git atualizado para {report.candidate_short_sha}, mas falhou ao reconstruir Desktop: {b_msg}", report)
            rebuild_msg = f" ({b_msg})"

        # Record new approved commit
        self.approve_commit(
            ref=report.candidate_sha,
            notes=notes or f"Update aplicado com sucesso via Hermes Update Gate (Risco: {report.risk_level.value})",
            author=author,
        )

        return (True, f"Hermes atualizado com sucesso para {report.candidate_short_sha} (v{report.candidate_version}).{rebuild_msg}", report)

    def rollback(self, rebuild_desktop: bool = True, dry_run: bool = False) -> Tuple[bool, str]:
        """Rolls back Hermes working tree and rebuilds executable to the last approved SHA."""
        state = self.load_state()
        approved = state.approved

        if not approved.sha:
            return (False, "Nenhum commit aprovado registrado para rollback.")

        current = self.get_current_commit()
        if current.sha == approved.sha:
            return (True, f"Hermes já está no commit aprovado {approved.short_sha} (v{approved.version}).")

        if dry_run:
            msg = f"[DRY-RUN] Rollback planejado de {current.short_sha} para {approved.short_sha} (v{approved.version})."
            if rebuild_desktop:
                msg += " Reconstrução do Desktop executável planejada."
            return (True, msg)

        try:
            self._run_git(["checkout", approved.sha])
        except Exception as e:
            return (False, f"Falha ao executar rollback para {approved.short_sha}: {e}")

        rebuild_msg = ""
        if rebuild_desktop:
            success_build, b_msg = self.rebuild_desktop()
            if not success_build:
                return (False, f"Rollback para {approved.short_sha} concluído no Git, mas falhou ao reconstruir o Desktop: {b_msg}")
            rebuild_msg = f" ({b_msg})"

        return (True, f"Rollback concluído com sucesso. Hermes restaurado para {approved.short_sha} (v{approved.version}).{rebuild_msg}")

    def format_report_text(self, report: DiffReport, verbose: bool = False) -> str:
        """Formats the DiffReport into a clear terminal / markdown document."""
        lines = []
        lines.append("=" * 80)
        lines.append("                      HERMES UPDATE GATE REPORT")
        lines.append("=" * 80)
        lines.append(f"Versão Atual:       v{report.current_version} @ {report.current_short_sha} ({report.current_sha})")
        lines.append(f"Último Aprovado:    v{report.approved_version} @ {report.approved_short_sha} ({report.approved_sha})")
        lines.append(f"Candidato:          v{report.candidate_version} @ {report.candidate_short_sha} ({report.candidate_sha})")
        lines.append("-" * 80)

        # Summary stats
        num_commits = len(report.commits)
        num_files = len(report.changed_files)
        lines.append(f"Commits a aplicar:  {num_commits}")
        lines.append(f"Arquivos alterados: {num_files}")
        lines.append(f"Classificação Risco:{report.risk_level.value}")

        badge = "[ GO - APROVADO ]" if report.decision == GateDecision.GO else "[ NO-GO - BLOQUEADO ]"
        lines.append(f"Decisão Canônica:   {badge}")
        lines.append("-" * 80)

        if report.reasons:
            lines.append("MOTIVOS DA DECISÃO:")
            for r in report.reasons:
                lines.append(f"  * {r}")
            lines.append("")

        if report.warnings:
            lines.append("ALERTAS E ADVERTÊNCIAS:")
            for w in report.warnings:
                lines.append(f"  ! {w}")
            lines.append("")

        if report.commits:
            lines.append("COMMITS ENCONTRADOS:")
            for c in report.commits:
                lines.append(f"  - [{c.short_sha}] v{c.version} | {c.author} | {c.summary}")
            lines.append("")

        if report.changed_files:
            lines.append("ARQUIVOS IMPACTADOS:")
            for f in report.changed_files:
                risk_tag = f"[{f.risk_level.value}]"
                cat_tag = f"({f.category})"
                lines.append(f"  {f.status} {f.path:<50} {risk_tag:<10} {cat_tag}")
            lines.append("")

        if verbose and report.raw_diff_stat:
            lines.append("DIFF STAT:")
            for line in report.raw_diff_stat.split("\n"):
                lines.append(f"  {line}")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)
