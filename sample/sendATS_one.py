# -*- coding: utf-8 -*-
# code for console Encoding difference. Dont' mind on it
import imp
import sys

imp.reload(sys)
try:
    sys.setdefaultencoding("UTF8")
except Exception as E:
    pass

import sample.sendATS_info_the1 as sendATS_info_the1
from popbill import KakaoService, PopbillException

kakaoService                 = KakaoService(sendATS_info_the1.LinkID, sendATS_info_the1.SecretKey)
kakaoService.IsTest          = sendATS_info_the1.IsTest
kakaoService.IPRestrictOnOff = sendATS_info_the1.IPRestrictOnOff
kakaoService.UseStaticIP     = sendATS_info_the1.UseStaticIP
kakaoService.UseLocalTimeYN  = sendATS_info_the1.UseLocalTimeYN

"""
승인된 템플릿의 내용을 작성하여 1건의 알림톡 전송을 팝빌에 접수합니다.
- 전송실패 시 사전에 지정한 변수 'altSendType' 값으로 대체문자를 전송할 수 있고 이 경우 문자(SMS/LMS) 요금이 과금됩니다.
- https://developers.popbill.com/reference/kakaotalk/python/api/send#SendATSOne
"""

try:
    print("=" * 15 + " 알림톡 단건 전송 " + "=" * 15)

    # 팝빌회원 사업자번호("-"제외 10자리)
    CorpNum = sendATS_info_the1.testCorpNum

    # 팝빌회원 아이디
    UserID = sendATS_info_the1.testUserID

    # 승인된 알림톡 템플릿코드
    # └ 알림톡 템플릿 관리 팝업 URL(GetATSTemplateMgtURL API) 함수, 알림톡 템플릿 목록 확인(ListATStemplate API) 함수를 호출하거나
    #   팝빌사이트에서 승인된 알림톡 템플릿 코드를  확인 가능.
    templateCode = "023050000043"

    # 팝빌에 사전 등록된 발신번호
    # ※ 대체문자를 전송하는 경우에만 필수 입력
    snd = "07047395596"

    # 알림톡 내용 (최대 1000자)
    # 사전에 승인된 템플릿의 내용과 알림톡 전송내용(content)이 다를 경우 전송실패 처리됩니다.
    content = "[해외주식 양도세 신고 완료]"
    content += "#이메일 발송 안내"

    content += "정율섭 고객님"
    
    content += "안녕하세요. 세무법인 더원입니다."
    content += "고객님의 해외주식 양도소득세 신고가 모두 완료되어 연락드립니다."

    content += "신고서 등 관련서류는 고객님께서 증권사에 신청하셨던 \"imgoodfeel@naver.com\" 메일로 보내드렸습니다."

    content += "고객님의 이번 해외주식 신고는 각종 공제 등으로 납부하실 세금이 없습니다."

    content += "보내드리는 신고서는 홈택스를 통해 이미 신고서를 접수하였으므로 별도로 신고하실 필요가 없으며, 신고내용을 확인하신 후 고객님께서 보관하시면 됩니다."

    content += "감사합니다."

    content += "※ 메일 스팸함 유의부탁드리며, 메일 수신 확인이 안되는 경우 연락주시면 재발송드리겠습니다."


    content += "ㆍ주소 : 서울특별시 강남구 "
    content += "             테헤란로86길 12"
    content += "             TKOK빌딩 7층"
    content += "ㆍ TEL : 02-1234-1234 "
    content += "ㆍ 담당자  : 강솔이"

    # 대체문자 제목
    # - 메시지 길이(90byte)에 따라 장문(LMS)인 경우에만 적용.
    altSubject = "대체문자 제목"

    # 대체문자 유형(altSendType)이 "A"일 경우, 대체문자로 전송할 내용 (최대 2000byte)
    # └ 팝빌이 메시지 길이에 따라 단문(90byte 이하) 또는 장문(90byte 초과)으로 전송처리
    altContent = "알림톡 대체 문자"

    # 대체문자 유형 (None , "C" , "A" 중 택 1)
    # None = 미전송, C = 알림톡과 동일 내용 전송 , A = 대체문자 내용(altContent)에 입력한 내용 전송
    altSendType = ""

    # 예약일시 (작성형식 : yyyyMMddHHmmss)
    sndDT = ""

    # 수신번호
    receiver = "01036565574"

    # 수신자 이름
    receiverName = "partner"

    # 전송요청번호
    # 파트너가 전송 건에 대해 관리번호를 구성하여 관리하는 경우 사용.
    # 1~36자리로 구성. 영문, 숫자, 하이픈(-), 언더바(_)를 조합하여 팝빌 회원별로 중복되지 않도록 할당.
    requestNum = "023050000043_01"

    # 알림톡 버튼정보를 템플릿 신청시 기재한 버튼정보와 동일하게 전송하는 경우 btns를 빈 배열로 처리.
    btns = []

    # 알림톡 버튼 URL에 #{템플릿변수}를 기재한경우 템플릿변수 값을 변경하여 버튼정보 구성
    # btns.append(
    #     KakaoButton(
    #         n="템플릿 안내",  # 버튼명
    #         t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
    #         u1="https://www.popbill.com",  # [앱링크-iOS, 웹링크-Mobile]
    #         u2="http://www.popbill.com"  # [앱링크-Android, 웹링크-PC URL]
    #     )
    # )

    receiptNum = kakaoService.sendATS(
        CorpNum,
        templateCode,
        snd,
        content,
        altContent,
        altSendType,
        sndDT,
        receiver,
        receiverName,
        UserID,
        requestNum,
        btns,
        altSubject,
    )
    print("접수번호 (receiptNum) : %s" % receiptNum)

except PopbillException as PE:
    print("Exception Occur : [%d] %s" % (PE.code, PE.message))
