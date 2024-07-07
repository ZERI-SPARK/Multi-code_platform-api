import json
import re

import grequests
import requests
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from util import get_safe_nested_key

class UsernameError(Exception):
    pass

class PlatformError(Exception):
    pass

class BrokenChangesError(Exception):
    pass

class UserData:
    def __init__(self, username=None):
        self.__username = username

    def update_username(self, username):
        self.__username = username

    def __codeforces(self):
        urls = {
            "user_info": {"url": f'https://codeforces.com/api/user.info?handles={self.__username}'},
            "user_contests": {"url": f'https://codeforces.com/contests/with/{self.__username}'}
        }

        reqs = [grequests.get(item["url"]) for item in urls.values() if item.get("url")]
        responses = grequests.map(reqs)

        details_api = {}
        contests = []
        for page in responses:
            if page.status_code != 200:
                raise UsernameError('User not Found')
            if page.request.url == urls["user_info"]["url"]:
                details_api = page.json()
            elif page.request.url == urls["user_contests"]["url"]:
                soup = BeautifulSoup(page.text, 'html.parser')
                table = soup.find('table', attrs={'class': 'user-contests-table'})
                table_body = table.find('tbody')
                rows = table_body.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    cols = [ele.text.strip() for ele in cols]
                    contests.append({
                        "Contest": cols[1],
                        "Rank": cols[3],
                        "Solved": cols[4],
                        "Rating Change": cols[5],
                        "New Rating": cols[6]
                    })

        if details_api.get('status') != 'OK':
            raise UsernameError('User not Found')

        details_api = details_api['result'][0]

        try:
            rating = details_api['rating']
            max_rating = details_api['maxRating']
            rank = details_api['rank']
            max_rank = details_api['maxRank']
        except KeyError:
            rating = 'Unrated'
            max_rating = 'Unrated'
            rank = 'Unrated'
            max_rank = 'Unrated'

        return {
            'status': 'Success',
            'username': self.__username,
            'platform': 'Codeforces',
            'rating': rating,
            'max rating': max_rating,
            'rank': rank,
            'max rank': max_rank,
            'contests': contests
        }
    

    # def __interviewbit(self):
    #     url = 'https://www.interviewbit.com/profile/{}'.format(self.__username)
    #     page = requests.get(url)
    #     if page.status_code != 200:
    #         raise UsernameError('User not Found')

    #     soup = BeautifulSoup(page.text, 'html.parser')
    #     details_main = soup.find('div', class_='user-stats')
    #     details_container = details_main.findChildren('div', recursive=False)

    #     return {
    #         'status': 'Success',
    #         'username': self.__username,
    #         'platform': 'Interviewbit',
    #         'rank': int(details_container[0].find('div', class_='txt').text),
    #         'score': int(details_container[1].find('div', class_='txt').text),
    #         'streak': details_container[2].find('div', class_='txt').text
    #     }
    

    def __spoj(self):
        url = 'https://www.spoj.com/users/{}/'.format(self.__username)
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        details_container = soup.find_all('p')

        points = details_container[2].text.split()[3][1:]
        rank = details_container[2].text.split()[2][1:]
        join_date = details_container[1].text.split()[1] + ' ' + details_container[1].text.split()[2]
        institute = ' '.join(details_container[3].text.split()[1:])

        try:
            points = float(points)
        except ValueError:
            raise UsernameError('User not Found')

        def get_solved_problems():
            table = soup.find('table', class_='table table-condensed')
            rows = table.findChildren('td')
            solved_problems = [row.a.text for row in rows if row.a.text]
            return solved_problems

        def get_todo():
            try:
                table = soup.find_all('table', class_='table')[1]
            except IndexError:
                return None
            rows = table.findChildren('td')
            todo_problems = [row.a.text for row in rows if row.a.text]
            return todo_problems

        return {
            'status': 'Success',
            'username': self.__username,
            'platform': 'SPOJ',
            'points': float(points),
            'rank': int(rank),
            'solved': get_solved_problems(),
            'todo': get_todo(),
            'join data': join_date,
            'institute': institute
        }



    def __atcoder(self):
        url = "https://atcoder.jp/users/{}".format(self.__username)
        page = requests.get(url)
        if page.status_code != 200:
            raise UsernameError("User not Found")

        soup = BeautifulSoup(page.text, "html.parser")
        tables = soup.find_all("table", class_="dl-table")
        if len(tables) < 2:
            return {
                "status": "Success",
                "username": self.__username,
                "platform": "Atcoder",
                "rating": "NA",
                "highest": "NA",
                "rank": "NA",
                "level": "NA",
            }

        rows = tables[1].find_all("td")
        try:
            rank = int(rows[0].text[:-2])
            current_rating = int(rows[1].text)
            spans = rows[2].find_all("span")
            highest_rating = int(spans[0].text)
            level = spans[2].text
        except Exception as e:
            raise BrokenChangesError(e)

        return {
            "status": "Success",
            "username": self.__username,
            "platform": "Atcoder",
            "rating": current_rating,
            "highest": highest_rating,
            "rank": rank,
            "level": level,
        }

    def get_details(self, platform):
        if platform == 'codeforces': #done
            return self.__codeforces()
        if platform == 'spoj': # done
            try:
                return self.__spoj()
            except AttributeError:
                raise UsernameError('User not Found')
            
        if platform == 'interviewbit':
            return self.__interviewbit()
        if platform == 'atcoder': # done
            return self.__atcoder()

        raise PlatformError('Platform not Found')

if __name__ == '__main__':
    ud = UserData('uwi')
    ans = ud.get_details('codeforces')
    print(ans)
