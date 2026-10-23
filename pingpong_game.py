"""
Pingpong AI - Neon Table Tennis (ITTF Standard)
==============================================
Module: pingpong_game.py
Part of GAME AHMAD Suite
"""

import pygame
import math
import random
import sys
import struct

# Palet Warna Desain Neon Klasik
COURT_BG = (2, 6, 23)
WHITE = (255, 255, 255)
CYAN = (0, 240, 255)
PINK = (255, 0, 85)
GOLD = (250, 204, 21)
NET_COLOR = (255, 255, 255, 50)
BORDER_COLOR = (255, 255, 255, 80)

# Sound Manager
class PingpongAudio:
    def __init__(self):
        self.enabled = True
        self.sounds = {}
        try:
            self._init_sounds()
        except Exception:
            self.enabled = False

    def _synth_wave(self, freq, duration, decay=25, wave_type="sine", volume=0.7):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = bytearray()
        for i in range(n_samples):
            t = float(i) / sample_rate
            env = math.exp(-decay * t)
            if wave_type == "sine":
                val = math.sin(2 * math.pi * freq * t)
            elif wave_type == "square":
                val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
            else:
                val = math.sin(2 * math.pi * freq * t)
            sample = int(32767 * val * env * volume)
            sample = max(-32768, min(32767, sample))
            buf += struct.pack('<h', sample)
        return pygame.mixer.Sound(bytes(buf))

    def _init_sounds(self):
        self.sounds["paddle"] = self._synth_wave(780, 0.06, decay=35, volume=0.6)
        self.sounds["wall"] = self._synth_wave(420, 0.07, decay=30, volume=0.5)
        self.sounds["score"] = self._synth_wave(920, 0.22, decay=10, wave_type="sine", volume=0.6)
        self.sounds["deuce"] = self._synth_wave(650, 0.25, decay=8, wave_type="square", volume=0.35)
        self.sounds["cheer"] = self._synth_wave(587, 0.5, decay=5, volume=0.7)

    def play(self, name):
        if not self.enabled: return
        snd = self.sounds.get(name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass

audio = PingpongAudio()

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = (random.random() - 0.5) * 14
        self.vy = (random.random() - 0.5) * 14
        self.life = 255
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 14

    def draw(self, surface):
        if self.life > 0:
            surf = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, max(0, int(self.life))), (4, 4), 4)
            surface.blit(surf, (int(self.x - 4), int(self.y - 4)))

class Paddle:
    def __init__(self, x, color, name, is_left, court_cy):
        self.x = x
        self.y = court_cy - 50
        self.width = 15
        self.height = 100
        self.color = color
        self.name = name
        self.is_left = is_left
        self.speed = 10
        self.vy = 0

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height), border_radius=8)

class Ball:
    def __init__(self, cx, cy):
        self.radius = 11
        self.x = cx
        self.y = cy
        self.speed = 8.5
        self.vx = 0
        self.vy = 0
        self.color = WHITE
        self.state = "SERVING"
        self.serve_timer = 40
        self.server_paddle = None

    def start_serve(self, server_paddle):
        self.server_paddle = server_paddle
        self.state = "SERVING"
        self.serve_timer = 45
        self.color = server_paddle.color
        if server_paddle.is_left:
            self.x = server_paddle.x + server_paddle.width + 16
        else:
            self.x = server_paddle.x - 16
        self.y = server_paddle.y + server_paddle.height // 2
        self.vx = 0
        self.vy = 0

    def launch(self):
        self.state = "IN_PLAY"
        direction = 1 if self.server_paddle.is_left else -1
        self.speed = 8.5
        self.vx = direction * self.speed
        self.vy = (random.random() - 0.5) * 6
        audio.play("paddle")

    def draw(self, surface):
        glow_surf = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 45), (self.radius * 2, self.radius * 2), self.radius * 2)
        surface.blit(glow_surf, (int(self.x - self.radius * 2), int(self.y - self.radius * 2)))

        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x - 2), int(self.y - 2)), max(2, self.radius - 6))

