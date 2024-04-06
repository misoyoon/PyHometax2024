-- 한투: 주민번호 뒷자리 없는 리스트
select u.nm, holder_nm, holder_ssn1, holder_ssn2, main_account
from ht_tt t
join user u on u.id = t.reg_id 
where ht_series_yyyymm ='202405'  and sec_company_cd = 'SEC03'
		and left(main_account, 7)  = holder_ssn2
		and step_cd != 'CANCEL'
order by u.nm


-- 세금신고 단계에서의 한투 주민번호 점검
select u.nm, holder_nm, holder_ssn1, holder_ssn2, main_account
from ht_tt t
join user u on u.id = t.reg_id 
where ht_series_yyyymm ='202405'  and sec_company_cd = 'SEC03'
		and (left(main_account, 7)  = holder_ssn2  or  holder_ssn2 is null or holder_ssn2='' )
		and step_cd = 'REPORT'
order by u.nm


-- 주민등록(생년월일)이 같은 사람이 있는지 조회
select u.nm, holder_nm, holder_ssn1, count(*)
from ht_tt t
join user u on u.id = t.reg_id 
where ht_series_yyyymm ='202405'
		and step_cd != 'CANCEL'
group by holder_nm, holder_ssn1
having count(*) > 1
order by holder_nm





-- 담당자별 수량 (반자동)
select u.nm, t.reg_id, data_type
from ht_tt t
left join user u on u.id = t.reg_id 
where t.ht_series_yyyymm ='202405'
		and t.step_cd = 'REPORT'
		and t.data_type = 'SEMI'
order by u.nm, data_type


select  * -- u.nm, t.reg_id, data_type, count(*)
from ht_tt t
left join user u on u.id = t.reg_id 
where ht_series_yyyymm ='202405'
		and step_cd != 'CANCEL'
		and data_type = 'SEMI'
group by u.id
order by t.reg_id, data_type





select holder_nm, holder_ssn1, holder_ssn2, main_account
from ht_tt
where ht_series_yyyymm ='202405'  and sec_company_cd = 'SEC03'
		and holder_nm ='강건택'
order by holder_nm


-- 담당자 정보
select u.nm,  ht.REG_ID, u.HOMETAX_ID, u.HOMETAX_PW , u.SMS_NUM ,u.EMAIL , u.tel
from ht_tt ht 
left join user u on u.id = ht.reg_id
where ht.ht_series_yyyymm = '202405'
and ht.step_cd <> 'CANCEL'
and u.isEnabled = 1
group by ht.reg_id 
order by nm



-- 1단계 진행 상황
SELECT ht_tt_seq, holder_nm , reg_id , au1, au1_msg, hometax_installment1 , hometax_installment2 , hometax_income_tax , hometax_reg_num  
FROM ht_tt 
WHERE ifnull(use_yn, 'Y') != 'N'
    AND ht_series_yyyymm = '202405'
    AND step_cd='REPORT' 
	AND au1 != 'S'
--	and ht_tt_seq = 5016


SELECT ht_tt_seq, holder_nm , reg_id , au1, au1_msg, hometax_installment1 , hometax_installment2 , hometax_income_tax , hometax_reg_num  
FROM ht_tt 
WHERE ifnull(use_yn, 'Y') != 'N'
    AND ht_series_yyyymm = '202405'
    AND step_cd='REPORT' 
	and (au1='E'  )

-- update ht_tt set au1=null where au1='E'  AND ht_series_yyyymm = '202405'	
	
-- ===============================================================================================================	
-- 단계별 처리 건수
-- ===============================================================================================================	
select  '1단계 홈택스신고' step, ifnull(au1, '대기') nm, count(*)
FROM ht_tt 
WHERE ifnull(use_yn, 'Y') != 'N'
    AND ht_series_yyyymm = '202405'
    AND step_cd='REPORT' 
	and data_type = 'AUTO'
