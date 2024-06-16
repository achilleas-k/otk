import sys

import yaml


def process_dict(data):
    for k, v in data.copy().items():
        if k.startswith("otk.include"):
            print(f"Loading {v}")
            del data[k]
            data.update(process_include(v))
        else:
            data[k] = process(v)

    return data


def process_list(data):
    for idx, item in enumerate(data.copy()):
        data[idx] = process(item)
    return data


def process_include(path: str) -> dict:
    with open(path, mode="r", encoding="utf=8") as fp:
        return process(yaml.safe_load(fp))


def process(data):
    if isinstance(data, dict):
        return process_dict(data)
    if isinstance(data, list):
        return process_list(data)
    return data


def main():
    path = sys.argv[1]
    data = process_include(path)

    print("---")
    print(yaml.dump(data))


if __name__ == "__main__":
    main()
