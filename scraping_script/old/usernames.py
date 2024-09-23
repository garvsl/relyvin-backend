import logging
import random
import sys
from selenium_driverless import webdriver
from selenium_driverless.types.by import By
import asyncio
import ssl  
from bs4 import BeautifulSoup
import re
import unicodedata
from prisma import Prisma
import json
import datetime
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText
import resend
from dotenv import load_dotenv
import os
import bcrypt
load_dotenv()

resend.api_key = os.getenv('RESEND_API_KEY')
ssl._create_default_https_context = ssl._create_unverified_context

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(message)s",
    handlers=[
        logging.FileHandler("username.log"),  # Save logs to a file
        logging.StreamHandler(sys.stdout)  # Output logs to stdout
    ]
)

logger = logging.getLogger(__name__)

XPATHS = {
    'SCRAPE_DETECT': '/html/body/div[2]/div/div/div[2]/div/div/div[1]/section/main/div[2]/div/div/div/div/div[1]/div/div/div[2]/div[2]/div',
    'POSTS': '/html/body/div[2]/div/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/div[2]/div/div[1]',
    'EXIT_BUTTON': '/html/body/div[7]/div[1]/div/div[2]/div',
    'MORE_BUTTON': '/html/body/div[7]/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/div[3]/div/div/li/div/button',
    'MORE_BUTTON_TWO': '/html/body/div[8]/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/div[3]/div/div/li/div/button',               
    'COMMENTS': '/html/body/div[7]/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/div[3]/div/div',
    'COMMENTS_TWO': '/html/body/div[8]/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/div[3]/div/div'
}

async def navigate(driver, handle):
    try:
        await driver.get(f"https://www.instagram.com/{handle}")
        await asyncio.sleep(1)
        return True
    except Exception as e:
        logger.info(f"Error navigating to {handle}: {e}")
        return False

        
async def get_element_text(driver, xpath, timeout=3):
    try:
        element = await driver.find_element(By.XPATH, xpath, timeout=timeout)
        return BeautifulSoup(await element.source, 'html.parser').get_text(separator='\n', strip=True)
    except Exception as e:
        logger.info(f"Error finding element with xpath {xpath}: {e}")
        return None
        

async def scrape_detect(driver):
    try:
        scrape = await driver.find_element(By.XPATH, XPATHS['SCRAPE_DETECT'])
        logger.info('Scrape detected, clicking...')
        await scrape.click()
        await asyncio.sleep(1)
    except:
        # logger.info('No scrape detection')
        pass

async def get_influencers(prisma):

    total_unchecked = await prisma.influencer.count(
        where={
            'checked': False,
        }
    )

    if total_unchecked == 0:
        return None
    
    random_offset = random.randint(0, max(0, total_unchecked - 100))
    
    influencers = await prisma.influencer.find_many(
        take=100,
        skip=random_offset,
        where={
            'checked': False,
        },
        order={
            'created': 'asc'  
        }
    )

    if len(influencers) < 100:
        additional_influencers = await prisma.influencer.find_many(
            take=100 - len(influencers),
            where={
                'checked': False,
            },
            order={
                'created': 'desc'
            }
        )
        influencers.extend(additional_influencers)

    random.shuffle(influencers)

    
    return influencers if len(influencers) > 0 else None


async def create_username(prisma:Prisma, usernames):
    try:
        usernames = await prisma.username.create_many(
            data=usernames,
            skip_duplicates=True
        )
        logger.info(usernames)
        logger.info("Usernames created")
        return usernames
    except Exception as e:
        logger.info(f"Couldn't create username: {e}")
        return None
    
async def load_comments(driver):
    while True:
        load_more = None
        load_more_two = None

        try:
            # Attempt to find the first load more button
            load_more = await driver.find_element(By.XPATH, XPATHS['MORE_BUTTON'], timeout=3)
        except:
            load_more = None

        if load_more is not None:
            try:
                await load_more.click(move_to=True)
                logger.info('Loading comments using first button')
                await driver.sleep(3)
            except Exception as e:
                logger.error(f"Error clicking first button: {e}")
                break
        else:
            # If the first button was not found, check for the second button
            try:
                load_more_two = await driver.find_element(By.XPATH, XPATHS['MORE_BUTTON_TWO'], timeout=3)
                if load_more_two is not None:
                    try:
                        await load_more_two.click(move_to=True)
                        logger.info('Loading comments using second button')
                        await driver.sleep(3)
                    except Exception as e:
                        logger.error(f"Error clicking second button: {e}")
                        break
                else:
                    logger.info("No more comments to load")
                    break
            except:
                logger.info("No more comments to load")
                break



async def add_comments(driver):
    try:
        comments = await driver.find_element(By.XPATH, XPATHS['COMMENTS'], timeout=3)
        logger.info("Added comments")
    except:
        try:
            comments = await driver.find_element(By.XPATH, XPATHS["COMMENTS_TWO"], timeout=3)
            logger.info("Added comments two")
        except:
            logger.info("No comments to add")
            return
        
    comments_src = await comments.source

    soup = BeautifulSoup(comments_src, 'html.parser')    
    people = soup.find_all('h3')
    return people
    
    
   

