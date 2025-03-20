import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

class PokiScraper:
    def __init__(self):
        self.base_url = 'https://poki.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.games_data = []
        self.setup_driver()

    def setup_driver(self):
        """设置Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')
            chrome_options.add_argument('--lang=en-US')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option('prefs', {
                'intl.accept_languages': 'en-US,en',
            })
            
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': '''
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        })
                    '''
                })
            except Exception as e:
                print(f"Failed to use webdriver_manager: {e}")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            print("WebDriver setup successful")
        except Exception as e:
            print(f"Error setting up WebDriver: {str(e)}")
            raise

    def wait_for_element(self, selector, timeout=20):
        """等待元素出现"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return True
        except Exception as e:
            print(f"Timeout waiting for element {selector}: {e}")
            return False

    def get_game_details(self, game_url):
        """获取游戏详情页面的描述和分类信息"""
        try:
            print(f"Loading game details: {game_url}")
            self.driver.get(game_url)
            time.sleep(3)  # 等待页面加载
            
            # 获取游戏描述
            description = self.driver.execute_script("""
                const article = document.querySelector('article');
                return article ? article.textContent.trim() : '';
            """)
            
            # 获取游戏分类
            categories = self.driver.execute_script("""
                const ul = document.querySelector('article + ul');
                if (!ul) return [];
                return Array.from(ul.querySelectorAll('li')).map(li => li.textContent.trim());
            """)
            
            return description, categories
        except Exception as e:
            print(f"Error getting game details: {str(e)}")
            return '', []

    def get_page_content(self, url):
        """使用Selenium获取页面内容"""
        try:
            print(f"Loading URL: {url}")
            self.driver.get(url)
            time.sleep(5)
            
            current_url = self.driver.current_url
            print(f"Current URL: {current_url}")
            
            selectors = [
                'a[href*="/g/"]',
                '.game-list-item',
                '.game-wrapper',
                '.game-tile',
                '.grid-item'
            ]
            
            for selector in selectors:
                if self.wait_for_element(selector):
                    print(f"Found elements with selector: {selector}")
                    break
            
            # 获取所有游戏链接
            games = self.driver.execute_script("""
                return Array.from(document.querySelectorAll('a[href*="/g/"]')).map(a => {
                    const img = a.querySelector('img');
                    return {
                        title: img ? img.alt : a.textContent.trim(),
                        href: a.href,
                        image: img ? img.src : ''
                    };
                });
            """)
            
            if games:
                print(f"Found {len(games)} games using JavaScript")
                for game in games:
                    if game['title'] and game['href']:
                        # 获取游戏详情
                        description, categories = self.get_game_details(game['href'])
                        
                        self.games_data.append({
                            'title': game['title'],
                            'game_url': game['href'],
                            'image_url': game['image'],
                            'description': description,
                            'category': categories
                        })
                        print(f"Added game: {game['title']}")
                        print(f"Description: {description[:100]}...")  # 打印描述的前100个字符
                        print(f"Categories: {categories}")
                        
                        # 添加短暂延迟，避免请求过快
                        time.sleep(1)
            
            return self.driver.page_source
            
        except Exception as e:
            print(f"Error loading {url}: {str(e)}")
            return None

    def scrape_games(self):
        """爬取游戏信息"""
        print("Starting to scrape games...")
        self.get_page_content(self.base_url)
        print(f"\nTotal games found: {len(self.games_data)}")

    def save_to_json(self, filename='games_data.json'):
        """保存爬取的数据到JSON文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.games_data, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(self.games_data)} games to {filename}")

    def close(self):
        """关闭浏览器"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("WebDriver closed successfully")

def main():
    scraper = PokiScraper()
    try:
        scraper.scrape_games()
        scraper.save_to_json()
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    finally:
        scraper.close()

if __name__ == '__main__':
    main() 