group by au1
union all
select '2단계 홈택스다운로드' step, ifnull(au2, '대기') nm, count(*)
FROM ht_tt 
WHERE ifnull(use_yn, 'Y') != 'N'
	and au1='S'
    AND ht_series_yyyymm = '202405'
    AND step_cd='REPORT' 
group by au2
union all
select '3단계 위택스신고' step, ifnull(au3, '대기') nm, count(*)
FROM ht_tt 
WHERE ifnull(use_yn, 'Y') != 'N'
	and au1='S'
    AND ht_series_yyyymm = '202405'
    AND step_cd='REPORT' 
group by au3
union all
select '4단계 위택스다운로드' step, ifnull(au4, '대기') nm, count(*)
FROM ht_tt 
WHERE ifnull(use_yn, 'Y') != 'N'
	and au1='S'
	and au3='S'
    AND ht_series_yyyymm = '202405'
    AND step_cd='REPORT' 
group by au4
-- ===============================================================================================================	
	

-- ===============================================================================================================	
-- 담당자별 수량 : 1단계
select '1단계' step, u.nm, t.reg_id,  au1, count(*) cnt
from ht_tt t
left join user u on u.id = t.reg_id 
where t.ht_series_yyyymm ='202405'
		and t.step_cd = 'REPORT'
		and t.data_type = 'AUTO'
group by  u.nm, t.reg_id,  au1
order by au1, cnt desc

select ht_tt_seq, step_cd, au1 from ht_tt t where  t.ht_series_yyyymm ='202405' and t.step_cd = 'REPORT' and t.au1 = 'E'

-- 담당자별 수량 : 2단계
select '2단계' step, u.nm, t.reg_id,  au2, count(*) cnt
from ht_tt t
left join user u on u.id = t.reg_id 
where t.ht_series_yyyymm ='202405'
		and t.step_cd = 'REPORT'
		and t.au1 = 'S'
group by  u.nm, t.reg_id,  au2
order by au2, cnt desc

select * from ht_tt t where  t.ht_series_yyyymm ='202405' and t.step_cd = 'REPORT' and t.au2 = 'E'

-- 담당자별 수량 : 3단계 
select '3단계' step, u.nm, t.reg_id,  au3, count(*) cnt
from ht_tt t
left join user u on u.id = t.reg_id 
where t.ht_series_yyyymm ='202405'
		and t.step_cd = 'REPORT'
		and t.au1 = 'S'
group by  u.nm, t.reg_id,  au3
order by au3, cnt desc




select '4단계 신청대상' title, ht_tt_seq , step_cd, u.nm, t.reg_id, holder_nm , holder_ssn1, holder_ssn2, hometax_reg_num , wetax_reg_num, au1, au2, au3, au4
from ht_tt t
left join user u on u.id = t.reg_id 
where t.ht_series_yyyymm ='202405'
		and t.step_cd = 'REPORT'
		and t.au1 = 'S'
		and t.au3 = 'S'
	

select *
from ht_tt
where ht_series_yyyymm  = '202405'
	and notify_type_cd is null

-- 세액이 없는 사람
select ht_tt_seq, data_type, reg_id, holder_nm , holder_ssn1 , holder_ssn2 , hometax_income_tax , hometax_reg_num , hometax_installment1, au1, au2, au3, au4
from ht_tt
where ht_series_yyyymm  = '202405'
	and au1 = 'S'
	-- and hometax_income_tax  = 0
	and hometax_installment1 >0
	and au2 != 'S'

select ht_tt_seq, data_type, reg_id, holder_nm , holder_ssn1 , holder_ssn2 , hometax_income_tax , hometax_reg_num , hometax_installment1, au1, au2, au3, au4  
from ht_tt
where ht_series_yyyymm  = '202405'
	and au1 = 'S'
	and au3 is null


	
