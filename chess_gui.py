"""
Master Chess GUI - Official FIDE Interactive Interface
======================================================
Module: chess_gui.py
Part of GAME AHMAD Suite
"""

import pygame
import sys
import math
import random
from typing import Optional, Tuple, List
from chess_engine import ChessBoard, Color, PieceType, Piece, Move, GameStatus

# Color Theme
BG_COLOR = (15, 23, 42)
PANEL_COLOR = (30, 41, 59)
PANEL_BORDER = (51, 65, 85)
LIGHT_SQ = (240, 217, 181)
DARK_SQ = (181, 136, 99)
SELECT_COLOR = (255, 235, 59, 140)
LAST_MOVE_COLOR = (129, 140, 248, 110)
CHECK_COLOR = (239, 68, 68, 160)
MOVE_DOT_COLOR = (34, 197, 94, 180)
CAPTURE_RING_COLOR = (239, 68, 68, 200)

GOLD = (250, 204, 21)
WHITE = (255, 255, 255)
CYAN = (0, 240, 255)
TEXT_MUTED = (148, 163, 184)

SQ_SIZE = 64
BOARD_SIZE = SQ_SIZE * 8  # 512 x 512
BOARD_X = 50
BOARD_Y = 60

# =============================================================================
# PROCEDURAL PIECE RENDERER (Crisp Vector Glyphs, Zero External Asset Dep)
# =============================================================================
def draw_piece(surface: pygame.Surface, piece: Piece, x: int, y: int, size: int):
    cx = x + size // 2
    cy = y + size // 2

    is_white = piece.color == Color.WHITE
    body_color = (252, 252, 252) if is_white else (35, 39, 45)
    border_color = (50, 50, 50) if is_white else (210, 215, 225)
    inner_detail = (200, 205, 215) if is_white else (75, 85, 99)

    pt = piece.piece_type

    # Base Pedestal for all pieces
    base_w = int(size * 0.6)
    base_h = int(size * 0.12)
    base_y = cy + int(size * 0.28)
    pygame.draw.ellipse(surface, body_color, (cx - base_w // 2, base_y, base_w, base_h))
    pygame.draw.ellipse(surface, border_color, (cx - base_w // 2, base_y, base_w, base_h), width=2)

    if pt == PieceType.PAWN:
        # Pawn Head & Neck
        r = int(size * 0.17)
        pygame.draw.circle(surface, body_color, (cx, cy - int(size * 0.08)), r)
        pygame.draw.circle(surface, border_color, (cx, cy - int(size * 0.08)), r, width=2)
        # Body cone
        pts = [(cx - int(size * 0.18), base_y + 2), (cx + int(size * 0.18), base_y + 2),
               (cx + int(size * 0.08), cy), (cx - int(size * 0.08), cy)]
        pygame.draw.polygon(surface, body_color, pts)
        pygame.draw.polygon(surface, border_color, pts, width=2)

    elif pt == PieceType.KNIGHT:
        # Horse Head & Mane
        pts = [
            (cx - int(size * 0.2), base_y + 2),
            (cx + int(size * 0.2), base_y + 2),
            (cx + int(size * 0.18), cy - int(size * 0.05)),
            (cx + int(size * 0.05), cy - int(size * 0.28)),
            (cx - int(size * 0.1), cy - int(size * 0.28)),
            (cx - int(size * 0.24), cy - int(size * 0.12)),
            (cx - int(size * 0.24), cy),
            (cx - int(size * 0.1), cy + int(size * 0.05)),
        ]
        pygame.draw.polygon(surface, body_color, pts)
        pygame.draw.polygon(surface, border_color, pts, width=2)
        # Eye
        eye_color = (40, 40, 40) if is_white else (230, 230, 230)
        pygame.draw.circle(surface, eye_color, (cx - int(size * 0.1), cy - int(size * 0.15)), 2)

    elif pt == PieceType.BISHOP:
        # Mitre oval & ball
        body_r = int(size * 0.2)
        pygame.draw.ellipse(surface, body_color, (cx - body_r, cy - int(size * 0.22), body_r * 2, int(size * 0.45)))
        pygame.draw.ellipse(surface, border_color, (cx - body_r, cy - int(size * 0.22), body_r * 2, int(size * 0.45)), width=2)
        # Top ball
        pygame.draw.circle(surface, body_color, (cx, cy - int(size * 0.24)), 4)
        pygame.draw.circle(surface, border_color, (cx, cy - int(size * 0.24)), 4, width=1)
        # Cross slit
        slit_c = border_color
        pygame.draw.line(surface, slit_c, (cx - 4, cy - int(size * 0.08)), (cx + 4, cy - int(size * 0.02)), 2)

    elif pt == PieceType.ROOK:
        # Castle Tower with Battlements
        tower_w = int(size * 0.36)
        tower_h = int(size * 0.42)
        ty = cy - int(size * 0.16)
        pygame.draw.rect(surface, body_color, (cx - tower_w // 2, ty, tower_w, tower_h))
        pygame.draw.rect(surface, border_color, (cx - tower_w // 2, ty, tower_w, tower_h), width=2)
        # Battlements (crenellations)
        bw = tower_w // 4
        bh = int(size * 0.1)
        for i in [0, 2]:
            pygame.draw.rect(surface, body_color, (cx - tower_w // 2 + i * bw, ty - bh + 2, bw, bh))
            pygame.draw.rect(surface, border_color, (cx - tower_w // 2 + i * bw, ty - bh + 2, bw, bh), width=2)

    elif pt == PieceType.QUEEN:
        # Coronet with 5 crown points
        body_w = int(size * 0.38)
        body_h = int(size * 0.4)
        ty = cy - int(size * 0.12)
        pts = [
            (cx - body_w // 2, base_y),
            (cx + body_w // 2, base_y),
            (cx + body_w // 2 + 3, ty - 6),
            (cx + body_w // 4, ty + 4),
            (cx, ty - 8),
            (cx - body_w // 4, ty + 4),
            (cx - body_w // 2 - 3, ty - 6),
        ]
        pygame.draw.polygon(surface, body_color, pts)
        pygame.draw.polygon(surface, border_color, pts, width=2)
        # Jewels on tips
        for px in [cx - body_w // 2 - 3, cx, cx + body_w // 2 + 3]:
            pygame.draw.circle(surface, GOLD, (px, ty - 8), 3)

    elif pt == PieceType.KING:
        # Royal Robe & FIDE Cross Crown
        body_w = int(size * 0.42)
        ty = cy - int(size * 0.15)
        pts = [
            (cx - body_w // 2, base_y),
            (cx + body_w // 2, base_y),
            (cx + body_w // 2 + 2, ty),
            (cx, ty - 6),
            (cx - body_w // 2 - 2, ty),
        ]
        pygame.draw.polygon(surface, body_color, pts)
        pygame.draw.polygon(surface, border_color, pts, width=2)
        # Distinctive Cross
        cross_c = GOLD if is_white else (230, 230, 230)
        cross_y = ty - 10
        pygame.draw.line(surface, cross_c, (cx, cross_y - 8), (cx, cross_y + 4), 3)
        pygame.draw.line(surface, cross_c, (cx - 5, cross_y - 2), (cx + 5, cross_y - 2), 3)


def draw_trophy(surface: pygame.Surface, cx: int, cy: int, color: Tuple[int, int, int]):
    """Renders an elegant vector trophy icon for game victory / status dialogs."""
    # Pedestal Base
    pygame.draw.rect(surface, color, (cx - 20, cy + 12, 40, 6), border_radius=2)
    pygame.draw.rect(surface, color, (cx - 7, cy + 3, 14, 10))
    # Cup polygon
    pts = [(cx - 24, cy - 20), (cx + 24, cy - 20), (cx + 15, cy + 3), (cx - 15, cy + 3)]
    pygame.draw.polygon(surface, color, pts)
    pygame.draw.ellipse(surface, color, (cx - 24, cy - 24, 48, 8))
    # Left & Right handles
    pygame.draw.circle(surface, color, (cx - 23, cy - 8), 10, width=3)
    pygame.draw.circle(surface, color, (cx + 23, cy - 8), 10, width=3)
    # Center emblem star / spark
    pygame.draw.circle(surface, (255, 255, 255), (cx, cy - 8), 3)



# =============================================================================
# EVALUATION & HEURISTIC ENGINE (Fast Tactical AI)
# =============================================================================
PIECE_VALUES = {
    PieceType.PAWN: 100,
    PieceType.KNIGHT: 320,
    PieceType.BISHOP: 330,
    PieceType.ROOK: 500,
    PieceType.QUEEN: 900,
    PieceType.KING: 20000
}

CENTER_SCORES = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [5, -5, 15, 25, 25, 15, -5, 5],
    [0, 0, 20, 30, 30, 20, 0, 0],
    [0, 5, 20, 30, 30, 20, 5, 0],
    [5, 10, 15, 25, 25, 15, 10, 5],
    [5, 10, 10, 10, 10, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0]
]

def evaluate_board(board: ChessBoard) -> int:
    score = 0
    for r in range(8):
        for f in range(8):
            p = board.board[r][f]
            if p:
                val = PIECE_VALUES[p.piece_type]
                pst = CENTER_SCORES[r][f] if p.color == Color.WHITE else CENTER_SCORES[7 - r][f]
                total = val + pst
                score += total if p.color == Color.WHITE else -total
    return score

def get_best_move(board: ChessBoard, depth: int = 2) -> Optional[Move]:
    moves = board.generate_legal_moves()
    if not moves:
        return None

    # Sort moves: captures & promotions first
    def move_priority(m: Move) -> int:
        p = 0
        if m.captured_piece:
            p += PIECE_VALUES[m.captured_piece.piece_type] * 10
        if m.promotion:
            p += PIECE_VALUES[m.promotion] * 5
        if m.is_castling:
            p += 50
        return p

    moves.sort(key=move_priority, reverse=True)

    is_white = board.turn == Color.WHITE
    best_move = random.choice(moves)
    best_eval = -999999 if is_white else 999999

    for m in moves:
        board.make_move(m)
        val = evaluate_board(board)
        board.undo_move()

        if is_white:
            if val > best_eval:
                best_eval = val
                best_move = m
        else:
            if val < best_eval:
                best_eval = val
                best_move = m

    return best_move


# =============================================================================
# CHESS GUI MAIN FUNCTION
# =============================================================================
def run_chess(screen: pygame.Surface, clock: pygame.time.Clock):
    W, H = screen.get_size()

    font_title = pygame.font.SysFont("helvetica", 24, bold=True)
    font_bold = pygame.font.SysFont("helvetica", 16, bold=True)
    font_reg = pygame.font.SysFont("helvetica", 14, bold=False)
    font_sub = pygame.font.SysFont("helvetica", 12, bold=False)
    font_moves = pygame.font.SysFont("courier", 13, bold=False)

    font_modal_title = pygame.font.SysFont("helvetica", 23, bold=True)
    font_modal_sub = pygame.font.SysFont("helvetica", 16, bold=True)
    font_btn_main = pygame.font.SysFont("helvetica", 15, bold=True)
    font_btn_hint = pygame.font.SysFont("helvetica", 11, bold=False)

    # Game Over Pop-up Modal Geometry
    modal_gameover_w = 480
    modal_gameover_h = 280
    mg_x = (W - modal_gameover_w) // 2
    mg_y = (H - modal_gameover_h) // 2
    btn_replay_rect = pygame.Rect(mg_x + 35, mg_y + 195, 195, 58)
    btn_quit_rect = pygame.Rect(mg_x + 250, mg_y + 195, 195, 58)

    board = ChessBoard()
    selected_sq: Optional[Tuple[int, int]] = None
    legal_destinations: List[Move] = []
    last_move: Optional[Move] = None

    # Game Modes: 0 = Human (White) vs AI (Black), 1 = Human vs Human, 2 = AI (White) vs Human (Black), 3 = AI vs AI
    game_mode = 0
    mode_names = ["Player (Putih) vs AI (Hitam)", "2 Pemain (Pass & Play)", "AI (Putih) vs Player (Hitam)", "AI vs AI (Simulasi)"]

    pending_promotion_move: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
    ai_thinking_timer = 0

    running = True
    while running:
        status_enum, status_desc = board.get_game_status()
        is_game_over = status_enum != GameStatus.ACTIVE

        is_ai_turn = False
        if not is_game_over:
            if game_mode == 0 and board.turn == Color.BLACK:
                is_ai_turn = True
            elif game_mode == 2 and board.turn == Color.WHITE:
                is_ai_turn = True
            elif game_mode == 3:
                is_ai_turn = True

        # AI Move execution
        if is_ai_turn and pending_promotion_move is None:
            ai_thinking_timer += 1
            if ai_thinking_timer >= 18:
                ai_thinking_timer = 0
                best_m = get_best_move(board, depth=2)
                if best_m:
                    board.make_move(best_m)
                    last_move = best_m
                    selected_sq = None
                    legal_destinations.clear()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            elif event.type == pygame.KEYDOWN:
                if is_game_over:
                    if event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                        board = ChessBoard()
                        selected_sq = None
                        legal_destinations.clear()
                        last_move = None
                        pending_promotion_move = None
                        continue
                    elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                        return "MENU"
                else:
                    if event.key == pygame.K_ESCAPE:
                        return "MENU"
                    elif event.key == pygame.K_u:
                        # Undo move
                        board.undo_move()
                        if game_mode in (0, 2) and board.state_history:
                            board.undo_move()
                        selected_sq = None
                        legal_destinations.clear()
                        last_move = board.move_history[-1] if board.move_history else None
                    elif event.key == pygame.K_r:
                        board = ChessBoard()
                        selected_sq = None
                        legal_destinations.clear()
                        last_move = None
                        pending_promotion_move = None
                    elif event.key == pygame.K_m:
                        game_mode = (game_mode + 1) % len(mode_names)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # 0. Check Game Over popup clicks first
                if is_game_over:
                    if btn_replay_rect.collidepoint(mx, my):
                        board = ChessBoard()
                        selected_sq = None
                        legal_destinations.clear()
                        last_move = None
                        pending_promotion_move = None
                    elif btn_quit_rect.collidepoint(mx, my):
                        return "MENU"
                    continue

                # 1. Check promotion popup clicks
                if pending_promotion_move:
                    modal_x = W // 2 - 140
                    modal_y = H // 2 - 50
                    choices = [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]
                    for idx, pt in enumerate(choices):
                        btn_rect = pygame.Rect(modal_x + 15 + idx * 65, modal_y + 35, 55, 55)
                        if btn_rect.collidepoint(mx, my):
                            from_s, to_s = pending_promotion_move
                            prom_move = Move(from_s, to_s, promotion=pt)
                            if board.make_move(prom_move):
                                last_move = prom_move
                            pending_promotion_move = None
                            selected_sq = None
                            legal_destinations.clear()
                            break
                    continue

                # 2. Check panel button clicks
                btn_undo = pygame.Rect(W - 320, H - 110, 135, 36)
                btn_restart = pygame.Rect(W - 170, H - 110, 135, 36)
                btn_mode = pygame.Rect(W - 320, 280, 285, 34)

                if btn_undo.collidepoint(mx, my):
                    board.undo_move()
                    if game_mode in (0, 2) and board.state_history:
                        board.undo_move()
                    selected_sq = None
                    legal_destinations.clear()
                    last_move = board.move_history[-1] if board.move_history else None
                    continue
                elif btn_restart.collidepoint(mx, my):
                    board = ChessBoard()
                    selected_sq = None
                    legal_destinations.clear()
                    last_move = None
                    continue
                elif btn_mode.collidepoint(mx, my):
                    game_mode = (game_mode + 1) % len(mode_names)
                    continue

                # 3. Check Board square clicks
                if BOARD_X <= mx < BOARD_X + BOARD_SIZE and BOARD_Y <= my < BOARD_Y + BOARD_SIZE:
                    file_clicked = (mx - BOARD_X) // SQ_SIZE
                    # In standard chess, rank 8 is top (y index 0), rank 1 is bottom (y index 7)
                    rank_clicked = 7 - ((my - BOARD_Y) // SQ_SIZE)
                    sq_clicked = (file_clicked, rank_clicked)

                    # Destination clicked?
                    dest_match = [m for m in legal_destinations if m.to_sq == sq_clicked]
                    if dest_match:
                        # Check promotion
                        p_moving = board.get_piece(selected_sq[0], selected_sq[1])
                        if p_moving and p_moving.piece_type == PieceType.PAWN and (sq_clicked[1] in (0, 7)):
                            pending_promotion_move = (selected_sq, sq_clicked)
                        else:
                            board.make_move(dest_match[0])
                            last_move = dest_match[0]
                            selected_sq = None
                            legal_destinations.clear()
                    else:
                        # Select piece of active color
                        p = board.get_piece(file_clicked, rank_clicked)
                        if p and p.color == board.turn:
                            selected_sq = sq_clicked
                            all_legal = board.generate_legal_moves()
                            legal_destinations = [m for m in all_legal if m.from_sq == selected_sq]
                        else:
                            selected_sq = None
                            legal_destinations.clear()

        # =============================================================
        # RENDER
        # =============================================================
        screen.fill(BG_COLOR)

        # 1. Draw 8x8 Chessboard
        # Outer border
        pygame.draw.rect(screen, (71, 85, 105), (BOARD_X - 6, BOARD_Y - 6, BOARD_SIZE + 12, BOARD_SIZE + 12), width=3, border_radius=6)

        king_in_check_sq = board.find_king(board.turn) if board.is_in_check(board.turn) else None

        for r in range(8):
            for f in range(8):
                # r=0 is Rank 1 (drawn at bottom, y_idx = 7)
                draw_y = BOARD_Y + (7 - r) * SQ_SIZE
                draw_x = BOARD_X + f * SQ_SIZE
                sq_rect = pygame.Rect(draw_x, draw_y, SQ_SIZE, SQ_SIZE)

                # Base square color
                is_light = (f + r) % 2 == 1
                color = LIGHT_SQ if is_light else DARK_SQ
                pygame.draw.rect(screen, color, sq_rect)

                # Last move highlight
                if last_move and (sq_rect.collidepoint(BOARD_X + last_move.from_sq[0] * SQ_SIZE + 10,
                                                       BOARD_Y + (7 - last_move.from_sq[1]) * SQ_SIZE + 10) or
                                  sq_rect.collidepoint(BOARD_X + last_move.to_sq[0] * SQ_SIZE + 10,
                                                       BOARD_Y + (7 - last_move.to_sq[1]) * SQ_SIZE + 10)):
                    overlay = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
                    pygame.draw.rect(overlay, LAST_MOVE_COLOR, (0, 0, SQ_SIZE, SQ_SIZE))
                    screen.blit(overlay, (draw_x, draw_y))

                # King in Check highlight
                if king_in_check_sq and (f, r) == king_in_check_sq:
                    overlay = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
                    pygame.draw.rect(overlay, CHECK_COLOR, (0, 0, SQ_SIZE, SQ_SIZE))
                    screen.blit(overlay, (draw_x, draw_y))

                # Selected square highlight
                if selected_sq == (f, r):
                    overlay = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
                    pygame.draw.rect(overlay, SELECT_COLOR, (0, 0, SQ_SIZE, SQ_SIZE))
                    screen.blit(overlay, (draw_x, draw_y))

                # Draw Piece
                piece = board.board[r][f]
                if piece:
                    draw_piece(screen, piece, draw_x, draw_y, SQ_SIZE)

                # Legal Move hints
                for m in legal_destinations:
                    if m.to_sq == (f, r):
                        hint_surf = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
                        if piece:  # Capture ring
                            pygame.draw.circle(hint_surf, CAPTURE_RING_COLOR, (SQ_SIZE // 2, SQ_SIZE // 2), SQ_SIZE // 2 - 4, width=5)
                        else:  # Move dot
                            pygame.draw.circle(hint_surf, MOVE_DOT_COLOR, (SQ_SIZE // 2, SQ_SIZE // 2), 11)
                        screen.blit(hint_surf, (draw_x, draw_y))

        # Files (a-h) and Ranks (1-8) labels
        for f in range(8):
            lbl = font_sub.render(chr(ord('a') + f), True, TEXT_MUTED)
            screen.blit(lbl, (BOARD_X + f * SQ_SIZE + SQ_SIZE // 2 - 4, BOARD_Y + BOARD_SIZE + 6))
        for r in range(8):
            lbl = font_sub.render(str(r + 1), True, TEXT_MUTED)
            screen.blit(lbl, (BOARD_X - 18, BOARD_Y + (7 - r) * SQ_SIZE + SQ_SIZE // 2 - 6))

        # 2. Side Dashboard Panel
        panel_x = W - 350
        panel_rect = pygame.Rect(panel_x, BOARD_Y - 6, 320, BOARD_SIZE + 12)
        pygame.draw.rect(screen, PANEL_COLOR, panel_rect, border_radius=12)
        pygame.draw.rect(screen, PANEL_BORDER, panel_rect, width=2, border_radius=12)

        # Title & Badges
        screen.blit(font_title.render("MASTER CHESS", True, GOLD), (panel_x + 20, BOARD_Y + 14))
        screen.blit(font_sub.render("FIDE Rules Compliant Engine", True, TEXT_MUTED), (panel_x + 20, BOARD_Y + 44))

        # Status & Turn indicator
        status_enum, status_desc = board.get_game_status()
        turn_color_str = "Putih (White)" if board.turn == Color.WHITE else "Hitam (Black)"
        turn_badge_c = WHITE if board.turn == Color.WHITE else (71, 85, 105)

        turn_bg = pygame.Rect(panel_x + 20, BOARD_Y + 70, 280, 50)
        pygame.draw.rect(screen, (20, 28, 44), turn_bg, border_radius=8)
        pygame.draw.circle(screen, turn_badge_c, (panel_x + 42, BOARD_Y + 95), 10)
        pygame.draw.circle(screen, (255, 255, 255), (panel_x + 42, BOARD_Y + 95), 10, width=1)
        screen.blit(font_bold.render(f"Giliran: {turn_color_str}", True, WHITE), (panel_x + 62, BOARD_Y + 76))
        screen.blit(font_reg.render(f"Langkah #{board.fullmove_number}", True, TEXT_MUTED), (panel_x + 62, BOARD_Y + 96))

        # Game Status Callout
        st_color = GOLD if status_enum == GameStatus.ACTIVE else (239, 68, 68 if "Skakmat" in status_desc else CYAN)
        if board.is_in_check(board.turn) and status_enum == GameStatus.ACTIVE:
            status_desc = f"SKAK! {turn_color_str} dalam ancaman"
            st_color = (239, 68, 68)

        st_box = pygame.Rect(panel_x + 20, BOARD_Y + 130, 280, 36)
        pygame.draw.rect(screen, (20, 28, 44), st_box, border_radius=6)
        pygame.draw.rect(screen, st_color, st_box, width=1, border_radius=6)
        st_txt = font_bold.render(status_desc, True, st_color)
        screen.blit(st_txt, (panel_x + 20 + (280 - st_txt.get_width()) // 2, BOARD_Y + 138))

        # Move History (Last 6 moves)
        screen.blit(font_bold.render("Riwayat Langkah:", True, TEXT_MUTED), (panel_x + 20, BOARD_Y + 178))
        hist_box = pygame.Rect(panel_x + 20, BOARD_Y + 200, 280, 68)
        pygame.draw.rect(screen, (15, 23, 42), hist_box, border_radius=6)
        recent_moves = [m.to_uci() for m in board.move_history[-6:]]
        mv_text = " ".join(recent_moves) if recent_moves else "Belum ada langkah"
        mv_surf = font_moves.render(mv_text, True, CYAN)
        screen.blit(mv_surf, (panel_x + 30, BOARD_Y + 210))

        # Game Mode Button
        screen.blit(font_bold.render("Mode Pertandingan:", True, TEXT_MUTED), (panel_x + 20, BOARD_Y + 276))
        mode_btn = pygame.Rect(panel_x + 20, BOARD_Y + 296, 280, 36)
        pygame.draw.rect(screen, (37, 99, 235), mode_btn, border_radius=8)
        m_txt = font_bold.render(mode_names[game_mode], True, WHITE)
        screen.blit(m_txt, (panel_x + 20 + (280 - m_txt.get_width()) // 2, BOARD_Y + 304))

        # Special FIDE Rules indicator
        fide_box = pygame.Rect(panel_x + 20, BOARD_Y + 346, 280, 80)
        pygame.draw.rect(screen, (20, 28, 44), fide_box, border_radius=8)
        screen.blit(font_bold.render("FIDE Engine Status:", True, GOLD), (panel_x + 30, BOARD_Y + 352))
        ep_txt = f"En Passant: {Move.square_to_str(board.en_passant_sq) if board.en_passant_sq else '-'}"
        cast_txt = f"Rokade: {''.join([k for k, v in board.castling_rights.items() if v]) or '-'}"
        clk_txt = f"50-Move Clock: {board.halfmove_clock} / 100"
        screen.blit(font_sub.render(f"{ep_txt}  |  {cast_txt}", True, TEXT_MUTED), (panel_x + 30, BOARD_Y + 375))
        screen.blit(font_sub.render(clk_txt, True, TEXT_MUTED), (panel_x + 30, BOARD_Y + 395))

        # Buttons (Undo, Restart, Dashboard)
        btn_u = pygame.Rect(panel_x + 20, BOARD_Y + 440, 132, 34)
        btn_r = pygame.Rect(panel_x + 168, BOARD_Y + 440, 132, 34)
        pygame.draw.rect(screen, (51, 65, 85), btn_u, border_radius=6)
        pygame.draw.rect(screen, (51, 65, 85), btn_r, border_radius=6)
        screen.blit(font_bold.render("Undo [U]", True, WHITE), (panel_x + 48, BOARD_Y + 448))
        screen.blit(font_bold.render("Reset [R]", True, WHITE), (panel_x + 196, BOARD_Y + 448))

        btn_esc = pygame.Rect(panel_x + 20, BOARD_Y + 482, 280, 30)
        pygame.draw.rect(screen, (15, 23, 42), btn_esc, border_radius=6)
        pygame.draw.rect(screen, (71, 85, 105), btn_esc, width=1, border_radius=6)
        esc_t = font_sub.render("[ESC] KEMBALI KE GAME AHMAD", True, GOLD)
        screen.blit(esc_t, (panel_x + 20 + (280 - esc_t.get_width()) // 2, BOARD_Y + 490))

        # 3. Pawn Promotion Modal (if active)
        if pending_promotion_move:
            modal_w = 300
            modal_h = 130
            mx_box = (W - modal_w) // 2
            my_box = (H - modal_h) // 2

            m_overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            pygame.draw.rect(m_overlay, (0, 0, 0, 180), (0, 0, W, H))
            screen.blit(m_overlay, (0, 0))

            pygame.draw.rect(screen, (30, 41, 59), (mx_box, my_box, modal_w, modal_h), border_radius=12)
            pygame.draw.rect(screen, GOLD, (mx_box, my_box, modal_w, modal_h), width=2, border_radius=12)

            t_prom = font_bold.render("PILIH BIDAK PROMOSI:", True, GOLD)
            screen.blit(t_prom, (mx_box + (modal_w - t_prom.get_width()) // 2, my_box + 12))

            choices = [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]
            p_col = board.turn
            for idx, pt in enumerate(choices):
                bx = mx_box + 20 + idx * 65
                by = my_box + 45
                b_rect = pygame.Rect(bx, by, 58, 65)
                pygame.draw.rect(screen, (15, 23, 42), b_rect, border_radius=8)
                pygame.draw.rect(screen, (71, 85, 105), b_rect, width=1, border_radius=8)
                draw_piece(screen, Piece(pt, p_col), bx, by, 58)

        # 4. Pop-up Modal Kemenangan / Game Over (Checkmate, Remis, dll)
        if is_game_over:
            # Dark glassmorphism backdrop overlay
            overlay_surf = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay_surf.fill((8, 12, 24, 215))
            screen.blit(overlay_surf, (0, 0))

            # Drop shadow
            shadow_rect = pygame.Rect(mg_x + 5, mg_y + 7, modal_gameover_w, modal_gameover_h)
            pygame.draw.rect(screen, (0, 0, 0, 140), shadow_rect, border_radius=18)

            # Main Card Container
            card_rect = pygame.Rect(mg_x, mg_y, modal_gameover_w, modal_gameover_h)
            pygame.draw.rect(screen, (22, 30, 49), card_rect, border_radius=18)

            is_checkmate = (status_enum == GameStatus.CHECKMATE)
            theme_color = GOLD if is_checkmate else CYAN
            pygame.draw.rect(screen, theme_color, card_rect, width=2, border_radius=18)

            # Trophy Icon
            draw_trophy(screen, W // 2, mg_y + 44, theme_color)

            # Title Header
            title_text = "SKAKMAT! PERMAINAN SELESAI" if is_checkmate else "PERMAINAN BERAKHIR (REMIS)"
            t_head = font_modal_title.render(title_text, True, theme_color)
            screen.blit(t_head, (mg_x + (modal_gameover_w - t_head.get_width()) // 2, mg_y + 76))

            # Winner / Reason description
            if is_checkmate:
                winner_is_white = (board.turn == Color.BLACK)
                if game_mode == 0:  # Player White vs AI Black
                    w_text = "🎉 SELAMAT! ANDA MENANG (PUTIH)" if winner_is_white else "🤖 AI (HITAM) MEMENANGKAN GAME"
                elif game_mode == 2:  # AI White vs Player Black
                    w_text = "🤖 AI (PUTIH) MEMENANGKAN GAME" if winner_is_white else "🎉 SELAMAT! ANDA MENANG (HITAM)"
                elif game_mode == 1:  # 2 Players
                    w_name = "BIDAK PUTIH" if winner_is_white else "BIDAK HITAM"
                    w_text = f"🏆 {w_name} MERAIH KEMENANGAN!"
                else:  # AI vs AI
                    w_name = "PUTIH" if winner_is_white else "HITAM"
                    w_text = f"🏆 SIMULASI SELESAI: {w_name} MENANG!"
            else:
                w_text = status_desc

            t_sub = font_modal_sub.render(w_text, True, WHITE)
            screen.blit(t_sub, (mg_x + (modal_gameover_w - t_sub.get_width()) // 2, mg_y + 114))

            # Extra stats info
            stats_str = f"Langkah #{board.fullmove_number}  •  Mode: {mode_names[game_mode]}"
            t_stat = font_sub.render(stats_str, True, TEXT_MUTED)
            screen.blit(t_stat, (mg_x + (modal_gameover_w - t_stat.get_width()) // 2, mg_y + 144))

            # Divider line
            pygame.draw.line(screen, (51, 65, 85), (mg_x + 30, mg_y + 172), (mg_x + modal_gameover_w - 30, mg_y + 172), 1)

            # Button hover detection
            m_pos = pygame.mouse.get_pos()
            hover_replay = btn_replay_rect.collidepoint(m_pos)
            hover_quit = btn_quit_rect.collidepoint(m_pos)

            # Tombol ULANGI (Main Lagi) - Emerald Green
            c_replay_bg = (34, 197, 94) if hover_replay else (16, 185, 129)
            pygame.draw.rect(screen, c_replay_bg, btn_replay_rect, border_radius=10)
            if hover_replay:
                pygame.draw.rect(screen, WHITE, btn_replay_rect, width=2, border_radius=10)

            t_r1 = font_btn_main.render("🔄 ULANGI", True, WHITE)
            t_r2 = font_btn_hint.render("Main Lagi [R]", True, (220, 252, 231) if hover_replay else (187, 247, 208))
            screen.blit(t_r1, (btn_replay_rect.centerx - t_r1.get_width() // 2, btn_replay_rect.centery - 14))
            screen.blit(t_r2, (btn_replay_rect.centerx - t_r2.get_width() // 2, btn_replay_rect.centery + 7))

            # Tombol BERHENTI (Kembali ke Menu) - Crimson Rose
            c_quit_bg = (244, 63, 94) if hover_quit else (225, 29, 72)
            pygame.draw.rect(screen, c_quit_bg, btn_quit_rect, border_radius=10)
            if hover_quit:
                pygame.draw.rect(screen, WHITE, btn_quit_rect, width=2, border_radius=10)

            t_q1 = font_btn_main.render("⏹ BERHENTI", True, WHITE)
            t_q2 = font_btn_hint.render("Ke Menu [ESC]", True, (254, 226, 226) if hover_quit else (254, 205, 211))
            screen.blit(t_q1, (btn_quit_rect.centerx - t_q1.get_width() // 2, btn_quit_rect.centery - 14))
            screen.blit(t_q2, (btn_quit_rect.centerx - t_q2.get_width() // 2, btn_quit_rect.centery + 7))

        pygame.display.flip()
        clock.tick(60)

    return "MENU"


if __name__ == "__main__":
    pygame.init()
    screen_test = pygame.display.set_mode((1020, 640))
    pygame.display.set_caption("Master Chess - GAME AHMAD")
    clock_test = pygame.time.Clock()
    run_chess(screen_test, clock_test)
    pygame.quit()
    sys.exit()

