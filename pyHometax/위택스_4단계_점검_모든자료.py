
'''

function call_wetax_list(param) {
	$.ajax({
		type : "POST",
		url  : "https://www.wetax.go.kr/etr/api/titxaDclr/getListTitxaDclr",
		data : JSON.stringify(param),
		success: function(res) {
			console.log(res)
		},
		error : function(XMLHttpRequest, textStatus, errorThrown) {
			console.log("통신 실패");
		}
	});
}

var params = {	
    "titxaDclrDVO": {
        "dclrYmdBgng": "20240501",
        "dclrYmdEnd": "20240502",
        "dclrCmnRcptClCd": "",
        "inqCtpvCd": "",
        "inqSggCd": "",
        "payYn": ""
    },
    "pagerVO" : {
        "pageNo" : 1,
        "rowCount" : 2000,
        "totalCount" : 2000
    },
    "titxaDclrParamDVO": {
        "nowDclrScrnNo": "01",
        "objCd": "T",
        "txiCd": "140002"
    },
    "common": {
        "uxId": "6d7629ea-c2ea-41fb-85f9-36be5831928b",
        "sPgmId": "B070302",
        "menuId": ""
    }
}

params.titxaDclrDVO.dclrYmdBgng = "20240501"
params.titxaDclrDVO.dclrYmdEnd  = "20240512"
params.pagerVO.pageNo  		= 1
params.pagerVO.rowCount  	= 5000
params.pagerVO.totalCount  	= 17790
call_wetax_list(params)


// 상세페이지 이동
https://www.wetax.go.kr/etr/lit/b0703/B070302M02.do?dclrId=10000000000002194687&objCd=T&objType=P&bgDclrId=&linkTyp=

'''
from datetime import datetime
import logging 
import dbjob
import sys


DATA_KEY = "result_page_2"

# 로깅 설정
current_time = datetime.now()
now = current_time.strftime("%Y%m%d_%H%M%S")

log_filename = f"V:/PyHometax_Log_2024/WetaxDclrId/dclrid_{now}.log"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger = logging.getLogger()
logger.addHandler(file_handler)

sys.path.append("E:\\Temp\\wetax_dclr_0514")

print("import start")

import result_page_1 as result1
import result_page_2 as result2
import result_page_3 as result3
import result_page_4 as result4
import result_page_5 as result5
import result_page_6 as result6

print("import finish")

def getWetaxData():
    wetax_data1 = result1.data['titxaDclrDVOList']
    wetax_data2 = result2.data['titxaDclrDVOList']
    wetax_data3 = result3.data['titxaDclrDVOList']
    wetax_data4 = result4.data['titxaDclrDVOList']
    wetax_data5 = result5.data['titxaDclrDVOList']
    wetax_data6 = result6.data['titxaDclrDVOList']

    wetax_data = wetax_data1 + wetax_data2 + wetax_data3 + wetax_data4 + wetax_data5 + wetax_data6
    wetax_data = list(reversed(wetax_data))
    logger.info(f"가공 전 wetax_data LEN= {len(wetax_data)}")
    
    elpn_map = {}
    wetax_map = {}
    
    for idx, row in enumerate(wetax_data):
        dclrCmnRcptClCd = row['dclrCmnRcptClCd']
        payYmd          = row['payYmd']
        납부금액        = row['payPargTxa']

        납부여부 = '-'
        if dclrCmnRcptClCd == "00":
            납부여부 = "-"
        elif dclrCmnRcptClCd == "06" and 납부금액 != None and 납부금액 <= 0 :
            납부여부 = "-"
        elif dclrCmnRcptClCd == "06" and  payYmd != None: 
            납부여부 = "납부" 
        elif dclrCmnRcptClCd == "06" and payYmd == None:
            납부여부 = "미납"

        #logger.info(idx , ' 이름 {:<6}'.format(이름), 주민번호, dclrId, 납세번호,  납부금액, 전자납부번호, 신고완료_취소, 납부여부)
        
        if row['dclrCmnRcptClNm'] == '작성중':
            continue

        weinfo = {
            "index"             : idx
            , "dclrId"          : row['dclrId']
            , "이름"            : row['txpNm']
            , "주민번호"        : row['tnenc']
            , "납세번호"        : row['txpmNo']  
            , "납부금액"        : row['payPargTxa']
            , "전자납부번호"    : row['elpn'] # 신고 직후 확인 가능
            , "신고완료_취소"   : row['dclrCmnRcptClNm']
            , "납부여부"        : 납부여부
        }


        # if row['elpn'] in elpn_map:
        #     print(f"    {row['elpn']} ==> {weinfo}")
        #     print(f"==> {row['elpn']} ==> {weinfo} <== 중복")
        #     elpn_map[row['elpn']] = weinfo
        # elpn_map[row['elpn']] = weinfo



        key = f"{row['txpNm']}_{row['tnenc'][0:6]}"
        if key in wetax_map:
            중복신청_이전의_신고_미취소 = ''
            취소URL = ''
            if wetax_map[key]['신고완료_취소'] == '신고완료':
                중복신청_이전의_신고_미취소 = '    ###### 미취소 => 취소 필요'
                취소URL = f"\nhttps://www.wetax.go.kr/etr/lit/b0703/B070302M02.do?dclrId={wetax_map[key]['dclrId']}&objCd=T&objType=P&bgDclrId=&linkTyp="

            print(f"\n{wetax_map[key]}{중복신청_이전의_신고_미취소}{취소URL}")
            print(f"{weinfo} <== 중복신고")
        
        wetax_map[key] = weinfo

    return wetax_map, elpn_map


def main():
    affected_cnt = 0
    print("#" * 50)
    wetax_data, elpn_map = getWetaxData()
    logger.info(f"가공 후 wetax_data LEN= {len(wetax_data)}")

    #FIXME
    #print("작업 확인을 위한 중간에 고의 중단")
    # sys.exit()

    rs_ht_info = dbjob.select_hTtT_au4_for_dclrid_모든자료('the1')
    logger.info(f"문서 다운로드 rs LEN= {len(rs_ht_info)}")


    print("#" * 50)
    for row in rs_ht_info:
        key = f"{row['holder_nm']}_{row['holder_ssn1']}"
        if row['wetax_dclrid']:
            if key in wetax_data:
                if wetax_data[key]['dclrId'] != row['wetax_dclrid']:
                    print(f"DB=>{row}")
                    print(f"    Changed!!! {row['wetax_dclrid']}  ===>>>  {wetax_data[key]['dclrId']}")
            else:
                print(f'{key} 가 없음')

conn = dbjob.connect_db()
main()    