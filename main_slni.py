import os
import re
import json
import torch
from torch.utils import data
import params
import utils
from torch.utils.tensorboard import SummaryWriter
from bert_model import BertTransformer
from transformers import BertConfig
from training import train_snli
import transformer_model
import basic_rnn
import rnn_combined_model
import snli_dataset
import pandas as pd
import datetime


def run_training_by_config(model, train_dataset, val_dataset, device, model_name, config_dict, results_dict):


    if config_dict['checkpoint'] is not None:
        checkpoint_file = config_dict['checkpoint']
    else:
        checkpoint_file = None

    print()
    writer_name = os.path.join(params.RUNS_DIR, model_name +'_'+ config_dict['run_name'])
    writer = SummaryWriter(writer_name)

    run_history = train_snli(model, train_dataset, val_dataset, device, model_name, config_dict, writer,params.MODELS_DIR,checkpoint_file)


    for ind in range(len(run_history['Epoch'])):
        results_dict['run_name'].append(config_dict['run_name'])
        results_dict['lr'].append(config_dict['lr'])
        results_dict['checkpoint'].append(config_dict['checkpoint'])
        results_dict['model'].append(model_name)
        results_dict['train_loss'].append(run_history['Train loss'][ind])
        results_dict['val_loss'].append(run_history['Val loss'][ind])
        results_dict['val_accuracy'].append(run_history['Val accuracy'][ind])
        results_dict['epochs'].append(run_history['Epoch'][ind])
        #results_dict['batch_size'].append(config_dict['batch_size'])
        results_dict['embedding_type'].append(config_dict['embedding_type'])
        results_dict['train_iter'].append(run_history['Train iter'])
        results_dict['val_iter'].append(run_history['Val iter'])


    writer.add_hparams(
        hparam_dict={"LR": config_dict["lr"], "Model name": model_name, "Embeddings": config_dict["embedding_type"]},
        metric_dict={"Val Accuracy": run_history['Val accuracy'][-1], "Val loss": run_history['Val loss'][-1], "Epochs": run_history['Epoch'][-1]},
        run_name=config_dict['run_name'])
    writer.close()

    return results_dict




def train_Bert(train_dataset, val_dataset, config_search, device,constant_config):

    results = {'run_name': [], 'lr': [], 'model': [], 'train_loss': [], 'val_loss': [], 'val_accuracy': [],
               'checkpoint': [],'epochs':[], 'train_iter':[], 'val_iter':[],'embedding_type':[]}

    model_name='Bert'
    train_dataset.change_tokenizer_and_vocab(tokenizer='bert', eng_mode='one_sentence')
    val_dataset.change_tokenizer_and_vocab(tokenizer='bert', eng_mode='one_sentence')


    config=config_search

    for config_dict in config:

        model=BertTransformer(**constant_config).to(device)
        results=run_training_by_config(model, train_dataset, val_dataset, device, model_name, config_dict, results)


    results_pd = pd.DataFrame.from_dict(results)
    date_str = datetime.datetime.now().strftime("%m_%d_%Y_%H")
    results_file = os.path.join(params.RESULTS_DIR, model_name + date_str)
    results_pd.to_csv(results_file)

    return results_pd




def train_Transformer(train_dataset, val_dataset, config_search, device,constant_config):
    model_name = 'Transformer'

    results = {'run_name': [], 'lr': [], 'model': [], 'train_loss': [], 'val_loss': [], 'val_accuracy': [],
               'checkpoint': [], 'epochs': [], 'train_iter': [], 'val_iter': [], 'embedding_type': []}

    train_dataset.change_tokenizer_and_vocab(tokenizer='spacy', eng_mode='one_sentence')
    val_dataset.change_tokenizer_and_vocab(tokenizer='spacy', eng_mode='one_sentence')


    config = config_search
    for config_dict in config:

        model = transformer_model.SNLI_Transformer(train_dataset.vocab, device, use_pretrained_embeddings=(False if config_dict['embedding_type']==None else True), **constant_config).to(device)
        results = run_training_by_config(model, train_dataset, val_dataset, device, model_name, config_dict, results)


    results_pd = pd.DataFrame.from_dict(results)
    date_str = datetime.datetime.now().strftime("%m %d %Y, %H")
    results_file = os.path.join(params.RESULTS_DIR, model_name + date_str)
    results_pd.to_csv(results_file)
    return results_pd


