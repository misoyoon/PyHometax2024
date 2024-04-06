from urllib.request import urlopen
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import urllib.request

# 참고자료 - [파이썬] BS4... find() , find_all()
# https://systemtrade.tistory.com/345

""" 
# 헤더 사용
header = {'User-Agent' : 'Mozilla/5.0'}
req = urllib.request.Request(url, headers=header)
html = rullib.request.urlopen(req).read()
 """

search_word = '사과'
base_url = 'https://desarraigado.tistory.com/14' # + quote_plus(search_word)
html = urlopen(base_url).read()
soup = BeautifulSoup(html, 'html.parser')

print(base_url)
print(soup.prettify())
img = soup.find_all('img')

if len(img) == 0:
        print('NOT FOUND')
        exit()



#print(img[0])

n=1
for i in img:
        imgUrl = i['src']
        with urlopen(imgUrl) as f:
                print(imgUrl)
                with open('./img/' + search_word + str(n) +'.jgp' , 'wb') as h:
                        image = f.read()
                        h.write(image)
        n += 1

print('다운로드 완료')