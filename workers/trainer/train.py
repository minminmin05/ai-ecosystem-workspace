import asyncio
import shutil
import tempfile
from pathlib import Path

import evaluate
import mlflow
import numpy as np
from datasets import load_from_disk
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
    Trainer,
    TrainerCallback,
    TrainingArguments,
    pipeline,
)

from config import settings
from logger import get_logger


MODEL_CHECKPOINT = "distilbert-base-uncased"
DATASET_MINIO_PREFIX = "datasets/conll2003"
MLFLOW_EXPERIMENT_NAME = "token-classification"

# mirror ของ dataset ที่ใช้ (lhoestq/conll2003) เก็บ ner_tags เป็น int ธรรมดา ไม่มี ClassLabel
# metadata ติดมาด้วย เลยต้อง hardcode รายชื่อ label เอง — เรียงลำดับตรงกับ conll2003 ต้นฉบับ
LABEL_NAMES = ["O", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-LOC", "I-LOC", "B-MISC", "I-MISC"]

logger = get_logger("trainer_worker")

mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)


class _LoggingCallback(TrainerCallback):
    """ส่ง log ของ Trainer (loss, metric ต่อ step/epoch) เข้า custom logger แทนที่จะพิมพ์แค่ stdout เฉยๆ"""

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            logger.info(f"step={state.global_step} {logs}")


def _s3_storage_options() -> dict:
    protocol = "https" if settings.minio_secure else "http"
    return {
        "key": settings.minio_access_key,
        "secret": settings.minio_secret_key,
        "client_kwargs": {"endpoint_url": f"{protocol}://{settings.minio_endpoint}"},
    }


def _tokenize_and_align_labels(examples, tokenizer):
    tokenized_inputs = tokenizer(examples["tokens"], truncation=True, is_split_into_words=True)
    all_labels = examples["ner_tags"]
    new_labels = []
    for i, labels in enumerate(all_labels):
        word_ids = tokenized_inputs.word_ids(i)
        previous_word_id = None
        label_ids = []
        for word_id in word_ids:
            if word_id is None:
                label_ids.append(-100)
            elif word_id != previous_word_id:
                label_ids.append(labels[word_id])
            else:
                label_id = labels[word_id]
                # B- (เลขคี่) ต้องเปลี่ยนเป็น I- (เลขคู่ถัดไป) สำหรับ subword ต่อจาก token แรก
                if label_id % 2 == 1:
                    label_id += 1
                label_ids.append(label_id)
            previous_word_id = word_id
        new_labels.append(label_ids)
    tokenized_inputs["labels"] = new_labels
    return tokenized_inputs


def _train_sync(job_data: dict) -> dict:
    epochs = job_data.get("epochs", 1)
    logger.info(f"=== เริ่มเทรน token classification: epochs={epochs} ===")

    logger.info(f"โหลด dataset จาก MinIO: s3://{settings.minio_bucket}/{DATASET_MINIO_PREFIX}")
    raw_datasets = load_from_disk(
        f"s3://{settings.minio_bucket}/{DATASET_MINIO_PREFIX}",
        storage_options=_s3_storage_options(),
    )

    label_names = LABEL_NAMES
    id2label = {i: name for i, name in enumerate(label_names)}
    label2id = {name: i for i, name in enumerate(label_names)}
    logger.info(f"labels: {label_names}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_CHECKPOINT)

    tokenized_datasets = raw_datasets.map(
        lambda examples: _tokenize_and_align_labels(examples, tokenizer),
        batched=True,
        remove_columns=raw_datasets["train"].column_names,
    )

    model = AutoModelForTokenClassification.from_pretrained(
        MODEL_CHECKPOINT, id2label=id2label, label2id=label2id
    )

    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)
    metric = evaluate.load("seqeval")

    def compute_metrics(eval_preds):
        logits, labels = eval_preds
        predictions = np.argmax(logits, axis=-1)
        true_labels = [[label_names[l] for l in label if l != -100] for label in labels]
        true_predictions = [
            [label_names[p] for p, l in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]
        results = metric.compute(predictions=true_predictions, references=true_labels)
        return {
            "precision": results["overall_precision"],
            "recall": results["overall_recall"],
            "f1": results["overall_f1"],
            "accuracy": results["overall_accuracy"],
        }

    work_dir = Path(tempfile.mkdtemp())
    output_dir = work_dir / "output"

    args = TrainingArguments(
        output_dir=str(output_dir),
        eval_strategy="epoch",
        save_strategy="no",
        learning_rate=2e-5,
        num_train_epochs=epochs,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        weight_decay=0.01,
        logging_steps=50,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        data_collator=data_collator,
        processing_class=tokenizer,
        compute_metrics=compute_metrics,
        callbacks=[_LoggingCallback()],
    )

    train_result = trainer.train()
    eval_result = trainer.evaluate()
    logger.info(f"เทรนเสร็จ train_loss={train_result.training_loss:.4f} eval={eval_result}")

    # ห่อโมเดล+tokenizer ที่เทรนเสร็จเป็น pipeline พร้อมใช้งานจริง (aggregation_strategy="simple"
    # รวม subword token ที่ทำนายเป็น entity เดียวกันให้เป็นคำเต็มๆ) แล้ว log เข้า MLflow โดยตรง
    # ไม่ save ลง disk/tar เองอีกต่อไป — mlflow.transformers.log_model() จัดการ serialize +
    # อัปโหลดเข้า MinIO (ที่ตั้งเป็น artifact store ของ MLflow ไว้แล้ว) ให้ทั้งหมด
    inference_pipeline = pipeline(
        "token-classification",
        model=trainer.model,
        tokenizer=tokenizer,
        aggregation_strategy="simple",
    )

    with mlflow.start_run():
        mlflow.log_params({"model_checkpoint": MODEL_CHECKPOINT, "epochs": epochs})
        mlflow.log_metrics({k: v for k, v in eval_result.items() if isinstance(v, (int, float))})
        mlflow.transformers.log_model(
            transformers_model=inference_pipeline,
            name="model",
            registered_model_name=settings.mlflow_model_name,
        )
    logger.info(
        f"log โมเดลเข้า MLflow สำเร็จ (experiment={MLFLOW_EXPERIMENT_NAME}, "
        f"registered_model_name={settings.mlflow_model_name}) — MLflow Model Registry "
        "จัดการ version ของโมเดลให้เองในตัว"
    )

    shutil.rmtree(work_dir, ignore_errors=True)

    return {"eval": eval_result, "registered_model_name": settings.mlflow_model_name}


async def train_token_classification(ctx, job_data: dict) -> dict:
    """ARQ job function ต้องเป็น async def แต่ trainer.train() เป็นงาน CPU/GPU-bound แบบ
    blocking ล้วน (ใช้เวลาหลายนาที) ถ้าเรียกตรงๆ จะบล็อก event loop ของ ARQ worker เอง
    (กระทบ heartbeat/health-check ที่ ARQ ใช้บอก Redis ว่า worker ยังทำงานอยู่) เลย offload
    ไปรันใน thread executor แทน เหมือนหลักการเดียวกับที่ FastAPI รัน sync route ใน threadpool"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _train_sync, job_data)
