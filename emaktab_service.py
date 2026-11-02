import requests
import re
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def login_and_ping_emaktab(login, password, timeout=25):
    """
    eMaktab.uz tizimiga ota-ona hisobi bilan kirish va faollik sahifalarini ochish.
    Qaytaradi: dict(success=True/False, message="...", status_code=...)
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "uz-UZ,uz;q=0.9,ru;q=0.8,en;q=0.7",
        "Referer": "https://login.emaktab.uz/",
    })

    try:
        # 1-qadam: Kirish sahifasini ochish va sessiya/tokenlarni olish
        login_page_url = "https://login.emaktab.uz/"
        res_get = session.get(login_page_url, timeout=timeout)
        if res_get.status_code != 200:
            return {
                "success": False,
                "message": f"eMaktab serveriga ulanib bo'lmadi (Status: {res_get.status_code})",
                "status_code": res_get.status_code
            }

        html = res_get.text

        # Captcha.Id ni qidirish
        captcha_id_match = re.search(r'name=["\']Captcha\.Id["\'][^>]*value=["\']([^"\']*)["\']', html)
        captcha_id = captcha_id_match.group(1) if captcha_id_match else ""

        # 2-qadam: Login va parolni yuborish (POST)
        post_data = {
            "login": login,
            "password": password,
            "Captcha.Id": captcha_id,
            "Captcha.Input": "",
        }

        # Agar ReturnUrl bo'lsa
        return_url_match = re.search(r'name=["\']ReturnUrl["\'][^>]*value=["\']([^"\']*)["\']', html)
        if return_url_match:
            post_data["ReturnUrl"] = return_url_match.group(1)

        res_post = session.post(
            login_page_url,
            data=post_data,
            headers={
                "Origin": "https://login.emaktab.uz",
                "Referer": login_page_url,
                "Content-Type": "application/x-www-form-urlencoded"
            },
            allow_redirects=True,
            timeout=timeout
        )

        final_url = res_post.url
        post_html = res_post.text

        # Tekshirish: Kirish muvaffaqiyatli bo'ldimi?
        # Agar URL login.emaktab.uz dan boshqa joyga (masalan emaktab.uz yoki schools.emaktab.uz) yo'naltirilgan bo'lsa
        is_logged_in = False
        cookies_names = [c.name.lower() for c in session.cookies]
        
        # Odatda muvaffaqiyatli kirganda auth cookielari yoki URL o'zgaradi
        if "login.emaktab.uz" not in final_url:
            is_logged_in = True
        elif any(c in cookies_names for c in [".aspnet.applicationcookie", "auth", "dnevnik_auth"]):
            is_logged_in = True
        elif "logout" in post_html.lower() or "chiqish" in post_html.lower():
            is_logged_in = True

        if not is_logged_in:
            # Xatolik sababini aniqlash
            error_reason = "Login yoki parol noto'g'ri kiritilgan"
            
            # JSON config ichidan xatolikni qidirish
            error_match = re.search(r'firstErrorText\\*["\']\s*:\s*\\*["\']([^"\']*)', post_html)
            if error_match and error_match.group(1):
                clean_err = error_match.group(1).encode('utf-8').decode('unicode_escape')
                if clean_err.strip():
                    error_reason = clean_err

            if "exceededattempts" in post_html.lower() and "true" in post_html.lower():
                error_reason = "eMaktab tizimi vaqtinchalik xavfsizlik cheklovi (Captcha) qo'ydi. Birozdan so'ng qayta urinib ko'ring."

            return {
                "success": False,
                "message": f"Kirib bo'lmadi: {error_reason}",
                "status_code": res_post.status_code,
                "final_url": final_url
            }

        # 3-qadam: Faollikni to'liq qayd etish uchun asosiy sahifalarni yuklash
        visited_pages = []
        target_urls = [
            "https://schools.emaktab.uz/",
            "https://schools.emaktab.uz/feed",
            "https://emaktab.uz/user/"
        ]

        for url in target_urls:
            try:
                time.sleep(1) # eMaktab serverini zo'riqtirmaslik uchun
                p_res = session.get(url, timeout=timeout)
                if p_res.status_code == 200:
                    visited_pages.append(url)
            except Exception as e:
                logger.warning(f"{url} sahifasiga kirishda xato: {e}")

        return {
            "success": True,
            "message": f"Muvaffaqiyatli kirildi. Faollik qayd etildi ({len(visited_pages)} ta sahifa ko'rildi).",
            "status_code": 200,
            "final_url": final_url
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "eMaktab serveri javob bermadi (Vaqt tugadi / Timeout).",
            "status_code": 504
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Internet yoki eMaktab serveriga ulanishda xatolik yuz berdi.",
            "status_code": 503
        }
    except Exception as e:
        logger.error(f"Kutilmagan xatolik: {e}")
        return {
            "success": False,
            "message": f"Kutilmagan xatolik: {str(e)}",
            "status_code": 500
        }
