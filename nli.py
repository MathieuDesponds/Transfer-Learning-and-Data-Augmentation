from copy import deepcopy
from torch.utils.data import Dataset
from tqdm import tqdm
import jsonlines

import torch
import torch.utils.data
from torch import nn, optim
import numpy as np 
from torch.utils.data import DataLoader, RandomSampler, SequentialSampler
from transformers import AdamW
from transformers import get_constant_schedule_with_warmup

# 1.1
class NLIDataset(Dataset):
    """
    Implement NLIDataset in Pytorch
    """
    def __init__(self, data_repo, tokenizer, sent_max_length=128):
        
        self.label_to_id = {"entailment": 0, "neutral": 1, "contradiction": 2}
        self.id_to_label = {0: "entailment", 1: "neutral", 2: "contradiction"}
        
        self.tokenizer = tokenizer

        ##############################################################################################
        # TODO: Get the special token and token id for PAD from defined tokenizer (self.tokenizer).   #
        ##############################################################################################
        # Replace "..." with your code
        self.pad_token = '[PAD]' 
        self.pad_id = 0
        
        ############################################################################
        #                               END OF YOUR CODE                           #
        ############################################################################

        self.text_samples = []
        self.samples = []
        
        print("Building NLI Dataset...")
        
        with jsonlines.open(data_repo, "r") as reader:
            for sample in tqdm(reader.iter()):
                self.text_samples.append(sample)

                ###############################################################################
                # TODO: build input token indices(input_ids). You can follow these steps:     #
                #       - get split tokens (subtokens) with (self.tokenizer.tokenize);        #
                #       - truncate each list of tokens if it exceeds the sent_max_length;                                   #
                #       - map each text token to id;                                         #
                #       - apply above steps for hypothesis and premise sentences, then        #
                #         combine them with (self.tokenizer.build_inputs_with_special_tokens) #
                ###############################################################################
                # Replace "..." with your code
                p_ids = self.tokenizer.tokenize(sample['premise'])
                p_ids = p_ids if len(p_ids) <= sent_max_length else p_ids[:sent_max_length]
                p_ids = self.tokenizer.encode(p_ids)[1:-1]

                
                h_ids = self.tokenizer.tokenize(sample['hypothesis'])
                h_ids = h_ids if len(h_ids) <= sent_max_length else h_ids[:sent_max_length]
                h_ids = self.tokenizer.encode(h_ids)[1:-1]

                input_ids = self.tokenizer.build_inputs_with_special_tokens(p_ids, h_ids)
                
                ############################################################################
                #                               END OF YOUR CODE                           #
                ############################################################################
                
                label = self.label_to_id.get(sample["label"], None)
                self.samples.append({"ids": input_ids, "label": label})

    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, index):
        return deepcopy(self.samples[index])

    def padding(self, inputs, max_length=-1):
        """
        Pad inputs to the max_length.
        
        INPUT: 
          - inputs: input token ids
          - max_length: the maximum length you should add padding to.
          
        OUTPUT: 
          - pad_inputs: token ids padded to `max_length` """

        if max_length < 0:
            max_length = max(list(map(len, inputs)))
        ##############################################################################################
        # TODO: implement padding.                                                                   #
        ##############################################################################################
        # Replace "..." with your code
        pad_inputs = [inp + [self.pad_id] * (max_length - len(inp)) for inp in inputs]
        
        ############################################################################
        #                               END OF YOUR CODE                           #
        ############################################################################

        return pad_inputs
        
    def collate_fn(self, batch):
        """
        Convert batch inputs to tensor of batch_ids and labels.
        
        INPUT: 
          - batch: batch input, with format List[Dict1{"ids":..., "label":...}, Dict2{...}, ..., DictN{...}]
          
        OUTPUT: 
          - tensor_batch_ids: torch tensor of token ids of a batch, with format Tensor(List[ids1, ids2, ..., idsN])
          - tensor_labels: torch tensor for corresponding labels, with format Tensor(List[label1, label2, ..., labelN])
        """
        ##############################################################################################
        # TODO: implement collabte_fn for batchify input into preferable format.                     #
        ##############################################################################################
        # Replace "..." with your code
        batch_ids = [ex['ids'] for ex in batch]  
        tensor_batch_ids = torch.tensor(self.padding(batch_ids))
        
        batch_labels = [ex['label'] for ex in batch]  
        tensor_labels = torch.tensor(batch_labels).long()
        
        ############################################################################
        #                               END OF YOUR CODE                           #
        ############################################################################

        return tensor_batch_ids, tensor_labels
    
    def get_text_sample(self, index):
        return deepcopy(self.text_samples[index])
    
    def decode_class(self, class_ids):
        """
        Decode to output the predicted class name.
        
        INPUT: 
          - class_ids: index of each class.
          
        OUTPUT: 
          - labels_from_ids: a list of label names. """
        ##############################################################################################
        # TODO: implement class decoding function                              .                     #
        ##############################################################################################
        
        # Replace "..." with your code
        label_name_list = [self.id_to_label[class_id] for class_id in class_ids]

        ############################################################################
        #                               END OF YOUR CODE                           #
        ############################################################################
        
        return label_name_list

