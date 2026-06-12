# Teste de nocividade baseado em cobertura para transformação de código com LLMs

## Sumário

- [Conjunto de dados](#conjunto-de-dados)
- [Configuração do ambiente](#configuracao-do-ambiente)
- [Execução com Docker](#execucao-com-docker)
- [Execução dos testes de nocividade](#execucao-dos-testes-de-nocividade)
- [Rotulagem da saída](#rotulagem-da-saida)
- [Resultados](#resultados)
- [Análise estatística](#analise-estatistica)
- [Experimentos adicionais e esclarecimentos](#experimentos-adicionais-e-esclarecimentos)
- [Recursos suplementares](#recursos-suplementares)

## Conjunto de dados

- [Conjunto de palavras-chave nocivas](dataset/harmful_keyword_dataset.csv)
- [Hurtlex](https://github.com/valeriobasile/hurtlex)
- [Weaponized Word](https://weaponizedword.org/)
- [Conjunto de Programas Benignos (BPD)](dataset/refactoring_prompt_template.csv)
- [Conjunto de Programas Benignos em grande escala (BPD-L)](dataset/refactoringminers_init_classes_final.csv)

## Configuração do ambiente

1. Adicione sua chave da API da OpenAI em [config.yml](config/config.yml)
2. Instale o [Ollama](https://ollama.com/) e baixe os LLMs desejados
3. Instale as dependências Python necessárias:

   ```bash
   pip install -r requirements.txt
   ```

## Execução com Docker

Docker é a forma recomendada de executar este projeto, pois ele gerencia automaticamente o servidor Ollama e o ambiente Python.

**Pré-requisitos:** [Docker](https://docs.docker.com/get-docker/) e Docker Compose. Para aceleração por GPU, é necessário uma GPU NVIDIA com o [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) (o `docker-compose.yml` já inclui a reserva de GPU; remova o bloco `deploy` se você não tiver uma GPU).

### 1. Configure a chave da API

Edite [.env](.env) e defina sua chave da OpenAI (pule esta etapa se você não for usar o GPT-4o-mini):

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Construa e inicie o Ollama

```bash
docker compose build
docker compose up ollama -d
```

### 3. Baixe os modelos desejados

```bash
# Modelos originais (6–7B)
docker exec ollama_server ollama pull codellama:7b
docker exec ollama_server ollama pull qwen2.5-coder:7b
docker exec ollama_server ollama pull codegemma:7b
docker exec ollama_server ollama pull deepseek-coder:6.7b

# Modelos pequenos (1–3B)
docker exec ollama_server ollama pull qwen2.5-coder:1.5b
docker exec ollama_server ollama pull deepseek-coder:1.3b
```

### 4. Execute os testes de nocividade

```bash
docker compose run cht python main.py --model_type qwen2.5-coder:1.5b
docker compose run cht python main.py --model_type codellama:7b --bpdl True
```

### 5. Execute a análise

```bash
docker compose run cht python analysis.py 2026-05-31_01-33-53
```

Os resultados são gravados em `./result/` na máquina host por meio do volume montado.

---

## Execução dos testes de nocividade sem Docker

Para avaliar um modelo (por exemplo, `codellama:7b`):

```bash
python main.py --model_type codellama:7b
```

Para usar o BPD-L (padrão: BPD):

```bash
python main.py --model_type codellama:7b --bpdl True
```

Veja opções adicionais:

```bash
python main.py --help
```

Os resultados dos testes são salvos no diretório `result/`.

## Rotulagem da saída

Veja [analysis.py](./analysis.py) para a lógica de rotulagem de dano na saída, incluindo a lista de palavras-chave de alerta do LLM.

## Resultados

Os resultados abaixo vêm de [run_extra_analysis.ipynb](result/small_llms_experiments/run_extra_analysis.ipynb).

## Análise estatística

### Inserção de comentário vs. refatoração

| Modelo               | Qui²     | p-valor        | Significativo |
|----------------------|----------|----------------|-------------|
| deepcoder_1.5b       | 98.16    | 3.37e-01       | False       |
| opencoder_1.5b       | 128.89   | 6.75e-14       | True        |
| qwen2.5-coder_1.5b   | 194.97   | 3.30e-09       | True        |

### Frases vs. palavras isoladas

| Modelo               | Qui²     | p-valor        | Significativo |
|----------------------|----------|----------------|-------------|
| deepcoder_1.5b       | 54.40    | 3.77e-04       | True        |
| opencoder_1.5b       | 66.76    | 2.16e-11       | True        |
| qwen2.5-coder_1.5b   | 89.81    | 1.55e-09       | True        |


## Recursos suplementares

- **Modelos de prompt**: disponíveis em [prompt_template.md](./prompt_template.md).
- **Todas as refatorações**: os 66 métodos estão listados em [all_66_refactorings.md](./all_66_refactorings.md).
- **Material suplementar**: idêntico ao arquivo enviado com o artigo; disponível [aqui](harmfulness_testing_supplementary_material.pdf).
