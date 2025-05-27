import os
import asyncio
from dotenv import load_dotenv
from aiohttp import web
from pymongo import MongoClient
import random
from bs4 import BeautifulSoup
import re
from lzhaiofetcher import AioFetcher
from lzhasyncemailsender import AsyncEmailSender
from lzhbaidutranslate import baidu_translate
import logging
from lzhgetlogger import get_logger

logger = get_logger(level=logging.INFO)

load_dotenv()

PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "127.0.0.1")
APP_PATH = os.getenv("APP_PATH", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = os.getenv("SMTP_PORT", 587)
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
BAIDU_APP_ID = os.getenv("BAIDU_APP_ID", "")
BAIDU_APP_KEY = os.getenv("BAIDU_APP_KEY", "")

MongoClientUri = os.getenv("MONGODB_CLIENT_URL", "")
service = {}
hyu_me_ids = set()
hyu_oia_ids = set()
mailing_list = []

mongoDb_lock = asyncio.Lock()
service_lock = asyncio.Lock()
mailing_list_lock = asyncio.Lock()

fetcher = None
sender = None

async def task_hyu_oia():
    global hyu_me_ids
    global mailing_list
    global fetcher
    global sender
    while True:
        if not await is_service_active('hyu-oia'):
            await asyncio.sleep(3)
            continue
        url = 'https://oia.hanyang.ac.kr/notice'
        content = await fetcher.fetch(url)
        if not content:
            logger.info('task hyu-oia : error occurred')
            await sender.send("zhhtdm@gmail.com","task_hyu_oia 出错了", "没有下载到 HTML")
            await asyncio.sleep(await random_sec('hyu-oia'))
            continue
        soup = BeautifulSoup(content, "html.parser")
        table = soup.find('table', class_= 'list_wrap')
        tbody = table.find('tbody') if table else ''
        trs = tbody.find_all('tr') if tbody else ''
        logger.debug(f"hyu-oia 有 {len(trs)} 个 li 标签")
        if not trs:
            logger.info('task hyu-oia : error occurred')
            await sender.send("zhhtdm@gmail.com","task_hyu_oia 出错了", "没有找到条目 tag")
            await asyncio.sleep(await random_sec('hyu-oia'))
            continue
        items = {}
        delete_items_len = 0
        for tr in trs:
            title_td = tr.find('td',class_='title')
            a_tag = title_td.find("a", href=True)
            if a_tag:
                id_match = re.search(r"/notice/(\d+)", a_tag["href"])
                if id_match:
                    id = int(id_match.group(1))
                    subject_text = a_tag.get_text(strip=True) if a_tag else ''
                    if subject_text.startswith('[취업/채용]'): # 剔除就业招聘
                        logger.debug(f"hyu-oia 剔除了就业招聘通知: {subject_text}")
                        delete_items_len = delete_items_len + 1
                        continue
                    datetime_td = tr.find('td', class_='time m-no')
                    pub_date_value = datetime_td.get_text(strip=True) if datetime_td else ''
                    items[id] = {}
                    items[id]["datetime"] = pub_date_value
                    items[id]["title"] = subject_text
                else :
                    logger.debug(f"hyu-oia a标签内没有找到id: {tr}")
            else :
                logger.debug(f"hyu-oia 没有a标签: {tr}")
        logger.debug(f"hyu-oia 剔除了 {delete_items_len} 条就业招聘通知")
        ids = set(items.keys())
        if not ids:
            logger.info('task hyu-oia : error occurred')
            await sender.send("zhhtdm@gmail.com","task_hyu_oia 出错了", "没有找到条目")
            await asyncio.sleep(await random_sec('hyu-oia'))
            continue
        ids.difference_update(hyu_oia_ids)
        if not ids:
            logger.info('task hyu-oia is running...')
            await asyncio.sleep(await random_sec('hyu-oia'))
            continue
        logger.info(f'new_hyu_oia_ids: {ids}')
        titles = [items[id]['title'] for id in ids]
        translated_titles = baidu_translate(BAIDU_APP_ID,BAIDU_APP_KEY,titles,from_lang="auto")
        async with mailing_list_lock:
            emails = mailing_list.copy()
        
        for id, translated_title in zip(ids, translated_titles):
            logger.info(translated_title)
            await sender.send(
                to = emails,
                subject = f'''汉阳大国际处公告 - {items[id]['datetime']}''',
                body = f'''<h2>{translated_title}</h2><a href = 'https://oia.hanyang.ac.kr/notice/{id}' style="text-decoration:none;"><h2>{items[id]['title']}</h2></a>''',
                )
        hyu_oia_ids.update(ids)
        new_docs = [{'_id':new_id} for new_id in ids]
        async with mongoDb_lock:
            client = MongoClient(MongoClientUri)
            db = client['hyu-bulletin']
            collection = db['hyu-oia-ids']
            try:
                collection.insert_many(new_docs)
            except Exception as e:
                pass
            client.close()
        await asyncio.sleep(await random_sec('hyu-oia'))

async def is_service_active(name):
    global service
    async with service_lock:
        return service[name]["isActive"]

async def random_sec(key):
    global service
    async with service_lock:
        return round(random.uniform(3600*24/service[key]["qpd"][1], 3600*24/service[key]["qpd"][0]))

async def task_hyu_me():
    global hyu_me_ids
    global mailing_list
    global fetcher
    global sender
    while True:
        if not await is_service_active('hyu-me'):
            await asyncio.sleep(3)
            continue
        url = 'https://me.hanyang.ac.kr/kor/notice/graduate__1.html'
        content = await fetcher.fetch(url)
        if not content:
            logger.info('task hyu-me : error occurred')
            await sender.send("zhhtdm@gmail.com","task_hyu_me 出错了", "没有下载到 HTML")
            await asyncio.sleep(await random_sec('hyu-me'))
            continue
        soup = BeautifulSoup(content, "html.parser")
        ul = soup.find('ul', class_= 'list_bx')
        lis = ul.find_all('li') if ul else None
        logger.debug(f"hyu-me 有 {len(lis)} 个 li 标签")
        if not lis:
            logger.info('task hyu-me : error occurred')
            await sender.send("zhhtdm@gmail.com","task_hyu_me 出错了", "没有找到条目 tag")
            await asyncio.sleep(await random_sec('hyu-me'))
            continue
        items = {}
        delete_items_len = 0
        for li in lis:
            a_tag = li.find("a", href=True)
            if a_tag:
                id_match = re.search(r"uid=(\d+)", a_tag["href"])
                if id_match:
                    id = int(id_match.group(1))
                    subject_text = a_tag.get_text(strip=True)
                    if subject_text.startswith('[학부]'): # 剔除学部通知
                        logger.debug(f"hyu-me 剔除了学部通知: {subject_text}")
                        delete_items_len = delete_items_len + 1
                        continue
                    pub_date_value = li.find('div', class_='date').get_text(strip=True)
                    
                    items[id] = {}
                    items[id]["datetime"] = pub_date_value
                    items[id]["title"] = subject_text
                else :
                    logger.debug(f"hyu-me a标签内没有找到id: {li}")
            else :
                logger.debug(f"hyu-me 没有a标签: {li}")
        logger.debug(f"hyu-me 剔除了 {delete_items_len} 条学部通知")
        ids = set(items.keys())
        if not ids:
            logger.error('task hyu-me : error occurred')
            await sender.send("zhhtdm@gmail.com","task_hyu_me 出错了", "没有找到条目")
            await asyncio.sleep(await random_sec('hyu-me'))
            continue
        ids.difference_update(hyu_me_ids)
        if not ids:
            logger.info('task hyu-me is running...')
            await asyncio.sleep(await random_sec('hyu-me'))
            continue
        logger.info(f'new_hyu_me_ids: {ids}')
        titles = [items[id]['title'] for id in ids]
        translated_titles = baidu_translate(BAIDU_APP_ID,BAIDU_APP_KEY,titles,from_lang="kor")
        async with mailing_list_lock:
            emails = mailing_list.copy()
        for id, translated_title in zip(ids, translated_titles):
            logger.info(translated_title)
            await sender.send(
                to = emails,
                subject = f'''汉阳大机械工程系公告 - {items[id]['datetime']}''',
                body = f'''<h2>{translated_title}</h2><a href = 'https://me.hanyang.ac.kr/front/bulletin/bulletinSub1/notice-view?id={id}' style="text-decoration:none;"><h2>{items[id]['title']}</h2></a>''',
                )
        hyu_me_ids.update(ids)
        new_docs = [{'_id':id} for id in ids]
        async with mongoDb_lock:
            client = MongoClient(MongoClientUri)
            db = client['hyu-bulletin']
            collection = db['hyu-me-ids']
            try:
                collection.insert_many(new_docs)
            except Exception as e:
                pass
            client.close()
        await asyncio.sleep(await random_sec('hyu-me'))

async def handle_service_update(request):
    global service
    go = {}
    come = {}
    try :
        come = await request.json()
    except Exception as e:
        logger.info(e)
        go["message"]="error data"
        go["type"]="error"
        return web.json_response(go)
    go["type"]="success"
    go["message"] = "success"
    async with service_lock:
        if come :
            async with mongoDb_lock:
                client = MongoClient(MongoClientUri)
                db = client['hyu-bulletin']
                collection = db["service"]
                for	key, value in come.items():
                    # logger.info(value)
                    if "isActive" not in value or not isinstance(value["isActive"],bool) or "qpd" not in value or not isinstance(value["qpd"],list) or len(value["qpd"])!=2 or not all(isinstance(i,int) for i in value["qpd"]): 
                        go["message"]="error data"
                        go["type"]="error"
                        return web.json_response(go)
                    elif (service[key] != value):
                        service[key].update(value)
                        logger.info(key)
                        collection.update_one({"name":key},{"$set":value})
                client.close()
        go["data"] = service
    return web.json_response(go)

async def redirect_to_slash(request):
    return web.HTTPMovedPermanently(location=request.path + "/")

async def handle_settings_index(request):
    return web.FileResponse("settings/deploy/index.html")

async def start_server():
    app = web.Application()

    app.router.add_get(f"/{APP_PATH}settings/", handle_settings_index)
    app.router.add_get(f"/{APP_PATH}settings", redirect_to_slash)
    app.router.add_post(f"/{APP_PATH}settings/service-update", handle_service_update)
    app.router.add_static(f"/{APP_PATH}settings/", path="settings/deploy/")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()

    while True:
        await asyncio.sleep(3600)
        
async def service_setdefault(key, collection):
    global service
    async with service_lock:
        service[key] = {}
        result = collection.find_one({"name":key})
        if result and "isActive" in result and isinstance(result["isActive"],bool) and "qpd" in result and isinstance(result["qpd"],list) and len(result["qpd"])==2 and all(isinstance(i,int) for i in result["qpd"]):
            service[key]["isActive"] = result.get("isActive")
            service[key]["qpd"] = result.get("qpd")
        else :
            if result:
                collection.delete_many({"name",key})
            collection.insert_one({"name":key,"isActive":False,"qpd":[10, 50]})
            service[key]["isActive"] = False
            service[key]["qpd"] = [10, 50]

async def update_local_db():
    global hyu_me_ids
    global hyu_oia_ids
    global mailing_list
    client = MongoClient(MongoClientUri)
    db = client['hyu-bulletin']
    collection = db["service"]
    await service_setdefault('hyu-me',collection)
    await service_setdefault('hyu-oia',collection)
    collection = db['hyu-me-ids']
    hyu_me_ids = ({doc['_id'] for doc in collection.find({},{'_id':1})})
    collection = db['hyu-oia-ids']
    hyu_oia_ids = {doc['_id'] for doc in collection.find({},{'_id':1})}
    collection = db['mailing-list']
    mailing_list = [document['_id'] for document in collection.find({}, {'_id': 1})]
    client.close()

async def main():
    global fetcher
    global sender
    global mailing_list

    await update_local_db()
    logger.info(service)
    logger.info(mailing_list)
    logger.info(len(hyu_me_ids))
    logger.info(len(hyu_oia_ids))
    
    fetcher = AioFetcher()
    sender = AsyncEmailSender(SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD)

    await asyncio.gather(
        start_server(),
        task_hyu_me(),
        task_hyu_oia(),
        )
    
    await fetcher.close()
    await sender.stop()

if __name__ == "__main__":
    asyncio.run(main())
