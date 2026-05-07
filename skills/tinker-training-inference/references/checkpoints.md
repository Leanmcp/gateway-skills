# Checkpoints: the two kinds, and everything you can do with them

The distinction that causes the most confusion, and the most 400s.

## Two types, not interchangeable

| | `sampler_weights/…` | `weights/…` |
| --- | --- | --- |
| created by | `save_weights_for_sampler(name)` <br> `save_weights_and_get_sampling_client(name)` | `save_state(name)` |
| contains | LoRA weights | LoRA weights **+ optimizer state** |
| sample from it | ✅ | ❌ |
| download / export | ✅ | ❌ |
| resume training | ❌ (Adam restarts at zero) | ✅ |

Path format: `tinker://<run-id>/<type>/<name>`

Trying to download a training-state checkpoint gives:

```
400 - Checkpoint weights/<name> is not a sampler weights checkpoint.
The archive endpoint only supports sampler weights checkpoints
(checkpoint_id starting with 'sampler_weights/').
```

**Save both.** They are cheap relative to the run that produced them, and each
covers a failure the other does not: `save_state` every N steps so a crash costs
one interval instead of the whole run, `save_weights_for_sampler` at every point
you might want to evaluate or ship.

Re-using a name makes a new version rather than overwriting.

## In code

```python
# resumable
resp = training_client.save_state(name="iter-40").result()
print(resp.path)                       # tinker://<run>/weights/iter-40

# servable + downloadable
resp = training_client.save_weights_for_sampler(name="final").result()
print(resp.path)                       # tinker://<run>/sampler_weights/final

# both at once: persist AND get a client that samples exactly those weights
sampler = training_client.save_weights_and_get_sampling_client(name="iter-40")
```

## Resuming

```python
training_client = service_client.create_training_client_from_state_with_optimizer(
    "tinker://<run>/weights/iter-40")
```

Use the `_with_optimizer` form. Loading weights without the optimizer state
restarts Adam's moments at zero, which shows up as a loss spike exactly at the
resume point and is easy to misread as a data problem.

## The CLI

The command is `tinker checkpoint` — **singular**. `tinker checkpoints` errors
with `No such command`.

```bash
tinker checkpoint list                          # recent runs (default 20)
tinker checkpoint list --run-id <run-id>
tinker checkpoint list --limit 50
tinker checkpoint list -f json                  # table | json

tinker checkpoint info <path>

tinker checkpoint download <tinker-path> -o <dir> [--force]

tinker checkpoint push-hf <path> -r <user/repo> [--public] [--create-pr]
tinker checkpoint publish <path>                # make public
tinker checkpoint unpublish <path>

tinker checkpoint set-ttl <path> --ttl <seconds>    # minimum 3600
tinker checkpoint set-ttl <path> --remove          # keep forever
tinker checkpoint delete <path> [<path> ...]       # permanent
```

`tinker -h` / `tinker checkpoint -h` prints live help for your installed version.
Docs: <https://tinker-docs.thinkingmachines.ai/tinker/cli/checkpoint/>

**TTLs are worth setting deliberately.** A long sweep leaves hundreds of
checkpoints; the ones you might publish should get `--remove`, and the
per-iteration ones a TTL, before you forget which is which.

## Downloading in Python

```python
save_resp = training_client.save_weights_for_sampler(name=name).result()
rest_client = service_client.create_rest_client()
url_resp = rest_client.get_checkpoint_archive_url_from_tinker_path(save_resp.path).result()

with urllib.request.urlopen(url_resp.url, timeout=120) as r, open(tar_path, "wb") as f:
    shutil.copyfileobj(r, f)
with tarfile.open(tar_path, "r") as tar:
    tar.extractall(path=dest_dir)
```

Three steps: persist as *sampler* weights → ask REST for a short-lived signed
URL → stream and extract the tar.

## What you actually downloaded

A **LoRA adapter** (~350 MB for an 8B), not a model. It is the low-rank diff and
cannot run on its own.

To get a standalone model, merge it into the base:

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

base = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.bfloat16)
merged = PeftModel.from_pretrained(base, adapter_dir).merge_and_unload()
merged.save_pretrained(out_dir)
AutoTokenizer.from_pretrained(BASE_MODEL).save_pretrained(out_dir)
```

Requirements: `torch transformers peft accelerate safetensors`; ~16 GB base
download + ~16 GB output; ~32 GB RAM to merge on CPU (a GPU is faster but not
required). The result is a normal HuggingFace directory — run it offline,
convert to GGUF for Ollama, upload anywhere.

You do **not** need any of this to keep using the model on Tinker. Point a
sampling client at the `tinker://` path.

## Naming

Include what distinguishes the checkpoint from its neighbours: the run, the
iteration, the arm. `iter-40` alone is ambiguous the moment you have two arms.
Something like `<experiment>-<arm>-iter40` reads correctly in
`tinker checkpoint list` six weeks later, which is the only time you will read it.

And record the **prompt format** (raw completion vs chat template) alongside the
path in your run config — a checkpoint whose format you have to guess is a
checkpoint you will re-train. See [training-sft.md](training-sft.md).
