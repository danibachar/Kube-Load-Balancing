\* Service_Selection_Problem *\
Minimize
OBJ: 1600 j0_aws_sa_east + 983.333333333 j0_aws_us_east + 6800 j0_gcp_eu_west
 + 1600 j1_aws_sa_east + 983.333333333 j1_aws_us_east + 6800 j1_gcp_eu_west
 + 1600 j2_aws_sa_east + 983.333333333 j2_aws_us_east + 6800 j2_gcp_eu_west
 + 1600 j3_aws_sa_east + 983.333333333 j3_aws_us_east + 6800 j3_gcp_eu_west
 + 1600 j4_aws_sa_east + 983.333333333 j4_aws_us_east + 6800 j4_gcp_eu_west
Subject To
_C1: j0_aws_sa_east + j0_aws_us_east + j0_gcp_eu_west = 1
_C10: j0_gcp_eu_west + j1_gcp_eu_west + j2_gcp_eu_west + j3_gcp_eu_west
 + j4_gcp_eu_west >= 0.5
_C11: j0_aws_sa_east + j1_aws_sa_east + j2_aws_sa_east + j3_aws_sa_east
 + j4_aws_sa_east >= 0.5
_C2: j1_aws_sa_east + j1_aws_us_east + j1_gcp_eu_west = 1
_C3: j2_aws_sa_east + j2_aws_us_east + j2_gcp_eu_west = 1
_C4: j3_aws_sa_east + j3_aws_us_east + j3_gcp_eu_west = 1
_C5: j4_aws_sa_east + j4_aws_us_east + j4_gcp_eu_west = 1
_C6: j0_aws_us_east + j1_aws_us_east + j2_aws_us_east + j3_aws_us_east
 + j4_aws_us_east <= 20
_C7: j0_gcp_eu_west + j1_gcp_eu_west + j2_gcp_eu_west + j3_gcp_eu_west
 + j4_gcp_eu_west <= 20
_C8: j0_aws_sa_east + j1_aws_sa_east + j2_aws_sa_east + j3_aws_sa_east
 + j4_aws_sa_east <= 20
_C9: j0_aws_us_east + j1_aws_us_east + j2_aws_us_east + j3_aws_us_east
 + j4_aws_us_east >= 0.5
Bounds
j0_aws_sa_east <= 1
j0_aws_us_east <= 1
j0_gcp_eu_west <= 1
j1_aws_sa_east <= 1
j1_aws_us_east <= 1
j1_gcp_eu_west <= 1
j2_aws_sa_east <= 1
j2_aws_us_east <= 1
j2_gcp_eu_west <= 1
j3_aws_sa_east <= 1
j3_aws_us_east <= 1
j3_gcp_eu_west <= 1
j4_aws_sa_east <= 1
j4_aws_us_east <= 1
j4_gcp_eu_west <= 1
End
