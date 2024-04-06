from string import digits
import re
import sys


# 우편번호 검색 : https://www.epost.go.kr/search.RetrieveIntegrationNewZipCdList.comm



def readFile():
    data = []  
    f = open("주소록.txt", "r", encoding="utf8")
    while True:
        line = f.readline()
        if not line: break
        data.append(line)
    
    f.close()
    return data



#도로명 index 찾기 
def findRoadNameIndex(arrAddr): 
    retVal = -1 
    for index, value in enumerate(arrAddr): 
        # 슷자 및 특수문자 제거 : 봉황로65 와 같이 도로명과 건물번호가 뭍에 있는 경우 때문에 
        # #value = value. replace(', ', ' ).replace(' .', " ).replace(’번지’, ' ).rstrip() 
        value = value.replace('번지', '').rstrip() 
        #arrAddr[iridex] = value # 원본 데이터 변경 （컴마 제거） 
        
        newVal = value.replace('-', '').replace('(' , '').replace(')', '').replace(digits, '') 
        newVal = re.sub("[a-zA-Z0-9]*$", "", newVal) 

        if newVal[-1:] == '로' or newVal[-1:] == '길' :
            retVal = index
            break 

    return retVal 

# 도로명만 가져오기 （광금낭로699번길22-33 => 광금낭로699번길） 
def trancateRoadName(roadName): 
    #newVa l = roadwarne. replace(', ' , ' ).replace('. ', ' ').replace(’번지‘, " ').rstrip()
    newVal = roadName.replace('번지', '').rstrip()

    lastIdx = -1 
    for index in range(len(newVal)-1, 0, -1): 
        #print(newVal[index] ) 
        ch = newVal[index] 
        if ch.isdigit() or ch == '-' : 
            lastIdx = index 
        else: 
            break 

    if lastIdx > -1 : 
        newVal = newVal[0:lastIdx] 
    
    return newVal 

#건물번호， 상세주소 찾기 
def findBldNumAndEtc (arrAddr, roadNameIdx): 
    bldNumIdx = roadNameIdx 
    bldNum  = ""  # 건물번호
    etcAddr = "" # 상세주소 
 
    roadName = arrAddr[bldNumIdx] 
    newVal = roadName.replace('번지', '').rstrip() 
    
    #도로명 뒤에 건물번호가 붙어있는지 검사
    m = re.findall('[-0-9]+$', newVal) 

    if len(m) == 0 :
        #도로명에 건물번호가 없을 경우 다음 index에 건물번호가 있을 것으로 추측 
        if len(arrAddr) > bldNumIdx+1 :
            bldNumIdx = bldNumIdx + 1
            roadName = arrAddr[bldNumIdx] 
            roadName.replace(',', '').replace('.','').rstrip() 
            bldNum = roadName
        else :
            bldNum = ""
    else : #도로명에 건물번호가 존재하는 것으로 판단 
        bldNum = m[0] 

    if len(arrAddr) > bldNumIdx+1 : 
        for i in range(bldNumIdx+1, len(arrAddr)) : 
            etcAddr = etcAddr + arrAddr[i] + " "
    
    return [bldNum, etcAddr] 


# 건물번호가 숫자 혹은 -로만 구성되어 있는지 검사
def checkBldNum(bldNum): 
    lastIdx = -1 
    for index in range(0, len(bldNum)): 
        lastIdx = index 
        ch = bldNum[index] 
        if ch.isdigit() or ch == '-' : 
            pass
        else: 
            break 

    if len(bldNum)-1 == lastIdx : 
        return [ bldNum , "" ]
    else :
        return [ bldNum[0:lastIdx], bldNum[lastIdx:] ]

def parseAddress(data): 
    _DELI_ = "|"
    for itm in data: 
        #print("원본주소 : "  + itm)
        arrAddr = itm.replace(',', ' ').replace('.', ' ').replace('(', ' (').split() 

        # 도로명이 있는 배열 Index얻기
        roadNameIndex = findRoadNameIndex(arrAddr) 

        # 도/시 와 도로명 사이의 시군구 값
        middleSiGun = ""

        if roadNameIndex == -1 : 
            print ('FAIL|' + itm)
            continue
        else :
            if (roadNameIndex > 0) :
                for idx in range(1, roadNameIndex) :
                    middleSiGun += arrAddr[idx] + " "

        if middleSiGun != "" :
            print ( itm + " => "  + middleSiGun    )
        
        # 도로명
        roadName = trancateRoadName(arrAddr[roadNameIndex]) 

        # 도로명 뒤의 건물번호+상세주소 리턴
        bldNumAndEtc = findBldNumAndEtc (arrAddr, roadNameIndex) 

        # 건물번호, 상세 주소를 분리
        # bldNumChecked[0] : 건물번호
        # bldNumChecked[1] : 상세주소(기타주소)
        bldNumChecked = checkBldNum(bldNumAndEtc[0])

        line = arrAddr[0] + _DELI_  + middleSiGun + _DELI_ + roadName + _DELI_ + bldNumChecked[0] + _DELI_ + (bldNumChecked[1] + " " + bldNumAndEtc[1]).strip()
        print(line) 

if __name__ == "__main__":

    
    
    parseAddress(readFile())