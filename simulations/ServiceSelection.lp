\* Service_Selection_Problem *\
Minimize
OBJ: j0_aws_sa_east + 0.807291666667 j0_aws_us_east
 + 0.583333333333 j0_gcp_eu_west + j10_aws_sa_east
 + 0.807291666667 j10_aws_us_east + 0.583333333333 j10_gcp_eu_west
 + j11_aws_sa_east + 0.807291666667 j11_aws_us_east
 + 0.583333333333 j11_gcp_eu_west + j12_aws_sa_east
 + 0.807291666667 j12_aws_us_east + 0.583333333333 j12_gcp_eu_west
 + j13_aws_sa_east + 0.807291666667 j13_aws_us_east
 + 0.583333333333 j13_gcp_eu_west + j14_aws_sa_east
 + 0.807291666667 j14_aws_us_east + 0.583333333333 j14_gcp_eu_west
 + j15_aws_sa_east + 0.807291666667 j15_aws_us_east
 + 0.583333333333 j15_gcp_eu_west + j16_aws_sa_east
 + 0.807291666667 j16_aws_us_east + 0.583333333333 j16_gcp_eu_west
 + j17_aws_sa_east + 0.807291666667 j17_aws_us_east
 + 0.583333333333 j17_gcp_eu_west + j18_aws_sa_east
 + 0.807291666667 j18_aws_us_east + 0.583333333333 j18_gcp_eu_west
 + j19_aws_sa_east + 0.807291666667 j19_aws_us_east
 + 0.583333333333 j19_gcp_eu_west + j1_aws_sa_east
 + 0.807291666667 j1_aws_us_east + 0.583333333333 j1_gcp_eu_west
 + j20_aws_sa_east + 0.807291666667 j20_aws_us_east
 + 0.583333333333 j20_gcp_eu_west + j21_aws_sa_east
 + 0.807291666667 j21_aws_us_east + 0.583333333333 j21_gcp_eu_west
 + j22_aws_sa_east + 0.807291666667 j22_aws_us_east
 + 0.583333333333 j22_gcp_eu_west + j23_aws_sa_east
 + 0.807291666667 j23_aws_us_east + 0.583333333333 j23_gcp_eu_west
 + j24_aws_sa_east + 0.807291666667 j24_aws_us_east
 + 0.583333333333 j24_gcp_eu_west + j25_aws_sa_east
 + 0.807291666667 j25_aws_us_east + 0.583333333333 j25_gcp_eu_west
 + j2_aws_sa_east + 0.807291666667 j2_aws_us_east
 + 0.583333333333 j2_gcp_eu_west + j3_aws_sa_east
 + 0.807291666667 j3_aws_us_east + 0.583333333333 j3_gcp_eu_west
 + j4_aws_sa_east + 0.807291666667 j4_aws_us_east
 + 0.583333333333 j4_gcp_eu_west + j5_aws_sa_east
 + 0.807291666667 j5_aws_us_east + 0.583333333333 j5_gcp_eu_west
 + j6_aws_sa_east + 0.807291666667 j6_aws_us_east
 + 0.583333333333 j6_gcp_eu_west + j7_aws_sa_east
 + 0.807291666667 j7_aws_us_east + 0.583333333333 j7_gcp_eu_west
 + j8_aws_sa_east + 0.807291666667 j8_aws_us_east
 + 0.583333333333 j8_gcp_eu_west + j9_aws_sa_east
 + 0.807291666667 j9_aws_us_east + 0.583333333333 j9_gcp_eu_west
