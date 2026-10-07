"""Deterministic, three-valued applicability. Missing facts are never exclusions."""
from datetime import date


def temporal(version, as_of):
    review = version.get("review")
    if not review:
        return "unknown", "Document status and effective dates have not been reviewed."
    if review["status"] not in ("final", "superseded", "withdrawn"):
        return "inactive", f"Document review status is {review['status']}; not an active obligation."
    start, end = review.get("effective_from"), review.get("effective_to")
    if review["status"] in ("superseded", "withdrawn") and not end:
        return "unknown", "The historical end of validity has not been established."
    if not start:
        return "unknown", "Effective date is not established."
    if start > as_of:
        return "inactive", "The reviewed effective date is in the future for this assessment."
    if end and as_of >= end:
        return "inactive", "The reviewed validity period has ended."
    return "effective", "Within the reviewed effective period."


def version_conflicts(versions, as_of):
    active = {}
    for version in versions:
        if temporal(version, as_of)[0] == "effective":
            active.setdefault(version["document_id"], []).append(version["id"])
    return {key for key, values in active.items() if len(values) > 1}


def evaluate(entity, conditions, *, hypothetical=False, obligation=None, as_of=None, conflicts=None):
    as_of = as_of or date.today().isoformat()
    reasons = []
    result = {"entity_id": entity["id"], "company": entity["name"], "outcome": "unknown", "reasons": reasons,
              "missing_information": [], "profile_review": entity.get("review"), "as_of": as_of,
              "hypothetical": hypothetical, "method": "explicit_conditions_v2.0"}
    if not hypothetical:
        if not obligation or not obligation.get("review") or obligation["review"]["status"] != "approved":
            reasons.append("The extracted obligation has not been approved by a reviewer.")
            return result
        validity, reason = temporal(obligation["version"], as_of)
        reasons.append(reason)
        if validity != "effective":
            result["outcome"] = "not_active" if validity == "inactive" else "unknown"
            return result
        if obligation["version"]["document_id"] in (conflicts or set()):
            reasons.append("Multiple reviewed versions overlap on this date; resolve version validity first.")
            return result
    if not conditions.get("entity_types"):
        reasons.append("No reviewed target entity type is specified.")
        return result
    profile = entity.get("review")
    history = entity.get("review_history", [])
    if history:
        profile = next((review for review in reversed(history) if review["effective_from"] <= as_of
                        and (not review.get("effective_to") or as_of < review["effective_to"])), None)
    result["profile_review"] = profile
    if not profile or profile["effective_from"] > as_of or (profile.get("effective_to") and as_of >= profile["effective_to"]):
        reasons.append("No reviewed entity profile covers the assessment date. Sector labels are insufficient.")
        result["missing_information"] = ["Evidence-backed entity type, jurisdiction and activity for this date"]
        return result
    if profile["jurisdiction"] != conditions["jurisdiction"]:
        result["outcome"] = "does_not_match"
        reasons.append("Reviewed jurisdiction does not match the rule's target jurisdiction.")
        return result
    reasons.append(f"Jurisdiction matches: {profile['jurisdiction']}.")
    matches = set(profile["entity_types"]) & set(conditions["entity_types"])
    if not matches:
        if profile.get("complete_entity_types"):
            result["outcome"] = "does_not_match"
            reasons.append("Reviewed complete entity-type profile contains no targeted entity type.")
        else:
            reasons.append("Target entity type is not documented; profile is not marked complete.")
            result["missing_information"].append("Whether the entity also operates as " + ", ".join(conditions["entity_types"]))
        return result
    reasons.append("Reviewed entity type matches: " + ", ".join(sorted(matches)) + ".")
    if conditions.get("activity") and conditions["activity"] not in profile["activities"]:
        reasons.append("The specified activity is not established in the reviewed profile.")
        result["missing_information"].append(conditions["activity"])
        return result
    if conditions.get("activity"):
        reasons.append("Reviewed activity matches: " + conditions["activity"] + ".")
    result["outcome"] = "matches_conditions"
    reasons.append("Matches the stated hypothetical assumptions." if hypothetical else "Matches the reviewed conditions; this is not a legal compliance determination.")
    return result
