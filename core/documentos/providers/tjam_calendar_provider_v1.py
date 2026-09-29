"""TJAM calendar provider over explicitly reviewed official source rows."""
from __future__ import annotations

from typing import Any, Mapping

from core.documentos.court_calendar_provider_v1 import (
    CalendarProviderRequest, RawSourceSnapshot, normalize_records, validate_request,
)
from core.documentos.deadline_policies_v1 import CourtCalendar

PROVIDER_ID = "TJAM_CALENDAR_V1"
OFFICIAL_SOURCE = "https://www.tjam.jus.br/index.php/menu/calendario-judicial"
ACTS_SOURCE = "https://www.tjam.jus.br/index.php/transparencia/gestao/atos-normativos-e-legislacao-correlata"
AUTHORITY = "Tribunal de Justiça do Estado do Amazonas"
PARSER_VERSION = "tjam-reviewed-records-v1"


class TjamCalendarProvider:
    provider_id = PROVIDER_ID

    def provide(self, request: CalendarProviderRequest,
                records: tuple[Mapping[str, Any], ...]) -> tuple[CourtCalendar, ...]:
        validate_request("TJAM", request)
        families = {"ACT" if r.get("act_number") else "CALENDAR" for r in records}
        if len(families) > 1:
            raise ValueError("TJAM: registros de fontes oficiais distintas exigem snapshots/lotes separados")
        source_url = ACTS_SOURCE if families == {"ACT"} else OFFICIAL_SOURCE
        return normalize_records(provider_id=self.provider_id, authority=AUTHORITY,
            source_url=source_url,
            verified_at="2026-09-29", version="tjam-reviewed-records-v1",
            request=request, records=tuple(records))


def parse_snapshot(snapshot: RawSourceSnapshot, request: CalendarProviderRequest,
                   reviewed_records: tuple[Mapping[str, Any], ...]) -> tuple[CourtCalendar, ...]:
    expected_source = ACTS_SOURCE if any(row.get("act_number") for row in reviewed_records) else OFFICIAL_SOURCE
    if snapshot.source_url != expected_source:
        raise ValueError("TJAM snapshot deve vir de fonte oficial do calendário/atos")
    if not snapshot.content:
        raise ValueError("snapshot oficial vazio")
    return TjamCalendarProvider().provide(request, reviewed_records)
