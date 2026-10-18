#pragma once
#include <httplib.h>
#include <libpq-fe.h>
#include <nlohmann/json.hpp>
#include <string>
#include <vector>
#include <stdexcept>
#include <memory>
#include <functional>

using Json = nlohmann::json;
using Params = std::vector<std::string>;
using Clock = std::chrono::steady_clock;

struct Error : std::runtime_error {  
    int status;
    Error(int code, const std::string& msg) : std::runtime_error(msg), status(code) {}
};

class Db {
    PGconn* conn = nullptr;
public:
    Db() {
        const char* url = std::getenv("DATABASE_URL");
        conn = PQconnectdb(url ? url : "postgresql://postgres:postgres@localhost:5433/organ_allocation");
        if (PQstatus(conn) != CONNECTION_OK) fail(PQerrorMessage(conn));
    }
    ~Db() { PQfinish(conn); }
    Db(const Db&) = delete;

    Json rows(const std::string& sql, const Params& params = {}) {
        std::vector<const char*> vals;
        for (const auto& p : params) vals.push_back(p.c_str());
        std::unique_ptr<PGresult, decltype(&PQclear)> res(
            PQexecParams(conn, sql.c_str(), vals.size(), nullptr, vals.empty() ? nullptr : vals.data(), nullptr, nullptr, 0), PQclear);
        auto state = PQresultStatus(res.get());
        if (state != PGRES_COMMAND_OK && state != PGRES_TUPLES_OK) fail(PQerrorMessage(conn), PQresultErrorField(res.get(), PG_DIAG_SQLSTATE));
        Json out = Json::array();
        for (int r = 0; r < PQntuples(res.get()); ++r) {
            Json row = Json::object();
            for (int c = 0; c < PQnfields(res.get()); ++c) {
                const char* val = PQgetvalue(res.get(), r, c);
                auto type = PQftype(res.get(), c);
                if (PQgetisnull(res.get(), r, c)) row[PQfname(res.get(), c)] = nullptr;
                else if (type == 16) row[PQfname(res.get(), c)] = std::string(val) == "t"; 
                else if (type == 3802) row[PQfname(res.get(), c)] = Json::parse(val);      
                else row[PQfname(res.get(), c)] = val;                                     
            }
            out.push_back(row);
        }
        return out;
    }
    Json one(const std::string& sql, const Params& p = {}) { Json f = rows(sql, p); return f.empty() ? Json() : f[0]; }
    void run(const std::string& sql, const Params& p = {}) { rows(sql, p); }
    void script(const std::string& sql) { if (PQresultStatus(PQexec(conn, sql.c_str())) != PGRES_COMMAND_OK) fail(PQerrorMessage(conn)); }
    [[noreturn]] static void fail(const std::string& msg, const std::string& code = "") { throw Error(code == "23505" ? 409 : code.rfind("23", 0) == 0 ? 422 : 500, msg); }
};

inline std::string text(const Json& b, const char* key) { return (!b.contains(key) || b[key].is_null()) ? throw Error(422, "Missing: "+std::string(key)) : (b[key].is_string() ? b[key].get<std::string>() : b[key].dump()); }
inline std::string number(const Json& b, const char* key, int min, int max) { 
    if (!b.contains(key) || !b[key].is_number()) throw Error(422, "Invalid: "+std::string(key));
    int val = b[key].get<int>();
    if (val < min || val > max) throw Error(422, "Out of range: "+std::string(key));
    return std::to_string(val);
}
inline Json body(const httplib::Request& req) { Json d = Json::parse(req.body, nullptr, false); return (d.is_discarded() || !d.is_object()) ? throw Error(400, "Bad JSON") : d; }
inline void send(httplib::Response& res, int status, const Json& val) { res.status = status; res.set_content(val.dump(), "application/json"); }

using Handler = std::function<Json(Db&, const httplib::Request&)>;
inline httplib::Server::Handler route(Handler action) {
    return [action](const httplib::Request& req, httplib::Response& res) {
        try { Db db; send(res, 200, action(db, req)); }
        catch (const Error& e) { send(res, e.status, {{"error", e.what()}}); }
        catch (const std::exception& e) { send(res, 500, {{"error", e.what()}}); }
    };
}

inline void event(Db& db, const std::string& type, const std::string& entity, const std::string& id, const std::string& hospital, const Json& payload = Json::object()) {
    db.run("INSERT INTO allocation_events(event_type,entity_type,entity_id,hospital_id,payload) VALUES($1,$2,NULLIF($3,'')::bigint,NULLIF($4,'')::bigint,$5::jsonb)", {type, entity, id, hospital, payload.dump()});
}

inline void transaction(Db& db, const std::function<void()>& work) {
    db.run("BEGIN");
    try { work(); db.run("COMMIT"); } catch (...) { db.run("ROLLBACK"); throw; }
}

inline std::string idText(const Json& id, const std::string& ifNull = "") { return id.is_null() ? ifNull : id.get<std::string>(); }
inline double num(const Json& row, const char* key) { return std::stod(row[key].get<std::string>()); }
inline std::string demoCount(Db& db) { return db.one("SELECT count(*) AS n FROM recipients WHERE name LIKE 'Demo Patient %'")["n"]; }
