"""
GAME AHMAD - Arcade & Game Engine Suite
=======================================
Main Dashboard & Launcher Hub
Author: Ahmad
"""

import pygame
import sys
import math
import random

from pingpong_game import run_pingpong
from chess_gui import run_chess

# =============================================================================
# INISIALISASI DASAR
# =============================================================================
pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
except Exception:
    pass

WIDTH, HEIGHT = 1020, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GAME AHMAD - Arcade & Game Engine Suite")
clock = pygame.time.Clock()

# Palet Warna Dashboard
BG_DARK = (10, 15, 29)
CARD_BG = (17, 24, 39)
CARD_BORDER = (55, 65, 81)
CARD_HOVER_BORDER = (96, 165, 250)

CYAN = (0, 240, 255)
PINK = (255, 20, 147)
GOLD = (250, 204, 21)
WHITE = (255, 255, 255)
TEXT_GRAY = (156, 163, 175)
TEXT_MUTED = (107, 114, 128)

# Font Loader
def get_font(size, bold=False):
    for name in ["helvetica", "arial", "impact"]:
        try:
            path = pygame.font.match_font(name)
            if path:
                return pygame.font.Font(path, size)
        except Exception:
            continue
    return pygame.font.Font(None, size)

font_logo = get_font(52, bold=True)
font_subtitle = get_font(18, bold=False)
font_card_title = get_font(26, bold=True)
font_badge = get_font(12, bold=True)
font_body = get_font(14, bold=False)
font_btn = get_font(16, bold=True)
font_footer = get_font(13, bold=False)

