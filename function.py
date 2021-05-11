import collections.abc


def judge_rsp(a, b):
    # a 기준
    if a == b:
        return 0  # 비김
    elif a == 0:
        if b == 1:
            return 1
        elif b == 2:
            return -1
    elif a == 1:
        if b == 0:
            return -1
        elif b == 2:
            return 1
    elif a == 2:
        if b == 0:
            return 1
        if b == 1:
            return -1


def convert_rsp_int_str(rsp: int):
    if rsp == 0:
        return "바위"
    elif rsp == 1:
        return "가위"
    elif rsp == 2:
        return "보"
    else:
        return None


def convert_rsp_str_int(rsp: str):
    if rsp is None:
        return rsp
    if rsp.lower() in ("가위", "1", "scissor", "s", "sc"):
        return 1
    elif rsp.lower() in ("바위", "0", "rock", "r", "rk"):
        return 0
    elif rsp.lower() in ("보", "2", "paper", "p", "pp"):
        return 2
    else:
        return None


def convert_state_int_str(state: int):
    if state == 0:
        return "비겼습니다."
    elif state == 1:
        return "이겼습니다."
    elif state == -1:
        return "졌습니다."
    else:
        return None


def dict_update_recursive(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = dict_update_recursive(d.get(k, {}), v)
        else:
            d[k] = v
    return d
