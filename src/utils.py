# Format number
def format_number(curr_num, match_num) -> str:
    """

    :param curr_num:
    :param match_num:
    :return:
    """
    # print(f"format_number(\n"
    #       f"  curr_num={curr_num},\n"
    #       f"  match_num={match_num}\n)")  # @todo debug
    # curr_num_str = f"{curr_num}"
    match_num_str = f"{match_num}"

    if "." in match_num_str:
        match_decimals = len(match_num_str.split(".")[1])
        curr_num_str = f"{curr_num:.{match_decimals}f}"
        curr_num_str = curr_num_str[:]
        return curr_num_str

    return f"{int(curr_num)}"
