"""Shared response-schema base for the new routers: camelCase JSON over snake_case entities.

The frontend's `lib/api/types.ts` mirrors `models/entities.py` field-for-field but in camelCase
(`patientId`, `createdAt`, ...) - the same convention `intake_routes.py` already hand-writes per
field (`slotId`, `etaLabel`). `camel_schema` generalizes that once instead of repeating it per
entity: it builds a `CamelModel` with the same fields as the given entity, so
`Model.model_validate(entity)` round-trips straight into the JSON shape the frontend expects.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, create_model
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )


def camel_schema(entity_cls: type[BaseModel]) -> type[CamelModel]:
    """Build a `CamelModel` response schema mirroring `entity_cls`'s fields 1:1.

    The entity stays the single source of truth for field names/types/defaults (DRY) - this only
    adds the camelCase JSON alias on top, for use as a route's `response_model`.
    """
    fields = {name: (info.annotation, info) for name, info in entity_cls.model_fields.items()}
    return create_model(f"{entity_cls.__name__}Out", __base__=CamelModel, **fields)
