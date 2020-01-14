from unittest import TestCase
import pandas as pd
import numpy as np

# nice for when printing dataframes to console
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

player_stats = ["G", "A", "+/-", "PIM", "SOG", "FW", "HIT"]
# weight importance of the player stats
weights_series = pd.Series([2, 1.75, .5, .5, .5, .3, .5], index=player_stats)
roster_makeup = pd.Index("C,C,LW,LW,RW,RW,D,D,D,D".split(",")).value_counts()


def make_best_roster(x, roster_df, full_position_set, roster_makeup):
    elig_position = x['eligible_positions']
    for posn in elig_position:
        try:
            if roster_df.today_roster_position.value_counts()[posn] < roster_makeup[posn]:
                return posn
            else:
                # try to make room
                pass
        except KeyError:
            return posn
    return 'C'

class TestRoster(TestCase):

    # simple test which has 2 centres(C), and one player that be slotted into C,RW.
    # the C,RW player has a higher fantasy (fpts) ranking than 1 of the centres so
    # first iteration would probably place him in C, thus blocking out the 3rd player
    # who can only play centre.
    def test_daily_results(self):

        my_team = pd.read_csv('my-team.csv', converters = {"eligible_positions": lambda x: x.strip("[]").replace("'", "").split(", ")})
        my_team.set_index('player_id', inplace=True)
        # fpts is a weighted score assigned to each player which reflects their overall skill
        # for fantasy, and is used to choose players relative to others
        my_team['fpts'] = my_team[player_stats].mul(weights_series).sum(1)
        my_team.sort_values(by=['fpts'], ascending=False,inplace=True)
        # this test will work on a subset of 3 players as mentioned above
        day1 = [5462, 5984, 3982]
        day1_roster = my_team.loc[day1,['eligible_positions','fpts']]
        day1_roster['today_roster_position'] = np.nan
        # need to fill up roster with highest rate(fpts) players
        # create a new column (today_roster_position) that holds what spot player has been assigned
        # must match one of their eligible positions, there could be many players that are eligible for each position
        # for day1, should end up with 5462 and 3982 as C, 5984 down into RW

        #thinking we can store positions that can no longer accept players here so don't keep
        # doing futile lookups.  Will revisit this as we get to filling fuller rosters
        full_positions = set()

        #this series will hold the positions assigned for the players for the day
        todays_positions = pd.Series([np.nan] * len(day1_roster.index), index=day1_roster.index)
        for i in range(0, len(day1_roster.index)):
            avail_roster_position = None
            for posn in day1_roster.eligible_positions.values[i]:
                try:
                    if todays_positions.value_counts()[posn] < roster_makeup[posn]:
                        avail_roster_position = posn
                        break
                    else:
                        pass
                except KeyError:
                    avail_roster_position = posn
                    break
            if avail_roster_position is not None:
                todays_positions[i] = avail_roster_position
            else:
                # did not find a roster spot for this player
                print("Did not find roster spot for: {}, eligible positions: {}".format(day1_roster.index[i],day1_roster.loc[day1_roster.index[i],'eligible_positions']))
                # is there another player in one of my positions that can move?
                # look at already placed players and see if they can be moved.
        assert day1_roster.loc[5984,'today_roster_position'] == "RW"
        assert day1_roster.loc[5462, 'today_roster_position'] == "C"
        assert day1_roster.loc[3982, 'today_roster_position'] == "C"

