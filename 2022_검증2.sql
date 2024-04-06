select holder_ssn1
from audit_ht ah 


select count(*)
from audit_we aw 

update audit_ht
set  holder_ssn1 = substr(holder_ssn1, 1, 6) 



select ht_tt_seq , t.data_type , t.holder_nm , t.holder_ssn1 , t.reg_id , t.hometax_reg_num, t.wetax_reg_num, ah.ai ah_ai, aw.ai aw_ai
from ht_tt t
left join audit_ht ah on t.hometax_reg_num = ah.hometax_reg_id 
left join audit_we aw on t.wetax_reg_num = aw.wetax_reg_num 
where 1=1
 	and ht_series_yyyymm = '202405'
 	and step_cd = 'COMPLETE'
	