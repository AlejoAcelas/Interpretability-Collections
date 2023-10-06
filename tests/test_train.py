
import pytest
import os
import shutil

from src.train.train import Trainer, TrainArgs, load_model
from src.train.model import ModelArgs
from utils_for_tests import SingleNumDataConstructor

def test_trainer():
    trainer = get_trainer_simple_task()
    trainer.train()
    assert trainer.test_accuracy[-1] > 0.9

def test_save_and_load_model():
    trainer = get_trainer_simple_task()
    trainer.test_accuracy = [0.0]
    save_dir = 'tests/test_save_and_load'
    task_name = 'test'

    trainer.save_model(task_name=task_name, dir=save_dir)
    model_name = next((f for f in os.listdir(save_dir) if f.startswith(task_name)), None)
    
    try:
        filename = f"{save_dir}/{model_name}"
        model = load_model(filename, trainer.data_constructor)
    except Exception as e:
        pytest.fail(f"Could not load model from {model_name} with error: {e}")
    finally:
        shutil.rmtree(save_dir)

def get_trainer_simple_task() -> Trainer:
    data_constructor = SingleNumDataConstructor()
    model_args = ModelArgs(n_layers=1, n_heads=1, d_model=4)
    train_args = TrainArgs(epochs=1, trainset_size=10_000, valset_size=1_000, 
                           batch_size=64, use_wandb=False)

    trainer = Trainer(data_constructor=data_constructor, model_args=model_args, train_args=train_args)
    return trainer

test_trainer()