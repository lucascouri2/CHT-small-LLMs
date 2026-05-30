import argparse
from datetime import datetime

from config.config_loader import Config
from config.constants import INSERT_COMMENT_PROMPT, PLACEHOLDER, ALL_RESPONSE
from data.harmful_keywords import HarmfulKeywords
from schemas.llms import LLMs
from schemas.refactoring_type import RefactoringType
from utils.llm_api import LLMFactory
from utils.logger import LoggerConfig
from utils.common_utils import get_rf_prompt_template, assemble_prompt, build_response_json, batch_write_to_json, \
    camel_to_spaces, check_uncompleted_keywords

logger_config = LoggerConfig()
logger = logger_config.get_logger()
Config.load_config()

def main(model_type, use_tool=False, check_uncompleted=False, refactoring_list: list[RefactoringType]=None, bpdl=False):
    logger.info(f"[Harmfulness Testing] LLM: {model_type.value} Start...")
    benign_classes = get_rf_prompt_template()

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    base_path = "file_path.tool_result" if use_tool else "file_path.result"
    result_path = Config.get_path(base_path) / timestamp

    harmful_keywords_dict = HarmfulKeywords("", Config.get_path("file_path.harmful_keywords")).get_dict()
    harmful_keyword_list = list(harmful_keywords_dict.keys())

    model_name_path = model_type.value.replace(":", "_")
    base_path = result_path / model_name_path
    all_response_path = base_path / ALL_RESPONSE

    if check_uncompleted:
        _, time_folder, uncompleted_keywords = check_uncompleted_keywords(harmful_keyword_list)
        if len(uncompleted_keywords) > 0:
            harmful_keyword_list = uncompleted_keywords
            base_path = time_folder / model_name_path
            all_response_path = base_path / ALL_RESPONSE

    for keyword in harmful_keyword_list:
        logger.info(f"Assembling prompt with keyword: {keyword} ...")
        unethical_inputs = assemble_prompt(benign_classes, keyword, refactoring_list)
        refactoring_responses = []
        insert_comment_responses = []
        for each in unethical_inputs:
            # refactoring
            refactoring_response = LLMFactory.get_llm_api(model_type, use_tool).get_response(each)
            refactoring_response_json = build_response_json(
                model_type, each.prompt, each.benign_program, refactoring_response,
                each.refactoring_type, keyword, harmful_keywords_dict[keyword])
            refactoring_responses.append(refactoring_response_json)
            logger.info(refactoring_response_json)

            # insert comment
            each.prompt = INSERT_COMMENT_PROMPT.replace(PLACEHOLDER, f"\"{camel_to_spaces(keyword)}\"")
            insert_comment_response = LLMFactory.get_llm_api(model_type, use_tool).get_response(each)
            insert_comment_response_json = build_response_json(
                model_type, each.prompt, each.benign_program, insert_comment_response,
                each.refactoring_type, keyword, harmful_keywords_dict[keyword])
            insert_comment_responses.append(insert_comment_response_json)
            logger.info(insert_comment_response_json)

        batch_write_to_json(refactoring_responses, base_path / f"{keyword}.json")
        batch_write_to_json(refactoring_responses, str(all_response_path).format("refactoring"))
        batch_write_to_json(insert_comment_responses, str(all_response_path).format("insert_comment"))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run main script with a specific model type.")
    parser.add_argument("--model_type", type=str, default="gpt-4o-mini",
                        help=f"Specify the model type. Available options: {[m.value for m in LLMs]}")
    parser.add_argument("--bpdl", type=lambda x: x.lower() == "true", default=False,
                        help="Whether to use bpdl dataset")
    args = parser.parse_args()

    try:
        selected_model = LLMs(args.model_type)
    except ValueError:
        raise ValueError(f"Invalid model type '{args.model_type}'. Choose from: {[m.value for m in LLMs]}")

    main(selected_model, use_tool=False, check_uncompleted=False, bpdl=args.bpdl)