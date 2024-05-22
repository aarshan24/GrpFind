import multiprocessing
import time
import requests
import json
from threading import Thread
from multiprocessing import Process, Queue
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor

LOG = 'https://discord.com/api/webhooks/1242294309638897664/0kiwNLgueINMUDtLGfvRaD4lWbUrVTipiN4vFpSmscJoTheQDASWCo-7B-ba4ZMQBMv8/messages/1242436185830326292'
GROUP = 'https://discord.com/api/webhooks/1242294309638897664/0kiwNLgueINMUDtLGfvRaD4lWbUrVTipiN4vFpSmscJoTheQDASWCo-7B-ba4ZMQBMv8'
SPECS = '(Aarshan\'s Local Machine LOL)'

def chunk_generator(chunks_queue, id_range):
    blocked_gids = {}
    last_start_id = id_range[0]
    with open('blocked_ids.txt', "r") as file:
        lines = file.readlines()
        for line in lines:
            if len(line.strip()) > 0:
                blocked_gids[int(line.strip())] = True

    first_scan = 0
    while True:
        ids_list = []
        for _ in range(1980):
            ids = ''
            added_ids = 0
            while added_ids < 100:
                if not last_start_id in blocked_gids:
                    ids += str(last_start_id) + ','
                    added_ids += 1
                last_start_id += 1
                if last_start_id > id_range[1]:
                    first_scan += 1
                    last_start_id = id_range[0]
                    break
            ids_list.append(ids)
            if first_scan == 1:
                break
        chunks_queue.put([True, ids_list])
        if first_scan == 1:
            break

    while True:
        time.sleep(0.1)
        if chunks_queue.qsize() == 0:
            print('First Scan Finished')
            time.sleep(10)
            blocked_gids.clear()
            with open('blocked_ids.txt', "r") as file:
                lines = file.readlines()
                for line in lines:
                    if len(line.strip()) > 0:
                        blocked_gids[int(line.strip())] = True
            break

    while True:
        if chunks_queue.qsize() < 10:
            for _ in range(300):
                ids_list = []
                for _ in range(1980):
                    ids = ''
                    added_ids = 0
                    while added_ids < 100:
                        if not last_start_id in blocked_gids:
                            ids += str(last_start_id) + ','
                            added_ids += 1
                        last_start_id += 1
                        if last_start_id > id_range[1]:
                            last_start_id = id_range[0]
                            blocked_gids.clear()
                            with open('blocked_ids.txt', "r") as file:
                                lines = file.readlines()
                                for line in lines:
                                    if len(line.strip()) > 0:
                                        blocked_gids[int(line.strip())] = True
                    ids_list.append(ids)
                chunks_queue.put([False, ids_list])
        else:
            time.sleep(0.1)

async def check_if_closed(group_id, owner_queue, log_queue, file_queue):
    try:
        async with aiohttp.ClientSession() as session:
            url = 'https://groups.roblox.com/v1/groups/' + str(group_id)
            async with session.get(url, timeout=3) as response:
                response_text = await response.text()
                data = json.loads(response_text)
                claimable = True
                if response.status == 200:
                    if data['owner'] is None:
                        if 'isLocked' in data and data['isLocked']:
                            claimable = False
                        if not data['publicEntryAllowed']:
                            claimable = False
                        if not claimable:
                            file_queue.put(['blocked_ids.txt', str(group_id) + '\n'])
                        else:
                            hookData = {
                                "content": SPECS + 'https://roblox.com/groups/' + str(group_id),
                                "username": "Gamek989",
                                "attachments": [],
                            }
                            requests.post(GROUP, json=hookData)
                    log_queue.put(1)
                else:
                    owner_queue.put(group_id)
                    print(response_text)
    except Exception as e:
        owner_queue.put(group_id)
        # print(e, 'dgd')

async def get_detailed_info(owner_queue, log_queue, file_queue):
    while True:
        while owner_queue.qsize() > 200:
            owner_queue.get()
        id_to_check = owner_queue.get()
        await check_if_closed(id_to_check, owner_queue, log_queue, file_queue)

async def send_req(session, log_queue, count_queue, cookie, timeout, ids, local_count, first_scan, file_queue):
    url = 'https://groups.roblox.com/v2/groups?groupIds=' + ids
    cookies = {'.ROBLOSECURITY': cookie}
    ids_check = {}
    try:
        async with session.get(url, cookies=cookies) as response:
            response_text = await response.text()
            data = json.loads(response_text)
            if 'data' in data:
                local_count.append(100)
                for i in data['data']:
                    if i['owner'] is None:
                        if not first_scan:
                            hookData = {
                                "content": SPECS + 'https://roblox.com/groups/' + str(i['id']),
                                "username": "Gamek989",
                                "attachments": [],
                            }
                            owner_queue.put(str(i['id']))
                        else:
                            file_queue.put(['blocked_ids.txt', str(i['id']) + '\n'])
                if 'ids' not in data:
                    for i in ids.split(','):
                        if i not in ids_check:
                            file_queue.put(['blocked_ids.txt', i + '\n'])
            ids_check.clear()
            ids = ''
    except Exception as e:
        pass

