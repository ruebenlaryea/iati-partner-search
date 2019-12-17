import pandas as pd
import nltk
from os.path import join
from nltk.corpus import stopwords, wordnet
from nltk.stem.porter import PorterStemmer
from nltk.stem import WordNetLemmatizer
from langdetect import detect
import time

try:
    from ips_python.utils import get_data_path, get_input_path
    from ips_python.constants import (
        PROCESSED_RECORDS_FILENAME,
        INPUT_DATA_FILENAME,
        STOPWORDS_FILENAME,
        KEEPWORDS_FILENAME,
    )
except ModuleNotFoundError:
    from utils import get_data_path, get_input_path
    from constants import (
        PROCESSED_RECORDS_FILENAME,
        INPUT_DATA_FILENAME,
        STOPWORDS_FILENAME,
        KEEPWORDS_FILENAME,
    )


def preprocessing_initial_text_clean(p_df, p_text):
    # remove na description values
    p_df = p_df.dropna(subset=[p_text])
    # convert to string:
    p_df = p_df.astype(str)
    # remove punctuation
    p_df[p_text] = p_df[p_text].str.replace(r"[^\w\s]", "")
    # remove underscores not picked up as punctuation above
    p_df[p_text] = p_df[p_text].str.replace("_", " ")
    # remove  numbers
    p_df[p_text] = p_df[p_text].str.replace(r"[\d+]", "")
    # lowercase
    p_df[p_text] = p_df[p_text].apply(lambda x: " ".join(x.lower() for x in x.split()))
    return p_df


def preprocessing_nonenglish_paragraph_remove(p_df, p_text):
    # only English language please
    for index, row in p_df.iterrows():
        try:
            if detect(row[p_text]) != "en":
                p_df = p_df.drop(index)
        except Exception:
            # get rid of any garbage
            p_df = p_df.drop(index)
    return p_df


def preprocessing_nonenglish_words_remove(p_df, p_text):
    wordstokeep = nltk.corpus.words.words()
    # Remove word if not in keep list
    wordstokeep = append_to_list(
        wordstokeep, join(get_input_path(), KEEPWORDS_FILENAME)
    )
    wordstokeep = [w.lower() for w in wordstokeep]
    wordstokeep = split_flatten_list(wordstokeep)
    wordstokeep = set(wordstokeep)
    p_df[p_text] = p_df[p_text].apply(
        lambda x: " ".join(x for x in x.split() if x in wordstokeep)
    )
    return p_df


def append_to_list(inlist, inputfile):
    with open(inputfile, "r") as r:
        new_words = r.read().splitlines()
        new_words = [w.lower() for w in new_words]
    return inlist + new_words


def split_flatten_list(inputlist):
    splitlist = [s.split(" ") for s in inputlist]
    return [o for i in splitlist for o in i]


def preprocessing_stopwords_remove(p_df, p_text):
    # Remove english stop words
    stop = stopwords.words("english")
    stop = append_to_list(stop, join(get_input_path(), STOPWORDS_FILENAME))
    p_df[p_text] = p_df[p_text].apply(
        lambda x: " ".join(x for x in x.split() if x not in stop)
    )
    return p_df


def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {
        "J": wordnet.ADJ,
        "N": wordnet.NOUN,
        "V": wordnet.VERB,
        "R": wordnet.ADV,
    }

    return tag_dict.get(tag, wordnet.NOUN)


def preprocessing_lemmatise(p_df, p_text):
    lemmatizer = WordNetLemmatizer()
    p_df[p_text] = p_df[p_text].apply(
        lambda x: " ".join(
            [lemmatizer.lemmatize(x, get_wordnet_pos(x)) for x in x.split()]
        )
    )
    return p_df


def preprocessing_stem(p_df, p_text):
    st = PorterStemmer()
    p_df[p_text] = p_df[p_text].apply(
        lambda x: " ".join([st.stem(word) for word in x.split()])
    )
    return p_df


def preprocessing_empty_text_remove(p_df, p_text):
    # Remove na string
    p_df = p_df[~p_df[p_text].isna()]
    # Remove empty string
    p_df = p_df[p_df[p_text] != ""]
    # Remove entirely whitespace strings in description column
    p_df = p_df[~p_df[p_text].str.isspace()]
    # Remove nan stored as string
    p_df = p_df[p_df[p_text] != "nan"]
    return p_df


def preprocess_query_text(query_text):
    # transform into dataframe
    df = pd.DataFrame([query_text], columns=["description"])
    # Apply specific preprocessing functions
    df = preprocessing_initial_text_clean(df, "description")
    df = preprocessing_nonenglish_words_remove(df, "description")
    df = preprocessing_stopwords_remove(df, "description")
    df = preprocessing_stem(df, "description")
    return preprocessing_empty_text_remove(df, "description")


def preprocess_pipeline(df):
    """
    Default process for taking the raw IATI data dump and processing the text for vectorizing

    Args:
        df: dataframe of the raw IATI data with columns including identifier, description and title

    Returns:
        dataframe of with preprocessed data with _only_ the columns "iati.identifier" and "description"
    """
    df = df[["iati.identifier", "description", "title"]]

    # Remove record in current full dataset with null iati.identifer
    df = df[~df["iati.identifier"].str.isspace()]

    # If both description and title not NA concatenate them into description column
    df.loc[~df["description"].isna() & ~df["title"].isna(), ["description"]] = (
        df["title"] + " " + df["description"]
    )

    # If description is NA replace with title
    df.loc[df["description"].isna(), ["description"]] = df["title"]

    df = df[["iati.identifier", "description"]]

    # preprocessing
    df = preprocessing_initial_text_clean(df, "description")
    df = preprocessing_nonenglish_words_remove(df, "description")
    df = preprocessing_stopwords_remove(df, "description")
    df = preprocessing_stem(df, "description")
    df = preprocessing_empty_text_remove(df, "description")
    return df


if __name__ == "__main__":
    start = time.time()

    # To import full dataset
    df = pd.read_csv(join(get_data_path(), INPUT_DATA_FILENAME), encoding="iso-8859-1")

    df = preprocess_pipeline(df)

    # write out df with reduced records
    df.to_csv(
        join(join(get_data_path(), PROCESSED_RECORDS_FILENAME)),
        index=False,
        encoding="iso-8859-1",
    )

    end = time.time()

    print("completed in {0} seconds".format(end - start))
