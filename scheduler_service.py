import time
import random
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import database
from emaktab_service import login_and_ping_emaktab

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def process_single_account(account):
    """
    Bitta ota-ona hisobi bo'yicha eMaktabga kirish va natijani saqlash.
    """
    logger.info(f"Ota-ona [{account['full_name']} / {account['login']}] uchun kirish boshlandi...")
    res = login_and_ping_emaktab(account["login"], account["password"])
    
    status = "success" if res["success"] else "error"
    msg = res["message"]
    
    database.update_account_stats(account["id"], status, msg)
    database.add_log(account["id"], account["login"], account["full_name"], status, msg)
    
    logger.info(f"Natija [{account['login']}]: {msg}")
    return res

def run_all_active_accounts():
    """
    Barcha faol hisoblar uchun ketma-ket kirib chiqish.
    """
    settings = database.get_settings()
    if settings.get("auto_run_enabled") != "1":
        logger.info("Avtomatik kirish sozlamalarda o'chirib qo'yilgan.")
        return

    accounts = database.get_accounts(active_only=True)
    logger.info(f"Rejali avto-kirish boshlandi. Jami faol hisoblar soni: {len(accounts)}")
    
    for acc in accounts:
        try:
            process_single_account(acc)
            # Har bir hisob orasida tabiiy tanaffus (blokdan saqlanish uchun)
            delay = random.randint(4, 10)
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Hisobda xatolik [{acc['login']}]: {e}")
            database.add_log(acc["id"], acc["login"], acc["full_name"], "error", f"Tizim xatosi: {str(e)}")

def init_scheduler():
    """
    Rejalashtiruvchini ishga tushirish
    """
    if scheduler.running:
        return

    settings = database.get_settings()
    time1 = settings.get("schedule_time", "08:30")
    time2 = settings.get("schedule_time_second", "18:00")

    try:
        h1, m1 = map(int, time1.split(":"))
        scheduler.add_job(
            run_all_active_accounts,
            'cron',
            hour=h1,
            minute=m1,
            id='morning_run',
            replace_existing=True
        )
    except Exception as e:
        logger.error(f"1-vaqtni o'rnatishda xato: {e}")

    try:
        h2, m2 = map(int, time2.split(":"))
        scheduler.add_job(
            run_all_active_accounts,
            'cron',
            hour=h2,
            minute=m2,
            id='evening_run',
            replace_existing=True
        )
    except Exception as e:
        logger.error(f"2-vaqtni o'rnatishda xato: {e}")

    scheduler.start()
    logger.info(f"Scheduler muvaffaqiyatli ishga tushdi: {time1} va {time2}")

def update_schedule_times(time1, time2):
    try:
        if scheduler.get_job('morning_run'):
            scheduler.remove_job('morning_run')
        if scheduler.get_job('evening_run'):
            scheduler.remove_job('evening_run')

        h1, m1 = map(int, time1.split(":"))
        scheduler.add_job(run_all_active_accounts, 'cron', hour=h1, minute=m1, id='morning_run')

        h2, m2 = map(int, time2.split(":"))
        scheduler.add_job(run_all_active_accounts, 'cron', hour=h2, minute=m2, id='evening_run')
        
        database.update_setting("schedule_time", time1)
        database.update_setting("schedule_time_second", time2)
        logger.info(f"Jadval yangilandi: {time1} va {time2}")
        return True
    except Exception as e:
        logger.error(f"Jadvalni yangilashda xato: {e}")
        return False
