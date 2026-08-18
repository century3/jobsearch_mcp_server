#默认 只取上海
from urllib.parse import urlencode, urlparse
import os
import base64
import tempfile


from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import InvalidSessionIdException
from selenium.common.exceptions import WebDriverException

import random
import time
from pathlib import Path

listurl="https://www.zhipin.com/web/geek/job?{}"

CHROME_EXE = Path("D:/AIAgent-main/tools/chrome-for-testing/chrome-win64-152.0.7977.42/chrome-win64/chrome.exe")
CHROMEDRIVER_EXE = Path("D:/AIAgent-main/tools/chrome-for-testing/chromedriver-win64-152.0.7977.42/chromedriver-win64/chromedriver.exe")
STABLE_CHROME_CANDIDATES = [
    Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
    Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
]

PROXY_TUNNEL = "g952.kdltps.com:15818"
PROXY_USERNAME = "t18660799235271"
PROXY_PASSWORD = "umsklw5h"
PROFILE_DIR = Path("D:/AIAgent-main/.chrome-boss-profile")
USE_PROXY = os.getenv("USE_PROXY", "0") == "1"
USE_PROFILE = os.getenv("USE_PROFILE", "0") == "1"
EXPECTED_HOST = "www.zhipin.com"

def get_UA():      
    UA_list = [            
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36',    
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4651.0 Safari/537.36',    
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36'  
        ]      
    randnum = random.randint(0, len(UA_list) - 1)  
    UA = UA_list[randnum]  
    return UA

def set_cookies(browser):    # 在已登录后的网站页面中获取Cookie信息    
    cookie_string = "ab_guid=d2ef3a90-ff18-4646-9ec0-408b44394ab4; lastCity=101120100; __zp_seo_uuid__=365bccd9-aa81-4fdc-a90b-5718a5e6432c; __g=-; Hm_lvt_194df3105ad7148dcf2b98a91b5e727a=1739522069,1741359607; HMACCOUNT=8174E1A21EC21A07; __l=r=https%3A%2F%2Fcn.bing.com%2F&l=%2Fwww.zhipin.com%2Fweb%2Fgeek%2Fjob&s=1&s=3&friend_source=0; SERVERID=669c12b6205dadc4b25f7f10ddc9cc19|1741441738|1741440644; Hm_lpvt_194df3105ad7148dcf2b98a91b5e727a=1741522802; wt2=DTn-yz7ad4E6Vgodv0yEAo5A0cWVJEQxQ5m979XmRzTmXuYowAvPcrj4w3uksnkLLfhbjWOPYO9ZaeZ5yUljXDQ~~; wbg=0; zp_at=tlWmkvZ1jjJ6fIfQJO34KzTKmdr4VP--3SX8Th56fKI~; __c=1741359607; __a=76416774.1739522068.1739522068.1741359607.29.2.27.29; __zp_stoken__=6ee4fw4sKw5kXPBZoZxcWeUxuemR2UVdLTGfDhWLCtnPCr8KGwprCrcK%2FwqvCkcKtwql5UUvDiMOIV8Ktw73CssSGTcKbUMK2wr%2FCjk3DrVHCnsSaw7HEusWFeMOHwr7CpkE0GRcYExYWGBcUGX%2FCgRMYFRAOEQoPEA4RCg89MsSBwpgsOzxGOjFZV1gMVWhlUWlRDltQTT88ChJkFDw4QTo%2FQMOJQcOAwqfDhz7Cu8Kiw4hAwrzDsTpHQD7Cu1AqRDwNwrrDqAxMDcK6w68MPEHDimbDr8KzIcOBdzQ8O8K6xL5HPR9EPDtHOkFHOz0vQTTDkGfDrsK3H8K7UCo6HEM9Okg6Oz06RjxJMTpJwokxPUEqSBMLDBAKKkjCvcKswr%2FDqD06"    # 拆分cookie字符串为键值对列表    
    cookie_pairs = cookie_string.split("; ")    # 添加cookie    
    for pair in cookie_pairs:      
        key, value = pair.strip().split("=", 1)      # cookie字典      
        cookie = {        
            'domain': '.zhipin.com',        
            'name': key,        
            'value': value,        
            'path': '/'      
            }      
        browser.add_cookie(cookie)      
        time.sleep(3)            # 刷新页面      
        browser.refresh()      
        return browser

