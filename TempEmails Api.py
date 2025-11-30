#dev LINUXXIT
from flask import Flask, request, jsonify;import requests as _r;import random as linux;import string as _s
app = Flask(__name__)
class _M:
    def __init__(self, u="https://api.mail.tm"):
        self._u = (u or "").rstrip("/") or "https://api.mail.tm"
        self._s = _r.Session()
        self._t = None
        self._s.headers.update(dict([("User-Agent", "Mozilla/5.0"),("Accept", "application/json"),("Content-Type", "application/json"),]))
    def _g(self, p, **kw):
        return self._s.get(f"{self._u}{p}", **kw)
    def _p(self, p, **kw):
        return self._s.post(f"{self._u}{p}", **kw)
    def _d(self, p, **kw):
        return self._s.delete(f"{self._u}{p}", **kw)
    def d(self):
        r = self._g("/domains")
        try:return r.json()
        except Exception:return {}
    def c(self, a, pw):
        j = {"address": a, "password": pw}
        r = self._p("/accounts", json=j)
        return r.json() if getattr(r, "status_code", None) == 201 else None
    def t(self, a, pw):
        j = {"address": a, "password": pw}
        r = self._p("/token", json=j)
        if getattr(r, "status_code", None) == 200:
            j2 = r.json()
            self._t = j2.get("token") if isinstance(j2, dict) else None
            if self._t:
                self._s.headers.update({"Authorization": f"Bearer {self._t}"})
            return j2
        return None
    def _chk(self):
        if not self._t:raise RuntimeError("NO_TOKEN")
    def ms(self, p=1):
        self._chk()
        r = self._g("/messages", params={"page": int(p) if p else 1})
        return r.json()
    def m1(self, mid):
        self._chk()
        r = self._g(f"/messages/{mid}")
        return r.json()
    def rm(self, mid):
        self._chk()
        r = self._d(f"/messages/{mid}")
        return r.status_code == 204
    def me(self):
        self._chk()
        r = self._g("/me")
        return r.json()
_mail = _M()
def _flatten_domains(d):
    if isinstance(d, dict):
        for k in ("hydra:member", "members", "items"):
            v = d.get(k)
            if isinstance(v, list):
                return v
        return []
    if isinstance(d, list):
        return d
    return []
def _rnd_email(d):
    L = _flatten_domains(d)
    if not L:
        return None
    u = "".join(linux.choice(_s.ascii_lowercase + _s.digits) for _ in range(10))
    choice = linux.choice(L)
    dom = (
        choice.get("domain")
        if isinstance(choice, dict)
        else (str(choice) if choice else "mail.tm")
    )
    return f"{u}@{dom}"
def _rnd_pw(n=12):
    ch = _s.ascii_letters + _s.digits + "!@#$%"
    return "".join(linux.choice(ch) for _ in range(int(n) if n else 12))
def _wrap(fn):
    def inner(*a, **kw):
        try:
            return fn(*a, **kw)
        except RuntimeError as e:
            if "NO_TOKEN" in str(e):
                return jsonify({"error": "Not authenticated"}), 401
            return jsonify({"error": "Auth error"}), 401
        except Exception as e:
            return jsonify({"error": str(e) or "Server error"}), 500
    return inner
@app.route("/domains", methods=["GET"])
def _dom():
    r = None
    try:r = _mail.d()
    except Exception:r = {"error": "Failed"};return jsonify(r), 500
    return jsonify(r)
@app.route("/create_random_account", methods=["GET"])
def _cra():
    d = None
    try:d = _mail.d()
    except Exception as e:return jsonify({"error": "Could not fetch domains", "detail": str(e)}), 500
    em = _rnd_email(d)
    pw = _rnd_pw()
    if not em:
        return jsonify({"error": "Domain error"}), 500
    acc = _mail.c(em, pw)
    if not acc:
        return jsonify({"error": "Failed creating account"}), 400
    tk = _mail.t(em, pw)
    if isinstance(tk, dict):
        for k, v in {
            "token": tk.get("token"),
            "address": em,
            "password": pw,
        }.items():
            acc[k] = v
    return jsonify(acc)
@app.route("/token", methods=["GET"])
def _tok():
    q = request.args
    a, p = q.get("address"), q.get("password")
    if not (a and p):
        return jsonify({"error": "Missing fields"}), 400
    t = _mail.t(a, p)
    return jsonify(t) if t else (jsonify({"error": "Wrong credentials"}), 401)
@app.route("/messages", methods=["GET"])
def _msgs():
    p = request.args.get("page", 1)
    try:
        p_int = int(p)
    except Exception:
        p_int = 1
    try:
        data = _mail.ms(p_int)
        return jsonify(data)
    except RuntimeError:
        return jsonify({"error": "Not authenticated"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/messages/<mid>", methods=["GET"])
def _one(mid):
    try:m = _mail.m1(mid);return jsonify(m)
    except RuntimeError:return jsonify({"error": "Not authenticated"}), 401
    except Exception:return jsonify({"error": "Not found"}), 404
@app.route("/messages/<mid>", methods=["DELETE"])
def _del(mid):
    try:ok = _mail.rm(mid)
    except RuntimeError:return jsonify({"error": "Not authenticated"}), 401
    except Exception as e:return jsonify({"error": "Delete error", "detail": str(e)}), 400
    return (jsonify({"message": "Deleted"}), 200) if ok else (jsonify({"error": "Failed"}), 400)
@app.route("/me", methods=["GET"])
@_wrap
def _me():return jsonify(_mail.me())
if __name__ == "__main__":
    app.run(debug=True)
