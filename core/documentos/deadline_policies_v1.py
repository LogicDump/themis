"""Independent temporal policy contracts; no date arithmetic or real calendars."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

DayMode = Literal["BUSINESS", "CONTINUOUS"]
CalendarStatus = Literal["BUSINESS_DAY", "HOLIDAY", "SUSPENDED", "RECESS"]

# Reserved identifiers only. No real policy records or legal content are implied.
COUNTING_POLICY_IDENTITIES = (
    "CPC_BUSINESS_DAYS", "CPP_CONTINUOUS_DAYS", "CLT_BUSINESS_DAYS", "LAW_9099_BUSINESS_DAYS",
)
COMMUNICATION_METHODS = (
    "DJEN_PUBLICATION", "PERSONAL_ELECTRONIC_NOTICE", "SERVICE", "HEARING_NOTIFICATION", "OTHER",
)


@dataclass(frozen=True)
class CountingPolicy:
    policy_id: str
    policy_version: str
    legal_domain: str
    base_regime: str
    day_mode: DayMode
    include_start: bool | None
    include_end: bool | None
    expiry_adjustment: str
    suspension_policy_ids: tuple[str, ...]
    legal_basis: dict[str, Any]
    effective_from: str | None
    effective_to: str | None
    official_source: str | None
    authority: str
    verified_at: str


@dataclass(frozen=True)
class CommunicationPolicy:
    policy_id: str
    policy_version: str
    applicable_regimes: tuple[str, ...]
    communication_method: str
    trigger_event_type: str
    applicability_condition: str
    excluded_when_personal_required: bool
    legal_basis: dict[str, Any]
    effective_from: str | None
    effective_to: str | None
    official_source: tuple[str, ...]
    authority: str
    verified_at: str
    trigger_date_field: str | None = None

    def applies(self, *, regime: str, requires_personal_notice: bool) -> bool:
        regime_ok = "*" in self.applicable_regimes or regime in self.applicable_regimes
        personal_ok = not (self.excluded_when_personal_required and requires_personal_notice)
        return regime_ok and personal_ok


@dataclass(frozen=True)
class SuspensionPolicy:
    policy_id: str
    policy_version: str
    legal_domain: str
    base_regime: str
    period_start: str
    period_end: str
    inclusive: bool
    exceptions: tuple[dict[str, str], ...]
    legal_basis: dict[str, Any]
    effective_from: str
    effective_to: str | None
    official_source: str
    authority: str
    verified_at: str


@dataclass(frozen=True)
class CourtCalendar:
    jurisdiction: str
    court: str | None
    locality_unit: str | None
    date: str
    status: CalendarStatus
    scope: str
    official_source: str
    verified_at: str
    version: str


_VERIFIED = "2026-09-29"
_CPC = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm"
_CPP = "https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm"
_CLT = "https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm"
_CLT_13467 = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2017/lei/l13467.htm"
_CLT_13545 = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2017/lei/l13545.htm"
_JEC = "https://www.planalto.gov.br/ccivil_03/leis/l9099.htm"
_JEC_AMENDMENT = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13728.htm"
_RES455 = "https://atos.cnj.jus.br/atos/detalhar/4509"
_RES569 = "https://atos.cnj.jus.br/atos/detalhar/5691"

SUSPENSION_POLICIES: tuple[SuspensionPolicy, ...] = (
    SuspensionPolicy("CPC_ART_220_GENERAL", "1.0.0", "CIVIL", "CPC", "12-20", "01-20", True, (),
        {"statute": "Lei 13.105/2015", "article": "220", "paragraph": None}, "2016-03-18", None, _CPC,
        "Presidência da República", _VERIFIED),
    SuspensionPolicy("CPP_ART_798A_RECESS", "1.0.0", "CRIMINAL", "CPP", "12-20", "01-20", True,
        ({"exception_id": "INCISO_I", "exception": "réus presos nos processos vinculados a essas prisões", "basis": "inciso I"},
         {"exception_id": "INCISO_II", "exception": "procedimentos da Lei Maria da Penha", "basis": "inciso II"},
         {"exception_id": "INCISO_III", "exception": "medida urgente por despacho fundamentado", "basis": "inciso III"}),
        {"statute": "Lei 14.365/2022", "article": "798-A", "paragraph": None}, "2022-06-03", None,
        f"{_CPP} | https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/lei/l14365.htm",
        "Presidência da República", _VERIFIED),
    SuspensionPolicy("CLT_ART_775A_RECESS", "1.0.0", "LABOR", "CLT", "12-20", "01-20", True, (),
        {"statute": "Decreto-Lei 5.452/1943", "article": "775-A", "paragraph": None}, "2017-12-20", None, f"{_CLT} | {_CLT_13545}",
        "Presidência da República", _VERIFIED),
)

COUNTING_POLICIES: tuple[CountingPolicy, ...] = (
    CountingPolicy("CPC_BUSINESS_DAYS", "1.0.0", "CIVIL", "CPC", "BUSINESS", False, True,
        "NEXT_BUSINESS_DAY_PER_CPC_224", ("CPC_ART_220_GENERAL",),
        {"statute": "Lei 13.105/2015", "articles": ["219", "224"], "paragraph": None},
        "2016-03-18", None, _CPC, "Presidência da República", _VERIFIED),
    CountingPolicy("CPP_CONTINUOUS_DAYS", "1.0.0", "CRIMINAL", "CPP", "CONTINUOUS", False, True,
        "NEXT_BUSINESS_DAY_IF_SUNDAY_OR_HOLIDAY", ("CPP_ART_798A_RECESS",),
        {"statute": "Decreto-Lei 3.689/1941", "articles": ["798", "798-A"], "paragraphs": ["§ 1º", "§ 3º"]},
        "1942-01-01", None, f"{_CPP} | https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/lei/l14365.htm", "Presidência da República", _VERIFIED),
    CountingPolicy("CLT_BUSINESS_DAYS", "1.0.0", "LABOR", "CLT", "BUSINESS", False, True,
        "COURT_EXTENSION_ONLY_UNDER_CLT_775_1", ("CLT_ART_775A_RECESS",),
        {"statute": "Decreto-Lei 5.452/1943", "articles": ["775", "775-A"], "paragraph": "art. 775, § 1º"},
        "2017-11-11", None, f"{_CLT} | {_CLT_13467} | {_CLT_13545}", "Presidência da República", _VERIFIED),
    CountingPolicy("LAW_9099_BUSINESS_DAYS", "1.0.0", "SPECIAL_COURTS", "LAW_9099", "BUSINESS", None, None,
        "UNSPECIFIED_BY_ART_12A", (),
        {"statute": "Lei 9.099/1995", "article": "12-A", "paragraph": None,
         "unresolved": "art. 12-A não especifica inclusão do dia inicial/final"},
        "2018-11-01", None, f"{_JEC} | {_JEC_AMENDMENT}", "Presidência da República", _VERIFIED),
)

COMMUNICATION_POLICIES: tuple[CommunicationPolicy, ...] = (
    CommunicationPolicy("DJEN_PUBLICATION", "1.0.0", ("*",), "DJEN_PUBLICATION", "PUBLICATION",
        "Somente quando a lei não exigir vista ou intimação pessoal",
        True,
        {"statute": "Resolução CNJ 455/2022", "article": "11", "paragraph": "§ 3º",
         "amended_by": "Resolução CNJ 569/2024", "cpc_reference": "art. 224, §§ 1º e 2º"},
        "2024-08-15", None, (_RES455, _RES569), "Conselho Nacional de Justiça", _VERIFIED,
        "published_on"),
)

# Declarative regime defaults used only for express judicial terms without an
# explicit structured counting qualifier. Order is retained for auditability.
REGIME_COUNTING_POLICY_IDS: tuple[tuple[str, str], ...] = (
    ("CPC", "CPC_BUSINESS_DAYS"),
    ("CPP", "CPP_CONTINUOUS_DAYS"),
    ("CLT", "CLT_BUSINESS_DAYS"),
    ("LAW_9099", "LAW_9099_BUSINESS_DAYS"),
)

COUNTING_QUALIFIER_MODES: tuple[tuple[str, str], ...] = (
    ("BUSINESS_DAYS", "BUSINESS"),
    ("CONTINUOUS_DAYS", "CONTINUOUS"),
)


def validate_counting_policy(policy: CountingPolicy) -> None:
    if policy.day_mode not in {"BUSINESS", "CONTINUOUS"}:
        raise ValueError("day_mode inválido")
    if not policy.policy_id or not policy.policy_version or not policy.official_source or not policy.authority or not policy.verified_at:
        raise ValueError("CountingPolicy exige versionamento e provenance oficial")
    if not isinstance(policy.legal_basis, dict) or not policy.effective_from:
        raise ValueError("CountingPolicy exige base legal e vigência")


def validate_communication_policy(policy: CommunicationPolicy) -> None:
    if not all((policy.policy_id, policy.policy_version, policy.trigger_event_type,
                policy.official_source, policy.authority, policy.verified_at)):
        raise ValueError("CommunicationPolicy exige identidade, versão e provenance oficial")
    if not policy.legal_basis or not policy.effective_from:
        raise ValueError("CommunicationPolicy exige base legal e vigência")
    if not all(source.startswith("https://") for source in policy.official_source):
        raise ValueError("CommunicationPolicy aceita somente fontes HTTPS oficiais")


def validate_suspension_policy(policy: SuspensionPolicy) -> None:
    if not policy.official_source or not policy.authority or not policy.verified_at:
        raise ValueError("SuspensionPolicy exige provenance oficial")
    if not policy.legal_basis or not policy.effective_from:
        raise ValueError("SuspensionPolicy exige base legal e vigência")
