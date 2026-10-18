#include "db.hpp"
#include "matching.hpp"
#include "scheduler.hpp"
#include "allocation.hpp"

#ifdef _WIN32
#include <process.h>
#else
#include <unistd.h>
#endif
#include <fstream>
#include <thread>

#ifdef _WIN32
#define getpid _getpid
#define setenv(key, value, overwrite) _putenv_s(key, value)
#endif

struct Demo { const char* organ; const char* blood; int urgency; int wait; };
const Demo DEMO[] = {{"Kidney", "O+", 9, 12}, {"Heart", "A-", 10, 4}, {"Liver", "AB+", 8, 18}, {"Kidney", "A+", 7, 25}, {"Kidney", "O-", 6, 40}, {"Heart", "O+", 8, 16}, {"Liver", "B+", 9, 10}, {"Kidney", "AB+", 7, 31}, {"Heart", "A+", 9, 7}, {"Liver", "O-", 6, 22}, {"Kidney", "B-", 10, 3}, {"Heart", "AB+", 7, 28}, {"Liver", "A-", 8, 19}, {"Kidney", "B+", 6, 35}, {"Heart", "O-", 9, 11}};

Json seed(Db& db) {
    const int added = std::stoi(demoCount(db));
    if (added >= 15) return {{"done", true}};
    const int total = std::min(added + 3, 15);
    transaction(db, [&] {
        if (db.one("SELECT count(*) AS n FROM hospitals")["n"] == "0") db.run("INSERT INTO hospitals(name) VALUES('Demo City Hospital'),('Demo Metro Hospital'),('Demo Life Care Hospital')");
        const Json h = db.rows("SELECT hospital_id FROM hospitals LIMIT 3");
        for (int i = added; i < total; ++i) {
            char name[32]; std::snprintf(name, sizeof name, "Demo Patient %02d", i + 1);
            db.run("INSERT INTO recipients(name,organ_type,blood_type,urgency_score,waiting_days,hospital_id) VALUES($1,$2,$3,$4,$5,$6)", {name, DEMO[i].organ, DEMO[i].blood, std::to_string(DEMO[i].urgency), std::to_string(DEMO[i].wait), h[i % h.size()]["hospital_id"]});
        }
    });
    return {{"added_count", total - added}};
}

Json analytics(Db& db) {
    return db.one("SELECT count(*) FILTER(WHERE status='AVAILABLE') AS available, count(*) FILTER(WHERE status='ALLOCATED') AS allocated, count(*) FILTER(WHERE status='WASTED') AS wasted, count(*) AS total, COALESCE((SELECT round(avg(waiting_days)::numeric,1) FROM allocations a JOIN recipients r USING(recipient_id)),0) AS average_wait_days FROM organs");
}

Json data(Db& db) {
    expire(db); Json stats = analytics(db); stats["demo_records"] = demoCount(db);
    return {
        {"hospitals", db.rows("SELECT * FROM hospitals ORDER BY hospital_id")},
        {"donors", db.rows("SELECT * FROM donors ORDER BY donor_id")},
        {"organs", db.rows("SELECT o.*,GREATEST(0,EXTRACT(EPOCH FROM (o.expires_at-now())))::int AS seconds_remaining FROM organs o ORDER BY organ_id")},
        {"recipients", db.rows("SELECT r.*,h.name AS hospital_name FROM recipients r JOIN hospitals h USING(hospital_id) ORDER BY urgency_score DESC,waiting_days DESC")},
        {"allocations", db.rows("SELECT a.*,o.organ_type,r.name AS recipient_name,h.name AS hospital_name FROM allocations a JOIN organs o USING(organ_id) JOIN recipients r USING(recipient_id) JOIN hospitals h ON h.hospital_id=a.hospital_id ORDER BY allocated_at DESC")},
        {"events", db.rows("SELECT event_id,event_type,entity_type,entity_id,hospital_id,payload,created_at FROM allocation_events ORDER BY event_id DESC LIMIT 60")},
        {"analytics", stats}};
}

