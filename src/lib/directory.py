import  os
from    typing import List, Dict, Callable
import  pandas as pd
from    icecream import ic
import  src.lib.command_line as CL


def cd(directory: str) -> None:
    _check_dir_exists(directory)
    
    try:
        os.chdir(directory)
    except Exception as e:
        raise Exception(f"Error changing into directory; '{directory} | {e}'") from None


def file_to_df(filename: str) -> pd.DataFrame:
    try:
        _check_file_exists(filename)

        reader = _get_file_reader(filename)
        df = reader(filename)
    except Exception as e:
        raise Exception(f"Error creating df from file '{filename}:\n\t{e}") from None

    return df


def df_to_file(df: pd.DataFrame, filename: str, index: bool = False) -> None:
    if df is None or df.empty or df.isna().all().all():
        raise Exception(f"DataFrame {df} doesn't exist")
    
    try:
        writer = _get_file_writer(filename)
        writer(df, filename, index=index)
    except Exception as e:
        raise Exception(f"Error converting df to filename of '{filename}'; {e}") from None


def get_files(directory: str) -> List[str]:
    _check_dir_exists(directory)
    all_files = []    

    for root, _, files in os.walk(directory):
        for file in files:
            if file[0] == ".":
                continue
            file_path = os.path.abspath(os.path.join(root, file))
            all_files.append(file_path)

    return all_files


def get_dfs(directory: str) -> List[str]:
    _check_dir_exists(directory)

    df_file_types = [
        ".csv",
        ".xslx"
    ]

    all_files = []
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.abspath(os.path.join(root, file))
                for ext in df_file_types:
                    if file_path.endswith(ext):
                        all_files.append(file_path)
    except Exception as e:
        raise Exception(f"Failed to list files in {directory}: {str(e)}") from None

    return all_files


def search(*terms: str, directory=f".{os.sep}") -> List[str]:
    _check_dir_exists(directory)
    files = get_files(directory)

    terms = [word.lower() for string in terms for word in string.split()]

    def matches_terms(file_path):
        file_name = get_basename(file_path)
        return (all(term in file_name.lower() for term in terms)
                and file_name != ".DS_Store")

    filtered_files = filter(matches_terms, files)
    
    return list(filtered_files) 


def add_file_suffix(filename: str, suffix: str) -> str:
    dirname, basename = os.path.split(filename)
    name, ext = os.path.splitext(basename)

    if not ext:
        raise Exception(f"File extension not found in '{filename}'") from None

    new_basename = f"{name}_{suffix}{ext}"
    return os.path.join(dirname, new_basename)


def add_file_prefix(filename: str, prefix: str) -> str:
    dirname, basename = os.path.split(filename)
    name, ext = os.path.splitext(basename)

    if not ext:
        raise Exception(f"File extension not found in '{filename}'") from None

    new_basename = f"{prefix}_{name}{ext}"
    return os.path.join(dirname, new_basename)


def gum_search() -> List[str]:
    terms = CL.bash_prompt("gum input --placeholder='enter search term...'")
    files = search(terms)

    return files


def get_basename(filename: str) -> str:
    _check_file_exists(filename)

    _, basename = os.path.split(filename)
    name, _ = os.path.splitext(basename)
    
    return name


def _check_file_exists(filename: str) -> None:
    exists = os.path.exists(filename)  
    isfile = os.path.isfile(filename)
    if not exists or not isfile:
        raise Exception(f"File '{filename} doesn't exist") from None


def _get_file_writer(filename: str) -> Callable:
    extension = filename.rsplit('.', 1)[-1].lower()
    file_writers: Dict[str, Callable] = {
        "csv": pd.DataFrame.to_csv,
        "xlsx": pd.DataFrame.to_excel
    }

    if extension not in file_writers:
        raise Exception(f"File Extension in file '{filename}' not supported") from None
    
    file_writer = file_writers[extension]

    return file_writer


def _get_file_reader(filename: str) -> Callable:
    extension = filename.rsplit('.', 1)[-1].lower()
    file_readers: Dict[str, Callable] = {
        "csv": pd.read_csv,
        "xlsx": pd.read_excel
    }

    if extension not in file_readers:
        raise Exception(f"File extension in file '{extension}' not supported") from None
    
    file_reader = file_readers[extension]

    return file_reader


def _check_dir_exists(directory: str) -> None:
    if not os.path.exists(directory):
        raise Exception(f"Directory '{directory}' does not exist") from None
