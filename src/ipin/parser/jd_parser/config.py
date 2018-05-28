#coding=utf-8
import sys
sys.path.append('../')
from utils.path import *
from utils.util import *
import cPickle
import numpy as np
reload(sys)
class config():
    def __init__(self):
        #训练参数
        config.label_size = 48
        config.batch_size = 256
        config.nb_epoch = 10
        #载入样本不均衡时的权重
        label_count = data_path+'label_counts.pkl'
        # if not os.path.exists(label_count):
        #     dump_labelCounts()
        file_label = file(pkl_path+'label_counts.pkl','r')
        labels = cPickle.load(file_label)
        config.class_weight = np.ones(config.label_size)

        for cid,label in enumerate(labels):   
            config.class_weight[int(label)] = min(1e0,109000./(labels[label]))
        # print config.class_weight
        #是否利用上下文
        config.total_sents = 1
        #embedding
        config.max_len = 20
        config.word_dims = 200
        #CNN基本配置
        config.nb_filters = [200,200,200,200,200]
        config.filter_lengths = [2,4,6,8,10]
        config.hidden_dims = 300
        config.hidden_dropout = 0.3
        config.pool_method = "max"
        config.model_name = "flatten_"+str(len(config.nb_filters))
