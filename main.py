import sys
from typing import Any

import yaml


def replace_define(value, defines):
    print(f"Replacing value {value}")
    for k, v in defines.items():
        value = value.replace(f"{{{k}}}", v)
    return value


def process_dict(data, defines):
    for k, v in data.copy().items():
        if k.startswith("otk.include"):
            print(f"Loading {v}")
            del data[k]
            data.update(process_include(v, defines))
        elif k.startswith("otk.define"):
            print(f"Defining: {v}")
            defines.update(v)
        else:
            data[k] = process_value(v, defines)

    return data


def process_list(data, defines):
    for idx, item in enumerate(data.copy()):
        data[idx] = process_value(item, defines)
    return data


def process_include(path: str, defines: dict) -> dict:
    with open(path, mode="r", encoding="utf=8") as fp:
        return process_value(yaml.safe_load(fp), defines)


def process_value(data, defines):
    if isinstance(data, dict):
        return process_dict(data, defines)
    if isinstance(data, list):
        return process_list(data, defines)
    if isinstance(data, str):
        data = replace_define(data, defines)
    return data


def main():
    path = sys.argv[1]
    defines: dict[str, Any] = {}
    data = process_include(path, defines)

    print(defines)
    print("---")
    print(yaml.dump(data))


if __name__ == "__main__":
    main()
