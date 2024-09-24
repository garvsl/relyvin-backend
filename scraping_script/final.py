import logging
import random
import sys
from selenium_driverless import webdriver

import asyncio
import ssl
from prisma import Prisma
import datetime

from dotenv import load_dotenv

from scraping_script.utils.paths import USER_XPATHS
from utils.general import scraper_sign_in, time_calc
from utils.prisma import app_auth, get_user, get_usernames, set_checked
from utils.processes import gather_usernames, process_profile

load_dotenv()


ssl._create_default_https_context = ssl._create_unverified_context

logging.basicConfig( 
    level=logging.INFO,
    format="%(asctime)s: %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  
        logging.StreamHandler(sys.stdout)  
    ]
)

logger = logging.getLogger(__name__)



async def main(cur_user:str):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    # proxy = f"http://{proxy_info['username']}:{proxy_info['password']}@{proxy_info['host']}:{proxy_info['port']}"
    # print(proxy)
    # options.add_argument(f"--proxy-server=http://{proxy_string}")
    # options.add_argument('--ignore-certificate-errors')
    # options.single_proxy = proxy
    # Optional: Disable WebRTC (prevents IP leaks via WebRTC)
    # options.add_argument('--disable-webrtc')
    # 2f3a89ac-73b1-48c6-a6bc-44c76bd3877b
    # moh =  await get_user("b72731c5-6f3c-4414-b293-bf28d6611dda", prisma)
    # garv =  await get_user('9c86640e-af9a-432b-a198-7b794f6456e9', prisma)

    logger.info('Connected')
    prisma = Prisma()
    await prisma.connect()
    
    kp = await get_user("c58cd9c3-76da-4790-92f8-54e27d432cc2", prisma, logger)
    user = await app_auth(cur_user, prisma, logger)

    scrapers = {
        '0': {},
        '1': {},
        '2': {}
    }

    
    for scrape in user.get('Scraper', None):
        scrape_email = scrape.get('email', None)

        if not scrape_email:
            return

        if 'kp' in scrape_email:   
            scrapers['0'] = scrape
        elif 'harry' in scrape_email:  
            scrapers['1'] = scrape
        elif 'ateeq' in scrape_email:  
            scrapers['2'] = scrape


        
    usernames = await get_usernames(prisma, logger)

    index = 2
    emailsSent = 0
    iterations = 0
    now = datetime.datetime.now()
    while True:

        if index != 0:
            print('Sleeping')
            # await asyncio.sleep(30) 
            await asyncio.sleep(random.uniform(400, 1600)) 
        
        if index == 3:
            index = 0

        user_scraper = scrapers.get(str(index))

        async with webdriver.Chrome(options=options) as driver:

            logger.info('Starting Scrape')

            await driver.get("https://www.instagram.com", wait_load=True)
            await driver.sleep(5)

            logger.info(f"Continuing with Scraper {index}")
            

            await scraper_sign_in(driver, prisma, user_scraper, logger, asyncio)

                
            await asyncio.sleep(10)


            loop = True
            
            while loop:
                if usernames is None or len(usernames) == 0 :
                    logger.info("Getting more usernames")
                    usernames = await get_usernames(prisma, logger) 
                    if usernames is None: 
                        logger.info("No usernames to process, gathering")
                        await gather_usernames(driver, prisma, USER_XPATHS[index], logger, asyncio)
                        continue 
                        
                time_calc(emailsSent, now, iterations, logger)
                
                username = usernames.pop(0)
                
                proc = await process_profile(driver, prisma, username.handle, kp, USER_XPATHS[index], logger, asyncio)

                # #test
                # if iterations == 10:
                #     proc = {'status': 'detected'}


                if proc and proc.get('status') == 'detected':
                    loop = False
                    break

                logger.info("Set Checked")
                await set_checked(prisma, username.handle, logger)

                if proc and proc.get('status') == 'success':
                    emailsSent += 1

                await asyncio.sleep(random.uniform(1.5, 2.5))
                iterations += 1

            index += 1
            logger.info('Waiting')

            
            
    await prisma.disconnect()
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.info("Error: User ID not provided")
        sys.exit(1)
    cur_user = sys.argv[1]
    try:
        asyncio.run(main(cur_user))
    except Exception as e:
        logger.info(f'\n\nScript has encountered an error: {str(e)}')
        import traceback
        logger.info(traceback.format_exc())