void installRoutes(httplib::Server& srv, Clock::time_point start) {
    auto get = [&](const char* path, Handler h) { srv.Get(path, route(h)); };
    auto post = [&](const char* path, Handler h) { srv.Post(path, route(h)); };
    auto list = [&](const char* path, std::string sql) { get(path, [=](Db& db, const httplib::Request&) { return db.rows(sql); }); };

    srv.Get("/api/health", [](const httplib::Request&, httplib::Response& res) { send(res, 200, {{"status", "ok"}}); });
    get("/api/status", [start](Db& db, const httplib::Request&) { return Json{{"pid", getpid()}, {"state", "RUNNING"}, {"uptime_seconds", std::chrono::duration_cast<std::chrono::seconds>(Clock::now() - start).count()}}; });
    
    get("/api/data", [](Db& db, const httplib::Request&) { return data(db); });
    get("/api/analytics", [](Db& db, const httplib::Request&) { return analytics(db); });
    list("/api/hospitals", "SELECT * FROM hospitals");
    list("/api/donors", "SELECT * FROM donors");
    get("/api/organs", [](Db& db, const httplib::Request&) { expire(db); return db.rows("SELECT * FROM organs"); });
    list("/api/recipients", "SELECT * FROM recipients");
    list("/api/allocations", "SELECT * FROM allocations");
    list("/api/events", "SELECT * FROM allocation_events LIMIT 100");

    get(R"(/api/organs/(\d+)/matches)", [](Db& db, const httplib::Request& req) { expire(db); return matches(db, std::stoll(req.matches[1])); });
    
    post("/api/hospitals", [](Db& db, const httplib::Request& req) { return db.one("INSERT INTO hospitals(name) VALUES($1) RETURNING *", {text(body(req), "name")}); });
    post("/api/donors", [](Db& db, const httplib::Request& req) { Json b=body(req); return db.one("INSERT INTO donors(name,blood_type,medically_eligible) VALUES($1,$2,$3) RETURNING *", {text(b, "name"), text(b, "blood_type"), b.value("medically_eligible", true) ? "true" : "false"}); });
    post("/api/organs", [](Db& db, const httplib::Request& req) { Json b=body(req); Json hosp = b.value("donor_hospital_id", Json()); return db.one("INSERT INTO organs(donor_id,organ_type,blood_type,donor_hospital_id,expires_at) SELECT donor_id,$2,blood_type,NULLIF($3,'')::bigint,now()+($4||' hours')::interval FROM donors WHERE donor_id=$1 RETURNING *", {number(b, "donor_id", 1, 2147483647), text(b, "organ_type"), hosp.is_null() ? "" : hosp.dump(), std::to_string(b.value("viable_hours", 24.0))}); });
    post("/api/recipients", [](Db& db, const httplib::Request& req) { Json b=body(req); return db.one("INSERT INTO recipients(name,organ_type,blood_type,urgency_score,waiting_days,hospital_id) VALUES($1,$2,$3,$4,$5,$6) RETURNING *", {text(b, "name"), text(b, "organ_type"), text(b, "blood_type"), number(b, "urgency_score", 1, 10), number(b, "waiting_days", 0, 100000), number(b, "hospital_id", 1, 2147483647)}); });
    
    post("/api/claim", [](Db& db, const httplib::Request& req) { expire(db); return claim(db, body(req)); });
    post("/api/reject", [](Db& db, const httplib::Request& req) { Json b=body(req); event(db, "HOSPITAL_REJECTED", "organ", number(b, "organ_id", 1, 2147483647), number(b, "hospital_id", 1, 2147483647), {{"reason", text(b, "reason")}}); return Json{{"recorded", true}}; });
    post("/api/deadlines", [](Db& db, const httplib::Request&) { return expire(db); });
    post("/api/deadlock", [](Db& db, const httplib::Request&) { return deadlockDemo(db); });
    post("/api/crash", [](Db& db, const httplib::Request&) { return simulateCrash(db); });
    post("/api/recover", [](Db& db, const httplib::Request&) { return recover(db); });
    post("/api/seed", [](Db& db, const httplib::Request&) { return seed(db); });
}

int main(int argc, char** argv) {
    if (!std::getenv("DATABASE_URL")) setenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/organ_allocation", 1);
    
    try {
        std::ifstream schema("schema.sql");
        std::stringstream sql; sql << schema.rdbuf();
        Db db; db.script(sql.str()); expire(db);
    } catch (const std::exception& e) { std::cerr << "DB Error: " << e.what() << '\n'; return 1; }

    httplib::Server server;
    server.set_mount_point("/", "web");
    installRoutes(server, Clock::now());

    std::atomic<bool> stop{false};
    std::thread deadlineWorker([&] {
        while (!stop) {
            std::this_thread::sleep_for(std::chrono::seconds(10));
            if (!stop) { try { Db db; expire(db); } catch (...) {} }
        }
    });

    std::cout << "Server running on port 8000\n";
    bool listening = server.listen("127.0.0.1", 8000);
    stop = true; deadlineWorker.join();
    return listening ? 0 : 1;
}