Subject To
_C1: j0_aws_sa_east + j0_aws_us_east + j0_gcp_eu_west = 1
_C10: j9_aws_sa_east + j9_aws_us_east + j9_gcp_eu_west = 1
_C11: j10_aws_sa_east + j10_aws_us_east + j10_gcp_eu_west = 1
_C12: j11_aws_sa_east + j11_aws_us_east + j11_gcp_eu_west = 1
_C13: j12_aws_sa_east + j12_aws_us_east + j12_gcp_eu_west = 1
_C14: j13_aws_sa_east + j13_aws_us_east + j13_gcp_eu_west = 1
_C15: j14_aws_sa_east + j14_aws_us_east + j14_gcp_eu_west = 1
_C16: j15_aws_sa_east + j15_aws_us_east + j15_gcp_eu_west = 1
_C17: j16_aws_sa_east + j16_aws_us_east + j16_gcp_eu_west = 1
_C18: j17_aws_sa_east + j17_aws_us_east + j17_gcp_eu_west = 1
_C19: j18_aws_sa_east + j18_aws_us_east + j18_gcp_eu_west = 1
_C2: j1_aws_sa_east + j1_aws_us_east + j1_gcp_eu_west = 1
_C20: j19_aws_sa_east + j19_aws_us_east + j19_gcp_eu_west = 1
_C21: j20_aws_sa_east + j20_aws_us_east + j20_gcp_eu_west = 1
_C22: j21_aws_sa_east + j21_aws_us_east + j21_gcp_eu_west = 1
_C23: j22_aws_sa_east + j22_aws_us_east + j22_gcp_eu_west = 1
_C24: j23_aws_sa_east + j23_aws_us_east + j23_gcp_eu_west = 1
_C25: j24_aws_sa_east + j24_aws_us_east + j24_gcp_eu_west = 1
_C26: j25_aws_sa_east + j25_aws_us_east + j25_gcp_eu_west = 1
_C27: j0_aws_us_east + j10_aws_us_east + j11_aws_us_east + j12_aws_us_east
 + j13_aws_us_east + j14_aws_us_east + j15_aws_us_east + j16_aws_us_east
 + j17_aws_us_east + j18_aws_us_east + j19_aws_us_east + j1_aws_us_east
 + j20_aws_us_east + j21_aws_us_east + j22_aws_us_east + j23_aws_us_east
 + j24_aws_us_east + j25_aws_us_east + j2_aws_us_east + j3_aws_us_east
 + j4_aws_us_east + j5_aws_us_east + j6_aws_us_east + j7_aws_us_east
 + j8_aws_us_east + j9_aws_us_east <= 16
_C28: j0_gcp_eu_west + j10_gcp_eu_west + j11_gcp_eu_west + j12_gcp_eu_west
 + j13_gcp_eu_west + j14_gcp_eu_west + j15_gcp_eu_west + j16_gcp_eu_west
 + j17_gcp_eu_west + j18_gcp_eu_west + j19_gcp_eu_west + j1_gcp_eu_west
 + j20_gcp_eu_west + j21_gcp_eu_west + j22_gcp_eu_west + j23_gcp_eu_west
 + j24_gcp_eu_west + j25_gcp_eu_west + j2_gcp_eu_west + j3_gcp_eu_west
 + j4_gcp_eu_west + j5_gcp_eu_west + j6_gcp_eu_west + j7_gcp_eu_west
 + j8_gcp_eu_west + j9_gcp_eu_west <= 14
_C29: j0_aws_sa_east + j10_aws_sa_east + j11_aws_sa_east + j12_aws_sa_east
 + j13_aws_sa_east + j14_aws_sa_east + j15_aws_sa_east + j16_aws_sa_east
 + j17_aws_sa_east + j18_aws_sa_east + j19_aws_sa_east + j1_aws_sa_east
 + j20_aws_sa_east + j21_aws_sa_east + j22_aws_sa_east + j23_aws_sa_east
 + j24_aws_sa_east + j25_aws_sa_east + j2_aws_sa_east + j3_aws_sa_east
 + j4_aws_sa_east + j5_aws_sa_east + j6_aws_sa_east + j7_aws_sa_east
 + j8_aws_sa_east + j9_aws_sa_east <= 20
_C3: j2_aws_sa_east + j2_aws_us_east + j2_gcp_eu_west = 1
_C30: j0_aws_us_east + j10_aws_us_east + j11_aws_us_east + j12_aws_us_east
 + j13_aws_us_east + j14_aws_us_east + j15_aws_us_east + j16_aws_us_east
 + j17_aws_us_east + j18_aws_us_east + j19_aws_us_east + j1_aws_us_east
 + j20_aws_us_east + j21_aws_us_east + j22_aws_us_east + j23_aws_us_east
 + j24_aws_us_east + j25_aws_us_east + j2_aws_us_east + j3_aws_us_east
 + j4_aws_us_east + j5_aws_us_east + j6_aws_us_east + j7_aws_us_east
 + j8_aws_us_east + j9_aws_us_east >= 2.6
_C31: j0_gcp_eu_west + j10_gcp_eu_west + j11_gcp_eu_west + j12_gcp_eu_west
 + j13_gcp_eu_west + j14_gcp_eu_west + j15_gcp_eu_west + j16_gcp_eu_west
 + j17_gcp_eu_west + j18_gcp_eu_west + j19_gcp_eu_west + j1_gcp_eu_west
 + j20_gcp_eu_west + j21_gcp_eu_west + j22_gcp_eu_west + j23_gcp_eu_west
 + j24_gcp_eu_west + j25_gcp_eu_west + j2_gcp_eu_west + j3_gcp_eu_west
 + j4_gcp_eu_west + j5_gcp_eu_west + j6_gcp_eu_west + j7_gcp_eu_west
 + j8_gcp_eu_west + j9_gcp_eu_west >= 2.6
