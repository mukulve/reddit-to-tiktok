import asyncio
import logging
from gtts import gTTS
from playwright.async_api import async_playwright
from moviepy.editor import VideoFileClip, AudioFileClip
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_video(video, audio, title):
    try:
        video_clip = VideoFileClip(video)
        audio_clip = AudioFileClip(audio)
        length_of_audio = audio_clip.duration
        video_clip = video_clip.subclip(0, length_of_audio)
        final_clip = video_clip.set_audio(audio_clip)
        final_clip.write_videofile(f"{title}.mp4")
        logger.info(f"Video created: {title}.mp4")
    except Exception as e:
        logger.error(f"Error in create_video: {str(e)}")

def create_audio_file(text, title):
    try:
        audioObj = gTTS(text=text, lang='en', slow=False)
        audio_path = f"{title}.mp3"
        audioObj.save(audio_path)
        logger.info(f"Audio created: {audio_path}")
        return audio_path
    except Exception as e:
        logger.error(f"Error in create_audio_file: {str(e)}")
        return None

async def scrape_reddit_post(url):
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_load_state("networkidle")

            title = await page.query_selector("a.title")
            title_text = await title.inner_text()
            comment_section = await page.query_selector(".sitetable.nestedlisting")
            comment = await comment_section.query_selector(".comment")
            comment_text = await comment.query_selector(".usertext-body")
            comment_text = await comment_text.inner_text()
            
            logger.info(f"Title: {title_text}")
            logger.info(f"Comment: {comment_text}")
            
            videoText = f"{title_text}\n{comment_text}."
            videoTitle = str(uuid.uuid4())
            audioPath = create_audio_file(videoText, videoTitle)
            if audioPath:
                create_video("subway.mp4", audioPath, videoTitle)
            
            await browser.close()
        except Exception as e:
            logger.error(f"Error in scrape_reddit_post: {str(e)}")

async def scrape_reddit_posts():
    async with async_playwright() as p:
        try:
            subreddit = "https://old.reddit.com/r/AskReddit/top/"
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.goto(subreddit)
            await page.wait_for_load_state("networkidle")
            posts = await page.query_selector_all(".thing")
            
            if not posts:
                logger.error("Cannot find posts")
                await browser.close()
                return
            
            for count, post in enumerate(posts):
                if count >= 3:
                    break
                link = await post.query_selector("a")            
                if link:
                    link_href = await link.get_attribute("href")
                    post_link = "https://old.reddit.com" + link_href
                    await scrape_reddit_post(post_link)
            await browser.close()
        except Exception as e:
            logger.error(f"Error in scrape_reddit_posts: {str(e)}")

asyncio.run(scrape_reddit_posts())