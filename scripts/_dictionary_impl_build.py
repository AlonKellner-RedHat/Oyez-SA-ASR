# Edited by Cursor: enchant dict building (lintok; no new exclusions).
"""Build enchant Dict list for en_US and la."""


def _enchant_providers_for_tag(tag: str) -> list[str]:
    """Read enchant.ordering and return provider names for tag in cascade order."""
    for path in (
        "/usr/share/enchant-2/enchant.ordering",
        "/usr/share/enchant/enchant.ordering",
    ):
        try:
            with open(path, encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" not in line:
                        continue
                    lang, order = line.split(":", 1)
                    if lang.strip() == tag:
                        return [p.strip() for p in order.split(",") if p.strip()]
        except OSError:
            continue
    return []


def _build_enchant_dicts_for_tag(tag: str) -> list:
    """Build list of enchant Dict for one language tag (one per provider), cascade order."""
    import enchant  # noqa: PLC0415

    dicts_list: list = []
    seen_providers: set[str] = set()
    providers = _enchant_providers_for_tag(tag)
    if providers:
        for prov_name in providers:
            try:
                broker = enchant.Broker()
                broker.set_ordering(tag, prov_name)
                d = broker.request_dict(tag)
                pname = d.provider.name  # type: ignore[attr-defined]
                if pname not in seen_providers:
                    dicts_list.append(d)
                    seen_providers.add(pname)
            except Exception:  # noqa: S110
                pass
    if not dicts_list:
        try:
            default = enchant.Dict(tag)
            dicts_list = [default]
            try:
                broker = enchant.Broker()
                seen = {default.provider.name}  # type: ignore[attr-defined]
                for list_tag, prov in broker.list_dicts():
                    if list_tag == tag and prov.name not in seen:
                        try:
                            b2 = enchant.Broker()
                            b2.set_ordering(tag, prov.name)
                            d2 = b2.request_dict(tag)
                            dicts_list.append(d2)
                            seen.add(prov.name)
                        except Exception:  # noqa: S110
                            pass
            except Exception:  # noqa: S110
                pass
        except Exception:  # noqa: S110
            pass
    return dicts_list


def _build_enchant_dicts() -> list:
    """Build list of enchant Dict: en_US first, then la (Latin) if available."""
    dicts_list: list = _build_enchant_dicts_for_tag("en_US")
    if not dicts_list:
        return dicts_list
    latin_dicts = _build_enchant_dicts_for_tag("la")
    dicts_list.extend(latin_dicts)
    return dicts_list
