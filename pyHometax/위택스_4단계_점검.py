import 위택스_4단계_점검_data as data
import dbjob
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
        "uxId": "cdc829ee-02f1-4bb4-8040-4e9747d7fa40",
        "sPgmId": "B070302",
        "menuId": ""
    }
}

params.titxaDclrDVO.dclrYmdBgng = "20240501"
params.titxaDclrDVO.dclrYmdEnd  = "20240502"
params.titxaDclrDVO.rowCount  = 2000
params.titxaDclrDVO.totalCount  = 2000
call_wetax_list(params)



// 상세페이지 이동
https://www.wetax.go.kr/etr/lit/b0703/B070302M02.do?dclrId=10000000000002194687&objCd=T&objType=P&bgDclrId=&linkTyp=

'''



def getWetaxData():
    wetax_data = data.result_0502['titxaDclrDVOList']
    elpn_map = {}

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

        #print(idx , ' 이름 {:<6}'.format(이름), 주민번호, dclrId, 납세번호,  납부금액, 전자납부번호, 신고완료_취소, 납부여부)
        
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

        elpn_map[row['elpn']] = weinfo

    return elpn_map




def main():
    rs_ht_info = dbjob.select_hTtT_au4_for_dclrid('the1')
    
    print("LEN", len(rs_ht_info))

    affected_cnt = 0
    wetax_data = getWetaxData()
    for ht_info in rs_ht_info:
        wetax_reg_num = ht_info['wetax_reg_num'].replace('-', '')
        matching_data = wetax_data[wetax_reg_num]
        if matching_data:
            # print(ht_info['ht_tt_seq'], ht_info['holder_nm'], ht_info['holder_ssn1'], ht_info['holder_ssn2'], matching_data['dclrId'])
            
            wetax_paid_yn = None
            if matching_data['납부여부'] == '납부': wetax_paid_yn = 'Y'

            if ht_info['wetax_income_tax'] == matching_data['납부금액']:
                affected_cnt += dbjob.update_HtTt_wetaxDclrId(ht_info['ht_tt_seq'], matching_data['dclrId'], wetax_paid_yn)
                ...
            else:
                print(f"납부금액에 차이가 있음. {ht_info['wetax_income_tax'] } != {matching_data['납부금액']}")
        else:
            print(ht_info['ht_tt_seq'], ht_info['holder_nm'], ht_info['holder_ssn1'], ht_info['holder_ssn2'], "NO MATCH ~~~~~~~~~~~~");

    print(f"총 {affected_cnt} 개가 업데이트 됨")

conn = dbjob.connect_db()
main()    