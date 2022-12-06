from pprint import pp
from typing import List, Dict
from datetime import time


def __parse_time(time: str) -> Dict[str, int]:
    time_split = time.split(":")

    if len(time_split) == 1:
        # case of time = "24h"
        return {
            "hours": 99,
            "minutes": 99,
            "seconds": 99,
            "string": time
        }

    (hours, minutes, seconds) = time.split(":")

    return {
        "hours": int(hours, base=10),
        "minutes": int(minutes, base=10),
        "seconds": int(seconds, base=10),
        "string": time
    }


# could swap this out with a nice regex but I don't know how to do that yet
def validate_leaderboard(leaderboard: str) -> bool:
    lines = list(filter(lambda x: x != "", map(
        lambda x: x.strip(), leaderboard.split("\n"))))

    # validate first line
    # rule: the title line needs to have at least "Part 1"
    if not "Part 1" in lines[0]:
        print("HERE2")
        return False

    # validate second line
    # rule: the second line needs to have this piece of text
    def contains(line, words):
        for word in words:
            if not word in line:
                return False

        return True

    if not contains(lines[1], ["Day", "Time", "Rank", "Score"]):
        print("HERE3")
        return False

    # validate length of entries
    # rule: need to have at least 1 entry and no more than 25
    if len(lines[1:]) < 1 or len(lines[1:]) > 25:
        print("HERE1")
        return False

    # write a regex to validate the entry values
    return True


def parse_leaderboard(leaderboard: str) -> List[List[str]]:
    lines = list(filter(lambda x: x.strip() != "",
                 leaderboard.splitlines()))[2:]

    # split the line and filter out all the empty string
    def clean(line):
        return list(filter(lambda x: x != "", line.strip().split(" ")))

    lines = list(map(clean, lines))

    # go through and parse everything into a data structure that makes sense
    for i in range(len(lines)):
        stat = lines[i]

        data = {
            "day": 0,
            "problem_one": {
                "time": "",
                "rank": ""
            },
            "problem_two": {
                "time": "",
                "rank": ""

            }
        }

        (day, problem_one_time, problem_one_rank, *rest_of_stats) = stat
        data["day"] = int(day, base=10)
        data["problem_one"]["time"] = __parse_time(problem_one_time)
        data["problem_one"]["rank"] = int(problem_one_rank, base=10)
        # still don't know what to do with empty days so just empty strings for
        # now
        if len(stat) > 4:
            (_, problem_two_time, problem_two_rank, _) = rest_of_stats
            data["problem_two"]["time"] = __parse_time(problem_two_time)
            data["problem_two"]["rank"] = int(problem_two_rank, base=10)

        lines[i] = data

    return lines


if __name__ == '__main__':
    leaderboard = """
      --------Part 1--------   --------Part 2--------
Day       Time   Rank  Score       Time   Rank  Score
  3   00:16:55   6028      0   00:32:40   7289      0
  2   00:28:05  10929      0   00:39:37  10608      0
  1   00:04:24   2194      0   00:06:32   2084      0
    """

    leaderboard_no_two_star = """
      --------Part 1--------   --------Part 2--------
Day       Time   Rank  Score       Time   Rank  Score
  3   00:16:55   6028      0
  2   00:28:05  10929      0   00:39:37  10608      0
  1   00:04:24   2194      0   00:06:32   2084      0
    """

    leaderboard_24_hour = """
    --------Part 1---------   --------Part 2---------
Day       Time    Rank  Score       Time    Rank  Score
  4   02:03:52   21022      0   02:20:46   21242      0
  3   02:09:12   20922      0   02:47:23   21268      0
  2       >24h  121380      0       >24h  115438      0
  1   12:48:47   87903      0   12:53:13   83407      0

    """

    pp(validate_leaderboard(leaderboard))
    pp(validate_leaderboard(leaderboard_no_two_star))
    pp(validate_leaderboard(leaderboard_24_hour))

    # pp(parse_leaderboard(leaderboard))
    # pp(parse_leaderboard(leaderboard_no_two_star))
    # pp(parse_leaderboard(leaderboard_24_hour))
