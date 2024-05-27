import itertools
import jsonlines
import nltk
nltk.download('stopwords')
stop_words = nltk.corpus.stopwords.words('english')
stop_words.append('uh')

import string
puncs = string.punctuation
def remove_puncs(s) :
    return ''.join([c for c in s if c not in puncs ])

def remove_stopwords(s) :
    return ' '.join([c for c in s.split() if c not in stop_words ])
    
def word_pair_extraction(prediction_files, tokenizer):
    '''
    Extract all word pairs (word_from_premise, word_from_hypothesis) from input as features.
    
    INPUT: 
      - prediction_files: file path for all predictions
      - tokenizer: tokenizer used for tokenization
    
    OUTPUT: 
      - word_pairs: a dict of all word pairs as keys, and label frequency of values. 
    '''
    word_pairs = {}
    label_to_id = {"entailment": 0, "neutral": 1, "contradiction": 2}
    
    for pred_file in prediction_files:
        with jsonlines.open(pred_file, "r") as reader:
            for pred in reader.iter():
                #########################################################
                #          TODO: construct word_pairs dictionary        # 
                #  - tokenize the text with 'tokenizer'                 # 
                #  - pair words as keys (you can use itertools)         #
                #  - count predictions for each paired words as values  # 
                #  - remenber to filter undesired word pairs            # 
                #########################################################
                # Replace "..." statement with your code
                premise = tokenizer.tokenize(remove_stopwords(remove_puncs(pred['premise'])))[1:-1]
                hypothesis = tokenizer.tokenize(remove_stopwords(remove_puncs(pred['hypothesis'])))[1:-1]
                prod = list(itertools.product(premise, hypothesis))
                

                for a,b in prod :
                    if not (a == b or a.startswith('##') or b.startswith('##')):
                        if (a,b) not in word_pairs :
                            word_pairs[(a,b)] = [0,0,0]
                        word_pairs[(a,b)][label_to_id[pred['label']]] +=1
                
                #####################################################
                #                   END OF YOUR CODE                #
                #####################################################
    
    return word_pairs
