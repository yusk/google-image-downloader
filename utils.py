import time

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

IMG_EXTS = ('.jpg', '.jpeg', '.png', '.gif')


def get_extension(url):
    url_lower = url.lower()
    for img_ext in IMG_EXTS:
        if img_ext in url_lower:
            extension = '.jpg' if img_ext == '.jpeg' else img_ext
            break
    else:
        extension = ''
    return extension


def download_image(url, headers, loop=3, timeout=20):
    for i in range(loop):
        try:
            r = requests.get(url, headers=headers, stream=True, timeout=20)
            r.raise_for_status()
            return r.content
        except requests.exceptions.SSLError:
            print('***** SSL エラー')
            break
        except requests.exceptions.RequestException as e:
            print(f'***** requests エラー({e}): {i + 1}/{loop}')
            time.sleep(1)
        else:
            break
    return None


def get_img_bins(name, limit=30, skip_ext_valid=False):
    RETRY_NUM = 3
    ACCESS_WAIT = 1

    options = Options()
    # options.add_argument('--headless')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    # driver.set_window_size(1500, 1500)

    url = f'https://www.google.com/search?q={name}&tbm=isch'
    driver.get(url)

    tmb_elems = driver.find_elements_by_css_selector('#islmp img')
    tmb_alts = [tmb.get_attribute('alt') for tmb in tmb_elems]

    count = len(tmb_alts) - tmb_alts.count('')

    while count < limit:
        driver.execute_script(
            'window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(1)

        tmb_elems = driver.find_elements_by_css_selector('#islmp img')
        tmb_alts = [tmb.get_attribute('alt') for tmb in tmb_elems]

        count = len(tmb_alts) - tmb_alts.count('')

    imgframe_elem = driver.find_element_by_id('islsp')
    HTTP_HEADERS = {
        'User-Agent': driver.execute_script('return navigator.userAgent;')
    }

    EXCLUSION_URL = 'https://lh3.googleusercontent.com/'
    count = 0
    for tmb_elem, tmb_alt in zip(tmb_elems, tmb_alts):
        if tmb_alt == '':
            continue

        print(f'{count}: {tmb_alt}')

        for i in range(RETRY_NUM):
            try:
                tmb_elem.click()
            except ElementClickInterceptedException:
                print(f'***** click エラー: {i + 1}/{RETRY_NUM}')
                driver.execute_script('arguments[0].scrollIntoView(true);',
                                      tmb_elem)
                time.sleep(1)
            else:
                break
        else:
            print('***** キャンセル')
            continue

        time.sleep(ACCESS_WAIT)

        alt = tmb_alt.replace("'", "\\'")
        try:
            img_elem = imgframe_elem.find_element_by_css_selector(
                f'img[alt=\'{alt}\']')
        except NoSuchElementException:
            print('***** img要素検索エラー')
            print('***** キャンセル')
            continue

        tmb_url = tmb_elem.get_attribute('src')
        for i in range(RETRY_NUM):
            url = img_elem.get_attribute('src')
            if EXCLUSION_URL in url:
                print('***** 除外対象url')
                url = ''
                break
            elif url == tmb_url:
                print(f'***** urlチェック: {i + 1}/{RETRY_NUM}')
                time.sleep(1)
                url = ''
            else:
                break

        if url == '':
            print('***** キャンセル')
            continue

        ext = get_extension(url)
        if ext == '':
            if skip_ext_valid:
                ext = '.png'
            else:
                print('***** urlに拡張子が含まれていないのでキャンセル')
                print(f'{url}')
                continue

        result = download_image(url, HTTP_HEADERS, loop=RETRY_NUM)
        if result:
            yield (result, ext)
        else:
            print('***** キャンセル')
            continue

        count += 1
        if count >= limit:
            break
