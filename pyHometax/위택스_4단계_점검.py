

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
        "dclrYmdEnd": "20240531",
        "dclrCmnRcptClCd": "",
        "inqCtpvCd": "",
        "inqSggCd": "",
        "payYn": ""
    },
    "pagerVO" : {
        "pageNo" : 1,
        "rowCount" : 1000,
        "totalCount" : 1000
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

params.titxaDclrDVO.dclrYmdBgng = "20230501"
params.titxaDclrDVO.dclrYmdEnd = "20230531"
// call_wetax_list(params)



// 상세페이지 이동
https://www.wetax.go.kr/etr/lit/b0703/B070302M02.do?dclrId=10000000000002194687&objCd=T&objType=P&bgDclrId=&linkTyp=

'''


ALTER TABLE ht_tt ADD wetax_dclrid varchar(25) NULL COMMENT '위택스 dclrId (위택스 관리키)';
ALTER TABLE ht_tt CHANGE wetax_dclrid wetax_dclrid varchar(25) NULL COMMENT '위택스 dclrId (위택스 관리키)' AFTER wetax_reg_num;


from 위택스_4단계_점검_data import *



for idx, row in enumerate(result_1['titxaDclrDVOList']):
    dclrId          = row['dclrId']
    이름            = row['txpNm']
    주민번호        = row['tnenc']
    납세번호        = row['txpmNo']  
    납부금액        = row['payPargTxa']
    전자납부번호    = row['elpn'] # 신고 직후 확인 가능
    신고완료_취소   = row['dclrCmnRcptClNm']

    dclrCmnRcptClCd =  row['dclrCmnRcptClCd']
    payYmd          =  row['payYmd']

    납부여부 = '-'
    if dclrCmnRcptClCd == "00":
        납부여부 = "-"
    elif dclrCmnRcptClCd == "06" and 납부금액 != null and 납부금액 <= 0 :
        납부여부 = "-"
    elif dclrCmnRcptClCd == "06" and  payYmd != null: 
        납부여부 = "납부" 
    elif dclrCmnRcptClCd == "06" and payYmd == null:
        납부여부 = "미납"

    print('이름 {:<6}'.format(이름), dclrId, 납부여부)