# 1.2
def compute_metrics(predictions, gold_labels):
    """
    Compute evaluation metrics (accuracy and F1 score) for NLI task.
    
    INPUT: 
      - gold_labels: real labels;
      - predictions: model predictions.
    OUTPUT: 4 float scores
      - accuracy score (float);
      - f1 score for each class (3 classes in total).
    """
    ##############################################################################
    # TODO: Implement metrics computation.                                       #
    ##############################################################################
    # Replace "..." statement with your code
    acc = sum([1 for i in range(len(gold_labels)) if gold_labels[i] == predictions[i]])/len(gold_labels)
    f1 = [0,0,0]
    for cl in [0,1,2] :
        TP = sum([1 for i in range(len(gold_labels)) if gold_labels[i] == cl and predictions[i] ==cl ])
        TN = sum([1 for i in range(len(gold_labels)) if gold_labels[i] != cl and predictions[i] !=cl ])
        FP = sum([1 for i in range(len(gold_labels)) if gold_labels[i] != cl and predictions[i] ==cl ])
        FN = sum([1 for i in range(len(gold_labels)) if gold_labels[i] == cl and predictions[i] !=cl ])
        
        f1[cl] = 2*TP/(2*TP + FP + FN) 
    ##############################################################################
    #                              END OF YOUR CODE                              #
    ##############################################################################
    return acc, f1[0], f1[1], f1[2]


def train(train_dataset, dev_dataset, model, device, batch_size, epochs,
          learning_rate, warmup_percent, max_grad_norm, model_save_root):
    '''
    Train models with predefined datasets.

    INPUT:
      - train_dataset: dataset for training
      - dev_dataset: dataset for evlauation
      - model: model to train
      - device: hardware device for training ('cpu' or 'cuda')
      - batch_size: batch size for load the dataset
      - epochs: total epochs to train the model
      - learning_rate: learning rate of optimizer
      - warmup_percent: percentage of warmup steps
      - max_grad_norm: maximum gradient for clipping
      - model_save_root: path to save model checkpoints
    '''
    
    train_sampler = RandomSampler(train_dataset)
    train_dataloader = DataLoader(
        train_dataset,
        sampler=train_sampler,
        batch_size=batch_size,
        collate_fn=train_dataset.collate_fn
    )
    
    ###########################################################################################
    # TODO: Define optimizer and learning rate scheduler with learning rate and warmup steps.  # 
    ###########################################################################################
    # Replace "..." statement with your code
    
    # calculate total training steps (epochs * number of data batches per epoch)
    total_steps = epochs * len(train_dataloader)
    warmup_steps = int(warmup_percent * total_steps)
    
    # set up AdamW optimizer and constant learning rate scheduleer with warmup (get_constant_schedule_with_warmup)
    optimizer = torch.optim.AdamW(
           model.parameters(), lr=learning_rate
    )
    scheduler = get_constant_schedule_with_warmup(optimizer = optimizer, num_warmup_steps = warmup_steps)
    
    ##############################################################################
    #                              END OF YOUR CODE                              #
    ##############################################################################
    
    model.zero_grad()
    model.train()
    best_dev_macro_f1 = 0
    save_repo = model_save_root + 'lr{}-warmup{}'.format(learning_rate, warmup_percent)
    
    for epoch in range(epochs):
        
        train_loss_accum = 0
        epoch_train_step = 0
        ##############################################################################################################
        # TODO: Implement the training process. You should calculate the loss then update the model with optimizer.  # 
        #       You should also keep track on the training step and update the learning rate scheduler.              # 
        ##############################################################################################################
        # Replace "..." with your code
        for batch in tqdm(train_dataloader, desc="Training"):
            # Set the gradients of all optimized parameters to zero
            optimizer.zero_grad()

            epoch_train_step += 1

            batch_tuple = tuple(input_tensor.to(device) for input_tensor in batch)
            input_ids, labels = batch_tuple

            # get model's single-batch outputs and loss
            outputs = model(input_ids, labels = labels)
            loss = outputs.loss
            
            # conduct back-proporgation
            loss.backward()
            

            # trancate gradient to max_grad_norm
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm = max_grad_norm)

            train_loss_accum += loss.mean().item()

            # step forward optimizer and scheduler
            optimizer.step()
            scheduler.step()

        ##############################################################################
        #                              END OF YOUR CODE                              #
        ##############################################################################
        
        epoch_train_loss = train_loss_accum / epoch_train_step

        # epoch evaluation
        dev_loss, acc, f1_ent, f1_neu, f1_con = evaluate(dev_dataset, model, device, batch_size)
        macro_f1 = (f1_ent + f1_neu + f1_con) / 3
        
        print(f'Epoch: {epoch} | Training Loss: {epoch_train_loss:.3f} | Validation Loss: {dev_loss:.3f}')
        print(f'Epoch {epoch} NLI Validation:')
        print(f'Accuracy: {acc*100:.2f}% | F1: ({f1_ent*100:.2f}%, {f1_neu*100:.2f}%, {f1_con*100:.2f}%) | Macro-F1: {macro_f1*100:.2f}%')
        
        ##############################################################################################################
        # TODO: Update the highest macro_f1. Save best model and tokenizer to <save_repo>.                           # 
        ##############################################################################################################
        # Replace "..." statement with your code
        if macro_f1 > best_dev_macro_f1:
            best_dev_macro_f1 = macro_f1
            
            model.save_pretrained(save_repo)
            train_dataset.tokenizer.save_pretrained(save_repo)
            print("Model Saved!")
        
        ##############################################################################
        #                              END OF YOUR CODE                              #
        ##############################################################################