select ht_tt_seq, data_type, reg_id, holder_nm , holder_ssn1 , holder_ssn2 , hometax_income_tax , hometax_reg_num , hometax_installment1, au1, au2, au3, au4  
from ht_tt
where ht_series_yyyymm  = '202405'
	and step_cd = 'REPORT'
	and data_type = 'SEMI'
	and au2 != 'S'


	
	
	
-- 1단계 예상금액과 접수금액 차이
select SUB.*
from (
	SELECT
		@ROWNUM:=@ROWNUM+1 no
		, A.ht_tt_seq 
		, A.holder_nm 
		, A.holder_ssn1 
		, A.holder_ssn2
		, CD5.nm data_type_nm
		, CD1.nm step_nm
		, CD4.nm sec_company_nm
		, U1.nm reg_nm
		, U2.nm modi_nm
		, A.au1
		, A.au2
		, A.au3
		, A.au4
		, A.au5
		, IFNULL(B.ht_tt_list_count, 0) sum_ht_tt_list_count
		, IFNULL(B.sum_audit, 0) sum_audit
		, IFNULL(B.sum_income_amount, 0) sum_income_amount
		, IFNULL(sum_income, 0) sum_income
		, IFNULL(sum_hometax_tax, 0) sum_hometax_tax
		, FLOOR(IFNULL(sum_hometax_tax, 0) / 100) * 10 sum_wetax_tax
		, CASE
				when (IFNULL(sum_hometax_tax, 0) between 10000000 and 20000000) then 10000000
				when (IFNULL(sum_hometax_tax, 0) > 20000000) then FLOOR(sum_hometax_tax / 2)
				else 0
		  		end as sum_hometax_installment1
		, CASE
				when (IFNULL(sum_hometax_tax, 0) between 10000000 and 20000000) then sum_hometax_tax - 10000000
				when (IFNULL(sum_hometax_tax, 0) > 20000000) then sum_hometax_tax - FLOOR(sum_hometax_tax / 2)
				else 0
		  		end as sum_hometax_installment2
		 , A.hometax_income_tax 
	FROM HT_TT A
		LEFT OUTER JOIN CODE CD1 ON CD1.group_cd = 'HOMETAX_STEP'   AND CD1.cd = A.step_cd
		LEFT OUTER JOIN CODE CD2 ON CD2.group_cd = 'HOMETAX_STATUS' AND CD2.cd = A.status_cd
		LEFT OUTER JOIN CODE CD4 ON CD4.group_cd = 'SEC'            AND CD4.cd = A.sec_company_cd
		LEFT OUTER JOIN CODE CD5 ON CD5.group_cd = 'HT_DATA_TYPE'   AND CD5.cd = A.data_type
		LEFT OUTER JOIN user U1 ON U1.id = A.reg_id
		LEFT OUTER JOIN user U2 ON U2.id = A.modi_id
		LEFT OUTER JOIN (
			SELECT ht_tt_seq
				, COUNT(*) ht_tt_list_count
				, SUM(income_amount) sum_income_amount
				, (SUM(sell_amount) - SUM(buy_amount) - SUM(fees_amount) - SUM(income_amount)) sum_audit
				, SUM(income_amount) - 2500000 sum_income
				, FLOOR(((SUM(income_amount) - 2500000) * 0.2) /10) * 10  sum_hometax_tax
			FROM HT_TT_LIST
			GROUP BY ht_tt_seq
		) B ON  A.ht_tt_seq = B.ht_tt_seq
		, (SELECT @ROWNUM:=0) R
	where 1=1
		AND A.ht_series_yyyymm  = '202405'
		and A.au1 = 'S'
) SUB
where hometax_income_tax - sum_hometax_tax >= 10
	and hometax_income_tax > 0

	
	
	
	
select ht_tt_seq , step_cd , data_type 
from ht_tt
where step_cd = 'MANUAL' and ht_series_yyyymm  = '202405'


update ht_tt
set data_type = 'MANUAL'
where step_cd = 'MANUAL' and ht_series_yyyymm  = '202405'