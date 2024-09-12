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
    'NAME': '/html/body/div[2]/div/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[4]/div/div[1]/span',
    'PRIVATE': '/html/body/div[2]/div/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/div[1]/div/div[1]/div[2]/div/div/span'
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
        return "Love"

    full_name = full_name.strip()

    full_name = re.sub(r'[^\w\s\-|]', '', full_name)

    parts = re.split(r'[\s|]', full_name)

    parts = [part for part in parts if part and len(part) > 1 and not part.isnumeric()]

    if not parts:
        return "Love"

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

    logger.info(f'Total unchecked Usernames: {total_unchecked}')

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
    
    
    return usernames if len(usernames) > 0 else None

async def set_checked(prisma, username):
    try:
        await prisma.username.update(
        where={
            'handle': username
        },
        data={
            'checked': True
        }
        )
    except:
        logger.info("Failed to set checked")

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

    # private = await get_element_text(driver, XPATHS['PRIVATE'], timeout=)

    followers = await get_element_text(driver, XPATHS['FOLLOWERS_COUNT'], timeout=2)
    if followers is None:
    
        # iterate xpath fail counter
        await asyncio.sleep(2)
        return
    
    if parse_followers_count(followers) <= 1500:
        logger.info(f"{username}: Less than 1500 followers")

        # iterate xpath fail counter
        await asyncio.sleep(2)
        return

    biography = await extract_bio(driver)
    if biography is None:
   
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
                logger.info(f"Email sent for {user_dict.get('name')}")
            except Exception as e:
                logger.info(f"Failed to send: {e}")
                return False
                
            await asyncio.sleep(2)
            return True

        
            
    else:
        logger.info("No email found in bio")
    
        return
        # iterate xpath fail counter


async def get_user(id:str, prisma:Prisma):
    try:
        user = await prisma.user.find_unique(
            where={
                'id': id 
            },
            include={
                'Scraper':True,
                'Script':True
            }
        )
        return user.model_dump(exclude={"hashedPassword"})
    except Exception as e:
        return logger.info(f"User not found {e}")



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
    
    
   

async def process_usernames(driver, prisma, influencer) -> int:
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
        logger.info('Start reading post')
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

        logger.info('Finished reading post')
        


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


async def gather_usernames(driver, prisma:Prisma):
    usernamesAdded = 0
    iterations = 0
    now = datetime.datetime.now()
    
    while iterations < 5:
        if len(influencers) == 0:
            logger.info("Getting more usernames")
            influencers = await get_influencers(prisma) 
            if influencers is None: 
                logger.info("No influencers to process, exiting")
                iterations = 999
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
        proc = await process_usernames(driver, prisma, influencere.handle)

        if proc > 0:
            usernamesAdded += proc

        await asyncio.sleep(2)
        iterations += 1


async def main(cur_user:str):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    logger.info('Connected')
    prisma = Prisma()
    await prisma.connect()

    kp = await get_user("c58cd9c3-76da-4790-92f8-54e27d432cc2", prisma)
    moh =  await get_user("b72731c5-6f3c-4414-b293-bf28d6611dda", prisma)
    garv =  await get_user('9c86640e-af9a-432b-a198-7b794f6456e9', prisma)

    
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
        
    user = user.model_dump(exclude={'hashedPassword'})
    
    if user is None:
        logger.info("User not found")
        return

    logger.info(f"Welcome {user.get('name', 'User')}!\n\n")

    if user.get('Scraper', None) is None or len(user.get('Scraper', None)) == 0 :
        logger.info("You need to create a scraper first")
        return
        
            
    usernames = await get_usernames(prisma)

    if usernames is None:
        return logger.info("No usernames to process, please get more to begin... exiting")
    
    ##############

    async with webdriver.Chrome(options=options) as driver:

        logger.info('Starting Scrape')
        # BEGIN

        await driver.get("https://www.instagram.com", wait_load=True)
        await driver.sleep(3)

        user_scraper = user.get('Scraper')[-1] #Use latest scraper, allow ability to select

        logger.info(f"Continuing with latest Scraper")
        

        if user_scraper.get('cookie', None) is not None:
            logger.info("Loading Cookie from Scraper")
            # TODO check expiration
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
                    logger.info("No usernames to process, gathering")
                    await gather_usernames(driver, prisma)
                    continue 
                    
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
            # logger.info(f"Usernames left: {usernames}")
            logger.info(f"Total: {int(emailsSent)} emails sent")
            logger.info('\n')
            
            username = usernames.pop(0)
            
            
            proc = await process_profile(driver, prisma, username.handle, kp if emailsSent % 2 == 0 else moh)
            logger.info("Set Checked")
            await set_checked(prisma, username.handle)

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