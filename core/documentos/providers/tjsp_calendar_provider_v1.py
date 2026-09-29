"""TJSP calendar provider over explicitly reviewed official source rows."""
from __future__ import annotations

from typing import Any, Mapping

from core.documentos.court_calendar_provider_v1 import (
    CalendarProviderRequest, RawSourceSnapshot, normalize_records, validate_request,
)
from core.documentos.deadline_policies_v1 import CourtCalendar

PROVIDER_ID = "TJSP_CALENDAR_V1"
OFFICIAL_SOURCE = "https://www.tjsp.jus.br/CanaisComunicacao/SuspensaoPrazos"
PHYSICAL_SUSPENSIONS_SOURCE = "https://www.tjsp.jus.br/CanaisComunicacao/Feriados/ProcessosFisicos"
AUTHORITY = "Tribunal de Justiça do Estado de São Paulo"
PARSER_VERSION = "tjsp-reviewed-records-v1"


class TjspCalendarProvider:
    provider_id = PROVIDER_ID

    def provide(self, request: CalendarProviderRequest,
                records: tuple[Mapping[str, Any], ...]) -> tuple[CourtCalendar, ...]:
        validate_request("TJSP", request)
        if not request.locality_unit:
            raise ValueError("TJSP exige comarca para filtrar calendário local")
        families = {"PHYSICAL" if str(r.get("applicability", "ALL")).upper() == "PHYSICAL" else "GENERAL"
                    for r in records}
        if len(families) > 1:
            raise ValueError("TJSP: registros de fontes oficiais distintas exigem snapshots/lotes separados")
        source_url = PHYSICAL_SUSPENSIONS_SOURCE if families == {"PHYSICAL"} else OFFICIAL_SOURCE
        return normalize_records(provider_id=self.provider_id, authority=AUTHORITY,
            source_url=source_url,
            verified_at="2026-09-29", version="tjsp-reviewed-records-v1",
            request=request, records=tuple(records))


def parse_snapshot(snapshot: RawSourceSnapshot, request: CalendarProviderRequest,
                   reviewed_records: tuple[Mapping[str, Any], ...]) -> tuple[CourtCalendar, ...]:
    """Normalize manually reviewed records supported by a preserved raw source.

    The TJSP page has interactive/dynamic content and its physical-case list is
    distinct. This adapter deliberately does not scrape rendered prose.
    """
    expected_source = (PHYSICAL_SUSPENSIONS_SOURCE
                       if any(str(row.get("applicability", "ALL")).upper() == "PHYSICAL" for row in reviewed_records)
                       else OFFICIAL_SOURCE)
    if snapshot.source_url != expected_source:
        raise ValueError("TJSP snapshot deve vir da página oficial de suspensão de prazos")
    if not snapshot.content:
        raise ValueError("snapshot oficial vazio")
    return TjspCalendarProvider().provide(request, reviewed_records)
