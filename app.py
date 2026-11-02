import threading
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import database
from scheduler_service import init_scheduler, process_single_account, run_all_active_accounts, update_schedule_times

app = Flask(__name__)
app.secret_key = "emaktab_auto_secret_key_random_12345"

# Ma'lumotlar bazasini va rejalashtiruvchini initsializatsiya qilish
database.init_db()
init_scheduler()

@app.route("/")
def index():
    accounts = database.get_accounts()
    stats = database.get_stats()
    settings = database.get_settings()
    return render_template("index.html", accounts=accounts, stats=stats, settings=settings)

@app.route("/api/accounts", methods=["POST"])
def add_account():
    data = request.form
    full_name = data.get("full_name")
    login = data.get("login")
    password = data.get("password")
    frequency = data.get("frequency", "daily")

    if not full_name or not login or not password:
        flash("Iltimos, barcha maydonlarni to'ldiring!", "danger")
        return redirect(url_for("index"))

    try:
        database.add_account(full_name, login, password, frequency)
        flash(f"{full_name} hisobi muvaffaqiyatli qo'shildi!", "success")
    except Exception as e:
        flash(f"Xatolik yuz berdi (balki bu login avval qo'shilgan): {str(e)}", "danger")

    return redirect(url_for("index"))

@app.route("/api/accounts/<int:account_id>/test", methods=["POST"])
def test_account(account_id):
    account = database.get_account(account_id)
    if not account:
        return jsonify({"success": False, "message": "Hisob topilmadi"}), 404

    # Tekshiruvni alohida oqimda emas, darhol bajarib natijani qaytaramiz
    res = process_single_account(account)
    return jsonify(res)

@app.route("/api/accounts/<int:account_id>/toggle", methods=["POST"])
def toggle_account(account_id):
    database.toggle_account_status(account_id)
    return jsonify({"success": True})

@app.route("/api/accounts/<int:account_id>/edit", methods=["POST"])
def edit_account(account_id):
    data = request.form
    full_name = data.get("full_name")
    login = data.get("login")
    password = data.get("password")
    frequency = data.get("frequency", "daily")

    database.update_account(account_id, full_name, login, password, frequency)
    flash("Hisob ma'lumotlari muvaffaqiyatli yangilandi!", "success")
    return redirect(url_for("index"))

@app.route("/api/accounts/<int:account_id>/delete", methods=["POST"])
def delete_account(account_id):
    database.delete_account(account_id)
    flash("Hisob o'chirildi.", "info")
    return redirect(url_for("index"))

@app.route("/api/run-all", methods=["POST"])
def run_all():
    # Fonda ishga tushirish (sayt qotib qolmasligi uchun)
    t = threading.Thread(target=run_all_active_accounts)
    t.daemon = True
    t.start()
    return jsonify({"success": True, "message": "Barcha faol hisoblar uchun avto-kirish fonda boshlandi!"})

@app.route("/logs")
def logs_page():
    logs = database.get_logs(limit=150)
    return render_template("logs.html", logs=logs)

@app.route("/api/logs/clear", methods=["POST"])
def clear_logs():
    database.clear_logs()
    flash("Barcha jurnallar tozalandi.", "info")
    return redirect(url_for("logs_page"))

@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    if request.method == "POST":
        time1 = request.form.get("schedule_time", "08:30")
        time2 = request.form.get("schedule_time_second", "18:00")
        auto_enabled = "1" if request.form.get("auto_run_enabled") else "0"

        database.update_setting("auto_run_enabled", auto_enabled)
        update_schedule_times(time1, time2)

        flash("Sozlamalar muvaffaqiyatli saqlandi!", "success")
        return redirect(url_for("settings_page"))

    settings = database.get_settings()
    return render_template("settings.html", settings=settings)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