class MatchEngine:
    def __init__(self, p_left, p_right):
        self.p_left = p_left
        self.p_right = p_right
        self.score_left = 0
        self.score_right = 0
        self.games_left = 0
        self.games_right = 0
        self.current_game_num = 1
        self.target_games = 3
        self.server = p_left
        self.first_server_of_game = p_left
        self.match_over = False
        self.match_winner = None
        self.banner_text = "PERTANDINGAN DIMULAI (BEST OF 5)"
        self.banner_sub = "Target: 11 Poin (Selisih 2) | Servis berganti tiap 2 poin"
        self.banner_color = GOLD
        self.banner_timer = 180
        self.rally_count = 0

    def update_service_turn(self):
        total_pts = self.score_left + self.score_right
        is_deuce = (self.score_left >= 10 and self.score_right >= 10)
        turn = (total_pts % 2) if is_deuce else ((total_pts // 2) % 2)
        self.server = self.first_server_of_game if turn == 0 else (self.p_right if self.first_server_of_game == self.p_left else self.p_left)

    def announce(self, main_msg, sub_msg="", color=GOLD, timer=140):
        self.banner_text = main_msg
        self.banner_sub = sub_msg
        self.banner_color = color
        self.banner_timer = timer

    def award_point(self, winner_paddle, ball, particles):
        if self.match_over: return
        audio.play("score")
        if winner_paddle == self.p_left:
            self.score_left += 1
            loser = self.p_right
        else:
            self.score_right += 1
            loser = self.p_left

        self.announce(f"POIN UNTUK {winner_paddle.name}!", f"{loser.name} gagal mengembalikan bola", winner_paddle.color, 120)

        diff = abs(self.score_left - self.score_right)
        max_score = max(self.score_left, self.score_right)

        if max_score >= 11 and diff >= 2:
            self.win_game(winner_paddle, ball, particles)
        else:
            if self.score_left >= 10 and self.score_right >= 10:
                if diff == 0:
                    audio.play("deuce")
                    self.announce("DEUCE (10 - 10)!", "Servis berganti setiap 1 poin hingga selisih 2!", GOLD, 150)
                elif diff == 1:
                    adv_name = self.p_left.name if self.score_left > self.score_right else self.p_right.name
                    self.announce(f"GAME POINT UNTUK {adv_name}!", "Unggul 1 poin!", GOLD, 110)
            elif (self.score_left == 10 and self.score_right < 10) or (self.score_right == 10 and self.score_left < 10):
                leader = self.p_left.name if self.score_left == 10 else self.p_right.name
                self.announce(f"GAME POINT UNTUK {leader}!", "Tinggal 1 poin untuk mengunci set", GOLD, 110)

            self.update_service_turn()
            ball.start_serve(self.server)

    def win_game(self, winner_paddle, ball, particles):
        if winner_paddle == self.p_left:
            self.games_left += 1
        else:
            self.games_right += 1

        audio.play("cheer")
        if self.games_left >= self.target_games or self.games_right >= self.target_games:
            self.match_over = True
            self.match_winner = winner_paddle
            self.announce(f"MATCH SELESAI: {winner_paddle.name} JUARA!",
                          f"Menang {self.games_left} - {self.games_right} (Best of 5)", GOLD, 300)
            for _ in range(70):
                particles.append(Particle(500, 300, GOLD))
        else:
            self.announce(f"{winner_paddle.name} MENANG GAME {self.current_game_num}!",
                          f"Skor: {self.score_left} - {self.score_right}. Bersiap game berikutnya...", winner_paddle.color, 180)
            self.current_game_num += 1
            self.score_left = 0
            self.score_right = 0
            self.first_server_of_game = self.p_right if self.first_server_of_game == self.p_left else self.p_left
            self.update_service_turn()
            ball.start_serve(self.server)

    def update(self):
        if self.banner_timer > 0:
            self.banner_timer -= 1


def run_pingpong(screen, clock):
    """Main loop for Pingpong AI, returns to main menu on ESC or Quit."""
    W, H = screen.get_size()
    c_top = 130
    c_bottom = H - 30
    c_left = 30
    c_right = W - 30
    c_cx = W // 2
    c_cy = c_top + (c_bottom - c_top) // 2

    font_score = pygame.font.SysFont("helvetica", 60, bold=True)
    font_name = pygame.font.SysFont("helvetica", 22, bold=True)
    font_sub = pygame.font.SysFont("helvetica", 14, bold=True)
    font_banner = pygame.font.SysFont("helvetica", 24, bold=True)
    font_msg = pygame.font.SysFont("helvetica", 16, bold=False)

    player_left = Paddle(c_left + 5, CYAN, "AI ALPHA", is_left=True, court_cy=c_cy)
    player_right = Paddle(c_right - 20, PINK, "AI OMEGA", is_left=False, court_cy=c_cy)
    ball = Ball(c_cx, c_cy)
    match = MatchEngine(player_left, player_right)
    ball.start_serve(match.server)

    particles = []
    paused = False
    is_manual_mode = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Return to GAME AHMAD Dashboard
                    return "MENU"
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_TAB:
                    is_manual_mode = not is_manual_mode
                    mode_str = "Player vs AI" if is_manual_mode else "AI vs AI"
                    match.announce(f"MODE: {mode_str}", "Gunakan Panah Atas/Bawah atau W/S untuk raket kiri", CYAN, 120)
                elif event.key == pygame.K_s:
                    audio.enabled = not audio.enabled
                    stat = "AKTIF" if audio.enabled else "MATI"
                    match.announce(f"AUDIO EFEK: {stat}", "", GOLD, 80)
                elif event.key == pygame.K_r:
                    player_left = Paddle(c_left + 5, CYAN, "AI ALPHA", is_left=True, court_cy=c_cy)
                    player_right = Paddle(c_right - 20, PINK, "AI OMEGA", is_left=False, court_cy=c_cy)
                    ball = Ball(c_cx, c_cy)
                    match = MatchEngine(player_left, player_right)
                    ball.start_serve(match.server)

        if not paused and not match.match_over:
            # AI Move
            for pad in [player_left, player_right]:
                if pad == player_left and is_manual_mode:
                    keys = pygame.key.get_pressed()
                    pad.speed = 10
                    if keys[pygame.K_UP] or keys[pygame.K_w]: pad.y -= pad.speed
                    if keys[pygame.K_DOWN] or keys[pygame.K_s]: pad.y += pad.speed
                    pad.y = max(c_top, min(c_bottom - pad.height, pad.y))
                else:
                    is_left = pad.is_left
                    approaching = (is_left and ball.vx < 0) or (not is_left and ball.vx > 0)
                    if approaching and ball.state == "IN_PLAY":
                        time = abs(pad.x - ball.x) / max(1.0, abs(ball.vx))
                        exp_y = ball.y + ball.vy * time
                        while exp_y < c_top or exp_y > c_bottom:
                            if exp_y < c_top: exp_y = 2 * c_top - exp_y
                            if exp_y > c_bottom: exp_y = 2 * c_bottom - exp_y
                        tgt_y = exp_y - pad.height / 2
                        if random.random() < 0.04:
                            tgt_y += (random.random() - 0.5) * 45
                    else:
                        tgt_y = c_cy - pad.height / 2

                    pad.speed = min(16, max(7, ball.speed * 0.95 + 1.2))
                    if pad.y < tgt_y - pad.speed:
                        pad.y += pad.speed
                        pad.vy = pad.speed
                    elif pad.y > tgt_y + pad.speed:
                        pad.y -= pad.speed
                        pad.vy = -pad.speed
                    else:
                        pad.vy = 0
                    pad.y = max(c_top, min(c_bottom - pad.height, pad.y))

            # Ball update
            if ball.state == "SERVING":
                if ball.server_paddle.is_left:
                    ball.x = player_left.x + player_left.width + 16
                else:
                    ball.x = player_right.x - 16
                ball.y = ball.server_paddle.y + ball.server_paddle.height // 2
                ball.serve_timer -= 1
                if ball.serve_timer <= 0:
                    ball.launch()
                    match.rally_count = 0
                    for _ in range(16): particles.append(Particle(ball.x, ball.y, ball.color))

            elif ball.state == "IN_PLAY":
                ball.x += ball.vx
                ball.y += ball.vy

                # Wall Bounce
                if ball.y - ball.radius < c_top:
                    ball.y = c_top + ball.radius
                    ball.vy = abs(ball.vy)
                    audio.play("wall")
                    for _ in range(10): particles.append(Particle(ball.x, ball.y, ball.color))
                elif ball.y + ball.radius > c_bottom:
                    ball.y = c_bottom - ball.radius
                    ball.vy = -abs(ball.vy)
                    audio.play("wall")
                    for _ in range(10): particles.append(Particle(ball.x, ball.y, ball.color))

                # Paddle hit
                tgt = player_left if ball.vx < 0 else player_right
                p_rect = pygame.Rect(tgt.x, tgt.y, tgt.width, tgt.height)
                b_rect = pygame.Rect(ball.x - ball.radius, ball.y - ball.radius, ball.radius * 2, ball.radius * 2)
                if p_rect.colliderect(b_rect):
                    cp = (ball.y - (tgt.y + tgt.height / 2)) / (tgt.height / 2)
                    cp = max(-1.0, min(1.0, cp))
                    ang = (math.pi / 3.1) * cp
                    direction = 1 if tgt.is_left else -1
                    ball.speed = min(30.0, ball.speed + 1.2)
                    ball.vx = direction * ball.speed * math.cos(ang)
                    ball.vy = ball.speed * math.sin(ang) + tgt.vy * 0.35
                    ball.color = tgt.color
                    audio.play("paddle")
                    for _ in range(20): particles.append(Particle(ball.x, ball.y, tgt.color))
                    match.rally_count += 1

                # Goal
                if ball.x + ball.radius < c_left:
                    for _ in range(40): particles.append(Particle(ball.x, ball.y, player_right.color))
                    match.award_point(player_right, ball, particles)
                elif ball.x - ball.radius > c_right:
                    for _ in range(40): particles.append(Particle(ball.x, ball.y, player_left.color))
                    match.award_point(player_left, ball, particles)

            # Particles
            for p in reversed(particles):
                p.update()
                if p.life <= 0: particles.remove(p)

            match.update()

        # Render
        screen.fill(COURT_BG)
        # Court
        pygame.draw.rect(screen, BORDER_COLOR, (c_left, c_top, c_right - c_left, c_bottom - c_top), 4, border_radius=6)
        for i in range(c_top, c_bottom, 36):
            pygame.draw.rect(screen, BORDER_COLOR, (c_cx - 2, i, 4, 18))
        pygame.draw.circle(screen, BORDER_COLOR, (c_cx, c_cy), 75, 4)

        for p in particles: p.draw(screen)
        player_left.draw(screen)
        player_right.draw(screen)
        ball.draw(screen)

        # HUD
        l_txt = player_left.name + (" (YOU)" if is_manual_mode else "")
        n_L = font_name.render(l_txt, True, CYAN)
        screen.blit(n_L, (c_left + 20, 20))
        if match.server == player_left:
            pygame.draw.circle(screen, GOLD, (c_left + 20 + n_L.get_width() + 14, 32), 5)
            screen.blit(font_sub.render("SERVE", True, GOLD), (c_left + 20 + n_L.get_width() + 24, 25))
        screen.blit(font_sub.render(f"GAMES: {match.games_left}", True, (148, 163, 184)), (c_left + 20, 48))
        screen.blit(font_score.render(f"{match.score_left:02d}", True, CYAN), (c_left + 20, 68))

        ct = font_sub.render(f"STANDAR TENIS MEJA  |  GAME {match.current_game_num} (BEST OF {match.target_games * 2 - 1})", True, GOLD)
        screen.blit(ct, (c_cx - ct.get_width() // 2, 25))
        vs = font_score.render("VS", True, (255, 255, 255, 60))
        screen.blit(vs, (c_cx - vs.get_width() // 2, 52))
        rl = font_sub.render(f"RALLY: {match.rally_count} PUKULAN", True, (100, 116, 139))
        screen.blit(rl, (c_cx - rl.get_width() // 2, 105))

        n_R = font_name.render(player_right.name, True, PINK)
        screen.blit(n_R, (c_right - 20 - n_R.get_width(), 20))
        if match.server == player_right:
            srv_R = font_sub.render("SERVE", True, GOLD)
            screen.blit(srv_R, (c_right - 20 - n_R.get_width() - srv_R.get_width() - 24, 25))
            pygame.draw.circle(screen, GOLD, (c_right - 20 - n_R.get_width() - 14, 32), 5)
        screen.blit(font_sub.render(f"GAMES: {match.games_right}", True, (148, 163, 184)), (c_right - 20 - font_sub.render(f"GAMES: {match.games_right}", True, (148, 163, 184)).get_width(), 48))
        s_R = font_score.render(f"{match.score_right:02d}", True, PINK)
        screen.blit(s_R, (c_right - 20 - s_R.get_width(), 68))

        # Banner
        if match.banner_timer > 0:
            bw, bh = 640, 56
            bs = pygame.Surface((bw, bh), pygame.SRCALPHA)
            pygame.draw.rect(bs, (15, 23, 42, 230), (0, 0, bw, bh), border_radius=10)
            pygame.draw.rect(bs, match.banner_color, (0, 0, bw, bh), width=2, border_radius=10)
            t1 = font_banner.render(match.banner_text, True, match.banner_color)
            t2 = font_msg.render(match.banner_sub, True, (226, 232, 240))
            bs.blit(t1, ((bw - t1.get_width()) // 2, 6))
            bs.blit(t2, ((bw - t2.get_width()) // 2, 32))
            screen.blit(bs, ((W - bw) // 2, c_bottom - 68))
        else:
            it = font_sub.render("[ESC] Menu Dashboard  |  [SPACE] Pause  |  [TAB] Mode AI/Player  |  [R] Reset", True, (80, 95, 115))
            screen.blit(it, ((W - it.get_width()) // 2, H - 22))

        if paused:
            ps = pygame.Surface((W, H), pygame.SRCALPHA)
            pygame.draw.rect(ps, (0, 0, 0, 160), (0, 0, W, H))
            pt = font_score.render("PAUSED", True, GOLD)
            ps.blit(pt, ((W - pt.get_width()) // 2, H // 2 - 30))
            screen.blit(ps, (0, 0))

        pygame.display.flip()
        clock.tick(60)

    return "MENU"
