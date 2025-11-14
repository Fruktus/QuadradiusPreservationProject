import logging
import os
import uuid
from datetime import datetime, timezone

from QRServer.config import Config
from QRServer.db.common import UpdateCollisionError, retry_on_update_collision
import aiosqlite

from QRServer.common.classes import GameResultHistory, RankingEntry
from QRServer.common import utils
from QRServer.db import migrations
from QRServer.db.models import DbUser, DbMatchReport, TournamentDuel, TournamentMatch, TournamentParticipant, \
    Tournament, UserRating
from QRServer.db.password import password_verify, password_hash

log = logging.getLogger('qr.dbconnector')


class DbConnector:
    conn: aiosqlite.Connection

    def __init__(self, file, config: Config):
        self.file = file
        self.config = config

    async def connect(self):
        self.conn = await aiosqlite.connect(self.file, autocommit=False)
        c = await self.conn.cursor()
        await migrations.setup_metadata(c)
        await migrations.execute_migrations(c, self.config)
        await self.conn.commit()

    async def close(self):
        await self.conn.close()

    async def get_user(self, user_id: str) -> DbUser | None:
        c = await self.conn.cursor()
        await c.execute(
            "select id, username, password, created_at, discord_user_id from users where id = ?", (
                user_id,
            ))
        row = await c.fetchone()
        if row is None:
            return None
        return DbUser(
            user_id=row[0],
            username=row[1],
            password=row[2],
            created_at=row[3],
            discord_user_id=row[4],
        )

    async def get_user_by_username(self, username) -> DbUser | None:
        c = await self.conn.cursor()
        await c.execute(
            "select id, username, password, created_at, discord_user_id from users where username = ?", (
                username,
            ))
        row = await c.fetchone()
        if row is None:
            return None
        return DbUser(
            user_id=row[0],
            username=row[1],
            password=row[2],
            created_at=row[3],
            discord_user_id=row[4],
        )

    async def get_users_by_discord_id(self, discord_user_id: str) -> list[DbUser]:
        c = await self.conn.cursor()
        await c.execute(
            "select id, username, password, created_at, discord_user_id from users where discord_user_id = ?", (
                discord_user_id,
            ))
        rows = await c.fetchall()
        if rows is None:
            return []
        result = []

        for row in rows:
            result.append(
                DbUser(
                    user_id=row[0],
                    username=row[1],
                    password=row[2],
                    created_at=row[3],
                    discord_user_id=row[4]
                )
            )
        return result

    async def create_member(self, username: str, password: bytes, discord_user_id: str | None = None) -> str:
        id_ = str(uuid.uuid4())
        c = await self.conn.cursor()
        await c.execute(
            "insert into users("
            "  id, username, password, created_at, discord_user_id"
            ") values (?, ?, ?, ?, ?)", (
                id_,
                username,
                password_hash(password) if password else None,
                datetime.now(timezone.utc).timestamp(),
                discord_user_id,
            ))
        await self.conn.commit()
        return id_

    async def authenticate_user(self, username: str, password: bytes | None, auto_create=False,
                                verify_password=True) -> DbUser | None:
        c = await self.conn.cursor()
        if auto_create:
            await c.execute(
                "insert or ignore into users("
                "  id, username, password, created_at, discord_user_id"
                ") values (?, ?, ?, ?, ?)", (
                    str(uuid.uuid4()),
                    username,
                    password_hash(password) if password else None,
                    datetime.now(timezone.utc).timestamp(),
                    None
                )
            )
            await self.conn.commit()

        await c.execute("select id, username, password, created_at, discord_user_id from users where username = ?",
                        (username,))

        row = await c.fetchone()
        if row is None:
            return None

        db_user = DbUser(
            user_id=row[0],
            username=row[1],
            password=row[2],
            created_at=row[3],
            discord_user_id=row[4],
        )

        if not db_user.is_guest and verify_password and not password_verify(password, db_user.password):
            return None

        return db_user

    async def change_user_password(self, user_id: str, password: bytes | None):
        c = await self.conn.cursor()
        await c.execute(
            "update users set password = ? where id = ?", (
                password_hash(password) if password else None,
                user_id
            ))
        await self.conn.commit()

    async def claim_member(self, user_id: str, password: bytes | None, discord_user_id: str):
        c = await self.conn.cursor()
        await c.execute(
            "update users set password = ?, discord_user_id = ? where id = ? and password is null", (
                password_hash(password) if password else None,
                discord_user_id,
                user_id,
            ))
        await self.conn.commit()

    async def add_match_result(self, match_result: DbMatchReport):
        c = await self.conn.cursor()
        await c.execute(
            "insert into matches ("
            "  id,"
            "  winner_id,"
            "  loser_id,"
            "  winner_pieces_left,"
            "  loser_pieces_left,"
            "  move_counter,"
            "  grid_size,"
            "  squadron_size,"
            "  started_at,"
            "  finished_at,"
            "  is_ranked,"
            "  is_void"
            ") values ("
            "?, ?, ?, ?, ?, ?,"
            "?, ?, ?, ?, ?, ?"
            ")", (
                match_result.match_id,
                match_result.winner_id,
                match_result.loser_id,
                match_result.winner_pieces_left,
                match_result.loser_pieces_left,
                match_result.move_counter,
                match_result.grid_size,
                match_result.squadron_size,
                match_result.started_at.timestamp(),
                match_result.finished_at.timestamp(),
                match_result.is_ranked,
                match_result.is_void
            ))

        start_date, end_date = utils.make_month_dates(
            month=match_result.finished_at.month, year=match_result.finished_at.year)

        ranked_only = self.config.leaderboards_ranked_only.get()
        include_void = self.config.leaderboards_include_void.get()

        try:
            if (match_result.is_ranked or not ranked_only) and (not match_result.is_void or include_void):
                await self.update_users_rating(
                    match_result.winner_id, match_result.loser_id,
                    match_result.finished_at.month, match_result.finished_at.year)
        except UpdateCollisionError as e:
            log.error(f'Failed to save rating to DB after all retries: {e}')

        new_ranking = await self._generate_ranking(
            start_date, end_date)

        await self._update_ranking(new_ranking, year=start_date.year, month=start_date.month)

        await self.conn.commit()

    async def get_match(self, match_id: str) -> DbMatchReport | None:
        c = await self.conn.cursor()
        await c.execute(
            "select id, winner_id, loser_id, winner_pieces_left,"
            " loser_pieces_left, move_counter, grid_size,"
            " squadron_size, started_at, finished_at, is_ranked,"
            " is_void"
            " from matches where id = ?", (
                match_id,
            ))
        row = await c.fetchone()
        if row is None:
            return None
        return DbMatchReport(
            match_id=row[0],
            winner_id=row[1],
            loser_id=row[2],
            winner_pieces_left=row[3],
            loser_pieces_left=row[4],
            move_counter=row[5],
            grid_size=row[6],
            squadron_size=row[7],
            started_at=datetime.fromtimestamp(row[8], tz=timezone.utc),
            finished_at=datetime.fromtimestamp(row[9], tz=timezone.utc),
            is_ranked=bool(row[10]),
            is_void=bool(row[11]),
        )

    async def get_match2(self, match_id: str):
        c = await self.conn.cursor()

        await c.execute(
            "select"
            " u1.username,"
            " u2.username,"
            " m.winner_pieces_left,"
            " m.loser_pieces_left,"
            " m.started_at,"
            " m.finished_at,"
            " m.move_counter"
            " from matches m"
            " left join users u1 on m.winner_id = u1.id"
            " left join users u2 on m.loser_id = u2.id"
            " where m.id = ?", (match_id,))

        row = await c.fetchone()
        if row is None:
            return None
        return GameResultHistory(
            player_won=row[0],
            player_lost=row[1],
            won_score=row[2],
            lost_score=row[3],
            start=datetime.fromtimestamp(row[4], tz=timezone.utc),
            finish=datetime.fromtimestamp(row[5], tz=timezone.utc),
            moves=row[6],
        )

    async def get_recent_matches(self, count=15) -> list[GameResultHistory]:
        c = await self.conn.cursor()

        # Gets all recent matches, minus void ones
        await c.execute("select"
                        " u1.username,"
                        " u2.username,"
                        " m.winner_pieces_left,"
                        " m.loser_pieces_left,"
                        " m.started_at,"
                        " m.finished_at,"
                        " m.move_counter"
                        " from matches m"
                        " left join users u1 on m.winner_id = u1.id"
                        " left join users u2 on m.loser_id = u2.id"
                        " where m.is_void = 0"
                        " order by m.finished_at desc"
                        " limit ?", (count,))

        recent_matches = []
        rows = await c.fetchall()
        for row in rows:
            recent_matches.append(GameResultHistory(
                player_won=row[0],
                player_lost=row[1],
                won_score=row[2],
                lost_score=row[3],
                start=datetime.fromtimestamp(row[4], tz=timezone.utc),
                finish=datetime.fromtimestamp(row[5], tz=timezone.utc),
                moves=row[6],
            ))
        return recent_matches

    async def get_ranking(self, start_date: datetime, end_date: datetime, ranked_only=True,
                          include_void=False) -> list[RankingEntry]:
        c = await self.conn.cursor()

        # Gets matches sort
        await c.execute(
            "select"
            " u.username,"
            " r.user_id,"
            " wins,"
            " total_games,"
            " ur.rating"
            " from rankings r"
            " inner join users u on u.id = r.user_id"
            " left join user_ratings ur on u.id = ur.user_id"
            "  and ur.year = r.year and ur.month = r.month"
            " where r.year == ?"
            " and r.month == ?"
            " order by r.position asc"  # Lower position - higher in leaderboards
            " limit 100", (
                start_date.year,
                start_date.month,
            )
        )

        ranking_entries = []
        rows = await c.fetchall()
        for row in rows:
            ranking_entries.append(RankingEntry(
                username=row[0],
                user_id=row[1],
                wins=row[2],
                games=row[3],
                rating=row[4],
            ))
        return ranking_entries

    async def _update_ranking(self, ranking_entries: list[RankingEntry], year: int, month: int) -> None:
        for position, entry in enumerate(ranking_entries):
            c = await self.conn.cursor()
            await c.execute(
                "insert or replace into rankings ("
                "  year,"
                "  month,"
                "  position,"
                "  user_id,"
                "  wins,"
                "  total_games"
                ") values ("
                "?, ?, ?, ?, ?, ?"
                ")", (
                    year,
                    month,
                    position+1,
                    entry.user_id,
                    entry.wins,
                    entry.games,
                ))

    async def _generate_ranking(self, start_date: datetime, end_date: datetime) -> list[RankingEntry]:
        ranked_only = self.config.leaderboards_ranked_only.get()
        include_void = self.config.leaderboards_include_void.get()

        c = await self.conn.cursor()

        # Gets matches sort
        await c.execute(
            "select"
            " u.username,"
            " u.id,"
            " sum(m.winner_id = u.id) as total_wins,"
            " count(*) as total_games"
            " from users u"
            " inner join matches m on (u.id = m.winner_id or u.id = m.loser_id)"
            " inner join user_ratings r on (u.id = r.user_id) and r.month = ? and r.year = ?"
            " where m.finished_at >= ?"
            " and m.finished_at < ?"
            " and (case when ? = 1 then m.is_ranked = 1 else 1=1 end)"
            " and (case when ? = 0 then m.is_void = 0 else 1=1 end)"
            " group by u.username"
            " order by rating desc, total_games desc, total_wins desc, u.id desc"
            " limit 100", (
                start_date.month,
                start_date.year,
                start_date.timestamp(),
                end_date.timestamp(),
                1 if ranked_only else 0,
                1 if include_void else 0
            )
        )

        ranking_entries = []
        rows = await c.fetchall()
        for row in rows:
            ranking_entries.append(RankingEntry(
                username=row[0],
                user_id=row[1],
                wins=row[2],
                games=row[3],
            ))
        return ranking_entries

    async def get_user_rating(self, user_id: str, month: int, year: int) -> UserRating | None:
        c = await self.conn.cursor()
        await c.execute(
            "select"
            " rating,"
            " revision"
            " from user_ratings"
            " where user_id = ?"
            " and month = ?"
            " and year = ?",
            (user_id, month, year)
            )
        row = await c.fetchone()
        if row:
            return UserRating(user_id, month, year, rating=row[0], revision=row[1])
        return None

    @retry_on_update_collision(retries=3)
    async def update_users_rating(self, winner_id: str, loser_id: str, month: int, year: int, on_before_update=None):
        winner = await self.get_user_rating(winner_id, month, year)
        winner_exists = True
        if winner is None:
            winner_exists = False
            winner = UserRating(winner_id, month, year)

        loser = await self.get_user_rating(loser_id, month, year)
        loser_exists = True
        if loser is None:
            loser_exists = False
            loser = UserRating(loser_id, month, year)

        new_winner_rating, new_loser_rating = utils.calculate_new_ratings(winner.rating, loser.rating)

        if on_before_update:
            await on_before_update()

        c = await self.conn.cursor()

        await self._update_or_insert_rating(c, winner, new_winner_rating, winner_exists, month, year)
        await self._update_or_insert_rating(c, loser, new_loser_rating, loser_exists, month, year)

        await self.conn.commit()

    async def _update_or_insert_rating(self, c, user: UserRating, new_rating: float, user_exists: bool, month: int,
                                       year: int):
        if not user_exists:
            try:
                await c.execute(
                    "insert into user_ratings (user_id, month, year, revision, rating) values (?, ?, ?, ?, ?)", (
                        user.user_id, month, year, user.revision, new_rating
                    )
                )
            except aiosqlite.IntegrityError:
                await self.conn.rollback()
                raise UpdateCollisionError()
        else:
            await c.execute(
                "update user_ratings set rating = ?, revision = ?"
                " where user_id = ? and month = ? and year = ? and revision = ? returning *", (
                    new_rating, user.revision + 1, user.user_id, month, year, user.revision
                )
            )

            row = await c.fetchone()
            if not row:
                await self.conn.rollback()
                raise UpdateCollisionError()

    async def create_tournament(self, tournament_name: str, created_by_dc_id: str, tournament_msg_dc_id: str,
                                required_matches_per_duel: int) -> str | None:
        """
        Returns:
            str: Id of the created tournament
        """
        id_ = str(uuid.uuid4())
        c = await self.conn.cursor()
        await c.execute(
            "insert or ignore into tournaments ("
            " id,"
            " name,"
            " created_by_dc_id,"
            " tournament_msg_dc_id,"
            " created_at,"
            " required_matches_per_duel"
            ")"
            " values (?, ?, ?, ?, ?, ?)", (
                id_,
                tournament_name,
                created_by_dc_id,
                tournament_msg_dc_id,
                int(datetime.now(timezone.utc).timestamp()),
                required_matches_per_duel,
            )
        )
        await self.conn.commit()
        if bool(c.rowcount):
            return id_
        return None

    async def get_tournament(self, tournament_id: str) -> Tournament | None:
        c = await self.conn.cursor()
        await c.execute(
            "select id, name, created_by_dc_id, tournament_msg_dc_id,"
            " required_matches_per_duel, created_at,"
            " started_at, finished_at"
            " from tournaments"
            " where id = ?",
            (tournament_id,)
        )

        row = await c.fetchone()
        if row is None:
            return None
        return Tournament(
            tournament_id=row[0],
            name=row[1],
            created_by_dc_id=row[2],
            tournament_msg_dc_id=row[3],
            required_matches_per_duel=row[4],
            created_at=datetime.fromtimestamp(row[5], tz=timezone.utc),
            started_at=datetime.fromtimestamp(row[6], tz=timezone.utc) if row[6] else None,
            finished_at=datetime.fromtimestamp(row[7], tz=timezone.utc) if row[7] else None,
        )

    async def list_tournament_users(self, tournament_id: str) -> list[DbUser] | None:
        c = await self.conn.cursor()
        await c.execute(
            "select users.id, username, password, users.created_at, discord_user_id"
            " from tournaments"
            " left join tournament_participants"
            " on tournaments.id = tournament_participants.tournament_id"
            " left join users"
            " on users.id = tournament_participants.user_id"
            " where tournaments.id = ?",
            (tournament_id,)
        )

        rows = list(await c.fetchall())
        if not rows:
            # Tournament does not exist
            return None

        if rows[0][0] is None:
            # tournament exists but no participants
            return []

        result = []
        for row in rows:
            result.append(DbUser(
                user_id=row[0],
                username=row[1],
                password=row[2],
                created_at=row[3],
                discord_user_id=row[4],
            ))
        return result

    async def start_tournament(self, tournament_id: str) -> bool:
        """
        Returns:
            bool: True if succesfully started the tournament
        """
        c = await self.conn.cursor()
        now_ts = int(datetime.now(timezone.utc).timestamp())  # current datetime as integer timestamp
        await c.execute(
            "update tournaments"
            " set started_at = ?"
            " where id = ? and started_at is null",
            (now_ts, tournament_id)
        )
        await self.conn.commit()
        return bool(c.rowcount)

    async def add_participant(self, tournament_id: str, user_id: str) -> bool:
        """
        Returns:
            bool: True if successfully added the participant
        """
        c = await self.conn.cursor()
        await c.execute(
            "insert into tournament_participants (tournament_id, user_id)"
            "select ?, ?"
            "where exists ("
            "    select 1 from tournaments"
            "    where id = ? and started_at is null"
            ")",
            (tournament_id, user_id, tournament_id)
        )
        await self.conn.commit()
        return bool(c.rowcount)

    async def list_participants(self, tournament_id: str) -> list[TournamentParticipant]:
        c = await self.conn.cursor()
        await c.execute(
            "select tournament_id, user_id from tournament_participants where tournament_id = ?",
            (tournament_id,)
        )
        rows = await c.fetchall()
        if not rows:
            return []
        return [TournamentParticipant(row[0], row[1]) for row in rows]

    async def remove_participant(self, tournament_id, user_id) -> bool:
        """
        Returns:
            bool: True if row deleted, False if tournament or user id does not exist or tournament already began.
        """
        c = await self.conn.cursor()
        await c.execute(
            "delete from tournament_participants"
            " where tournament_id = ? and user_id = ? and exists ("
            "    select 1 from tournaments"
            "    where id = tournament_participants.tournament_id"
            "    and started_at is null"
            ")",
            (tournament_id, user_id)
        )
        await self.conn.commit()
        return bool(c.rowcount)

    async def add_duel(self, tournament_id: str, duel_idx: int, active_until: datetime,
                       user1_id: str | None, user2_id: str | None) -> bool:
        """
        Returns:
            bool: True if succesfully added the duel
        """
        c = await self.conn.cursor()
        await c.execute(
            "insert or ignore into tournament_duels ("
            " tournament_id,"
            " duel_idx,"
            " active_until,"
            " user1_id,"
            " user2_id"
            ")"
            " values (?, ?, ?, ?, ?)",
            (
                tournament_id,
                duel_idx,
                int(active_until.timestamp()),
                user1_id,
                user2_id,
            )
        )
        await self.conn.commit()
        return bool(c.rowcount)

    async def list_duels(self, tournament_id: str) -> list[TournamentDuel] | None:
        c = await self.conn.cursor()
        await c.execute(
            "select tournament_id, duel_idx, active_until, user1_id, user2_id"
            " from tournaments"
            " left join tournament_duels"
            " on tournaments.id = tournament_duels.tournament_id"
            " where tournaments.id = ? order by duel_idx",
            (tournament_id,)
        )

        rows = list(await c.fetchall())
        if not rows:
            # Tournament does not exist
            return None

        if rows[0][0] is None:
            # tournament exists but no participants
            return []

        return [TournamentDuel(
                    tournament_id=row[0],
                    duel_idx=row[1],
                    active_until=datetime.fromtimestamp(row[2], tz=timezone.utc),
                    user1_id=row[3],
                    user2_id=row[4],
                ) for row in rows]

    async def get_duel(self, tournament_id: str, duel_idx: int) -> TournamentDuel | None:
        c = await self.conn.cursor()
        await c.execute(
            "select tournament_id, duel_idx, active_until, user1_id, user2_id"
            " from tournament_duels where tournament_id = ? and duel_idx = ?",
            (tournament_id, duel_idx)
        )
        row = await c.fetchone()
        if not row:
            return None

        return TournamentDuel(
            tournament_id=row[0],
            duel_idx=row[1],
            active_until=datetime.fromtimestamp(row[2], tz=timezone.utc),
            user1_id=row[3],
            user2_id=row[4],
        )

    async def get_duel_matches(self, tournament_id: str, duel_idx: int) -> list[DbMatchReport]:
        c = await self.conn.cursor()
        await c.execute(
            "select id, winner_id, loser_id, winner_pieces_left,"
            " loser_pieces_left, move_counter, grid_size,"
            " squadron_size, started_at, finished_at, is_ranked,"
            " is_void"
            " from matches"
            " right join tournament_matches"
            " on matches.id = tournament_matches.match_id"
            " where tournament_matches.tournament_id = ? and tournament_matches.duel_idx = ?",
            (
                tournament_id,
                duel_idx,
            ))
        rows = await c.fetchall()
        if rows is None:
            return None

        result = []
        for row in rows:
            result.append(DbMatchReport(
                match_id=row[0],
                winner_id=row[1],
                loser_id=row[2],
                winner_pieces_left=row[3],
                loser_pieces_left=row[4],
                move_counter=row[5],
                grid_size=row[6],
                squadron_size=row[7],
                started_at=datetime.fromtimestamp(row[8], tz=timezone.utc),
                finished_at=datetime.fromtimestamp(row[9], tz=timezone.utc),
                is_ranked=bool(row[10]),
                is_void=bool(row[11]),
            ))
        return result

    async def list_tournament_matches(self, tournament_id: str) -> list[TournamentMatch] | None:
        c = await self.conn.cursor()
        await c.execute(
            "select matches.id, winner_id, loser_id, winner_pieces_left,"
            " loser_pieces_left, move_counter, grid_size,"
            " squadron_size, matches.started_at, matches.finished_at, is_ranked,"
            " is_void, duel_idx"
            " from tournaments"
            " left join tournament_matches"
            " on tournaments.id = tournament_matches.tournament_id"
            " left join matches"
            " on matches.id = tournament_matches.match_id"
            " where tournaments.id = ?",
            (tournament_id,)
        )
        rows = list(await c.fetchall())
        if not rows:
            # Tournament does not exist
            return None

        if rows[0][0] is None:
            # Tournament exists, matches do not (row full of Nones)
            return []

        result = []
        for row in rows:
            tournament_match = TournamentMatch(
                match=DbMatchReport(
                    match_id=row[0],
                    winner_id=row[1],
                    loser_id=row[2],
                    winner_pieces_left=row[3],
                    loser_pieces_left=row[4],
                    move_counter=row[5],
                    grid_size=row[6],
                    squadron_size=row[7],
                    started_at=datetime.fromtimestamp(row[8], tz=timezone.utc),
                    finished_at=datetime.fromtimestamp(row[9], tz=timezone.utc),
                    is_ranked=bool(row[10]),
                    is_void=bool(row[11]),
                ),
                duel_idx=row[12]
            )
            result.append(tournament_match)
        return result

    async def add_duel_match(self, tournament_id: str, duel_idx: int, match_id: str) -> bool:
        """
        Returns:
            bool: True if succesfully added the match to duel
        """
        c = await self.conn.cursor()
        await c.execute(
            "insert or ignore into tournament_matches ("
            " tournament_id,"
            " duel_idx,"
            " match_id"
            ")"
            "values (?, ?, ?)",
            (
                tournament_id,
                duel_idx,
                match_id,
            )
        )
        await self.conn.commit()
        return bool(c.rowcount)


async def create_connector(config) -> DbConnector:
    data_dir = os.path.abspath(config.data_dir.get())
    os.makedirs(data_dir, exist_ok=True)
    dbfile = os.path.join(data_dir, 'database.sqlite3')
    log.debug(f'Opening database: {dbfile}')
    c = DbConnector(dbfile, config)
    await c.connect()
    return c
