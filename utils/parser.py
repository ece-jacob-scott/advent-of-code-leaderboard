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
    pp(parse_leaderboard(leaderboard))
    pp(parse_leaderboard(leaderboard_no_two_star))
