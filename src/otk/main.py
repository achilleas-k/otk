import pathlib
import re
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
    Replace variables in a string. If the string consists of a single `${name}` value then we return the object it
    refers to by looking up its name in the defines.

    If the string has anything around a variable such as `foo${name}-${bar}` then we replace the values inside the
    string. This requires the type of the variable to be replaced to be either str, int, or float.
    """

    # return early if it's not a string
    if not isinstance(value, str):
        return value

    # return early if there's no variable symbol
    if "$" not in value:
        return value

    orig = value
    bracket = r"\$\{%s\}"
    pattern = bracket % r"(?P<name>[a-zA-Z0-9-_\.]+)"

    # If there is a single match and its span is the entire value then we return the matching value from defines
    # directly.
    if match := re.fullmatch(pattern, value):
        return get_value(defines, match.group("name"))

    # Let's find all matches if there are any. We use `list(re.finditer(...))`
    # to get a list of match objects instead of `re.findall` which gives a list
    # of matchgroups.

    # If there are multiple matches then we always interpolate strings.
    if matches := list(re.finditer(pattern, value)):
        for match in matches:
            name = match.group("name")
            data = get_value(defines, name)

            # We know how to turn ints and floats into str's
            if isinstance(data, (int, float)):
                data = str(data)

            # Any other type we do not
            if not isinstance(data, str):
                raise TypeError(
                    f"string variable resolves to an incorrect type, expected int, float, or str but got {repr(data)}"
                )

            # Replace all occurrences of this name in the str

            # NOTE: this means we can recursively replace names, do we want that?
            value = re.sub(bracket % re.escape(name), data, value)

        print(f"resolving {repr(name)} as substring to {repr(value)}", name, value)

    if value == orig:
        raise KeyError(f"{orig} not found in defines")

    return replace_define(value, defines)


def process_defines(data, defines, cur_file):
    for k, v in data.items():
        if k.startswith("otk.define"):
            # nested otk.define: process the value
            return process_defines(v, defines, cur_file)
        if k.startswith("otk.include"):
            # Include file and it will become the define block.
            incl = process_dict({k: v}, defines, cur_file)
            print(f"got includes {incl}")
            defines.update(incl)
        if isinstance(defines.get(k), dict):
            # defines[k] already exists and is a dictionary: merge in the new values
            print(f"defines for {k} already exists and is dict - merging")
            define = defines[k]
            # TODO: what if v isn't a dictionary?
            define.update(process_defines(v, defines, cur_file))
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
