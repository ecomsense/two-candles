from traceback import print_exc

try:
    from toolkit.logger import Logger
except ModuleNotFoundError:
    __import__("os").system("pip install git+https://github.com/pannet1/toolkit")
    __import__("time").sleep(5)
    from toolkit.logger import Logger

from toolkit.fileutils import Fileutils

S_DATA = "../data/"
S_UNIV = S_DATA + "universe.csv"
S_OUT = S_DATA + "out.csv"
S_DUMP = S_DATA + "master.csv"
logging = Logger(20)
O_FUTL = Fileutils()


def yml_to_obj(arg=None):
    if not arg:
        # return the parent folder name
        folder = __import__("os").getcwd().split("/")[-1]
        # reverse the words seperated by -
        lst = folder.split("_")
        file = "-".join(reversed(lst))
        file = "../../" + file + ".yml"
    else:
        file = S_DATA + arg

    flag = O_FUTL.is_file_exists(file)

    if not flag and arg:
        logging.warning(f"using default {file=}")
        __import__("shutil").copyfile("../settings.yml", file)
    elif not flag and arg is None:
        logging.error(f"fill the {file=} file and try again")
        __import__("sys").exit()

    return O_FUTL.get_lst_fm_yml(file)


def win_yml_to_obj(arg=None):
    try:
        if not arg:
            file = "../../socket-kite.yml"
        else:
            file = S_DATA + arg

        flag = O_FUTL.is_file_exists(file)
        if not flag and arg:
            logging.warning(f"using default {file} file")
            __import__("shutil").copyfile("../settings.yml", file)
        elif not flag and arg is None:
            logging.error(f"fill the {file=} and try again")

        return O_FUTL.get_lst_fm_yml(file)
    except Exception as e:
        logging.error(e)
        print_exc()


def os_and_objects():
    try:
        if __import__("os").name != "nt":
            O_CNFG = yml_to_obj()
            O_SETG = yml_to_obj("settings.yml")
        else:
            O_CNFG = win_yml_to_obj()
            O_SETG = win_yml_to_obj("settings.yml")
    except Exception as e:
        logging.error(e)
        print_exc()
        __import__("sys").exit(1)
    else:
        return O_CNFG, O_SETG


O_CNFG, O_SETG = os_and_objects()
print(O_CNFG, O_SETG)
