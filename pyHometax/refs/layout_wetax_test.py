import pymysql
import common
import layout_wetax_trans as wetax_layout

import pyHometax.gb_agent_env_개별 as agent_env
import gb_agent_db as autodb

def main_test():
  conn_t = autodb.connect_db()
  ht_series_yyyymm = '202305'
  group_id = 'the1'
  ht_tt_seq = 20000
  
  obj = wetax_layout.wetax_ele_form(conn_t, ht_series_yyyymm, group_id, ht_tt_seq)
  obj.make_electric_string()
  obj.make_file_for_one()
  
  #obj2 = wetax_layout.wetax_ele_form()
  #obj2.print_file_value_for_debug("test_data\\2023_양도소득지방세_정율섭_20000.y11")

  #result_text = obj.get_result_text()
  #result_text = result_text + result_text
  #obj.make_file_for_many(result_text, 'test.y11')

if __name__ == "__main__":
    main_test()
