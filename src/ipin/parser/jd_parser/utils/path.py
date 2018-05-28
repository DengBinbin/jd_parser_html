import os

#local
base_path =  os.path.abspath(os.path.join(__file__,os.pardir,os.pardir,os.pardir,os.pardir,os.pardir,os.pardir,os.pardir))
#94
#base_path =  os.path.abspath(os.path.join(__file__,os.pardir,os.pardir,os.pardir,os.pardir,os.pardir,os.pardir))

data_path = os.path.join(base_path,"jd_data/")

jd_path = os.path.join(data_path,"test_jds/")
co_path = os.path.join(data_path,"test_cos/")
xz_path = os.path.join(data_path+"test_xzs/")
cnn_path = os.path.join(jd_path,"jd_for_cnn/")
pkl_path = os.path.join( os.path.abspath(os.path.join(__file__,os.pardir,os.pardir)),"pkl/")