async def process_profile(driver, prisma, influencer, user_dict) -> int:
    num = 0
    usernames = []

    if not await navigate(driver, influencer):
        return num
    
    await asyncio.sleep(2)
    await scrape_detect(driver)

    try:
        await driver.find_element(By.XPATH, XPATHS['POSTS'], timeout=3)
    except Exception as e:
        logger.info(f"Error finding element with xpath {XPATHS['POSTS']}: {e}")
        return num
    
    posts = [XPATHS['POSTS'] + "/div[1]", XPATHS['POSTS'] + "/div[2]", XPATHS['POSTS'] + "/div[3]"]

    for post in posts:
        print("Start post")
        try:
            await driver.sleep(1)
            single = await driver.find_element(By.XPATH, post, timeout=3)
            await single.click()

            await driver.sleep(2)
            await load_comments(driver)
            
      
            people = await add_comments(driver)
            
   

            if people:
                for p in people:
                    username = p.find('a')
                    if username.text not in usernames:
                        usernames.append(username.text)

            logger.info(len(usernames))
            

            await driver.back()
        

        except Exception as e:
            logger.info(f"Post error: {e}")

        print("End post")
        


    usernames = [{'handle':username} for username in usernames]
    logger.info(usernames)
    logger.info(len(usernames))

    # await asyncio.sleep(500)
    num += len(usernames)
    usernames = await create_username(prisma, usernames)
    

    # update to checked afterward
    await prisma.influencer.update(
        where={
            'handle':influencer
        },
        data={
            'checked': True 
        }
    )

    return num




async def main(cur_user:str):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    logger.info('Connected')
    prisma = Prisma()
    await prisma.connect()
    logger.info("Prisma connect")

    
    try:
        user = await prisma.user.find_unique(
            where={
                'id': cur_user 
            },
            include={
                'Scraper':True,
                'Script':True
            }
        )

    except Exception as e:
        return logger.info(f"User not found {e}...exiting")
        
    
    if user is None:
        logger.info("User not found")
        return

    user_dict = user.dict()
    user_dict.pop('hashedPassword', None)
    logger.info(f"Welcome {user_dict.get('name', 'User')}!\n\n")

    if user_dict.get('Scraper', None) is None or len(user_dict.get('Scraper', None)) == 0 :
        logger.info("You need to create a scraper first")
        return

            
    influencers = await get_influencers(prisma)

    if influencers is None:
        return logger.info("No influencers to process, please get more to begin... exiting")
    
    ##############

    async with webdriver.Chrome(options=options) as driver:

        logger.info('Starting Scrape')
        # BEGIN

        await driver.get("https://www.instagram.com", wait_load=True)
        await driver.sleep(3)

        user_scraper = user_dict.get('Scraper')[-1] #Use latest scraper, allow ability to select

        logger.info(f"Continuing with Scraper {user_scraper}")

        

        if user_scraper.get('cookie', None) is not None:
            logger.info("Loading Cookie from Scraper")
            # check expiration
            cookie_dict = json.loads(user_scraper.get('cookie'))
            await driver.add_cookie(cookie_dict.get('ds_user_id'))
            await driver.add_cookie(cookie_dict.get('sessionid'))
        else:
            logger.info("No cookie saved, manually logging in")
            username_input = await driver.find_element(By.NAME, 'username')
            password_input = await driver.find_element(By.NAME, 'password')
            login_button = await driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[3]/button')

            await username_input.send_keys(user_scraper.get('email'))
            await asyncio.sleep(2)
            await password_input.send_keys(user_scraper.get('password'))
            await asyncio.sleep(3)
            await login_button.click()
            logger.info('Logged in')
            await driver.sleep(3)

            ds_user_id = await driver.get_cookie('ds_user_id')
            sessionId = await driver.get_cookie('sessionid')

            logger.info(f"Cookies: 'ds': {ds_user_id} 'session':{sessionId} ")

            if ds_user_id and sessionId:
                logger.info("Saving cookies")
                try:
                    scraper = await prisma.scraper.update(
                    where={
                        'id':user_scraper.get('id')
                    }
                    ,
                    data={
                        'cookie':json.dumps({'ds_user_id': ds_user_id, 'sessionid':sessionId})
                    }
                    )
                except Exception as e:
                    logger.info(f"Error updating scraper {e}")

            
        await asyncio.sleep(3)


        loop = True
        usernamesAdded = 0
        iterations = 0
        now = datetime.datetime.now()
        
        while loop:
            if len(influencers) == 0:
                logger.info("Getting more usernames")
                influencers = await get_influencers(prisma) 
                if influencers is None: 
                    logger.info("No usernames to process, exiting")
                    loop = False
                    break 
                    
            time_elapsed = datetime.datetime.now() - now
            total_minutes = time_elapsed.total_seconds() / 60
            total_hours = total_minutes / 60

            days = time_elapsed.days
            hours = time_elapsed.seconds // 3600
            minutes = (time_elapsed.seconds % 3600) // 60

            rate_per_hour = usernamesAdded / total_hours if total_hours > 0 else 0

            logger.info('\n')
            logger.info(f"Running for: {days} days, {hours} hours, and {minutes} minutes")
            logger.info(f"Rate: {rate_per_hour:.2f} usernames added per hour\n")
            logger.info(f"Checked: {iterations} accounts")
            logger.info(f"Total: {int(usernamesAdded)} usernames added")
            logger.info('\n')
           
            
            influencere = influencers.pop(0)
            proc = await process_profile(driver, prisma, influencere.handle, user_dict)

            if proc > 0:
                usernamesAdded += proc

            await asyncio.sleep(2)
            iterations += 1
            
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