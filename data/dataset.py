import json

class Dataset:
    def __init__(self, sampled_path, dataset_path, for_finetune=False):
        self.sampled_path = sampled_path
        if dataset_path is not None:
            self.file_path = dataset_path
            self.data = self.read_data(for_finetune)

    def read_data(self, for_finetune=False):
        with open(self.file_path, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)

    @staticmethod
    def filter_data(df, **filters):
        filtered_df = df
        for column, value in filters.items():
            filtered_df = filtered_df[filtered_df[column] == value]
        return filtered_df