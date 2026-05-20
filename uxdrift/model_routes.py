from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


LLM_CRITIQUE_ROUTE = "uxdrift.llm_critique"


@dataclass(frozen=True)
class ModelRoute:
    id: str
    owner: str
    surface: str
    provider: str
    model: str
    base_url: str | None


def model_for_route(route_id: str) -> str:
    return route_for(route_id).model


def base_url_for_route(route_id: str) -> str:
    route = route_for(route_id)
    if not route.base_url:
        raise RuntimeError(f"Model route {route.id} has no base_url")
    return route.base_url


def model_for_env_or_route(env_var: str, route_id: str) -> str:
    override = os.environ.get(env_var, "").strip()
    if override:
        return override
    return model_for_route(route_id)


def base_url_for_env_or_route(env_var: str, route_id: str) -> str:
    override = os.environ.get(env_var, "").strip()
    if override:
        return override
    return base_url_for_route(route_id)


def route_for(route_id: str) -> ModelRoute:
    normalized = route_id.strip().lower()
    try:
        return _load_routes()[normalized]
    except KeyError as exc:
        raise RuntimeError(f"Unknown model route: {route_id}") from exc


@lru_cache(maxsize=1)
def _load_routes() -> dict[str, ModelRoute]:
    data = tomllib.loads(_registry_path().read_text(encoding="utf-8"))
    provider_surfaces = data.get("provider_surfaces")
    raw_routes = data.get("model_routes")
    if not isinstance(provider_surfaces, dict):
        raise RuntimeError("Central model route registry has no [provider_surfaces] table")
    if not isinstance(raw_routes, dict):
        raise RuntimeError("Central model route registry has no [model_routes] table")

    routes: dict[str, ModelRoute] = {}
    for route_id, raw in raw_routes.items():
        if not isinstance(raw, dict):
            continue
        route = _coerce_route(route_id, raw, provider_surfaces)
        routes[route.id] = route
    return routes


def _coerce_route(
    route_id: str,
    raw: dict[str, Any],
    provider_surfaces: dict[str, Any],
) -> ModelRoute:
    normalized = route_id.strip().lower()
    surface = _required(raw, "surface", normalized)
    raw_surface = provider_surfaces.get(surface)
    if not isinstance(raw_surface, dict):
        raise RuntimeError(f"Model route {normalized} references unknown surface {surface}")
    return ModelRoute(
        id=normalized,
        owner=_required(raw, "owner", normalized),
        surface=surface,
        provider=_required(raw, "provider", normalized),
        model=_required(raw, "model", normalized),
        base_url=_optional(raw_surface, "base_url"),
    )


def _required(raw: dict[str, Any], key: str, route_id: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"Model route {route_id} is missing required field {key}")
    return value.strip()


def _optional(raw: dict[str, Any], key: str) -> str | None:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _registry_path() -> Path:
    configured = os.environ.get("PAIA_MODEL_ROUTE_REGISTRY_PATH", "").strip()
    repo_root = Path(__file__).resolve().parents[1]
    workspace_root = repo_root.parent
    candidates = [
        Path(configured) if configured else None,
        Path.cwd() / "../paia-agent-runtime/config/cognition-presets.toml",
        Path.cwd() / "../../paia-agent-runtime/config/cognition-presets.toml",
        Path.cwd() / "../../../paia-agent-runtime/config/cognition-presets.toml",
        workspace_root / "paia-agent-runtime/config/cognition-presets.toml",
    ]
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate.resolve()
    raise RuntimeError(
        "Unable to find central model route registry. Set PAIA_MODEL_ROUTE_REGISTRY_PATH."
    )
