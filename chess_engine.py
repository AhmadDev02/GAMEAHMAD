"""
FIDE-Compliant Chess Engine
===========================
Module: chess_engine.py
Author: Game Engine Architect (GAME AHMAD Suite)

Architecture:
- Pure headless engine class completely decoupled from UI/rendering.
- 8x8 Board representation with rank (0-7: ranks 1-8) and file (0-7: files a-h).
- Strict FIDE movement, castling (transit safety, check prevention), en passant tracking,
  promotion choices, legal move filtering, check/checkmate, stalemate, 50-move rule,
  threefold repetition, insufficient material, FEN loading/serialization, and UCI move parsing.
"""

from enum import Enum
from typing import List, Optional, Tuple, Dict, Set
import copy


class Color(Enum):
    WHITE = 0
    BLACK = 1

    @property
    def opponent(self) -> 'Color':
        return Color.BLACK if self == Color.WHITE else Color.WHITE

    @property
    def char(self) -> str:
        return 'w' if self == Color.WHITE else 'b'


class PieceType(Enum):
    PAWN = 'P'
    KNIGHT = 'N'
    BISHOP = 'B'
    ROOK = 'R'
    QUEEN = 'Q'
    KING = 'K'


class Piece:
    __slots__ = ('piece_type', 'color')

    def __init__(self, piece_type: PieceType, color: Color):
        self.piece_type = piece_type
        self.color = color

    def symbol(self) -> str:
        c = self.piece_type.value
        return c if self.color == Color.WHITE else c.lower()

    @staticmethod
    def from_char(c: str) -> Optional['Piece']:
        color = Color.WHITE if c.isupper() else Color.BLACK
        pt_map = {
            'P': PieceType.PAWN,
            'N': PieceType.KNIGHT,
            'B': PieceType.BISHOP,
            'R': PieceType.ROOK,
            'Q': PieceType.QUEEN,
            'K': PieceType.KING
        }
        pt = pt_map.get(c.upper())
        return Piece(pt, color) if pt else None

    def __repr__(self) -> str:
        return f"{self.color.name.capitalize()} {self.piece_type.name.capitalize()}"


class Move:
    __slots__ = ('from_sq', 'to_sq', 'promotion', 'is_castling', 'is_en_passant', 'captured_piece')

    def __init__(self, from_sq: Tuple[int, int], to_sq: Tuple[int, int],
                 promotion: Optional[PieceType] = None,
                 is_castling: bool = False,
                 is_en_passant: bool = False,
                 captured_piece: Optional[Piece] = None):
        self.from_sq = from_sq  # (file, rank) where file=0..7 (a..h), rank=0..7 (1..8)
        self.to_sq = to_sq
        self.promotion = promotion
        self.is_castling = is_castling
        self.is_en_passant = is_en_passant
        self.captured_piece = captured_piece

    def to_uci(self) -> str:
        f1, r1 = self.from_sq
        f2, r2 = self.to_sq
        s1 = f"{chr(ord('a') + f1)}{r1 + 1}"
        s2 = f"{chr(ord('a') + f2)}{r2 + 1}"
        prom = self.promotion.value.lower() if self.promotion else ""
        return f"{s1}{s2}{prom}"

    @staticmethod
    def square_to_str(sq: Tuple[int, int]) -> str:
        f, r = sq
        return f"{chr(ord('a') + f)}{r + 1}"

    @staticmethod
    def str_to_square(s: str) -> Tuple[int, int]:
        s = s.strip().lower()
        return (ord(s[0]) - ord('a'), int(s[1]) - 1)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Move):
            return False
        return (self.from_sq == other.from_sq and
                self.to_sq == other.to_sq and
                self.promotion == other.promotion)

    def __repr__(self) -> str:
        return f"Move({self.to_uci()})"


class GameStatus(Enum):
    ACTIVE = "Active"
    CHECKMATE = "Checkmate"
    STALEMATE = "Stalemate"
    DRAW_FIFTY_MOVES = "Draw (50-Move Rule)"
    DRAW_THREEFOLD_REPETITION = "Draw (Threefold Repetition)"
    DRAW_INSUFFICIENT_MATERIAL = "Draw (Insufficient Material)"