def train_RNNCombine(train_dataset, val_dataset, config_search, device, constant_config):
    model_name = 'RNNCombine'

    results = {'run_name': [], 'lr': [], 'model': [], 'train_loss': [], 'val_loss': [], 'val_accuracy': [],
               'checkpoint': [], 'epochs': [], 'train_iter': [], 'val_iter': [], 'embedding_type': []}

    train_dataset.change_tokenizer_and_vocab(tokenizer='spacy', eng_mode='two_sentence')
    val_dataset.change_tokenizer_and_vocab(tokenizer='spacy', eng_mode='two_sentence')


    config = config_search

    for config_dict in config:
        model = rnn_combined_model.RNN_Combined_Model(train_dataset.vocab, device, use_pretrained_embeddings=(False if config_dict['embedding_type']==None else True),**constant_config).to(device)
        results = run_training_by_config(model, train_dataset, val_dataset, device, model_name, config_dict, results)


    results_pd = pd.DataFrame.from_dict(results)
    date_str = datetime.datetime.now().strftime("%m %d %Y, %H")
    results_file = os.path.join(params.RESULTS_DIR, model_name + date_str)
    results_pd.to_csv(results_file)

    return results_pd


def train_BasicRNN(train_dataset, val_dataset, config_search, device, constant_config):
    model_name = 'BasicRNN'

    results = {'run_name': [], 'lr': [], 'model': [], 'train_loss': [], 'val_loss': [], 'val_accuracy': [],
               'checkpoint': [], 'epochs': [], 'train_iter': [], 'val_iter': [], 'embedding_type': []}

    train_dataset.change_tokenizer_and_vocab(tokenizer='spacy', eng_mode='one_sentence')
    val_dataset.change_tokenizer_and_vocab(tokenizer='spacy', eng_mode='one_sentence')

    config = config_search

    for config_dict in config:
        model = basic_rnn.Basic_RNN(train_dataset.vocab, device, use_pretrained_embeddings=(False if config_dict['embedding_type']==None else True), **constant_config).to(device)
        results = run_training_by_config(model, train_dataset, val_dataset, device, model_name, config_dict, results)


    results_pd = pd.DataFrame.from_dict(results)
    date_str = datetime.datetime.now().strftime("%m %d %Y, %H")
    results_file = os.path.join(params.RESULTS_DIR, model_name + date_str)
    results_pd.to_csv(results_file)

    return results_pd



def prepare_dataset(device):

    train_dataset = snli_dataset.SNLIDataset(params.TRAIN_DATA_DIR, device=device)
    print(f"Train dataset size: {len(train_dataset)} ")

    val_dataset = snli_dataset.SNLIDataset(params.VAL_DATA_DIR, device=device)
    print(f"Validation dataset size: {len(val_dataset)} ")

    return train_dataset, val_dataset


def tune_models(device):

    train_dataset, val_dataset=prepare_dataset(device)

    train_Bert(train_dataset, val_dataset, device)

    train_Transformer(train_dataset, val_dataset, device)

    #tune_BasicRNN(train_dataset, val_dataset, device)
    train_RNNCombine(train_dataset, val_dataset, device)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    device = torch.device('cpu')
    if (torch.cuda.is_available()):
        device = torch.device('cuda')
        #if torch.cuda.device_count()>1:
        #    parallel=True

    print(device)

    tune_models(device)

    #show_best_results_on_test()





