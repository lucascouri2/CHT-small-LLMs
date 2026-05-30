import pandas as pd

from config.config_loader import Config
from data.dataset import Dataset

Config.load_config()

class HarmfulKeywords(Dataset):
    def read_data(self, for_finetune=False):
        df = pd.read_csv(self.file_path)
        df.columns = df.columns.str.lower()
        dtype_mapping = {
            "term": "string",
            "category": "category",
            "offensiveness": "category",
            "source": "category",
        }

        df = df.astype(dtype_mapping)
        return df.map(lambda x: x.lower() if isinstance(x, str) else x)

    def get_dict(self):
        columns = ["category", "offensiveness", "source"]
        return self.data.set_index("term")[columns].to_dict(orient="index")

    def get_category_dict(self):
        columns = ["term", "offensiveness", "source"]
        return (self.data.groupby("category")[columns]
                .apply(lambda x : x.to_dict(orient="records"))
                .to_dict())