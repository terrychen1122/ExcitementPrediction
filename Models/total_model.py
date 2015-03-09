__author__ = 'Xingyu Zhou'

import os
import sys
import model_train_predict as model
import import_data

def read_features(read_fn):
    f = open(read_fn, 'r')
    features = []
    for line in f:
        feature = line.strip()
        features.append(feature)
    f.close()
    return features

if __name__ == '__main__':
    fn1 = 'general_plus_opt_support_stat.csv'
    fn2 = 'project_eligibility_orgin.csv'
    fn3 = 'adjusted_attributes.csv'
    fn4 = 'resource_cnt.csv'
    fn5 = 'essay_pred_val_3.csv'
    fn6 = 'refined_history_stat.csv'
    fn7 = 'cnt_bw_wk_mth_combo.csv'
    fn8 = 'prev_comprisons.csv'
    fn9 = 'exciting_project_rolling_average.csv'

    input_files = [fn1, fn2, fn3, fn4, fn5, fn6, fn7, fn8, fn9]
    output_file = 'total_predict.csv'
    features_fn = 'total_features.txt'

    features = read_features(features_fn)
    gbm = model.train_mode(model='gbm', features=features)
    gbm.set_model_parameters(number_trees=7300, learning_rate=0.01, min_sample_split=100, max_leaf_nodes=7)
    gbm.train_and_predict(input_files=input_files, output_fn=output_file)






