import re
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from config.constants import NO_RESPONSE, KEY_NOT_EXIST, PLACEHOLDER
from schemas.benign_class_info import BenignClassInfo, ClassDetail, ResponseContent
from config.config_loader import Config
from schemas.llms import LLMs
from schemas.refactoring_type import RefactoringType
from schemas.unethical_input import UnethicalInput
from utils.logger import LoggerConfig

logger_config = LoggerConfig()
logger = logger_config.get_logger()
Config.load_config()

def get_rf_prompt_template(bpdl=False) -> list[BenignClassInfo]:
    benign_program_prompt = []
    if bpdl:
        df = pd.read_csv(Config.get_path("file_path.bpdl"), encoding='utf-8')
    else:
        df = pd.read_csv(Config.get_path("file_path.refactoring_prompt_template"), encoding='utf-8')
    for index, row in df.iterrows():
        try:
            response_content_str = json.loads(row["response_content"], strict=False)["classes"][0]
            classes = [
                ClassDetail(
                    class_name=response_content_str["className"],
                    content=response_content_str["content"])
            ]
            response_content = ResponseContent(classes=classes)
        except (json.JSONDecodeError, KeyError):
            response_content = row["response_content"]

        benign_class_info = BenignClassInfo(
            html_url = row["html_url"],
            response_content = response_content,
            compile_result = 0 if pd.isna(row["compile_result"]) else int(row["compile_result"]),
            input_program_loc = 0 if pd.isna(row["input_program_loc"]) else int(row["input_program_loc"]),
            refactoring_type = row["refactoring_type"],
            prompt = row["prompt"],
        )
        benign_program_prompt.append(benign_class_info)
    return benign_program_prompt


def assemble_prompt(benign_class_info: list[BenignClassInfo], unethical_keyword: str,
                    specified_refactoring: Optional[list[RefactoringType]]=None) -> list[UnethicalInput]:
    unethical_inputs = []
    for each in benign_class_info:
        if specified_refactoring and each.refactoring_type.lower() not in specified_refactoring:
            continue
        benign_class_content = getattr(each.response_content, "classes", [])[0].content \
            if hasattr(each.response_content, "classes") else str(each.response_content)
        unethical_input = UnethicalInput(
            prompt=each.prompt.replace(PLACEHOLDER, to_camel_case(unethical_keyword)),
            benign_program=benign_class_content,
            refactoring_type=each.refactoring_type
        )
        unethical_inputs.append(unethical_input)
    return unethical_inputs


def get_root_path():
    return Path(__file__).resolve().parent


def build_response_json(model_type, prompt, benign_program, response,
                        refactoring_type, unethical_keyword, keyword_json):
    content_key = "content" if model_type == LLMs.GPT_4O_MINI else "response"
    refusal_key = "refusal" if model_type == LLMs.GPT_4O_MINI else None

    response_dict = {
        "prompt": prompt,
        "benign_program": benign_program,
        "content": response.get(content_key, KEY_NOT_EXIST) if response else NO_RESPONSE,
        "refactoring_type": refactoring_type,
        "unethical_keyword": unethical_keyword,
        "keyword_category": keyword_json["category"],
        "offensiveness": keyword_json["offensiveness"],
        "source": keyword_json["source"],
        "finish_reason": response.get("finish_reason", KEY_NOT_EXIST) if response else NO_RESPONSE,
        "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
        "keyword_from_identify_tool": response.get("keyword_from_identify_tool", KEY_NOT_EXIST) if response else NO_RESPONSE,
        "tool_output": response.get("tool_output", KEY_NOT_EXIST) if response else NO_RESPONSE,
    }

    if model_type == LLMs.GPT_4O_MINI:
        response_dict["refusal"] = response.get(refusal_key, KEY_NOT_EXIST) if response else NO_RESPONSE
    return response_dict


def batch_write_to_json(data, file_path=None):
    if file_path is None:
        file_path = Config.get_path("file_path.response_json")
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(file_path, "r") as file:
            existing_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    existing_data.extend(data)
    with open(file_path, "w") as file:
        json.dump(existing_data, file, indent=4)


def to_camel_case(term):
    words = re.split(r'[ -]+', term)
    return words[0].lower() + ''.join(word.capitalize() for word in words[1:])


def camel_to_spaces(camel_case_str):
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', camel_case_str)
    result = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', result)
    return result.lower()


def get_latest_folder(result_path: Path) -> Optional[Path]:
    """ get latest folder under the result_path """
    if not result_path.is_dir():
        return None
    folders = [folder for folder in result_path.iterdir() if folder.is_dir()]
    return max(folders, key=lambda x: x.name, default=None)


def get_json_names(folder: Path) -> set:
    return {f.stem for f in folder.glob("*.json") if not f.stem.startswith("all")}


def check_uncompleted_keywords(full_unethical_keywords,
                               result_path: Path = Path(Config.get_path("file_path.result"))):
    latest_folder = get_latest_folder(result_path)
    if latest_folder is None:
        return result_path, None, full_unethical_keywords

    llm_folder = next(latest_folder.iterdir(), None)
    if llm_folder is None or not llm_folder.is_dir():
        return latest_folder, None, full_unethical_keywords

    json_files = get_json_names(llm_folder)
    uncompleted_keywords = set(full_unethical_keywords) - json_files
    return llm_folder, latest_folder, list(uncompleted_keywords)


def check_completion_status(full_keywords, result_folder: Path):
    if not result_folder.is_dir():
        return False, full_keywords
    json_names = get_json_names(result_folder)
    uncompleted_keywords = set(full_keywords) - json_names
    return len(uncompleted_keywords) == 0, list(uncompleted_keywords)


def read_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def write_json_file(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def get_loc(code: str) -> int:
    return len(code.splitlines()) if code else 0


def extract_code(content: str) -> str:
    try:
        parsed = json.loads(content, strict=False)
        return parsed["classes"][0]["content"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return content


def analyze_program_loc(csv_path: str = None):
    if csv_path is None:
        csv_path = Config.get_path("file_path.refactoring_prompt_template")
    df = pd.read_csv(csv_path, encoding='utf-8')

    locs = []
    for _, row in df.iterrows():
        code = extract_code(row["response_content"])
        loc = get_loc(code)
        locs.append(loc)
        print(f"[EACH CODE INFO] LoC: {loc} Program:\n{code}\n")

    if locs:
        print(f"Min LOC: {min(locs)}, Max LOC: {max(locs)}, Total LOC: {sum(locs)}, Avg LOC: {sum(locs)/len(locs):.2f}")
    else:
        print("No valid code found.")


if __name__ == "__main__":
    analyze_program_loc()
