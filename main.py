import sys
from typing import Any

import yaml


def replace_define(value, defines):
    """
    Replace a variable in a string with the value from the defines.
    """
    print(f"Replacing value {value}")
    for k, v in defines.items():
        value = value.replace(f"{{{k}}}", v)
    return value


def process_dict(data, defines):
    """
    Dictionaries are iterated through and both the keys and values are processed.
    Keys define how a value is interpreted:
    - otk.include.* loads the file specified by the value.
    - otk.define.* updates the defines dictionary with all the values under it.
    - Values under any other key are processed as normal values (see process_value()).
    """
    for k, v in data.copy().items():
        if k.startswith("otk.include"):
            print(f"Loading {v}")
            del data[k]
            data.update(process_include(v, defines))
        elif k.startswith("otk.define"):
            print(f"Defining: {v}")
            defines.update(v)
            del data[k]
        else:
            data[k] = process_value(v, defines)

    return data


def process_list(data, defines):
    """
    Process each value in a list.
    """
    for idx, item in enumerate(data.copy()):
        data[idx] = process_value(item, defines)
    return data


def process_include(path: str, defines: dict) -> dict:
    """
    Load a yaml file and send it to process_value() for processing.
    """
    with open(path, mode="r", encoding="utf=8") as fp:
        return process_value(yaml.safe_load(fp), defines)


def process_value(data, defines):
    """
    Process a dictionary value based on its type.
    """
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

    # Treat the entrypoint as an include
    data = process_include(path, defines)

    print(defines)
    print("---")
    print(yaml.dump(data))


if __name__ == "__main__":
    main()