_C32: j0_aws_sa_east + j10_aws_sa_east + j11_aws_sa_east + j12_aws_sa_east
 + j13_aws_sa_east + j14_aws_sa_east + j15_aws_sa_east + j16_aws_sa_east
 + j17_aws_sa_east + j18_aws_sa_east + j19_aws_sa_east + j1_aws_sa_east
 + j20_aws_sa_east + j21_aws_sa_east + j22_aws_sa_east + j23_aws_sa_east
 + j24_aws_sa_east + j25_aws_sa_east + j2_aws_sa_east + j3_aws_sa_east
 + j4_aws_sa_east + j5_aws_sa_east + j6_aws_sa_east + j7_aws_sa_east
 + j8_aws_sa_east + j9_aws_sa_east >= 2.6
_C4: j3_aws_sa_east + j3_aws_us_east + j3_gcp_eu_west = 1
_C5: j4_aws_sa_east + j4_aws_us_east + j4_gcp_eu_west = 1
_C6: j5_aws_sa_east + j5_aws_us_east + j5_gcp_eu_west = 1
_C7: j6_aws_sa_east + j6_aws_us_east + j6_gcp_eu_west = 1
_C8: j7_aws_sa_east + j7_aws_us_east + j7_gcp_eu_west = 1
_C9: j8_aws_sa_east + j8_aws_us_east + j8_gcp_eu_west = 1
Bounds
j0_aws_sa_east <= 1
j0_aws_us_east <= 1
j0_gcp_eu_west <= 1
j10_aws_sa_east <= 1
j10_aws_us_east <= 1
j10_gcp_eu_west <= 1
j11_aws_sa_east <= 1
j11_aws_us_east <= 1
j11_gcp_eu_west <= 1
j12_aws_sa_east <= 1
j12_aws_us_east <= 1
j12_gcp_eu_west <= 1
j13_aws_sa_east <= 1
j13_aws_us_east <= 1
j13_gcp_eu_west <= 1
j14_aws_sa_east <= 1
j14_aws_us_east <= 1
j14_gcp_eu_west <= 1
j15_aws_sa_east <= 1
j15_aws_us_east <= 1
j15_gcp_eu_west <= 1
j16_aws_sa_east <= 1
j16_aws_us_east <= 1
j16_gcp_eu_west <= 1
j17_aws_sa_east <= 1
j17_aws_us_east <= 1
j17_gcp_eu_west <= 1
j18_aws_sa_east <= 1
j18_aws_us_east <= 1
j18_gcp_eu_west <= 1
j19_aws_sa_east <= 1
j19_aws_us_east <= 1
j19_gcp_eu_west <= 1
j1_aws_sa_east <= 1
j1_aws_us_east <= 1
j1_gcp_eu_west <= 1
j20_aws_sa_east <= 1
j20_aws_us_east <= 1
j20_gcp_eu_west <= 1
j21_aws_sa_east <= 1
j21_aws_us_east <= 1
j21_gcp_eu_west <= 1
j22_aws_sa_east <= 1
j22_aws_us_east <= 1
j22_gcp_eu_west <= 1
j23_aws_sa_east <= 1
j23_aws_us_east <= 1
j23_gcp_eu_west <= 1
j24_aws_sa_east <= 1
j24_aws_us_east <= 1
j24_gcp_eu_west <= 1
j25_aws_sa_east <= 1
j25_aws_us_east <= 1
j25_gcp_eu_west <= 1
j2_aws_sa_east <= 1
j2_aws_us_east <= 1
j2_gcp_eu_west <= 1
j3_aws_sa_east <= 1
j3_aws_us_east <= 1
j3_gcp_eu_west <= 1
j4_aws_sa_east <= 1
j4_aws_us_east <= 1
j4_gcp_eu_west <= 1
j5_aws_sa_east <= 1
j5_aws_us_east <= 1
j5_gcp_eu_west <= 1
j6_aws_sa_east <= 1
j6_aws_us_east <= 1
j6_gcp_eu_west <= 1
j7_aws_sa_east <= 1
j7_aws_us_east <= 1
j7_gcp_eu_west <= 1
j8_aws_sa_east <= 1
j8_aws_us_east <= 1
j8_gcp_eu_west <= 1
j9_aws_sa_east <= 1
j9_aws_us_east <= 1
j9_gcp_eu_west <= 1
End
