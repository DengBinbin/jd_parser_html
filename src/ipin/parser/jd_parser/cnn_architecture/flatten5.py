import os
import keras
from keras.preprocessing import sequence
from keras.models import  Sequential,Model
from keras.layers.core import Dense, Dropout, Activation, Lambda,Merge
from keras.layers.embeddings import Embedding
from keras.layers import  merge,Input
from keras.layers.convolutional import Convolution1D
from keras.constraints import nonneg,maxnorm
from keras import backend as K
from keras.callbacks import ModelCheckpoint,Callback
from keras.regularizers import l2, activity_l2

def max_1d(X):
    return K.max(X,axis=1)

def mean_1d(X):
    return K.mean(X,axis=1)

def build_model(config):
    sent_input = Input(shape=(config.max_len,),dtype='int32',name = "sent_input") # define inpute
    sent_embedding = Embedding(config.vocab_size,config.word_dims,
                                # W_regularizer=l2(0.01),
                                dropout=0.2,
                                name="sent_w2v",)(sent_input)
    convs = []
    if config.pool_method=="mean":
        pool_method =  mean_1d
    elif  config.pool_method=="max":
        pool_method = max_1d

    for nb_filter,filter_length in zip(config.nb_filters,config.filter_lengths):
        conv = Convolution1D(nb_filter=nb_filter,
                        filter_length=filter_length,
                        border_mode='valid',
                        activation='relu',
                        subsample_length=1,
                        name="conv_len_{}_nb_{}".format(filter_length,nb_filter))(sent_embedding)
        pooling = Lambda(pool_method, output_shape=(nb_filter,),name="max_pooling_len_{}_nb_{}".format(filter_length,nb_filter))(conv)
        convs.append(pooling)
    concat =  merge(convs, mode='concat',name = "sent_merge")
    hidden =    Dropout(p = config.hidden_dropout)(Dense(config.hidden_dims,activation="relu",name = "sent_hidden")(concat))
    out = Activation('softmax')(Dense(config.label_size)(hidden))
    model = Model(input=sent_input, output=out,name=config.model_name)
    print("build completed")
    model.compile(loss='sparse_categorical_crossentropy',
                  optimizer='adam',
                  metrics=['accuracy'])
    print(model.summary())
    from keras.utils.visualize_util import plot
    plot(model, to_file='flatten_10.png',show_shapes=True)
    return model