import pathlib
import sys
from typing import Any

import yaml


def get_value(defines, key):
    if "." not in key:
        return defines[key]

    k, rest = key.split(".", 1)
    return get_value(defines[k], rest)


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
        if value.startswith(r"${") and value.endswith(r"}"):  # full replacement
            return replace_define(get_value(defines, value[2:-1]), defines)
        value = value.replace(f"${{{k}}}", str(get_value(defines, k)))
    print(value)
    return replace_define(value, defines)


def process_defines(data, defines, cur_file):
    for k, v in data.items():
        if k.startswith("otk."):
            return process_dict({k: v}, defines, cur_file)
        if isinstance(defines.get(k), dict):
            define = defines[k]
            define.update(replace_define(v, defines))
        else:
            defines[k] = replace_define(v, defines)
    return defines


def process_dict(data, defines, cur_file):
    """
    Dictionaries are iterated through and both the keys and values are processed.
    Keys define how a value is interpreted:
    - otk.include.* loads the file specified by the value.
    - otk.define.* updates the defines dictionary with all the values under it.
    - Values under any other key are processed as normal values (see process_value()).
    """
    for k, v in data.copy().items():
        # replace any variables in a value immediately before doing anything else
        v = replace_define(v, defines)
        if k.startswith("otk.include"):
            print(f"Loading {v}")
            del data[k]
            v = pathlib.Path(v)
            data.update(process_include(v, defines, cur_file))
        elif k.startswith("otk.define"):
            print(f"Defining {v}")
            defines = process_defines(v, defines, cur_file)
            del data[k]
        elif k.startswith("otk.target"):
            print("Replacing otk.target")
            # just assume all our targets are osbuild for now
            # pop the contents of data[k] one level up
            v = data.pop(k)
            data.update(process_value(v, defines, cur_file))
            data["version"] = "2"
            if "sources" not in data:
                data["sources"] = {}
        elif k.startswith("otk.version"):
            print(f"Dropping {k}")
            del data[k]
        else:
            data[k] = process_value(v, defines, cur_file)

    return data


def process_list(data, defines, cur_file):
    """
    Process each value in a list.
    """
    for idx, item in enumerate(data.copy()):
        data[idx] = process_value(item, defines, cur_file)
    return data


def process_include(path: pathlib.Path, defines: dict, cur_file=pathlib.Path()) -> dict:
    """
    Load a yaml file and send it to process_value() for processing.

    The cur_file argument should be the path to the file that includes the otk.include line, not the path to the new
    file that will start processing after this call.
    """
    # resolve 'path' relative to 'cur_file'
    cur_path = cur_file.parent
    path = cur_path / path
    try:
        with open(path, mode="r", encoding="utf=8") as fp:
            data = yaml.safe_load(fp)
    except FileNotFoundError as fnfe:
        raise FileNotFoundError(f"file {path} referenced from {cur_file} was not found") from fnfe
    if data is not None:
        return process_value(data, defines, cur_file=path)
    return {}


def process_value(data, defines, cur_file):
    """
    Process a dictionary value based on its type.
    """
    if isinstance(data, dict):
        return process_dict(data, defines, cur_file)
    if isinstance(data, list):
        return process_list(data, defines, cur_file)
    if isinstance(data, str):
        data = replace_define(data, defines)
    return data


def main():
    path = pathlib.Path(sys.argv[1])
    defines: dict[str, Any] = {}

    # Treat the entrypoint as an include
    data = process_include(path, defines, cur_file=pathlib.Path())

    print(defines)
    print("---")
    print(yaml.dump(data))


if __name__ == "__main__":
    main()