def evaluate(eval_dataset, model, device, batch_size, no_labels=False, result_save_file=None):
    '''
    Evaluate the trained model.

    INPUT: 
      - eval_dataset: dataset for evaluation
      - model: trained model
      - device: hardware device for training ('cpu' or 'cuda')
      - batch_size: batch size for load the dataset
      - no_labels: whether the labels should be used as one input to the model
      - result_save_file: path to save the prediction results
    '''
    eval_sampler = SequentialSampler(eval_dataset)
    eval_dataloader = DataLoader(
        eval_dataset,
        sampler=eval_sampler,
        batch_size=batch_size,
        collate_fn=eval_dataset.collate_fn
    )
    
    eval_loss_accum = 0
    eval_step = 0
    batch_preds = []
    batch_labels = []
    
    model.eval()
    
    for batch in tqdm(eval_dataloader, desc="Evaluation"):
        
        eval_step += 1
        with torch.no_grad():
            batch_tuple = tuple(input_tensor.to(device) for input_tensor in batch)
            input_ids, labels = batch_tuple

            #####################################################
            #      TODO: get model outputs, loss and logits.    # 
            #####################################################
            # Replace "..." statement with your code
            if not no_labels:
                outputs = model(input_ids, labels = labels)
            else:
                outputs = model(input_ids)
            loss = outputs.loss
            logits = outputs.logits

            #######################################################
            #                    END OF YOUR CODE                 #
            #######################################################
            
            batch_preds.append(logits.detach().cpu().numpy())
            if not no_labels:
                batch_labels.append(labels.detach().cpu().numpy())
                eval_loss_accum += loss.mean().item()

    #####################################################
    #          TODO: get model predicted labels.        # 
    #####################################################
    # Replace "..." statement with your code
    
    pred_labels = []
    for batch in batch_preds :
      for sample in batch :
        pred_labels.append(np.argmax(sample))


    #####################################################
    #                   END OF YOUR CODE                #
    #####################################################
    
    if result_save_file:
        pred_results = eval_dataset.decode_class(pred_labels)
        with jsonlines.open(result_save_file, mode="w") as writer:
            for sid, pred in enumerate(pred_results):
                sample = eval_dataset.get_text_sample(sid)
                sample["prediction"] = pred
                writer.write(sample)
    
    if not no_labels:
        eval_loss = eval_loss_accum / eval_step
        gold_labels = list(np.concatenate(batch_labels))
        acc, f1_ent, f1_neu, f1_con = compute_metrics(pred_labels, gold_labels)
        return eval_loss, acc, f1_ent, f1_neu, f1_con
    else:
        return None
