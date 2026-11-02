import os
import sys
import threading
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, flash
import database
from scheduler_service import init_scheduler, process_single_account, run_all_active_accounts, update_schedule_times

app = Flask(__name__)
app.secret_key = "emaktab_auto_secret_key_random_12345"

database.init_db()
init_scheduler()

INDEX_HTML = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>eMaktab Avto-Kirish Boshqaruv Paneli</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <style>
        body { background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1e293b; }
        .navbar-custom { background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%); }
        .card-custom { border-radius: 14px; border: 1px solid #e2e8f0; background: #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
        .stat-card { transition: all 0.2s; border-radius: 14px; border: 1px solid #e2e8f0; }
        .stat-card:hover { transform: translateY(-2px); box-shadow: 0 8px 15px -3px rgba(0,0,0,0.08); }
        .table th { background-color: #f1f5f9; color: #64748b; font-size: 0.8rem; text-transform: uppercase; padding: 12px 16px; }
        .table td { padding: 12px 16px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark navbar-custom shadow-sm sticky-top">
        <div class="container">
            <a class="navbar-brand d-flex align-items-center gap-2 fw-bold" href="/">
                <i class="bi bi-mortarboard-fill fs-3"></i>
                <span>eMaktab Avto-Kirish (Server)</span>
            </a>
            <div class="ms-auto d-flex align-items-center gap-2">
                <span class="badge bg-success px-3 py-2 rounded-pill"><i class="bi bi-check-circle me-1"></i> Server Faol (24/7)</span>
            </div>
        </div>
    </nav>

    <div class="container py-4">
        <div class="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-2">
            <div>
                <h3 class="fw-bold mb-1"><i class="bi bi-person-lines-fill text-primary me-2"></i>Ota-onalar Hisoblari ({{ accounts|length }})</h3>
                <p class="text-muted small mb-0">Server har kuni 08:30 va 18:00 da o'zi avtomatik kirib, faollikni (KPI) 100% ushlab turadi</p>
            </div>
            <div class="d-flex gap-2">
                <button class="btn btn-outline-primary" id="btnRunAll" onclick="runAll()">
                    <i class="bi bi-play-circle-fill me-1"></i> Barchasiga Kirish
                </button>
                <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addModal">
                    <i class="bi bi-person-plus-fill me-1"></i> Yangi Hisob
                </button>
            </div>
        </div>

        <div class="row g-3 mb-4">
            <div class="col-sm-6 col-md-3">
                <div class="card stat-card p-3 bg-white">
                    <span class="text-muted small fw-semibold">Jami Hisoblar</span>
                    <h3 class="fw-bold mb-0 text-dark">{{ stats.total_accounts }}</h3>
                </div>
            </div>
            <div class="col-sm-6 col-md-3">
                <div class="card stat-card p-3 bg-white">
                    <span class="text-muted small fw-semibold">Faol Avto-Kirish</span>
                    <h3 class="fw-bold mb-0 text-success">{{ stats.active_accounts }}</h3>
                </div>
            </div>
            <div class="col-sm-6 col-md-3">
                <div class="card stat-card p-3 bg-white">
                    <span class="text-muted small fw-semibold">Muvaffaqiyatli</span>
                    <h3 class="fw-bold mb-0 text-info">{{ stats.total_success }}</h3>
                </div>
            </div>
            <div class="col-sm-6 col-md-3">
                <div class="card stat-card p-3 bg-white">
                    <span class="text-muted small fw-semibold">Avto-reja Soatlari</span>
                    <h4 class="fw-bold mb-0 text-primary">{{ settings.get('schedule_time', '08:30') }} / {{ settings.get('schedule_time_second', '18:00') }}</h4>
                </div>
            </div>
        </div>

        <div class="card card-custom overflow-hidden mb-4">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>F.I.Sh / O'quvchi</th>
                            <th>eMaktab Logini</th>
                            <th>Oxirgi Kirish</th>
                            <th>Holati</th>
                            <th class="text-center">Avto-kirish</th>
                            <th class="text-end">Amallar</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for acc in accounts %}
                            <tr>
                                <td class="text-muted">{{ loop.index }}</td>
                                <td>
                                    <strong>{{ acc.full_name }}</strong>
                                    <span class="badge bg-light text-dark border ms-1">{{ acc.frequency }}</span>
                                </td>
                                <td><code>{{ acc.login }}</code></td>
                                <td class="small text-muted">{{ acc.last_run or 'Hali kirmagan' }}</td>
                                <td>
                                    {% if acc.last_status == 'Muvaffaqiyatli' %}
                                        <span class="badge bg-success-subtle text-success border border-success-subtle px-2 py-1"><i class="bi bi-check-circle me-1"></i> Muvaffaqiyatli</span>
                                    {% elif acc.last_status == 'Xatolik' %}
                                        <span class="badge bg-danger-subtle text-danger border border-danger-subtle px-2 py-1" title="{{ acc.last_message }}"><i class="bi bi-x-circle me-1"></i> Xatolik</span>
                                    {% else %}
                                        <span class="badge bg-secondary-subtle text-secondary border px-2 py-1"><i class="bi bi-hourglass-split me-1"></i> Kutilmoqda</span>
                                    {% endif %}
                                </td>
                                <td class="text-center">
                                    <div class="form-check form-switch d-inline-block">
                                        <input class="form-check-input" type="checkbox" onchange="toggleStatus({{ acc.id }})" {% if acc.is_active == 1 %}checked{% endif %}>
                                    </div>
                                </td>
                                <td class="text-end">
                                    <button class="btn btn-sm btn-outline-success me-1" id="btn-test-{{ acc.id }}" onclick="testLogin({{ acc.id }})" title="Hoziroq kirish">
                                        <i class="bi bi-lightning-charge-fill"></i> Kirish
                                    </button>
                                </td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Modal -->
    <div class="modal fade" id="addModal" tabindex="-1">
        <div class="modal-dialog">
            <form action="/api/accounts" method="POST" class="modal-content border-0 shadow">
                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title"><i class="bi bi-person-plus-fill me-2"></i>Yangi Hisob Qo'shish</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label fw-semibold">F.I.Sh</label>
                        <input type="text" name="full_name" class="form-control" placeholder="F.I.Sh va sinfi" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">eMaktab Logini</label>
                        <input type="text" name="login" class="form-control" required autocomplete="off">
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">eMaktab Paroli</label>
                        <input type="password" name="password" class="form-control" required autocomplete="new-password">
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Kirish davriyligi</label>
                        <select name="frequency" class="form-select">
                            <option value="daily" selected>Har kuni (100% KPI)</option>
                            <option value="every_2_days">Har 2 kunda</option>
                            <option value="weekly">Haftada bir marta</option>
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Bekor qilish</button>
                    <button type="submit" class="btn btn-primary">Saqlash</button>
                </div>
            </form>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        async function testLogin(id) {
            const btn = document.getElementById("btn-test-" + id);
            const orig = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
            try {
                const res = await fetch("/api/accounts/" + id + "/test", { method: "POST" });
                const d = await res.json();
                alert((d.success ? "✅ " : "❌ ") + d.message);
                window.location.reload();
            } catch(e) {
                alert("Xatolik: " + e.message);
                btn.disabled = false;
                btn.innerHTML = orig;
            }
        }

        async function runAll() {
            if(!confirm("Barcha faol hisoblar uchun kirish boshlansinmi?")) return;
            const btn = document.getElementById("btnRunAll");
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Boshlandi...';
            try {
                const res = await fetch("/api/run-all", { method: "POST" });
                const d = await res.json();
                alert(d.message);
                setTimeout(() => window.location.reload(), 3000);
            } catch(e) {
                alert("Xato: " + e.message);
                btn.disabled = false;
            }
        }

        async function toggleStatus(id) {
            await fetch("/api/accounts/" + id + "/toggle", { method: "POST" });
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    accounts = database.get_accounts()
    stats = database.get_stats()
    settings = database.get_settings()
    logs = database.get_logs(limit=30)
    return render_template_string(INDEX_HTML, accounts=accounts, stats=stats, settings=settings, logs=logs)

@app.route("/api/accounts", methods=["POST"])
def add_account():
    data = request.form
    full_name = data.get("full_name")
    login = data.get("login")
    password = data.get("password")
    frequency = data.get("frequency", "daily")

    if not full_name or not login or not password:
        flash("Barcha maydonlarni to'ldiring!", "danger")
        return redirect(url_for("index"))

    try:
        database.add_account(full_name, login, password, frequency)
        flash(f"{full_name} muvaffaqiyatli qo'shildi!", "success")
    except Exception as e:
        flash(f"Xatolik: {str(e)}", "danger")

    return redirect(url_for("index"))

@app.route("/api/accounts/<int:account_id>/test", methods=["POST"])
def test_account(account_id):
    account = database.get_account(account_id)
    if not account:
        return jsonify({"success": False, "message": "Hisob topilmadi"}), 404
    res = process_single_account(account)
    return jsonify(res)

@app.route("/api/accounts/<int:account_id>/toggle", methods=["POST"])
def toggle_account(account_id):
    database.toggle_account_status(account_id)
    return jsonify({"success": True})

@app.route("/api/accounts/<int:account_id>/delete", methods=["POST"])
def delete_account(account_id):
    database.delete_account(account_id)
    flash("Hisob o'chirildi.", "info")
    return redirect(url_for("index"))

@app.route("/api/run-all", methods=["POST"])
def run_all():
    t = threading.Thread(target=run_all_active_accounts)
    t.daemon = True
    t.start()
    return jsonify({"success": True, "message": "Barcha faol hisoblar uchun avto-kirish fonda boshlandi!"})

@app.route("/api/logs/clear", methods=["POST"])
def clear_logs():
    database.clear_logs()
    flash("Jurnallar tozalandi.", "info")
    return redirect(url_for("index"))

@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "emaktab-server"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
