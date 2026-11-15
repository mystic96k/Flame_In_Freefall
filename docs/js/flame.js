// Animación de la llama con partículas en <canvas>.
// La forma la decide la gravedad (flotación) y el flujo; la intensidad, el margen del modelo.
import { scenario, prediction } from "./state.js?v=fad0ab4b";
import { EN } from "./i18n.js?v=fad0ab4b";

export function startFlame(canvas) {
  const ctx = canvas.getContext("2d");
  let W = 0, H = 0;
  const particles = [];
  let intensity = 1;

  function resize() {
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const r = canvas.getBoundingClientRect();
    W = r.width; H = r.height;
    canvas.width = W * dpr; canvas.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  window.addEventListener("resize", resize);
  if (window.ResizeObserver) new ResizeObserver(resize).observe(canvas); // al cambiar de pestaña
  resize();

  function spawn(n, g) {
    for (let i = 0; i < n; i++) {
      const a = Math.random() * Math.PI * 2;
      const sp = (0.35 + Math.random() * 0.55) * (1 - 0.45 * g);
      particles.push({ x: 0, y: 0, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, life: 0,
                       max: (55 + Math.random() * 45) * (1 - 0.3 * g) });
    }
  }

  function frame() {
    const g = scenario.gravity_g, u = scenario.flow_cm_s;
    const prob = prediction ? prediction.burn_probability : 0.9;
    const target = prob >= 0.5 ? Math.min(1, 0.25 + (prob - 0.5) * 1.6) : 0;
    intensity += (target - intensity) * 0.04;
    const flicker = prob >= 0.5 && prob < 0.7 ? 0.6 + 0.4 * Math.random() : 1;

    ctx.globalCompositeOperation = "source-over";
    ctx.fillStyle = "rgba(3,5,10,0.35)";
    ctx.fillRect(0, 0, W, H);

    const ox = W * 0.5 - Math.min(u, 45) * 1.2;
    const oy = H * (0.55 + 0.2 * g);
    const scale = Math.min(W, H) / 360;
    const soot = Math.min(1, g * 1.3);
    if (intensity > 0.02) spawn(Math.round(9 * intensity * flicker), g);

    ctx.globalCompositeOperation = "lighter";
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.vy -= 0.032 * g;      // flotación
      p.vx += 0.0016 * u;     // ventilación forzada
      p.vx *= 0.975; p.vy *= 0.975;
      p.x += p.vx; p.y += p.vy; p.life++;
      const t = p.life / p.max;
      if (t >= 1) { particles.splice(i, 1); continue; }
      // azul (sin hollín) → naranja (hollín incandescente, sólo con gravedad)
      const k = t < 0.22 ? 0 : soot * Math.min(1, (t - 0.22) * 2.4);
      const R = Math.round(70 + 185 * k), G = Math.round(130 + 30 * k), B = Math.round(255 - 205 * k);
      const a = (t < 0.22 ? 0.11 : 0.11 * (1 - t) * (0.55 + soot * 0.9)) * Math.max(intensity, 0.2);
      const r = (5 + t * 13) * scale * (0.6 + 0.4 * intensity);
      ctx.fillStyle = `rgba(${R},${G},${B},${a})`;
      ctx.beginPath();
      ctx.arc(ox + p.x * scale * 2.2, oy + p.y * scale * 2.2, r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalCompositeOperation = "source-over";

    // combustible
    const grd = ctx.createRadialGradient(ox - 2, oy - 2, 1, ox, oy, 7 * scale);
    grd.addColorStop(0, "#cfd6e6"); grd.addColorStop(1, "#3a4560");
    ctx.fillStyle = grd;
    ctx.beginPath(); ctx.arc(ox, oy, 6 * scale, 0, Math.PI * 2); ctx.fill();

    // flechas de flujo
    if (u > 0.5) {
      ctx.strokeStyle = "rgba(139,151,184,.35)"; ctx.fillStyle = "rgba(139,151,184,.6)";
      ctx.font = "11px JetBrains Mono";
      for (let j = 0; j < 3; j++) {
        const y = H * 0.2 + j * H * 0.3;
        ctx.beginPath(); ctx.moveTo(14, y); ctx.lineTo(54, y); ctx.lineTo(48, y - 4);
        ctx.moveTo(54, y); ctx.lineTo(48, y + 4); ctx.stroke();
      }
      ctx.fillText(EN ? "flow" : "flujo", 14, H * 0.2 - 8);
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}
