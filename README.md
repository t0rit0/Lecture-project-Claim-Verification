# Claim Verification via Knowledge-Grounding and Synthesizing Contrastive Arguments with Large Language Models

[Installation](#installation) | [To Run](#to-run)

## Installation

Install conda environment from `environment.yml` file.

```sh
conda env create -n 3160 --file environment.yml
conda activate 3160
```

Please add your OpenAI key, Google Custom Search API key, and Google Custom Search Engine ID in ```.env``` file.

## To Run

To perform a single claim verification task:

```sh
python main.py --max_token 1024 --temperature 0.7
```

To evaluate:

```sh
python evaluation.py --hover_num_hop "three" --max_token 1024 --temperature 0.7
```


