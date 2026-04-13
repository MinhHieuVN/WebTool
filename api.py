from flask import Flask,request,jsonify,render_template
import requests,sqlite3,hashlib

app = Flask(__name__, template_folder="templates")

BASE_URL="https://100067.connect.garena.com"
APP_ID="100067"
w
HEADERS={
"User-Agent":"GarenaMSDK/4.0.39 (Android)",
"Content-Type":"application/x-www-form-urlencoded"
}

# ================= DATABASE =================

def init_db():
    conn=sqlite3.connect("/tmp/database.db")
    c=conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS tokens(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid TEXT,
        nickname TEXT,
        region TEXT,
        access_token TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ================= UTIL =================

def sha256_hash(s):
    return hashlib.sha256(s.encode()).hexdigest()

def inspect_token(token):
    url="https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/"
    headers={"access-token":token}
    r=requests.get(url,headers=headers)
    if r.status_code==200:
        return r.json()
    return None

@app.route("/")
def home():
    return render_template("index.html")

# ================= TOKEN MANAGER =================

@app.route("/api/save_token",methods=["POST"])
def save_token():
    token=request.json["token"]
    info=inspect_token(token)
    if not info:
        return jsonify({"error":"invalid token"})
    conn=sqlite3.connect("database.db")
    c=conn.cursor()
    c.execute("""
    INSERT INTO tokens(uid,nickname,region,access_token)
    VALUES(?,?,?,?)
    """,(info.get("uid"),
         info.get("nickname"),
         info.get("region"),
         token))
    conn.commit()
    conn.close()
    return jsonify(info)

@app.route("/api/tokens")
def tokens():
    conn=sqlite3.connect("database.db")
    c=conn.cursor()
    c.execute("SELECT * FROM tokens")
    rows=c.fetchall()
    conn.close()

    data=[]
    for r in rows:
        data.append({
            "id":r[0],
            "uid":r[1],
            "nickname":r[2],
            "region":r[3]
        })
    return jsonify(data)

@app.route("/api/delete_token/<int:id>")
def delete_token(id):
    conn=sqlite3.connect("database.db")
    c=conn.cursor()
    c.execute("DELETE FROM tokens WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return jsonify({"deleted":id})

@app.route("/api/revoke_saved/<int:id>")
def revoke_saved(id):
    conn=sqlite3.connect("database.db")
    c=conn.cursor()
    c.execute("SELECT access_token FROM tokens WHERE id=?",(id,))
    row=c.fetchone()
    if not row:
        return jsonify({"error":"not found"})
    token=row[0]
    requests.get("https://100067.connect.garena.com/oauth/logout",
                 params={"access_token":token})
    c.execute("DELETE FROM tokens WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return jsonify({"revoked":True})

# ================= BIND FUNCTIONS =================

@app.route("/api/bind_info")
def bind_info():
    token=request.args.get("token")
    url=f"{BASE_URL}/game/account_security/bind:get_bind_info"
    r=requests.get(url,headers=HEADERS,
        params={"app_id":APP_ID,"access_token":token})
    return jsonify(r.json())

@app.route("/api/platforms")
def platforms():
    token=request.args.get("token")
    url=f"{BASE_URL}/bind/app/platform/info/get"
    r=requests.get(url,headers=HEADERS,
        params={"access_token":token})
    return jsonify(r.json())

@app.route("/api/send_otp",methods=["POST"])
def send_otp():
    d=request.json
    payload={
        "app_id":APP_ID,
        "access_token":d["token"],
        "email":d["email"]
    }
    url=f"{BASE_URL}/game/account_security/bind:send_otp"
    r=requests.post(url,headers=HEADERS,data=payload)
    return jsonify(r.json())

@app.route("/api/verify_otp",methods=["POST"])
def verify_otp():
    d=request.json
    payload={
        "app_id":APP_ID,
        "access_token":d["token"],
        "email":d["email"],
        "otp":d["otp"]
    }
    url=f"{BASE_URL}/game/account_security/bind:verify_otp"
    r=requests.post(url,headers=HEADERS,data=payload)
    return jsonify(r.json())

@app.route("/api/verify_security",methods=["POST"])
def verify_security():
    d=request.json
    payload={
        "app_id":APP_ID,
        "access_token":d["token"],
        "secondary_password":sha256_hash(d["code"])
    }
    url=f"{BASE_URL}/game/account_security/bind:verify_identity"
    r=requests.post(url,headers=HEADERS,data=payload)
    return jsonify(r.json())

@app.route("/api/rebind",methods=["POST"])
def rebind():
    d=request.json
    payload={
        "app_id":APP_ID,
        "access_token":d["token"],
        "identity_token":d["identity_token"],
        "verifier_token":d["verifier_token"],
        "email":d["new_email"]
    }
    url=f"{BASE_URL}/game/account_security/bind:create_rebind_request"
    r=requests.post(url,headers=HEADERS,data=payload)
    return jsonify(r.json())

@app.route("/api/unbind",methods=["POST"])
def unbind():
    d=request.json
    payload={
        "app_id":APP_ID,
        "access_token":d["token"],
        "identity_token":d["identity_token"]
    }
    url=f"{BASE_URL}/game/account_security/bind:unbind_identity"
    r=requests.post(url,headers=HEADERS,data=payload)
    return jsonify(r.json())

@app.route("/api/cancel")
def cancel():
    token=request.args.get("token")
    url=f"{BASE_URL}/game/account_security/bind:cancel_request"
    r=requests.post(url,headers=HEADERS,
        data={"app_id":APP_ID,"access_token":token})
    return jsonify(r.json())

@app.route("/api/revoke")
def revoke():
    token=request.args.get("token")
    r=requests.get(
        "https://100067.connect.garena.com/oauth/logout",
        params={"access_token":token})
    return jsonify({"status":r.status_code})

return jsonify({"status":r.status_code})
