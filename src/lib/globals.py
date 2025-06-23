import os

_file_path = os.path.abspath(__file__)
_parent_dir = os.path.dirname(_file_path)


CODE_DIR = os.path.dirname(os.path.dirname(_parent_dir))
LIB_DIR = os.path.join(CODE_DIR, 'src', 'lib')
RAW_DIR = os.path.join(CODE_DIR, 'visualizer_data')
PROCESSED_DIR = os.path.join(CODE_DIR, 'data', 'processed')
FIGURE_DIR = os.path.join(CODE_DIR, 'figures')
