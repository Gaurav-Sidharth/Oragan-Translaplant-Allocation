#pragma once
#include "db.hpp"
#include <algorithm>

// [OS CONCEPT: Priority Scheduling Algorithm]
inline bool compatible(const std::string& d, const std::string& r) {
    if (d.size() < 2 || r.size() < 2) return false;
    auto abo = [](const std::string& t) { return t.substr(0, t.size() - 1); };
    return (abo(d) == "O" || abo(r) == "AB" || abo(d) == abo(r)) && (d.back() == '-' || r.back() == '+');
}

inline Json matches(Db& db, long long organId) {
    Json organ = db.one("SELECT o.organ_id,o.organ_type,o.blood_type,o.donor_hospital_id,o.status,o.expires_at, d.medically_eligible FROM organs o JOIN donors d USING(donor_id) WHERE organ_id=$1", {std::to_string(organId)});
    if (organ.is_null() || organ["status"] != "AVAILABLE" || !organ["medically_eligible"].get<bool>()) throw Error(409, "Organ unavailable");

    Json candidates = db.rows(
        "SELECT r.recipient_id,r.name,r.organ_type,r.blood_type,r.urgency_score,r.waiting_days, r.hospital_id,h.name AS hospital_name, "
        "COALESCE((SELECT distance_km FROM hospital_distances d WHERE d.from_hospital_id=$1 AND d.to_hospital_id=r.hospital_id),0) AS distance_km "
        "FROM recipients r JOIN hospitals h USING(hospital_id) WHERE r.active=TRUE AND r.organ_type=$2 "
        "AND NOT EXISTS (SELECT 1 FROM allocations a WHERE a.recipient_id=r.recipient_id AND a.status='ALLOCATED')",
        {idText(organ["donor_hospital_id"], "0"), organ["organ_type"]});

    Json eligible = Json::array();
    for (auto& r : candidates) {
        if (!compatible(organ["blood_type"], r["blood_type"])) continue;
        r["priority_score"] = num(r, "urgency_score") * 10 + num(r, "waiting_days") * 2 - num(r, "distance_km");
        eligible.push_back(r);
    }
    std::sort(eligible.begin(), eligible.end(), [](const Json& a, const Json& b) { return a["priority_score"].get<double>() > b["priority_score"].get<double>(); });
    for (std::size_t i = 0; i < eligible.size(); ++i) eligible[i]["rank"] = i + 1;
    return {{"organ", organ}, {"matches", eligible}};
}
