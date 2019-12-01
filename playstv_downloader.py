# PlaysTV Auto Downloader by maxtheaxe
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs
import sys
import re
import urllib.request as urlr
import time
from tqdm import tqdm
import os

# login() - logs into PlaysTV
# reference: https://crossbrowsertesting.com/blog/test-automation/automate-login-with-selenium/
def login(driver, username, password):
	driver.get('https://plays.tv/login') # open playstv login page
	driver.find_element_by_id('login_urlname').send_keys(username) # enter username
	driver.find_element_by_id('login_pwd').send_keys(password) # enter password
	driver.find_element_by_id('login_pwd').send_keys(u'\ue007') # press enter key
	# wait and make sure we're logged in, everything's loaded
	try:
		WebDriverWait(driver, 10).until(EC.title_contains("Home")) # checks if page is Home
		if EC.title_contains("Home"):
			print("\tSuccessfully logged in.\n")
	except:
		print("\tError: Login Failed.\n")
		sys.exit()

# navigate() - navigate to uploads page, load all videos
# reference: https://stackoverflow.com/questions/41744368/scrolling-to-element-using-webdriver
# reference 2: https://selenium-python.readthedocs.io/locating-elements.html
def navigate(driver):
	driver.get('https://plays.tv/i/uploaded') # open the page
	try:
		WebDriverWait(driver, 10).until(EC.invisibility_of_element_located( (By.CLASS_NAME,
			'error-cta') )) # waits for login recognition
	except:
		print("\tError: Login Failed.\n")
		sys.exit()
	print("\tSuccessfully navigated to uploads page.\n")
	# scroll until all videos are loaded
	# (idk wtf they did but scrollTo and pagedown/end keys don't work before tabbing)
	# thanks to this guy https://stackoverflow.com/a/25365448
	actions = ActionChains(driver)
	for i in range(4): # press tab 4 times to get keys to work
		actions.send_keys(Keys.TAB).perform()
	while not end_checker(driver): # while end of page hasn't appeared, keep scrolling
		actions.send_keys(Keys.END).perform()
	print("\tSuccessfully loaded all uploads.\n")

# ender() - checks if all videos are loaded
def end_checker(driver):
	try: # see if end of page has appeared
		driver.find_element_by_xpath('//div[@class="empty"]//h1[@class="dim"]')
	except:
		return False # report it hasn't
	return True # report it has

# collector() - collect all download links and video names
# reference: https://towardsdatascience.com/web-scraping-using-selenium-and-beautifulsoup-99195cd70a58
def collector(driver, errors = True):
	source = bs(driver.page_source, 'html.parser') # make uploads page into bs obj
	# collect uploads
	upload_cards = source.find_all("li", class_="media-card")
	num_uploads = len(upload_cards)
	print("\tNumber of Uploads:", (num_uploads - 1),
	"\n") # counts an extra for some reason
	# build list of videos (will add screenshots later)
	videos = []
	for i in range(num_uploads):
		# print(str(upload_cards[i].contents))
		# get video link
		current_video = ["Something broke here.", "Something broke here."]
		thumbnail_div = upload_cards[i].find("section", class_="thumbnail")
		str_thumbnail_div = str(thumbnail_div.contents) # make bs into string for regex
		# print(str_thumbnail_div)
		try: # finding video id and quality from thumbnail url
			video_id = re.search('kamaihd\\.net\\/video\\/(.+?)\\/processed',
				str_thumbnail_div).group(1) # video id
			video_quality = re.search('\\/processed\\/(.+?)\\.jpg',
				str_thumbnail_div).group(1) # video quality
		except AttributeError: # thumbnail url not found in the original string
			if errors == True:
				print("\tError: No video id found (Probably a screenshot). Skipping.\n")
			continue # skip this one, move on to next loop
		video_link = 'https://vdl.plays.tv/video/' + video_id + '/processed/'
		video_link += video_quality + '.mp4' # was too long for 1 line, I'm lazy
		current_video[0] = video_link # add video link to sublist
		# get video name
		meta_section = upload_cards[i].find("section", class_="meta")
		meta_sub = meta_section.find("main")
		str_meta = str(meta_sub.contents) # make bs into string for regex
		try: # finding title from meta sub sub section
			video_title = re.search('\\<\\/i\\>(.+?)\\<\\/h3\\>',
				str_meta).group(1)
			video_title = re.sub('[^A-Za-z0-9\\s]+', '', video_title)
		except AttributeError: # title not found in the original string
			print("\t\tError: No title found for video id " + video_id + ". Skipping.")
			continue # skip this one, move on to next loop
		# look for videos with duplicate names
		for i in range (0, len(videos)): # in video list so far
			if (video_title == videos[i][1]): # if vid with same name already exists
				video_title = video_title + " id-" + video_id # add video id to name
		current_video[1] = video_title # add video title to sublist
		videos.append(current_video)
	print("\tSuccessfully collected all video information.\n")
	return videos

# downloader() - downloads and names all the uploaded videos
# reference: https://stackoverflow.com/a/20338590/4513452
def downloader(videos):
	print("\tDownloading...\n")
	for i in tqdm(range(len(videos))):
		fullfilename = videos[i][1] + ".mp4"
		if not os.path.exists(fullfilename): # if file doesn't already exist, download it
			urlr.urlretrieve(videos[i][0], fullfilename)

def main(argv):
	print("\n\t---PlaysTV Downloader by Max---")
	print("\n\tIf for whatever reason it stops in the middle, just close and restart it,"
		+ "\n\tit will not redownload previously downloaded files.\n")
	if (len(argv) != 3):
		print("\tIncorrect syntax. Use: python playstv_downloader <username> <password>")
		return
	# Start webdriver
	options = webdriver.ChromeOptions() # hiding startup info that pollutes terminal
	options.headless = True
	options.add_experimental_option('excludeSwitches', ['enable-logging'])
	driver = webdriver.Chrome(options=options)
	# run program
	login(driver, argv[1], argv[2])
	navigate(driver)
	videos = collector(driver)
	downloader(videos)
	print("\n\tFinished.")

if __name__ == '__main__':
	main(sys.argv)