def init_driver(use_proxy: bool = True, prefer_stable: bool = False)->webdriver.Chrome:
    def _build_options(binary_path: Path | None) -> Options:
        options = Options()
        if binary_path is not None:
            options.binary_location = str(binary_path)
        if USE_PROFILE:
            options.add_argument(f'--user-data-dir={PROFILE_DIR}')
        else:
            # 使用干净临时配置目录，避免历史配置/扩展把页面重定向到无关地址。
            temp_profile = Path(tempfile.mkdtemp(prefix="boss_chrome_"))
            options.add_argument(f'--user-data-dir={temp_profile}')
        options.add_argument('--disable-gpu') # 禁用GPU渲染
        options.add_argument('--ignore-certificate-errors-spki-list')  # 忽略与证书相关的错误
        options.add_argument('--disable-notifications')  # 禁用浏览器通知和推送API
        options.add_argument(f'user-agent={get_UA()}')   # 修改用户代理信息
        options.add_argument('--disable-extensions')  # 禁用浏览器扩展
        options.add_argument('--no-first-run')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--disable-default-apps')
        options.add_argument('--start-maximized')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        if use_proxy:
            options.add_argument(f'--proxy-server=http://{PROXY_TUNNEL}')  # 设置代理服务器（不在URL中拼账号密码）
        # options.add_argument('--headless=new')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--disable-features=NetworkServiceInProcess')
        return options

    def _apply_cdp(current_driver: webdriver.Chrome):
        # 尽量降低被目标站点识别为自动化浏览器的概率。
        current_driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )
        if use_proxy:
            # 某些环境下 --proxy-server 的账号密码不会自动生效，补充设置代理认证头。
            token = base64.b64encode(f"{PROXY_USERNAME}:{PROXY_PASSWORD}".encode("utf-8")).decode("ascii")
            current_driver.execute_cdp_cmd("Network.enable", {})
            current_driver.execute_cdp_cmd(
                "Network.setExtraHTTPHeaders",
                {"headers": {"Proxy-Authorization": f"Basic {token}"}},
            )

    attempts: list[tuple[str, Path | None, bool]] = []
    stable_paths = [p for p in STABLE_CHROME_CANDIDATES if p.exists()]

    if prefer_stable:
        for path in stable_paths:
            attempts.append((f"stable:{path}", path, False))
        attempts.append(("selenium-manager-default", None, False))
        if CHROME_EXE.exists() and CHROMEDRIVER_EXE.exists():
            attempts.append(("cft-fixed-driver", CHROME_EXE, True))
    else:
        if CHROME_EXE.exists() and CHROMEDRIVER_EXE.exists():
            attempts.append(("cft-fixed-driver", CHROME_EXE, True))
        for path in stable_paths:
            attempts.append((f"stable:{path}", path, False))
        attempts.append(("selenium-manager-default", None, False))

    launch_errors: list[str] = []
    for label, binary_path, use_fixed_driver in attempts:
        try:
            options = _build_options(binary_path)
            if use_fixed_driver:
                service = Service(executable_path=str(CHROMEDRIVER_EXE))
                driver = webdriver.Chrome(options=options, service=service)
            else:
                # 交给 Selenium Manager 自动匹配系统浏览器驱动。
                driver = webdriver.Chrome(options=options)
            _apply_cdp(driver)
            print(f"已使用浏览器策略: {label}")
            return driver
        except Exception as e:
            launch_errors.append(f"{label}: {e}")

    raise RuntimeError("Chrome 启动失败。尝试策略: " + " | ".join(launch_errors))

