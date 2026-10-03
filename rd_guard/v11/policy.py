"""Closed-world policy and shared normalization for action names."""

import re
import unicodedata

DEFAULT_DENY = True

READ_ONLY_ACTIONS = frozenset(
    {"inspect", "list_files", "noop", "open_file", "read", "read_file", "replan", "search_files"}
)
MUTATING_ACTIONS = frozenset(
    {"commit", "create_file", "edit_file", "mkdir", "publish", "push", "update_file", "write", "write_file"}
)
DESTRUCTIVE_ACTIONS = frozenset(
    {"delete", "drop", "erase", "purge", "remove", "rm", "rmtree", "shred", "truncate", "unlink", "wipe"}
)
_MUTATING_VERBS = frozenset(
    {"commit", "create", "edit", "mkdir", "publish", "push", "update", "write"}
)

_CONFUSABLES = str.maketrans(
    {
        "а": "a", "с": "c", "е": "e", "һ": "h", "і": "i", "ј": "j",
        "к": "k", "м": "m", "о": "o", "р": "p", "ѕ": "s", "х": "x",
        "у": "y", "Α": "a", "Β": "b", "Ε": "e", "Ι": "i", "Κ": "k",
        "Μ": "m", "Ν": "n", "Ο": "o", "Ρ": "p", "Τ": "t", "Χ": "x",
    }
)


def normalize_action_name(value):
    """Normalize separators, compatibility characters, and common homoglyphs."""
    if not isinstance(value, str):
        return ""
    value = unicodedata.normalize("NFKC", value).translate(_CONFUSABLES)
    value = "".join(
        char for char in value
        if unicodedata.category(char) not in {"Cc", "Cf", "Cs", "Zl", "Zp"}
    )
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    value = value.lower().strip()
    value = re.sub(r"[-\s./:]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, nested in value.items():
            if isinstance(key, str):
                yield key
            yield from _strings(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            yield from _strings(nested)


def _has_command(value):
    if isinstance(value, dict):
        return any(
            (key == "command" and bool(command))
            or _has_command(command)
            for key, command in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_has_command(item) for item in value)
    if isinstance(getattr(value, "command", None), str):
        return bool(value.command.strip())
    return False


def _action_parts(state):
    if isinstance(state, dict):
        raw = state.get("action", state.get("requested_action"))
        raw_type = getattr(raw, "type", None)
        fields = [state.get(key, "") for key in ("target", "path", "resource", "command", "branch")]
        if isinstance(raw, dict):
            fields.extend(raw.values())
            action_type = raw.get("type", raw.get("name"))
        elif isinstance(raw, str):
            action_type = raw
        elif isinstance(raw_type, str):
            fields.extend(
                getattr(raw, key, "")
                for key in ("target", "path", "resource", "command", "branch")
            )
            action_type = raw_type
        else:
            action_type = None
        return action_type, fields, state
    if isinstance(state, str):
        return state, [], {}
    action_type = getattr(state, "type", None)
    fields = [getattr(state, key, "") for key in ("target", "path", "resource", "command", "branch")]
    return action_type, fields, {}


def classify_action(state):
    """Return ``(category, reason)``; unknown and ambiguous actions deny."""
    action_type, fields, state_data = _action_parts(state)
    if isinstance(state_data, dict) and state_data.get("deleting_tests"):
        return "DENY", "Deleting tests is prohibited by the IAS floor"
    if not isinstance(action_type, str) or not action_type.strip():
        return "DENY", "Action type is missing, ambiguous, or not a string"

    normalized = normalize_action_name(action_type)
    if not normalized:
        return "DENY", "Action type normalizes to an empty value"

    texts = [normalize_action_name(item) for item in _strings([action_type, fields])]
    tokens = {token for text in texts for token in text.split("_") if token}
    if ({"test", "tests"} & tokens) and tokens.intersection(DESTRUCTIVE_ACTIONS):
        return "DENY", "Deleting tests is prohibited by the IAS floor"
    if normalized in DESTRUCTIVE_ACTIONS or tokens.intersection(DESTRUCTIVE_ACTIONS):
        return "DENY", f"Destructive action is prohibited: {normalized}"

    if tokens.intersection({"bypass", "skip", "ignore"}) and "alignment" in tokens:
        return "DENY", "Bypassing alignment prompts is prohibited by the IAS floor"

    category = (
        "READ_ONLY" if normalized in READ_ONLY_ACTIONS
        else "MUTATING" if normalized in MUTATING_ACTIONS
        else None
    )
    if category is None:
        return "DENY", f"Unknown action type is blocked by default: {normalized}"
    if category == "READ_ONLY":
        if _has_command(state):
            return "DENY", "Read-only action cannot carry a command"
        if tokens.intersection(_MUTATING_VERBS):
            return "DENY", "Read-only action contains a mutating operation"

    action_data = (
        state.get("action", state.get("requested_action"))
        if isinstance(state, dict) else None
    )
    branch = normalize_action_name(
        state_data.get("branch", "")
        or (action_data.get("branch", "") if isinstance(action_data, dict) else "")
    )
    pushes_main = normalized == "push" and (
        "main" in branch.split("_") or any(
            "main" in text.split("_") for text in texts
        )
    )
    ci = state_data.get("ci_passed", state_data.get("ci", False))
    if isinstance(action_data, dict):
        ci = state_data.get("ci_passed", state_data.get("ci", action_data.get("ci_passed", False)))
    elif action_data is not None and isinstance(getattr(action_data, "ci_passed", None), bool):
        ci = state_data.get("ci_passed", state_data.get("ci", action_data.ci_passed))
    if isinstance(ci, dict):
        ci = ci.get("passed", False)
    ci_passed = ci is True or (
        isinstance(ci, str) and ci.strip().lower() in {"passed", "success", "green"}
    )
    if pushes_main and not ci_passed:
        return "DENY", "Pushing to main requires passing CI"

    return category, ""