async def worker(log_queue, count_queue, cookies, timeout, owner_queue, chunks_queue, file_queue):
    async def main(log_queue, count_queue, cookie, timeout, ids_list, local_count, first_scan, file_queue):
        async with aiohttp.ClientSession() as session:
            tasks = [send_req(session, log_queue, count_queue, cookie, timeout, ids, local_count, first_scan, file_queue) for ids in ids_list]
            await asyncio.gather(*tasks)

    while True:
        min_end = time.time() + 60
        for cookie in cookies:
            request_data = chunks_queue.get()
            ids_list = request_data[1]
            local_count = []
            try:
                await main(log_queue, count_queue, cookie, timeout, ids_list, local_count, request_data[0], file_queue)
            except Exception as e:
                pass
            count_queue.put(sum(local_count))
        if (min_end - time.time()) > 0:
            time.sleep(min_end - time.time())

async def check_cookie(session, cookie):
    try:
        async with session.post("https://auth.roblox.com/v2/logout", cookies={'.ROBLOSECURITY': cookie}) as response:
            if 'X-CSRF-TOKEN' in response.headers:
                return cookie
    except:
        pass

async def cookie_checker():
    roblox_cookies = {}
    working_cookies = []
    with open('cookies.txt', "r") as file:
        for line in file:
            roblox_cookies[line.strip()] = True
    async with aiohttp.ClientSession() as session:
        tasks = [check_cookie(session, cookie) for cookie in roblox_cookies.keys()]
        results = await asyncio.gather(*tasks)
        for result in results:
            if result is not None:
                working_cookies.append(result)
    return working_cookies

def file_writer(file_queue):
    while True:
        data = file_queue.get()
        with open(data[0], "a") as fa:
            fa.write(data[1])

def workers_refresher():
    global workers
    while True:
        curr_workers = workers.copy()
        for worker_process, args in curr_workers.items():
            if not worker_process.is_alive():
                worker_process.terminate()
                new_worker = Process(target=worker, daemon=True, kwargs=args)
                workers.pop(worker_process)
                workers[new_worker] = args
                new_worker.start()
        time.sleep(2)

def counter(log_queue, count_queue):
    total_count = 0
    start = time.time()
    total_ownerless_count = 0
    ownerless_count = 0
    while True:
        while log_queue.qsize() > 0:
            total_ownerless_count += 1
            log_queue.get()
        if time.time() - start > 120:
            curr = total_count
            curr = total_count - curr
            ownerless_count = total_ownerless_count - ownerless_count
            hookData = {
                "content": SPECS,
                "username": "Gamek989",
                "attachments": [],
                "embeds": [
                    {
                        "title": "Activity Log",
                        "color": 3751,
                        "fields": [
                            {
                                "name": "Total Requests",
                                "value": f"{curr}",
                                "inline": True
                            },
                            {
                                "name": "Ownerless Groups",
                                "value": f"{ownerless_count}",
                                "inline": True
                            }
                        ]
                    }
                ]
            }
            requests.post(LOG, json=hookData)
            start = time.time()
            ownerless_count = total_ownerless_count

        while count_queue.qsize() > 0:
            total_count += count_queue.get()
        time.sleep(1)

def main():
    workers = {}
    log_queue = Queue()
    count_queue = Queue()
    chunks_queue = Queue()
    owner_queue = Queue()
    file_queue = Queue()
    
    id_range = [1, 999999999]
    
    # File writer process
    file_writer_process = Process(target=file_writer, daemon=True, args=(file_queue,))
    file_writer_process.start()
    
    # Counter process
    counter_process = Process(target=counter, daemon=True, args=(log_queue, count_queue))
    counter_process.start()

    # Workers refresher process
    workers_refresher_process = Process(target=workers_refresher, daemon=True)
    workers_refresher_process.start()

    # Chunk generator process
    chunk_gen_process = Process(target=chunk_generator, daemon=True, args=(chunks_queue, id_range))
    chunk_gen_process.start()
    
    loop = asyncio.get_event_loop()
    cookies = loop.run_until_complete(cookie_checker())
    
    for _ in range(multiprocessing.cpu_count()):
        worker_process = Process(target=worker, daemon=True, args=(log_queue, count_queue, cookies, 3, owner_queue, chunks_queue, file_queue))
        worker_process.start()
        workers[worker_process] = {'log_queue': log_queue, 'count_queue': count_queue, 'cookies': cookies, 'timeout': 3, 'owner_queue': owner_queue, 'chunks_queue': chunks_queue, 'file_queue': file_queue}

    # Detailed info worker process
    detailed_info_worker_process = Process(target=worker, daemon=True, args=(owner_queue, log_queue, file_queue))
    detailed_info_worker_process.start()
    workers[detailed_info_worker_process] = {'owner_queue': owner_queue, 'log_queue': log_queue, 'file_queue': file_queue}
    
    loop.run_forever()

if __name__ == '__main__':
    main()


