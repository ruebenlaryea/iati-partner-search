from utils import get_data_path
import pandas as pd
import numpy as np
from os.path import join
from gensim.models import Word2Vec
import pickle
from constants import WORD2VECMODEL_FILENAME, PROCESSED_RECORDS_FILENAME, WORD2VECAVG_FILENAME
import time

def average_per_doc(description_text, w2v_model, dim_size):
    description_list = description_text.split(" ")
    mean_array = np.zeros((dim_size,), dtype="float32")
    all_words = set(w2v_model.wv.vocab)
    n_words = 0
    for w in description_list:
        if w in all_words:
            mean_array = np.add(mean_array, w2v_model.wv.get_vector(w))
            n_words += 1
    if n_words > 0:
        mean_array = np.divide(mean_array, n_words)
    return mean_array


def results_per_corpus_df(input_df, dim_size, w2v_model, avg_filename):
    results_arr = np.empty([0, dim_size])
    for index, row in df1.iterrows():
        results_arr = np.vstack(
            (results_arr, average_per_doc(row["description"], w2v_model, dim_size))
        )
    with open(join(get_data_path(), avg_filename), "wb") as output_file:
        pickle.dump(results_arr, output_file)
    


if __name__ == "__main__":
    
    df1 = pd.read_csv(
        join(get_data_path(), PROCESSED_RECORDS_FILENAME), encoding="iso-8859-1"
    )
    


    model = Word2Vec.load(join(get_data_path(), WORD2VECMODEL_FILENAME))

    # This takes a while
    start = time.time()
    results_per_corpus_df(df1, 50, model, WORD2VECAVG_FILENAME)
    print("average array created in {0}".format(time.time()- start))