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
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  # Save logs to a file
        logging.StreamHandler(sys.stdout)  # Output logs to stdout
    ]
)

logger = logging.getLogger(__name__)

XPATHS = {
    'SCRAPE_DETECT': '/html/body/div[2]/div/div/div[2]/div/div/div[1]/section/main/div[2]/div/div/div/div/div[1]/div/div/div[2]/div[2]/div',
    'FOLLOWERS_COUNT': '/html/body/div[2]/div/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[3]/ul/li[2]/div/a/span/span',
    'MORE_BUTTON': '/html/body/div[2]/div/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[4]/div/span/span/div',
    'BIO': '/html/body/div[2]/div/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[4]/div/span/div/span',
    'NAME': '/html/body/div[2]/div/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[4]/div/div[1]/span'
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
        

def parse_followers_count(followers_str):
    followers_str = followers_str.replace(',', '')
    if followers_str.endswith('K'):
        return float(followers_str[:-1]) * 1000
    elif followers_str.endswith('M'):
        return float(followers_str[:-1]) * 1000000
    else:
        return float(followers_str)
    
async def extract_bio(driver):
    try:
        more = await driver.find_element(By.XPATH, XPATHS['MORE_BUTTON'], timeout=3)
        await more.click()
    except:
        logger.info('No "More" button found')
    
    return await get_element_text(driver, XPATHS['BIO'], timeout=2)
    
def normalize_stylized_text(text):
    char_map = {
        'ᴀ': 'a', 'ʙ': 'b', 'ᴄ': 'c', 'ᴅ': 'd', 'ᴇ': 'e', 'ꜰ': 'f', 'ɢ': 'g', 'ʜ': 'h', 'ɪ': 'i', 'ᴊ': 'j',
        'ᴋ': 'k', 'ʟ': 'l', 'ᴍ': 'm', 'ɴ': 'n', 'ᴏ': 'o', 'ᴘ': 'p', 'ǫ': 'q', 'ʀ': 'r', 'ꜱ': 's', 'ᴛ': 't',
        'ᴜ': 'u', 'ᴠ': 'v', 'ᴡ': 'w', 'x': 'x', 'ʏ': 'y', 'ᴢ': 'z',
        'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E', 'Ｆ': 'F', 'Ｇ': 'G', 'Ｈ': 'H', 'Ｉ': 'I', 'Ｊ': 'J',
        'Ｋ': 'K', 'Ｌ': 'L', 'Ｍ': 'M', 'Ｎ': 'N', 'Ｏ': 'O', 'Ｐ': 'P', 'Ｑ': 'Q', 'Ｒ': 'R', 'Ｓ': 'S', 'Ｔ': 'T',
        'Ｕ': 'U', 'Ｖ': 'V', 'Ｗ': 'W', 'Ｘ': 'X', 'Ｙ': 'Y', 'Ｚ': 'Z',
        'Ⓐ': 'A', 'Ⓑ': 'B', 'Ⓒ': 'C', 'Ⓓ': 'D', 'Ⓔ': 'E', 'Ⓕ': 'F', 'Ⓖ': 'G', 'Ⓗ': 'H', 'Ⓘ': 'I', 'Ⓙ': 'J',
        'Ⓚ': 'K', 'Ⓛ': 'L', 'Ⓜ': 'M', 'Ⓝ': 'N', 'Ⓞ': 'O', 'Ⓟ': 'P', 'Ⓠ': 'Q', 'Ⓡ': 'R', 'Ⓢ': 'S', 'Ⓣ': 'T',
        'Ⓤ': 'U', 'Ⓥ': 'V', 'Ⓦ': 'W', 'Ⓧ': 'X', 'Ⓨ': 'Y', 'Ⓩ': 'Z',
    }
    return ''.join(char_map.get(c, c) for c in text)

def extract_first_name(full_name):
    if not full_name or not isinstance(full_name, str):
        return "love"

    full_name = full_name.strip()

    full_name = re.sub(r'[^\w\s\-|]', '', full_name)

    parts = re.split(r'[\s|]', full_name)

    parts = [part for part in parts if part and len(part) > 1 and not part.isnumeric()]

    if not parts:
        return "love"

    first_name = parts[0]

    first_name = first_name.replace('_', ' ').strip()

    if first_name.isupper():
        first_name = first_name.title()

    first_name = ''.join(c for c in unicodedata.normalize('NFD', first_name)
                         if unicodedata.category(c) != 'Mn')
    
    first_name = normalize_stylized_text(first_name)

    if len(first_name) <= 1 and len(parts) > 1:
        first_name = parts[1]

    titles = ['dr', 'mr', 'mrs', 'ms', 'miss', 'prof', 'the', 'its']
    if first_name.lower() in titles and len(parts) > 1:
        first_name = parts[1]

    return first_name.title()

def extract_email(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return emails[0] if emails else None
    

async def scrape_detect(driver):
    try:
        scrape = await driver.find_element(By.XPATH, XPATHS['SCRAPE_DETECT'])
        logger.info('Scrape detected, clicking...')
        await scrape.click()
        await asyncio.sleep(1)
    except:
        # logger.info('No scrape detection')
        pass

async def get_usernames(prisma):

    total_unchecked = await prisma.username.count(
        where={
            'checked': False,
        }
    )

    if total_unchecked == 0:
        return None
    
    random_offset = random.randint(0, max(0, total_unchecked - 100))
    
    usernames = await prisma.username.find_many(
        take=100,
        skip=random_offset,
        where={
            'checked': False,
        },
        order={
            'created': 'asc'  
        }
    )

    if len(usernames) < 100:
        additional_usernames = await prisma.username.find_many(
            take=100 - len(usernames),
            where={
                'checked': False,
            },
            order={
                'created': 'desc'
            }
        )
        usernames.extend(additional_usernames)

    random.shuffle(usernames)

    username_ids = [u.id for u in usernames]
    # await prisma.username.update_many(
    #     where={
    #         'id': {
    #             'in': username_ids
    #         }
    #     },
    #     data={
    #         'checked': True
    #     }
    # )
    
    
    return usernames if len(usernames) > 0 else None

# async def set_checked(prisma, username):
#     try:
#         await prisma.username.update(
#         where={
#             'handle': username
#         },
#         data={
#             'checked': True
#         }
#         )
#     except:
#         logger.info("Failed to set checked")

async def create_influencer(prisma, username, email, first_name):
    try:
        influencer = await prisma.influencer.create(
            data={
                'handle': username,
                'email': email,
                'name': first_name
            }
        )
        logger.info("Influencer DB created")
        return influencer
    except Exception as e:
        logger.info(f"Couldn't create influencer: {e}")
        return None
   

async def process_profile(driver, prisma, username, user_dict):
    if not await navigate(driver, username):
        return
    
    await asyncio.sleep(1)
    await scrape_detect(driver)

    followers = await get_element_text(driver, XPATHS['FOLLOWERS_COUNT'], timeout=2)
    if followers is None:
        # await set_checked(prisma, username)
        # iterate xpath fail counter
        await asyncio.sleep(2)
        return
    
    if parse_followers_count(followers) <= 1500:
        logger.info(f"{username}: Less than 1500 followers")
        # await set_checked(prisma, username)
        # iterate xpath fail counter
        await asyncio.sleep(2)
        return

    biography = await extract_bio(driver)
    if biography is None:
        # await set_checked(prisma, username)
        # iterate xpath fail counter
        await asyncio.sleep(2)
        return
    
    logger.info(f"Username: {username}\nFollower count: {followers}\n")

    email = extract_email(biography)
    if email:
        logger.info(f"Email found in bio: {email}")
        username_text = await get_element_text(driver, XPATHS['NAME'], timeout=3)
        first_name = extract_first_name(username_text).split(" ")[0]
        logger.info(f"First name: {first_name}")
        influencer = await create_influencer(prisma, username, email, first_name)
        await asyncio.sleep(2)
        # await set_checked(prisma, username)
        if influencer is not None:
            # send email, make this a transaction

            #Allow to select which script to use
            logger.info(f"Sending Email to: {username}")
            params: resend.Emails.SendParams = {
                "from": f"{user_dict.get('name')} <{user_dict.get('email')}>",
                "to": f"{email.strip()}",
                "subject": user_dict.get('Script')[-1].get('title'),
                "html": f"{'<br><br>'.join(user_dict.get('Script')[-1].get('body').replace('{}', first_name).replace('Mohammad', 'Moh').split('\n\n'))}",
            }


            
            try:
                email = resend.Emails.send(params)
            except Exception as e:
                logger.info(f"Failed to send: {e}")
                return False
                
            await asyncio.sleep(2)
            return True

        
            
    else:
        logger.info("No email found in bio")
        # await set_checked(prisma, username)
        return
        # iterate xpath fail counter

def save_session(user_id):
    with open('session.json', 'w') as f:
        json.dump({'user_id': user_id, "scraper_info":False}, f)

def save_status(user_id):
    with open('session.json', 'w') as f:
        json.dump({'user_id': user_id, "scraper_info":True}, f)

def load_session():
    if os.path.exists('session.json'):
        with open('session.json', 'r') as f:
            return json.load(f).get('user_id')
    return None

def load_status():
    if os.path.exists('session.json'):
        with open('session.json', 'r') as f:
            return json.load(f).get('scraper_info')
    return None

async def main(cur_user:str):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    logger.info('Connected')
    prisma = Prisma()
    await prisma.connect()
    logger.info("Prisma connect")
    # # options.add_argument('--headless')

    # kp = "c58cd9c3-76da-4790-92f8-54e27d432cc2"
    # moh = "b72731c5-6f3c-4414-b293-bf28d6611dda"
    # garv = '9c86640e-af9a-432b-a198-7b794f6456e9'

    # loading_user = load_session()

    # if not loading_user:

    #     cur_user = input("Enter who you are: 'moh' or 'kp': ")
        
    #     if cur_user == "kp":
    #         cur_user = kp
    #     elif cur_user == "moh":
    #         cur_user = moh
    #     else:
    #         return logger.info("Incorrect input")
        
    #     user_password = input("Enter password: ")
    # else:
    #     cur_user = loading_user

    
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

    # if not loading_user:
    #     if not bcrypt.checkpw(user_password.encode(), user_dict.get('hashedPassword', "").encode()):
    #         return logger.info("Incorrect Password")    
    #     save_session(user_dict.get('id', None))

    user_dict.pop('hashedPassword', None)
    
    # if user_dict.get('name') == "Mohammad":
    #     user_dict['name'] = "Moh"
    logger.info(f"Welcome {user_dict.get('name', 'User')}!\n\n")

    # if not load_status():
    #     logger.info("Instagram account info for scraper:")
    #     logger.info("You need to create a scraper first")
        # EMAIL = input("Enter instagram email: ")
        # PASSWORD = input("Enter instagram password: ")


    if user_dict.get('Scraper', None) is None or len(user_dict.get('Scraper', None)) == 0 :
        # logger.info("Creating a new scraper")
        logger.info("You need to create a scraper first")
        return
        # if EMAIL and PASSWORD: 
        #     try:
        #         # Allow to change selected scraper
        #         scraper = await prisma.scraper.create(
        #         data={
        #             'email':EMAIL,
        #             'password':PASSWORD, 
        #             'User': {
        #                 'connect': {
        #                     'id': user_dict.get('id')
        #                 }
        #         }})
        #         user_dict['Scraper'].append(scraper.dict())
        #     except Exception as e:
        #         return logger.info(f"Error creating scraper: {e}")
        # else:
            # return logger.info("Please enter EMAIL and PASSWORD of instagram account...exiting")
        
   
            
    usernames = await get_usernames(prisma)

    if usernames is None:
        return logger.info("No usernames to process, please get more to begin... exiting")
    
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
        emailsSent = 0
        iterations = 0
        now = datetime.datetime.now()
        
        while loop:
            if len(usernames) == 0:
                logger.info("Getting more usernames")
                usernames = await get_usernames(prisma) 
                if usernames is None: 
                    logger.info("No usernames to process, exiting")
                    loop = False
                    break 
                    
            time_elapsed = datetime.datetime.now() - now
            total_minutes = time_elapsed.total_seconds() / 60
            total_hours = total_minutes / 60

            days = time_elapsed.days
            hours = time_elapsed.seconds // 3600
            minutes = (time_elapsed.seconds % 3600) // 60

            rate_per_hour = emailsSent / total_hours if total_hours > 0 else 0

            logger.info('\n')
            logger.info(f"Running for: {days} days, {hours} hours, and {minutes} minutes")
            logger.info(f"Rate: {rate_per_hour:.2f} emails per hour\n")
            logger.info(f"Checked: {iterations} accounts")
            logger.info(f"Total: {int(emailsSent)} emails sent")
            logger.info('\n')
           
            
            username = usernames.pop(0)
            proc = await process_profile(driver, prisma, username.handle, user_dict)

            if proc:
                emailsSent += 1

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