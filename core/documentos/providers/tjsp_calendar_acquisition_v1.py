"""Automatic acquisition/parser for TJSP's official holiday JSON endpoints."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Callable, Mapping

from core.documentos.court_calendar_composer_v1 import (
    CalendarComposition, CalendarCompositionRequest, compose_calendar,
)
from core.documentos.court_calendar_provider_v1 import (
    CalendarProviderRequest, RawSourceSnapshot, fetch_official_snapshot,
)
from core.documentos.court_calendar_store_v1 import get_snapshot, store_calendar_events, store_snapshot
from core.documentos.deadline_policies_v1 import CourtCalendar

PROVIDER_ID = "TJSP_JSON_CALENDAR_ACQUISITION_V1"
PARSER_VERSION = "tjsp-json-calendar-v1.0.0"
HOLIDAYS_ENDPOINT = "https://www.tjsp.jus.br/CanaisComunicacao/Feriados/PesquisarFeriados"
SUSPENSIONS_ENDPOINT = "https://www.tjsp.jus.br/CanaisComunicacao/Feriados/PesquisarSuspensoes"
INSTITUTIONAL_SOURCE = "https://www.tjsp.jus.br/CanaisComunicacao/SuspensaoPrazos"
OFFICIAL_HOSTS = ("www.tjsp.jus.br",)
_DATE_FORMAT = "%d/%m/%Y"
_RANGE = re.compile(r"^\s*(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})\s*$", re.IGNORECASE)


class UnclassifiedCalendarDescription(ValueError):
    """Raised when a suspension description has no registered safe mapping."""


@dataclass(frozen=True)
class TjspAcquisitionRequest:
    nome_municipio: str
    codigo_municipio: str | None
    ano: int

    def __post_init__(self) -> None:
        if not self.nome_municipio.strip():
            raise ValueError("nomeMunicipio é obrigatório")
        if self.ano < 1900 or self.ano > 9999:
            raise ValueError("ano inválido")

    @property
    def query_params(self) -> dict[str, str]:
        # The endpoint accepts name-only lookups. Preserve an empty code when
        # callers have not received the site's municipality code value.
        return {"nomeMunicipio": self.nome_municipio.strip(),
                "codigoMunicipio": str(self.codigo_municipio or ""),
                "ano": str(self.ano)}

    @property
    def calendar_request(self) -> CalendarProviderRequest:
        return CalendarProviderRequest("TJSP", "SP", self.nome_municipio.strip(),
            f"{self.ano:04d}-01-01", f"{self.ano:04d}-12-31")


def _decode_snapshot(snapshot: RawSourceSnapshot, endpoint: str,
                     request: TjspAcquisitionRequest) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    if snapshot.source_endpoint != endpoint:
        raise ValueError("snapshot pertence a outro endpoint TJSP")
    if dict(snapshot.request_params) != request.query_params:
        raise ValueError("query params do snapshot não correspondem à requisição TJSP")
    try:
        decoded = snapshot.content.decode("utf-8-sig")
        payload = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("resposta TJSP não é JSON UTF-8 válido") from exc
    rows = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("resposta TJSP deve conter data como lista de objetos")
    return payload, tuple(rows)


def _parse_official_date(value: Any, *, field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field} deve ser texto dd/mm/aaaa")
    try:
        parsed = datetime.strptime(value.strip(), _DATE_FORMAT).date()
    except ValueError as exc:
        raise ValueError(f"{field} inválido: {value!r}") from exc
    if parsed.strftime(_DATE_FORMAT) != value.strip():
        raise ValueError(f"{field} deve estar no formato dd/mm/aaaa")
    return parsed


def _base_event(*, snapshot: RawSourceSnapshot, request: TjspAcquisitionRequest,
                raw_row: Mapping[str, Any], day: date, status: str,
                endpoint: str, source_type: str) -> CourtCalendar:
    description = raw_row.get("Descricao")
    if not isinstance(description, str) or not description.strip():
        raise ValueError("registro TJSP sem Descricao original")
    date_original = raw_row.get("Data")
    dj_url = raw_row.get("DJE")
    provenance = {
        "provider_id": PROVIDER_ID,
        "endpoint": endpoint,
        "query_params": request.query_params,
        "fetched_at": snapshot.fetched_at,
        "content_hash": snapshot.content_hash,
        "raw_json_record": dict(raw_row),
        "description_original": description,
        "data_original": date_original,
        "dje_url": dj_url,
        "institutional_source": INSTITUTIONAL_SOURCE,
        "raw_snapshot_source_url": snapshot.source_url,
        "parser_version": PARSER_VERSION,
    }
    return CourtCalendar(
        jurisdiction="SP", court="TJSP", locality_unit=request.nome_municipio.strip(),
        date=day.isoformat(), status=status, scope="COMARCA", official_source=INSTITUTIONAL_SOURCE,
        verified_at=snapshot.fetched_at[:10],
        version=f"{PARSER_VERSION}:{str(snapshot.content_hash)[:16]}",
        source_type=source_type, authority="Tribunal de Justiça do Estado de São Paulo",
        act_number=None, act_date=None, applicability="ALL", notes=description.strip(),
        provenance=provenance,
    )


def parse_holidays(snapshot: RawSourceSnapshot,
                   request: TjspAcquisitionRequest) -> tuple[CourtCalendar, ...]:
    _, rows = _decode_snapshot(snapshot, HOLIDAYS_ENDPOINT, request)
    output = []
    for row in rows:
        # `Data` is the official textual calendar date. DataFeriado is an
        # implementation timestamp and is intentionally never consulted.
        day = _parse_official_date(row.get("Data"), field="Data")
        if day.year != request.ano:
            raise ValueError("Data de feriado diverge do ano solicitado")
        if not str(row.get("Descricao") or "").strip():
            raise ValueError("feriado TJSP sem descrição classificável")
        output.append(_base_event(snapshot=snapshot, request=request, raw_row=row, day=day,
            status="HOLIDAY", endpoint=HOLIDAYS_ENDPOINT, source_type="TJSP_JSON_HOLIDAY"))
    return tuple(output)


def _classify_suspension(description: str) -> str:
    normalized = unicodedata.normalize("NFKD", description)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    label = re.sub(r"\s+", " ", normalized).strip().upper().split(" - ", 1)[0].strip()
    known = {
        "RECESSO FORENSE": "RECESS",
        "SUSPENSAO DOS PRAZOS PROCESSUAIS": "SUSPENDED",
    }
    if label not in known:
        raise UnclassifiedCalendarDescription(f"descrição TJSP sem mapeamento seguro: {description!r}")
    return known[label]


def parse_suspensions(snapshot: RawSourceSnapshot,
                      request: TjspAcquisitionRequest) -> tuple[CourtCalendar, ...]:
    _, rows = _decode_snapshot(snapshot, SUSPENSIONS_ENDPOINT, request)
    output = []
    for row in rows:
        description = row.get("Descricao")
        if not isinstance(description, str) or not description.strip():
            raise UnclassifiedCalendarDescription("suspensão TJSP sem Descricao")
        status = _classify_suspension(description)
        original_range = row.get("Data")
        match = _RANGE.fullmatch(original_range if isinstance(original_range, str) else "")
        if match:
            start, end = (_parse_official_date(value, field="Data") for value in match.groups())
        else:
            start = end = _parse_official_date(original_range, field="Data")
        if start > end or start.year > request.ano or end.year < request.ano:
            raise ValueError("intervalo de suspensão inválido ou sem interseção com o ano solicitado")
        first_in_year = max(start, date(request.ano, 1, 1))
        last_in_year = min(end, date(request.ano, 12, 31))
        # DataInicial/DataFinal are retained verbatim in raw_json_record, but
        # dates are expanded exclusively from the official human-readable Data.
        for ordinal in range((last_in_year - first_in_year).days + 1):
            day = date.fromordinal(first_in_year.toordinal() + ordinal)
            output.append(_base_event(snapshot=snapshot, request=request, raw_row=row, day=day,
                status=status, endpoint=SUSPENSIONS_ENDPOINT, source_type="TJSP_JSON_SUSPENSION"))
    return tuple(output)



def compose_effective_tjsp_calendar(
    holiday_snapshot: RawSourceSnapshot,
    suspension_snapshot: RawSourceSnapshot,
    request: TjspAcquisitionRequest,
    *,
    start_date: str,
    end_date: str,
    proceeding_medium: str = "ELECTRONIC",
) -> CalendarComposition:
    """Build a complete effective calendar from the two official exception registries.

    A weekday becomes BUSINESS_DAY only when both official TJSP registries for
    the exact municipality/year are present and parse successfully. Official
    holiday/suspension events then override that derived baseline by normal
    calendar-composer precedence. This is intentionally fail-closed: callers
    cannot derive business weekdays from a partial registry.
    """
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if start > end:
        raise ValueError("start_date deve ser anterior ou igual a end_date")
    if start.year != request.ano or end.year != request.ano:
        raise ValueError("intervalo efetivo deve permanecer no ano solicitado")

    # Parsing validates endpoint identity, query params, dates and known
    # suspension classifications before any positive BUSINESS_DAY is derived.
    holidays = parse_holidays(holiday_snapshot, request)
    suspensions = parse_suspensions(suspension_snapshot, request)
    snapshots = (holiday_snapshot, suspension_snapshot)
    hashes = tuple(sorted(snapshot.content_hash for snapshot in snapshots))
    baseline_version = "tjsp-weekday-baseline-v1:" + hashlib.sha256(
        ("|".join(hashes) + "|" + json.dumps(request.query_params, sort_keys=True)).encode("utf-8")
    ).hexdigest()[:20]
    verified_at = max(snapshot.fetched_at[:10] for snapshot in snapshots)
    snapshot_provenance = tuple({
        "endpoint": snapshot.source_endpoint,
        "source_url": snapshot.source_url,
        "content_hash": snapshot.content_hash,
        "fetched_at": snapshot.fetched_at,
        "parser_version": snapshot.parser_version,
        "request_params": dict(snapshot.request_params),
    } for snapshot in snapshots)

    baseline: list[CourtCalendar] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            baseline.append(CourtCalendar(
                jurisdiction="SP", court="TJSP", locality_unit=request.nome_municipio.strip(),
                date=current.isoformat(), status="BUSINESS_DAY", scope="COMARCA",
                official_source="derived:tjsp-complete-exception-registry",
                verified_at=verified_at, version=baseline_version,
                source_type="DERIVED_WEEKDAY_BASELINE_FROM_TJSP_EXCEPTION_REGISTRY",
                authority="Themis deterministic calendar composer",
                applicability=proceeding_medium.upper(),
                notes="Dia útil derivado de dia de semana após validação dos cadastros oficiais completos de feriados e suspensões do TJSP.",
                provenance={
                    "derivation": "weekday() < 5 after successful parse of both TJSP exception registries",
                    "official_exception_snapshots": snapshot_provenance,
                    "institutional_source": INSTITUTIONAL_SOURCE,
                    "parser_version": PARSER_VERSION,
                },
            ))
        current += timedelta(days=1)

    return compose_calendar(
        CalendarCompositionRequest(
            "TJSP", "SP", request.nome_municipio.strip(), start_date, end_date,
            proceeding_medium=proceeding_medium,
        ),
        (*baseline, *holidays, *suspensions),
    )


def acquire_tjsp_calendar(db: Any, request: TjspAcquisitionRequest, *,
                          fetcher: Callable[..., RawSourceSnapshot] = fetch_official_snapshot,
                          commit: bool = True) -> dict[str, Any]:
    """Fetch, snapshot, parse and persist each endpoint independently.

    Each raw JSON snapshot is committed before parsing so malformed or newly
    introduced classifications remain available for review and reprocessing.
    """
    outputs: dict[str, Any] = {"calendar_events": [], "snapshots": [], "event_version_ids": []}
    for endpoint, parser in ((HOLIDAYS_ENDPOINT, parse_holidays),
                             (SUSPENSIONS_ENDPOINT, parse_suspensions)):
        snapshot = fetcher(endpoint, allowed_hosts=OFFICIAL_HOSTS,
                           parser_version=PARSER_VERSION, query_params=request.query_params)
        if snapshot.source_endpoint != endpoint or dict(snapshot.request_params) != request.query_params:
            raise ValueError("fetcher retornou snapshot incompatível com endpoint/params solicitados")
        snapshot_id = store_snapshot(db, snapshot, commit=commit)
        # Content-addressed cache may already hold these exact bytes. Parse its
        # canonical metadata so an unchanged refetch does not create a new
        # calendar event version only because fetched_at advanced.
        snapshot = get_snapshot(db, snapshot_id)
        events = parser(snapshot, request)
        event_ids = store_calendar_events(db, events, snapshot_id=snapshot_id, commit=commit)
        outputs["snapshots"].append({"snapshot_id": snapshot_id, "endpoint": endpoint,
            "query_params": request.query_params, "fetched_at": snapshot.fetched_at,
            "content_hash": snapshot.content_hash, "parser_version": snapshot.parser_version})
        outputs["calendar_events"].extend(events)
        outputs["event_version_ids"].extend(event_ids)
    return outputs