# Partikel Latar Belakang Dashboard
class BgSpark:
    def __init__(self):
        self.reset()
        self.y = random.uniform(0, HEIGHT)

    def reset(self):
        self.x = random.uniform(0, WIDTH)
        self.y = HEIGHT + 10
        self.vy = -random.uniform(0.3, 1.2)
        self.radius = random.uniform(1.0, 2.5)
        self.alpha = random.randint(40, 140)
        self.color = random.choice([CYAN, GOLD, (147, 197, 253)])

    def update(self):
        self.y += self.vy
        if self.y < -10:
            self.reset()

    def draw(self, surface):
        s = pygame.Surface((int(self.radius * 2 + 2), int(self.radius * 2 + 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, self.alpha), (int(self.radius + 1), int(self.radius + 1)), int(self.radius))
        surface.blit(s, (int(self.x - self.radius), int(self.y - self.radius)))

bg_sparks = [BgSpark() for _ in range(45)]

# =============================================================================
# MAIN DASHBOARD LOOP
# =============================================================================
def main_dashboard():
    running = True

    # Dimensi Kartu Game
    card_w = 420
    card_h = 390
    card_y = 150

    card1_x = 70
    card2_x = WIDTH - card_w - 70

    selected_index = 0  # 0 = Pingpong, 1 = Chess

    while running:
        mx, my = pygame.mouse.get_pos()
        card1_rect = pygame.Rect(card1_x, card_y, card_w, card_h)
        card2_rect = pygame.Rect(card2_x, card_y, card_w, card_h)

        is_hover1 = card1_rect.collidepoint(mx, my)
        is_hover2 = card2_rect.collidepoint(mx, my)

        if is_hover1: selected_index = 0
        if is_hover2: selected_index = 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_1, pygame.K_KP1):
                    res = run_pingpong(screen, clock)
                    if res == "QUIT":
                        running = False
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    res = run_chess(screen, clock)
                    if res == "QUIT":
                        running = False
                elif event.key == pygame.K_LEFT:
                    selected_index = 0
                elif event.key == pygame.K_RIGHT:
                    selected_index = 1
                elif event.key == pygame.K_RETURN:
                    if selected_index == 0:
                        res = run_pingpong(screen, clock)
                    else:
                        res = run_chess(screen, clock)
                    if res == "QUIT":
                        running = False
                elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                    pygame.quit()
                    sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if is_hover1:
                    res = run_pingpong(screen, clock)
                    if res == "QUIT":
                        running = False
                elif is_hover2:
                    res = run_chess(screen, clock)
                    if res == "QUIT":
                        running = False

        # =============================================================
        # RENDER DASHBOARD
        # =============================================================
        screen.fill(BG_DARK)

        # Latar Partikel
        for sp in bg_sparks:
            sp.update()
            sp.draw(screen)

        # -------------------------------------------------------------
        # HEADER LOGO "GAME AHMAD"
        # -------------------------------------------------------------
        # Glow Logo
        glow_surf = font_logo.render("GAME AHMAD", True, (37, 99, 235))
        screen.blit(glow_surf, (WIDTH // 2 - glow_surf.get_width() // 2 + 1, 28))

        logo_surf = font_logo.render("GAME AHMAD", True, WHITE)
        screen.blit(logo_surf, (WIDTH // 2 - logo_surf.get_width() // 2, 26))

        sub_surf = font_subtitle.render("Arcade & Game Engine Suite • Python Edition", True, CYAN)
        screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2, 88))

        # Garis aksen bawah header
        line_w = 360
        pygame.draw.line(screen, (59, 130, 246, 120), (WIDTH // 2 - line_w // 2, 118), (WIDTH // 2 + line_w // 2, 118), 2)
        pygame.draw.circle(screen, GOLD, (WIDTH // 2, 118), 4)

        # -------------------------------------------------------------
        # CARD 1: PINGPONG AI
        # -------------------------------------------------------------
        c1_glow = is_hover1 or selected_index == 0
        c1_border = CYAN if c1_glow else CARD_BORDER
        c1_elev = -4 if c1_glow else 0

        c1_box = pygame.Rect(card1_x, card_y + c1_elev, card_w, card_h)
        # Background Kartu
        pygame.draw.rect(screen, CARD_BG, c1_box, border_radius=16)
        pygame.draw.rect(screen, c1_border, c1_box, width=3 if c1_glow else 2, border_radius=16)

        # Badge Regulasi
        badge1_rect = pygame.Rect(card1_x + 24, card_y + c1_elev + 22, 160, 24)
        pygame.draw.rect(screen, (8, 47, 73), badge1_rect, border_radius=6)
        pygame.draw.rect(screen, CYAN, badge1_rect, width=1, border_radius=6)
        screen.blit(font_badge.render("ITTF OFFICIAL RULES", True, CYAN), (card1_x + 34, card_y + c1_elev + 27))

        # Judul Game
        screen.blit(font_card_title.render("PINGPONG AI", True, WHITE), (card1_x + 24, card_y + c1_elev + 56))
        screen.blit(font_body.render("Simulasi Tenis Meja Neon Klasik 2D", True, TEXT_GRAY), (card1_x + 24, card_y + c1_elev + 88))

        # Ilustrasi Grafis Kartu (Mini Pingpong Preview)
        thumb1_rect = pygame.Rect(card1_x + 24, card_y + c1_elev + 115, card_w - 48, 120)
        pygame.draw.rect(screen, (2, 6, 23), thumb1_rect, border_radius=10)
        pygame.draw.rect(screen, (30, 41, 59), thumb1_rect, width=2, border_radius=10)
        # Raket mini & bola
        t_cy = thumb1_rect.centery
        pygame.draw.rect(screen, CYAN, (thumb1_rect.left + 20, t_cy - 25, 8, 50), border_radius=4)
        pygame.draw.rect(screen, PINK, (thumb1_rect.right - 28, t_cy - 25, 8, 50), border_radius=4)
        for my_y in range(thumb1_rect.top + 8, thumb1_rect.bottom - 8, 14):
            pygame.draw.rect(screen, (255, 255, 255, 60), (thumb1_rect.centerx - 1, my_y, 2, 7))
        pygame.draw.circle(screen, GOLD, (thumb1_rect.centerx - 20, t_cy - 8), 7)

        # Poin Fitur
        screen.blit(font_body.render("• Target 11 Poin, Aturan Deuce & Rotasi Servis", True, (209, 213, 219)), (card1_x + 24, card_y + c1_elev + 250))
        screen.blit(font_body.render("• Best of 5 Games & Rekap Kemenangan Set", True, (209, 213, 219)), (card1_x + 24, card_y + c1_elev + 272))
        screen.blit(font_body.render("• Mode: AI vs AI atau Main Sendiri (Player)", True, (209, 213, 219)), (card1_x + 24, card_y + c1_elev + 294))

        # Tombol Mainkan
        btn1_rect = pygame.Rect(card1_x + 24, card_y + c1_elev + 328, card_w - 48, 42)
        btn1_bg = CYAN if c1_glow else (31, 41, 55)
        btn1_txt_c = (15, 23, 42) if c1_glow else WHITE
        pygame.draw.rect(screen, btn1_bg, btn1_rect, border_radius=8)
        b1_txt = font_btn.render("MAIN PINGPONG  [1]", True, btn1_txt_c)
        screen.blit(b1_txt, (btn1_rect.centerx - b1_txt.get_width() // 2, btn1_rect.centery - b1_txt.get_height() // 2))

        # -------------------------------------------------------------
        # CARD 2: MASTER CHESS FIDE
        # -------------------------------------------------------------
        c2_glow = is_hover2 or selected_index == 1
        c2_border = GOLD if c2_glow else CARD_BORDER
        c2_elev = -4 if c2_glow else 0

        c2_box = pygame.Rect(card2_x, card_y + c2_elev, card_w, card_h)
        # Background Kartu
        pygame.draw.rect(screen, CARD_BG, c2_box, border_radius=16)
        pygame.draw.rect(screen, c2_border, c2_box, width=3 if c2_glow else 2, border_radius=16)

        # Badge Regulasi
        badge2_rect = pygame.Rect(card2_x + 24, card_y + c2_elev + 22, 160, 24)
        pygame.draw.rect(screen, (66, 32, 6), badge2_rect, border_radius=6)
        pygame.draw.rect(screen, GOLD, badge2_rect, width=1, border_radius=6)
        screen.blit(font_badge.render("FIDE STANDARD ENGINE", True, GOLD), (card2_x + 30, card_y + c2_elev + 27))

        # Judul Game
        screen.blit(font_card_title.render("MASTER CHESS", True, WHITE), (card2_x + 24, card_y + c2_elev + 56))
        screen.blit(font_body.render("Engine Catur Resmi & Papan Interaktif FIDE", True, TEXT_GRAY), (card2_x + 24, card_y + c2_elev + 88))

        # Ilustrasi Grafis Kartu (Mini Chessboard Preview)
        thumb2_rect = pygame.Rect(card2_x + 24, card_y + c2_elev + 115, card_w - 48, 120)
        pygame.draw.rect(screen, (20, 28, 44), thumb2_rect, border_radius=10)
        pygame.draw.rect(screen, (51, 65, 85), thumb2_rect, width=2, border_radius=10)
        # Papan catur mini
        grid_sq = 15
        start_gx = thumb2_rect.centerx - grid_sq * 4
        start_gy = thumb2_rect.centery - grid_sq * 3
        for gr in range(6):
            for gf in range(8):
                sq_c = (240, 217, 181) if (gr + gf) % 2 == 0 else (181, 136, 99)
                pygame.draw.rect(screen, sq_c, (start_gx + gf * grid_sq, start_gy + gr * grid_sq, grid_sq, grid_sq))
        # Mahkota Emas Raja di tengah
        pygame.draw.circle(screen, GOLD, (thumb2_rect.centerx, thumb2_rect.centery), 12)
        pygame.draw.circle(screen, (30, 41, 59), (thumb2_rect.centerx, thumb2_rect.centery), 12, width=2)

        # Poin Fitur
        screen.blit(font_body.render("• 100% Regulasi FIDE: Rokade, En Passant, Promosi", True, (209, 213, 219)), (card2_x + 24, card_y + c2_elev + 250))
        screen.blit(font_body.render("• Remis Otomatis: 50 Langkah, Repetisi, Material Kurang", True, (209, 213, 219)), (card2_x + 24, card_y + c2_elev + 272))
        screen.blit(font_body.render("• Lawan AI Cerdas, Pass & Play, atau AI vs AI", True, (209, 213, 219)), (card2_x + 24, card_y + c2_elev + 294))

        # Tombol Mainkan
        btn2_rect = pygame.Rect(card2_x + 24, card_y + c2_elev + 328, card_w - 48, 42)
        btn2_bg = GOLD if c2_glow else (31, 41, 55)
        btn2_txt_c = (15, 23, 42) if c2_glow else WHITE
        pygame.draw.rect(screen, btn2_bg, btn2_rect, border_radius=8)
        b2_txt = font_btn.render("MAIN CATUR  [2]", True, btn2_txt_c)
        screen.blit(b2_txt, (btn2_rect.centerx - b2_txt.get_width() // 2, btn2_rect.centery - b2_txt.get_height() // 2))

        # -------------------------------------------------------------
        # FOOTER
        # -------------------------------------------------------------
        footer_str = "Navigasi: Tekan [1] atau [2] untuk memilih game  |  Gunakan Mouse untuk klik  |  Tekan [Q] untuk Keluar"
        f_surf = font_footer.render(footer_str, True, TEXT_MUTED)
        screen.blit(f_surf, (WIDTH // 2 - f_surf.get_width() // 2, HEIGHT - 35))

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main_dashboard()