def listjob_by_keyword(keyword:str,page:int=1,size:int=30)->str:
    print("listjob")
    url=listurl.format(urlencode({
        "query":keyword,
         "city":"101020100"
        }))
    print("url: ",url)
    driver=init_driver(use_proxy=USE_PROXY)
    if driver is None:
        raise Exception("创建无头浏览器失败")
    print("创建无头浏览器成功")
    #driver.maximize_window()

    jobs=[]

    def _host_of(current_url: str) -> str:
        try:
            return urlparse(current_url).netloc.lower()
        except Exception:
            return ""

    def _is_expected_page(current_url: str) -> bool:
        host = _host_of(current_url)
        return host.endswith("zhipin.com")

    def _is_security_page(current_url: str) -> bool:
        return "/web/passport/zp/security.html" in current_url

    def _is_bad_browser_page(current_url: str, page_source: str) -> bool:
        host = _host_of(current_url)
        return (
            "ERR_INVALID_ARGUMENT" in page_source
            or current_url.startswith("data:")
            or current_url.startswith("chrome://newtab")
            or current_url.startswith("chrome://new-tab-page")
            or host.endswith("google.com")
        )

    def _normalize_window(current_driver: webdriver.Chrome):
        handles = current_driver.window_handles
        if not handles:
            return

        target_handle = None
        for handle in handles:
            current_driver.switch_to.window(handle)
            current_url = current_driver.current_url
            if _is_security_page(current_url) or _is_expected_page(current_url):
                target_handle = handle
                break

        # 未识别到目标页面时，不关闭任何窗口，避免误关正在加载中的验证码页。
        if target_handle is None:
            return

        current_driver.switch_to.window(target_handle)

        for handle in list(current_driver.window_handles):
            if handle == target_handle:
                continue
            current_driver.switch_to.window(handle)
            try:
                current_driver.close()
            except Exception:
                pass

        current_driver.switch_to.window(target_handle)

    def _guard_and_recover(current_driver: webdriver.Chrome, max_retry: int = 3):
        for _ in range(max_retry):
            _normalize_window(current_driver)
            current_url = current_driver.current_url
            page_source = current_driver.page_source
            if _is_security_page(current_url):
                # 手机验证页属于正常中间态，不做自动跳转，避免打断手动验证。
                return
            if _is_expected_page(current_url) and "ERR_INVALID_ARGUMENT" not in page_source:
                return
            print(f"检测到页面被跳转或异常（{current_url}），自动拉回目标页...")
            current_driver.get(url)
            time.sleep(1.2)
            # 拉回后立刻再检查一次，避免 max_retry=1 时误判失败。
            _normalize_window(current_driver)
            recovered_url = current_driver.current_url
            recovered_source = current_driver.page_source
            if _is_expected_page(recovered_url) and "ERR_INVALID_ARGUMENT" not in recovered_source:
                return
        raise WebDriverException(f"页面多次被跳转，current_url={current_driver.current_url}")

    def _open_and_validate(current_driver: webdriver.Chrome, with_proxy: bool):
        current_driver.get(url)
        page_source = current_driver.page_source
        current_url = current_driver.current_url
        bad_page = _is_bad_browser_page(current_url, page_source)
        if bad_page:
            reason = "ERR_INVALID_ARGUMENT"
            if current_url.startswith("data:"):
                reason = "data: 空白页"
            elif current_url.startswith("chrome://newtab") or current_url.startswith("chrome://new-tab-page"):
                reason = "chrome://newtab 异常页"
            elif _host_of(current_url).endswith("google.com"):
                reason = "google 跳转页"
            print(f"检测到浏览器异常页面（{reason}），自动切换直连重试...")
            current_driver.quit()
            current_driver = init_driver(use_proxy=False, prefer_stable=True)
            current_driver.get(url)
            page_source = current_driver.page_source
            current_url = current_driver.current_url
            if _is_bad_browser_page(current_url, page_source):
                raise WebDriverException(
                    f"仍然进入异常页面，current_url={current_url}"
                )
        return current_driver

    try:
        driver = _open_and_validate(driver, with_proxy=USE_PROXY)
        _guard_and_recover(driver)

        print("title: ",driver.title)
        print("current_url: ",driver.current_url)
        driver.save_screenshot("page_screenshot.png")
        print("title: ",driver.title)

        # 进入手动验证前先确保不是新标签页/空白页/Google页。
        _guard_and_recover(driver)

        # 如果已进入手机验证页，先暂停，等待手动交互完成。
        if _is_security_page(driver.current_url):
            print("已进入 Boss 手机验证码页面，请先在浏览器完成验证。")
            try:
                input("完成验证并确认已跳转后，按回车继续抓取岗位列表: ")
            except EOFError:
                print("当前环境非交互模式，跳过手动回车等待，继续检测岗位列表。")

        # 这里仍可能需要手动完成 Boss 验证码。
        if os.getenv("MANUAL_VERIFY", "1") == "1":
            print("请在浏览器中完成 Boss 手机验证码，完成后回到终端按回车继续...")
            try:
                input("按回车继续抓取岗位列表: ")
            except EOFError:
                print("当前环境非交互模式，跳过手动回车等待，继续检测岗位列表。")

        # 验证后页面可能瞬间被劫持到其他站点，这里持续校正并等待岗位列表。
        deadline = time.time() + 120
        while time.time() < deadline:
            _guard_and_recover(driver, max_retry=1)
            if driver.find_elements(By.CSS_SELECTOR, '.job-list-box'):
                break
            time.sleep(0.8)
        else:
            raise TimeoutException("等待岗位列表超时")

        li_list=driver.find_elements(By.CSS_SELECTOR,
                                  ".job-list-box li.job-card-wrapper")
        for li in li_list:
            job_name_list=li.find_elements(By.CSS_SELECTOR,".job-name")
            if len(job_name_list)==0:
                continue
            job={}
            job["job_name"]=job_name_list[0].text
            job_salary_list=li.find_elements(By.CSS_SELECTOR,".job-info .salary")
            if job_salary_list and len(job_salary_list)>0:
                job["job_salary"]=job_salary_list[0].text
            else:
                job["job_salary"]="暂无"
            job_tags_list=li.find_elements(By.CSS_SELECTOR,".job-info .tag-list li")
            if job_tags_list and len(job_tags_list)>0:
                job["job_tags"]=[tag.text for tag in job_tags_list]
            else:
                job["job_tags"]=[]
            com_name=li.find_element(By.CSS_SELECTOR,".company-name")
            if com_name:
                job["com_name"]=com_name.text
            else:
                continue # 
            com_tags_list=li.find_elements(By.CSS_SELECTOR,".company-tag-list li")
            if com_tags_list and len(com_tags_list)>0:
                job["com_tags"]=[tag.text for tag in com_tags_list]
            else:
                job["com_tags"]=[]
            job_tags_list_footer=li.find_elements(By.CSS_SELECTOR,".job-card-footer  li")
            if job_tags_list_footer and len(job_tags_list_footer)>0:
                job["job_tags_footer"]=[tag.text for tag in job_tags_list_footer]
            else:
                job["job_tags_footer"]=[]
            jobs.append(job)
    except InvalidSessionIdException:
        return "浏览器会话已断开（Chrome 进程退出或 DevTools 连接中断）。请重试；若仍复现，优先检查代理插件/系统安全软件是否关闭了浏览器进程。"
    except WebDriverException as e:
        if "ERR_INVALID_ARGUMENT" in str(e):
            return "页面返回 ERR_INVALID_ARGUMENT。代理隧道可用，但浏览器当前代理会话异常；请重试一次，或临时关闭代理仅验证站点可达性。"
        if "current_url=data:" in str(e) or "异常页面" in str(e):
            return "浏览器进入 data: 不安全空白页，已自动重试仍失败。建议先关闭所有 Chrome 进程后再试；若仍失败，改用系统正式版 Chrome（二进制非 Chrome for Testing）。"
        return f"浏览器异常: {e}"
    except TimeoutException:
        return "等待岗位列表超时。请确认已完成代理认证与 Boss 验证，并成功跳转到岗位列表页后重试。"
    finally:
        driver.quit()
    job_tpl="""
{}. 岗位名称: {}
公司名称: {}
岗位要求: {}
技能要求: {}
薪资待遇: {}
     """
    ret=""
    if len(jobs)>0:
        for i, job in enumerate(jobs):
            job_desc = job_tpl.format(str(i + 1), job["job_name"],
                                    job["com_name"],
                                    ",".join(job["job_tags"]),
                                    ",".join(job["job_tags_footer"]),
                                    job["job_salary"])
            ret += job_desc + "\n"
        print("完成直聘网分析")
        return ret
    else:
        return "没有找到任何岗位列表。请确认页面已成功进入岗位搜索结果页。"

if __name__ == "__main__":
    print("listjob")
    ret = listjob_by_keyword("AI应用开发")
    print(ret)