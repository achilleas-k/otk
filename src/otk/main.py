import os
import sys
from typing import Any

import yaml


def replace_define(value, defines):
    """
    Replace a variable in a string with the value from the defines.
    """
    if not isinstance(value, str):
        return value
    if r"${" not in value:
        return value
    print(f"Replacing value {value} ->", end=" ")
    for k, v in defines.items():
        value = value.replace(f"${{{k}}}", v)
    print(value)
    return replace_define(value, defines)


def process_dict(data, defines, cwd):
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
            data.update(process_include(v, defines, cwd))
        elif k.startswith("otk.define"):
            print(f"Defining {v}")
            defines.update(v)
            del data[k]
        elif k.startswith("otk.target") or k.startswith("otk.version"):
            print(f"Dropping {k}")
            del data[k]
        else:
            data[k] = process_value(v, defines, cwd)

    return data


def process_list(data, defines, cwd):
    """
    Process each value in a list.
    """
    for idx, item in enumerate(data.copy()):
        data[idx] = process_value(item, defines, cwd)
    return data


def process_include(path: str, defines: dict, cwd: str) -> dict:
    """
    Load a yaml file and send it to process_value() for processing.
    """
    path = os.path.join(cwd, path)
    with open(path, mode="r", encoding="utf=8") as fp:
        return process_value(yaml.safe_load(fp), defines, cwd=os.path.dirname(path))


def process_value(data, defines, cwd):
    """
    Process a dictionary value based on its type.
    """
    if isinstance(data, dict):
        return process_dict(data, defines, cwd)
    if isinstance(data, list):
        return process_list(data, defines, cwd)
    if isinstance(data, str):
        data = replace_define(data, defines)
    return data


def main():
    path = sys.argv[1]
    defines: dict[str, Any] = {}

    # Treat the entrypoint as an include
    data = process_include(path, defines, cwd=".")

    print(defines)
    print("---")
    print(yaml.dump(data))


if __name__ == "__main__":
    main()
