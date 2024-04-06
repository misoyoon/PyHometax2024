
# STMP 서버의 url과 port 번호
SMTP_SERVER = 'mail.w.the1kks.com'
SMTP_PORT = 587

EMAIL_ADDR = 'the1tax_1@the1kks.com'
EMAIL_PASSWORD = 'kksjns1203!'


import imghdr #이미지 첨부를 위한 라이브러리
import smtplib
from email.message import EmailMessage

# 1. SMTP 서버 연결
smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
smtp.ehlo()
smtp.starttls()
# 2. SMTP 서버에 로그인
smtp.login(EMAIL_ADDR, EMAIL_PASSWORD)

# 3. MIME 형태의 이메일 메세지 작성
message = EmailMessage()
message.set_content('이메일 본문')
message["Subject"] = "이메일 제목2"
message["From"] = EMAIL_ADDR  #보내는 사람의 이메일 계정
message["To"] = "imgoodfeel@naver.com"
message["Cc"] = EMAIL_ADDR

#3-1. 이메일에 사진 첨부하기
with open('D:\\Project\\py\\PyHometax2024\\sample\\testPDF.pdf', 'rb') as image:
    image_file = image.read() # 이미지 파일 읽어오기

#image_type = imghdr.what('e-mail', image_file)
message.add_attachment(image_file, maintype='application', subtype='pdf', filename='example.pdf')



# 4. 서버로 메일 보내기
smtp.send_message(message)

# 5. 메일을 보내면 서버와의 연결 끊기
smtp.quit()