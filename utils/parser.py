from pprint import pp
from typing import List


def parse_leaderboard(leaderboard: str) -> List[List[str]]:
    lines = list(filter(lambda x: x.strip() != "",
                 leaderboard.splitlines()))[2:]

    # split the line and filter out all the empty string
    def clean(line):
        return list(filter(lambda x: x != "", line.strip().split(" ")))

    lines = list(map(clean, lines))

    return lines


# take the time for each problem
# take the rank for each problem


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