class ChessBoard:
    """
    FIDE-Standard Chess Game State & Logic Engine.
    """
    STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    def __init__(self, fen: str = STARTING_FEN):
        self.board: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.turn: Color = Color.WHITE
        self.castling_rights: Dict[str, bool] = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant_sq: Optional[Tuple[int, int]] = None
        self.halfmove_clock: int = 0
        self.fullmove_number: int = 1

        self.move_history: List[Move] = []
        self.state_history: List[dict] = []
        self.fen_history: List[str] = []

        self.load_fen(fen)

    def clear(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.turn = Color.WHITE
        self.castling_rights = {'K': False, 'Q': False, 'k': False, 'q': False}
        self.en_passant_sq = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.move_history.clear()
        self.state_history.clear()
        self.fen_history.clear()

    def get_piece(self, file: int, rank: int) -> Optional[Piece]:
        if 0 <= file < 8 and 0 <= rank < 8:
            return self.board[rank][file]
        return None

    def set_piece(self, file: int, rank: int, piece: Optional[Piece]):
        if 0 <= file < 8 and 0 <= rank < 8:
            self.board[rank][file] = piece

    # -------------------------------------------------------------------------
    # FEN SERIALIZATION & PARSING
    # -------------------------------------------------------------------------
    def load_fen(self, fen: str):
        self.clear()
        parts = fen.strip().split()
        if len(parts) < 4:
            raise ValueError(f"Invalid FEN format: {fen}")

        ranks = parts[0].split('/')
        if len(ranks) != 8:
            raise ValueError("FEN must specify 8 ranks")

        # Rank 8 is at index 7 (top), Rank 1 is at index 0 (bottom)
        for r_idx, rank_str in enumerate(reversed(ranks)):
            f_idx = 0
            for ch in rank_str:
                if ch.isdigit():
                    f_idx += int(ch)
                else:
                    self.board[r_idx][f_idx] = Piece.from_char(ch)
                    f_idx += 1

        # Turn
        self.turn = Color.WHITE if parts[1] == 'w' else Color.BLACK

        # Castling
        self.castling_rights = {
            'K': 'K' in parts[2],
            'Q': 'Q' in parts[2],
            'k': 'k' in parts[2],
            'q': 'q' in parts[2]
        }

        # En Passant
        if parts[3] != '-':
            self.en_passant_sq = Move.str_to_square(parts[3])
        else:
            self.en_passant_sq = None

        # Halfmove & Fullmove
        self.halfmove_clock = int(parts[4]) if len(parts) > 4 else 0
        self.fullmove_number = int(parts[5]) if len(parts) > 5 else 1

        self.fen_history.append(self.get_position_key())

    def get_position_key(self) -> str:
        """Key representation for threefold repetition: piece placement, turn, castling, en passant."""
        return " ".join(self.get_fen().split()[:4])

    def get_fen(self) -> str:
        rows = []
        for rank in range(7, -1, -1):
            empty = 0
            row_str = ""
            for file in range(8):
                piece = self.board[rank][file]
                if piece is None:
                    empty += 1
                else:
                    if empty > 0:
                        row_str += str(empty)
                        empty = 0
                    row_str += piece.symbol()
            if empty > 0:
                row_str += str(empty)
            rows.append(row_str)

        board_part = "/".join(rows)
        turn_part = self.turn.char

        castling_str = ""
        for key in ['K', 'Q', 'k', 'q']:
            if self.castling_rights[key]:
                castling_str += key
        if not castling_str:
            castling_str = "-"

        ep_str = Move.square_to_str(self.en_passant_sq) if self.en_passant_sq else "-"
        return f"{board_part} {turn_part} {castling_str} {ep_str} {self.halfmove_clock} {self.fullmove_number}"

    # -------------------------------------------------------------------------
    # ATTACK DETECTION & KING SAFETY
    # -------------------------------------------------------------------------
    def is_square_attacked(self, target_sq: Tuple[int, int], by_color: Color) -> bool:
        tx, ty = target_sq

        # 1. Pawn Attacks
        # If attacking color is WHITE, they attack target from rank ty - 1
        pawn_dir = 1 if by_color == Color.WHITE else -1
        src_rank = ty - pawn_dir
        if 0 <= src_rank < 8:
            for src_file in (tx - 1, tx + 1):
                if 0 <= src_file < 8:
                    p = self.board[src_rank][src_file]
                    if p and p.color == by_color and p.piece_type == PieceType.PAWN:
                        return True

        # 2. Knight Attacks
        knight_offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for dx, dy in knight_offsets:
            nx, ny = tx + dx, ty + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                p = self.board[ny][nx]
                if p and p.color == by_color and p.piece_type == PieceType.KNIGHT:
                    return True

        # 3. King Attacks (Adjacent squares)
        king_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dx, dy in king_offsets:
            kx, ky = tx + dx, ty + dy
            if 0 <= kx < 8 and 0 <= ky < 8:
                p = self.board[ky][kx]
                if p and p.color == by_color and p.piece_type == PieceType.KING:
                    return True

        # 4. Straight Sliders (Rook, Queen)
        straight_dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dx, dy in straight_dirs:
            cur_x, cur_y = tx + dx, ty + dy
            while 0 <= cur_x < 8 and 0 <= cur_y < 8:
                p = self.board[cur_y][cur_x]
                if p:
                    if p.color == by_color and p.piece_type in (PieceType.ROOK, PieceType.QUEEN):
                        return True
                    break
                cur_x += dx
                cur_y += dy

        # 5. Diagonal Sliders (Bishop, Queen)
        diagonal_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dx, dy in diagonal_dirs:
            cur_x, cur_y = tx + dx, ty + dy
            while 0 <= cur_x < 8 and 0 <= cur_y < 8:
                p = self.board[cur_y][cur_x]
                if p:
                    if p.color == by_color and p.piece_type in (PieceType.BISHOP, PieceType.QUEEN):
                        return True
                    break
                cur_x += dx
                cur_y += dy

        return False

    def find_king(self, color: Color) -> Optional[Tuple[int, int]]:
        for r in range(8):
            for f in range(8):
                p = self.board[r][f]
                if p and p.color == color and p.piece_type == PieceType.KING:
                    return (f, r)
        return None

    def is_in_check(self, color: Color) -> bool:
        king_pos = self.find_king(color)
        if not king_pos:
            return False
        return self.is_square_attacked(king_pos, color.opponent)

    # -------------------------------------------------------------------------
    # MOVE GENERATION
    # -------------------------------------------------------------------------
    def generate_pseudo_legal_moves(self, color: Optional[Color] = None) -> List[Move]:
        if color is None:
            color = self.turn

        moves: List[Move] = []
        forward = 1 if color == Color.WHITE else -1
        start_rank = 1 if color == Color.WHITE else 6
        prom_rank = 7 if color == Color.WHITE else 0

        for r in range(8):
            for f in range(8):
                piece = self.board[r][f]
                if not piece or piece.color != color:
                    continue

                pt = piece.piece_type

                # PAWN MOVES
                if pt == PieceType.PAWN:
                    # 1 Step forward
                    next_r = r + forward
                    if 0 <= next_r < 8 and self.board[next_r][f] is None:
                        if next_r == prom_rank:
                            for prom_choice in [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]:
                                moves.append(Move((f, r), (f, next_r), promotion=prom_choice))
                        else:
                            moves.append(Move((f, r), (f, next_r)))

                        # 2 Steps forward from initial rank
                        two_step_r = r + 2 * forward
                        if r == start_rank and self.board[two_step_r][f] is None:
                            moves.append(Move((f, r), (f, two_step_r)))

                    # Diagonal Captures & En Passant
                    for df in (-1, 1):
                        cf = f + df
                        if 0 <= cf < 8 and 0 <= next_r < 8:
                            target = self.board[next_r][cf]
                            if target and target.color == color.opponent:
                                if next_r == prom_rank:
                                    for prom_choice in [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]:
                                        moves.append(Move((f, r), (cf, next_r), promotion=prom_choice, captured_piece=target))
                                else:
                                    moves.append(Move((f, r), (cf, next_r), captured_piece=target))
                            # En Passant capture
                            elif self.en_passant_sq == (cf, next_r):
                                cap_pawn = self.board[r][cf]
                                moves.append(Move((f, r), (cf, next_r), is_en_passant=True, captured_piece=cap_pawn))

                # KNIGHT MOVES
                elif pt == PieceType.KNIGHT:
                    offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
                    for df, dr in offsets:
                        nf, nr = f + df, r + dr
                        if 0 <= nf < 8 and 0 <= nr < 8:
                            target = self.board[nr][nf]
                            if not target or target.color == color.opponent:
                                moves.append(Move((f, r), (nf, nr), captured_piece=target))

                # KING MOVES (Normal + Castling)
                elif pt == PieceType.KING:
                    offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                    for df, dr in offsets:
                        nf, nr = f + df, r + dr
                        if 0 <= nf < 8 and 0 <= nr < 8:
                            target = self.board[nr][nf]
                            if not target or target.color == color.opponent:
                                moves.append(Move((f, r), (nf, nr), captured_piece=target))

                    # Castling (FIDE requirements strictly enforced)
                    rank = 0 if color == Color.WHITE else 7
                    if r == rank and f == 4 and not self.is_in_check(color):
                        # Kingside (O-O)
                        k_flag = 'K' if color == Color.WHITE else 'k'
                        if self.castling_rights[k_flag]:
                            if (self.board[rank][5] is None and self.board[rank][6] is None and
                                    self.board[rank][7] and self.board[rank][7].piece_type == PieceType.ROOK and
                                    self.board[rank][7].color == color):
                                # Transit square (f) and destination (g) must not be attacked
                                if (not self.is_square_attacked((5, rank), color.opponent) and
                                        not self.is_square_attacked((6, rank), color.opponent)):
                                    moves.append(Move((4, rank), (6, rank), is_castling=True))

                        # Queenside (O-O-O)
                        q_flag = 'Q' if color == Color.WHITE else 'q'
                        if self.castling_rights[q_flag]:
                            if (self.board[rank][3] is None and self.board[rank][2] is None and self.board[rank][1] is None and
                                    self.board[rank][0] and self.board[rank][0].piece_type == PieceType.ROOK and
                                    self.board[rank][0].color == color):
                                # Transit square (d) and destination (c) must not be attacked
                                if (not self.is_square_attacked((3, rank), color.opponent) and
                                        not self.is_square_attacked((2, rank), color.opponent)):
                                    moves.append(Move((4, rank), (2, rank), is_castling=True))

                # SLIDING PIECES (Rook, Bishop, Queen)
                else:
                    directions = []
                    if pt in (PieceType.ROOK, PieceType.QUEEN):
                        directions.extend([(-1, 0), (1, 0), (0, -1), (0, 1)])
                    if pt in (PieceType.BISHOP, PieceType.QUEEN):
                        directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])

                    for df, dr in directions:
                        nf, nr = f + df, r + dr
                        while 0 <= nf < 8 and 0 <= nr < 8:
                            target = self.board[nr][nf]
                            if not target:
                                moves.append(Move((f, r), (nf, nr)))
                            elif target.color == color.opponent:
                                moves.append(Move((f, r), (nf, nr), captured_piece=target))
                                break
                            else:
                                break
                            nf += df
                            nr += dr

        return moves

    def generate_legal_moves(self) -> List[Move]:
        """Filters candidate moves: A move is strictly illegal if King remains or falls in check."""
        pseudo_moves = self.generate_pseudo_legal_moves(self.turn)
        legal_moves = []
        for m in pseudo_moves:
            if self._test_move_legality(m):
                legal_moves.append(m)
        return legal_moves

    def _test_move_legality(self, move: Move) -> bool:
        # Save snapshot
        state = self._push_state(move)
        self._apply_move_internal(move)
        is_legal = not self.is_in_check(state['turn'])
        self._pop_state(state)
        return is_legal

    # -------------------------------------------------------------------------
    # MOVE EXECUTION & UNDO
    # -------------------------------------------------------------------------
    def _push_state(self, move: Move) -> dict:
        return {
            'board': [row[:] for row in self.board],
            'turn': self.turn,
            'castling_rights': self.castling_rights.copy(),
            'en_passant_sq': self.en_passant_sq,
            'halfmove_clock': self.halfmove_clock,
            'fullmove_number': self.fullmove_number,
            'move': move
        }

    def _pop_state(self, state: dict):
        self.board = state['board']
        self.turn = state['turn']
        self.castling_rights = state['castling_rights']
        self.en_passant_sq = state['en_passant_sq']
        self.halfmove_clock = state['halfmove_clock']
        self.fullmove_number = state['fullmove_number']

    def _apply_move_internal(self, move: Move):
        f1, r1 = move.from_sq
        f2, r2 = move.to_sq
        piece = self.board[r1][f1]

        # Reset En Passant target unless a 2-step pawn push occurs
        new_ep_sq = None

        # Halfmove clock reset condition: pawn move or piece capture
        if piece.piece_type == PieceType.PAWN or self.board[r2][f2] is not None or move.is_en_passant:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # Move execution
        if move.is_en_passant:
            self.board[r2][f2] = piece
            self.board[r1][f1] = None
            # Captured pawn is on the same rank as r1, file f2
            self.board[r1][f2] = None

        elif move.is_castling:
            self.board[r2][f2] = piece
            self.board[r1][f1] = None
            # Move corresponding Rook
            if f2 == 6:  # Kingside
                rook = self.board[r1][7]
                self.board[r1][5] = rook
                self.board[r1][7] = None
            elif f2 == 2:  # Queenside
                rook = self.board[r1][0]
                self.board[r1][3] = rook
                self.board[r1][0] = None

        elif move.promotion:
            self.board[r2][f2] = Piece(move.promotion, piece.color)
            self.board[r1][f1] = None

        else:
            # 2-step pawn push creates en passant target
            if piece.piece_type == PieceType.PAWN and abs(r2 - r1) == 2:
                new_ep_sq = (f1, (r1 + r2) // 2)

            self.board[r2][f2] = piece
            self.board[r1][f1] = None

        self.en_passant_sq = new_ep_sq

        # Castling Rights updates
        if piece.piece_type == PieceType.KING:
            if piece.color == Color.WHITE:
                self.castling_rights['K'] = False
                self.castling_rights['Q'] = False
            else:
                self.castling_rights['k'] = False
                self.castling_rights['q'] = False

        if piece.piece_type == PieceType.ROOK:
            if (f1, r1) == (0, 0): self.castling_rights['Q'] = False
            elif (f1, r1) == (7, 0): self.castling_rights['K'] = False
            elif (f1, r1) == (0, 7): self.castling_rights['q'] = False
            elif (f1, r1) == (7, 7): self.castling_rights['k'] = False

        # If a Rook is captured on its original corner
        if (f2, r2) == (0, 0): self.castling_rights['Q'] = False
        elif (f2, r2) == (7, 0): self.castling_rights['K'] = False
        elif (f2, r2) == (0, 7): self.castling_rights['q'] = False
        elif (f2, r2) == (7, 7): self.castling_rights['k'] = False

        if self.turn == Color.BLACK:
            self.fullmove_number += 1
        self.turn = self.turn.opponent

    def make_move(self, move: Move) -> bool:
        """Executes a move if it is strictly legal."""
        legal_moves = self.generate_legal_moves()
        match = None
        for m in legal_moves:
            if m.from_sq == move.from_sq and m.to_sq == move.to_sq:
                if move.promotion:
                    if m.promotion == move.promotion:
                        match = m
                        break
                else:
                    match = m
                    break

        if not match:
            return False

        # Record state for undo & repetition
        state = self._push_state(match)
        self.state_history.append(state)
        self.move_history.append(match)

        self._apply_move_internal(match)
        self.fen_history.append(self.get_position_key())
        return True

    def make_uci_move(self, uci_str: str) -> bool:
        """Parses and executes a move in standard UCI notation (e.g. 'e2e4', 'e7e8q')."""
        uci_str = uci_str.strip().lower()
        if len(uci_str) < 4:
            return False

        from_sq = Move.str_to_square(uci_str[0:2])
        to_sq = Move.str_to_square(uci_str[2:4])
        promotion = None
        if len(uci_str) == 5:
            pt_map = {'q': PieceType.QUEEN, 'r': PieceType.ROOK, 'b': PieceType.BISHOP, 'n': PieceType.KNIGHT}
            promotion = pt_map.get(uci_str[4])

        m = Move(from_sq, to_sq, promotion=promotion)
        return self.make_move(m)

    def undo_move(self) -> bool:
        if not self.state_history:
            return False
        last_state = self.state_history.pop()
        self.move_history.pop()
        self.fen_history.pop()
        self._pop_state(last_state)
        return True

    # -------------------------------------------------------------------------
    # MATCH TERMINATION & FIDE DRAW CONDITIONS
    # -------------------------------------------------------------------------
    def is_insufficient_material(self) -> bool:
        """
        FIDE Insufficient Material Automatic Draw:
        - King vs King
        - King + Bishop vs King
        - King + Knight vs King
        - King + Bishop vs King + Bishop (where both bishops are on the same square color)
        """
        pieces_w: List[Tuple[PieceType, Tuple[int, int]]] = []
        pieces_b: List[Tuple[PieceType, Tuple[int, int]]] = []

        for r in range(8):
            for f in range(8):
                p = self.board[r][f]
                if p:
                    if p.color == Color.WHITE:
                        pieces_w.append((p.piece_type, (f, r)))
                    else:
                        pieces_b.append((p.piece_type, (f, r)))

        # If any Pawns, Rooks, or Queens remain, material is sufficient
        for pt, _ in pieces_w + pieces_b:
            if pt in (PieceType.PAWN, PieceType.ROOK, PieceType.QUEEN):
                return False

        types_w = [pt for pt, _ in pieces_w]
        types_b = [pt for pt, _ in pieces_b]

        # K vs K
        if types_w == [PieceType.KING] and types_b == [PieceType.KING]:
            return True

        # K + B vs K or K + N vs K
        if types_w == [PieceType.KING] and len(types_b) == 2 and (PieceType.BISHOP in types_b or PieceType.KNIGHT in types_b):
            return True
        if types_b == [PieceType.KING] and len(types_w) == 2 and (PieceType.BISHOP in types_w or PieceType.KNIGHT in types_w):
            return True

        # K + B vs K + B (same square color bishops)
        if len(pieces_w) == 2 and len(pieces_b) == 2:
            if PieceType.BISHOP in types_w and PieceType.BISHOP in types_b:
                wb_sq = [sq for pt, sq in pieces_w if pt == PieceType.BISHOP][0]
                bb_sq = [sq for pt, sq in pieces_b if pt == PieceType.BISHOP][0]
                wb_color = (wb_sq[0] + wb_sq[1]) % 2
                bb_color = (bb_sq[0] + bb_sq[1]) % 2
                if wb_color == bb_color:
                    return True

        return False

    def is_threefold_repetition(self) -> bool:
        """Checks if identical position, rights, and turns occurred 3+ times."""
        current_key = self.get_position_key()
        count = self.fen_history.count(current_key)
        return count >= 3

    def get_game_status(self) -> Tuple[GameStatus, str]:
        legal_moves = self.generate_legal_moves()
        in_check = self.is_in_check(self.turn)

        if not legal_moves:
            if in_check:
                winner = "Hitam (Black)" if self.turn == Color.WHITE else "Putih (White)"
                return (GameStatus.CHECKMATE, f"Skakmat! {winner} menang.")
            else:
                return (GameStatus.STALEMATE, "Remis (Stalemate): Tidak ada langkah sah.")

        if self.halfmove_clock >= 100:
            return (GameStatus.DRAW_FIFTY_MOVES, "Remis: 50 langkah tanpa bidak maju atau penangkapan.")

        if self.is_threefold_repetition():
            return (GameStatus.DRAW_THREEFOLD_REPETITION, "Remis: Posisi papan berulang 3 kali (Threefold Repetition).")

        if self.is_insufficient_material():
            return (GameStatus.DRAW_INSUFFICIENT_MATERIAL, "Remis: Sisa bidak tidak cukup untuk skakmat.")

        return (GameStatus.ACTIVE, "Giliran " + ("Putih" if self.turn == Color.WHITE else "Hitam"))


# =============================================================================
# SELF-VERIFICATION & UNIT TESTS
# =============================================================================
def run_unit_tests():
    print("=" * 60)
    print("RUNNING FIDE CHESS ENGINE UNIT TESTS")
    print("=" * 60)

    # 1. En Passant Expiry Test
    # Move e2-e4 (White), a7-a6 (Black), e4-e5 (White), d7-d5 (Black: triggers ep on d6).
    # White plays h2-h3 (ignores ep) -> On next turn, ep on d6 must expire!
    board = ChessBoard()
    board.make_uci_move("e2e4")
    board.make_uci_move("a7a6")
    board.make_uci_move("e4e5")
    board.make_uci_move("d7d5")
    assert board.en_passant_sq == (3, 5), "En passant square should be d6 immediately after d7-d5"
    board.make_uci_move("h2h3")  # White plays another move
    assert board.en_passant_sq is None, "En passant opportunity must expire after 1 move"
    print("[PASS] Test 1: En Passant creation and expiration verified.")

    # 2. Castling Through Check Prevention Test
    # White King e1, Rook h1. Black Queen on e8 attacking e1 (check) or f1 (transit attack).
    fen = "4k3/8/8/8/8/8/8/4K2R w K - 0 1"
    b_castle = ChessBoard(fen)
    legal = [m.to_uci() for m in b_castle.generate_legal_moves()]
    assert "e1g1" in legal, "Castling should be legal when path is clean and safe"

    # Put Black Rook on f8 attacking transit square f1
    fen_transit = "4kr2/8/8/8/8/8/8/4K2R w K - 0 1"
    b_transit = ChessBoard(fen_transit)
    legal_transit = [m.to_uci() for m in b_transit.generate_legal_moves()]
    assert "e1g1" not in legal_transit, "Castling through check (f1 under attack) must be illegal"
    print("[PASS] Test 2: Castling through check blocked strictly per FIDE.")

    # 3. Pinned Piece King Safety Test
    # White King on e1, White Bishop on e2, Black Rook on e8 (Bishop is absolutely pinned).
    fen_pin = "4r1k1/8/8/8/8/8/4B3/4K3 w - - 0 1"
    b_pin = ChessBoard(fen_pin)
    legal_pin = [m.to_uci() for m in b_pin.generate_legal_moves()]
    # Bishop on e2 cannot move to d3, c4, f3, etc. because King would be exposed to e8 Rook!
    bishop_moves = [m for m in legal_pin if m.startswith("e2")]
    assert len(bishop_moves) == 0, f"Pinned piece must not be allowed to move: {bishop_moves}"
    print("[PASS] Test 3: Absolute pin and King safety verified.")

    # 4. Pawn Promotion with Check/Checkmate Test
    # White pawn on a7 ready to promote on a8. Black King on h8.
    fen_prom = "7k/P7/8/8/8/8/8/K7 w - - 0 1"
    b_prom = ChessBoard(fen_prom)
    assert b_prom.make_uci_move("a7a8q"), "Promotion to Queen must succeed"
    assert b_prom.board[7][0].piece_type == PieceType.QUEEN, "Promoted piece must be Queen"
    print("[PASS] Test 4: Pawn promotion to Queen verified.")

    # 5. Threefold Repetition Test
    b_rep = ChessBoard()
    for _ in range(2):
        b_rep.make_uci_move("g1f3")
        b_rep.make_uci_move("g8f6")
        b_rep.make_uci_move("f3g1")
        b_rep.make_uci_move("f6g8")
    status, desc = b_rep.get_game_status()
    assert status == GameStatus.DRAW_THREEFOLD_REPETITION, "Threefold repetition must trigger draw"
    print("[PASS] Test 5: Threefold repetition draw verified.")

    print("=" * 60)
    print("ALL 5 FIDE UNIT TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_unit_tests()
