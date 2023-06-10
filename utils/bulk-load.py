import uuid

import pandas as pd
import json

# df = pd.read_csv("/Users/RBane7/Downloads/women.csv")
# df.to_json("output/raw.json", orient="records")

f = open("output/raw.json")
array = json.load(f)
valid_keys = [
    "category",
    "subcategory",
    "name",
    "current_price",
    "raw_price",
    "variation_0_image"
]
transact_items = []
for item in array:
    data = {}
    for k, v in item.items():
        if k in valid_keys:
            data["product_id"] = {
                "S": str(uuid.uuid4())
            }
            data[k] = {

                "S": str() if str(v) == "null" else str(v)
            }
            data["quantity"] = {"N": "20"}
    transact_items.append({
        "Put": {
            "Item": data,
            "TableName": "CatalogTable"
        }
    })
with open("output/data.json", "w") as file:
    file.write(json.dumps(transact_items))
f.close()
