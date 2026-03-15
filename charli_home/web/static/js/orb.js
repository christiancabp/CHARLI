/**
 * CHARLI Home — Animated Orb
 *
 * A glowing, wobbling sphere rendered on <canvas> that reacts to the
 * assistant's current state. Uses simplex-like noise for organic
 * deformation, glow layers, and orbiting particles.
 *
 * States and their visual profiles:
 *   idle      — slow pulse, blue tones
 *   listening — faster wobble, teal/cyan
 *   thinking  — rapid deformation, orange
 *   speaking  — smooth pulse, gold
 */

const Orb = (() => {
    // ── Configuration per state ─────────────────────────────────────
    const STATE_PROFILES = {
        idle: {
            baseColor:  [0, 136, 204],
            glowColor:  [0, 136, 204],
            noiseSpeed: 0.003,
            noiseAmp:   12,
            pulseSpeed: 0.01,
            particleColor: [0, 180, 255],
        },
        listening: {
            baseColor:  [0, 212, 255],
            glowColor:  [0, 212, 255],
            noiseSpeed: 0.008,
            noiseAmp:   20,
            pulseSpeed: 0.025,
            particleColor: [0, 255, 220],
        },
        thinking: {
            baseColor:  [255, 140, 0],
            glowColor:  [255, 100, 0],
            noiseSpeed: 0.012,
            noiseAmp:   25,
            pulseSpeed: 0.03,
            particleColor: [255, 180, 50],
        },
        speaking: {
            baseColor:  [255, 200, 69],
            glowColor:  [255, 180, 40],
            noiseSpeed: 0.006,
            noiseAmp:   15,
            pulseSpeed: 0.018,
            particleColor: [255, 220, 100],
        },
    };

    let canvas, ctx;
    let cx, cy, baseRadius;
    let currentProfile = STATE_PROFILES.idle;
    let targetProfile  = STATE_PROFILES.idle;
    let time = 0;
    let particles = [];
    const NUM_PARTICLES = 24;
    const BLOB_POINTS = 80;

    // ── Simple noise function (no dependency) ───────────────────────
    // A combination of sine waves to simulate smooth noise
    function noise(x, y, t) {
        return (
            Math.sin(x * 1.2 + t * 0.7) * 0.5 +
            Math.sin(y * 0.8 + t * 1.1) * 0.5 +
            Math.sin((x + y) * 0.6 + t * 0.9) * 0.4 +
            Math.sin(x * 2.1 - t * 0.5) * 0.3
        ) / 1.7;
    }

    // ── Interpolate between profiles ────────────────────────────────
    function lerpColor(a, b, t) {
        return a.map((v, i) => Math.round(v + (b[i] - v) * t));
    }

    function lerpValue(a, b, t) {
        return a + (b - a) * t;
    }

    // ── Particle system ─────────────────────────────────────────────
    function initParticles() {
        particles = [];
        for (let i = 0; i < NUM_PARTICLES; i++) {
            particles.push({
                angle: (Math.PI * 2 * i) / NUM_PARTICLES,
                radius: baseRadius + 30 + Math.random() * 25,
                speed: 0.003 + Math.random() * 0.004,
                size: 1 + Math.random() * 2,
                offset: Math.random() * Math.PI * 2,
            });
        }
    }

    function drawParticles() {
        const pc = currentProfile.particleColor;
        particles.forEach(p => {
            p.angle += p.speed;
            const wobble = Math.sin(time * 0.02 + p.offset) * 8;
            const x = cx + Math.cos(p.angle) * (p.radius + wobble);
            const y = cy + Math.sin(p.angle) * (p.radius + wobble);
            const alpha = 0.3 + Math.sin(time * 0.03 + p.offset) * 0.2;

            ctx.beginPath();
            ctx.arc(x, y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${pc[0]}, ${pc[1]}, ${pc[2]}, ${alpha})`;
            ctx.fill();
        });
    }

    // ── Main blob drawing ───────────────────────────────────────────
    function drawBlob() {
        const pulse = Math.sin(time * currentProfile.pulseSpeed) * 5;
        const r = baseRadius + pulse;

        // Outer glow layers
        for (let g = 3; g >= 1; g--) {
            const glowR = r + g * 15;
            const gc = currentProfile.glowColor;
            const alpha = 0.03 * (4 - g);

            ctx.beginPath();
            for (let i = 0; i <= BLOB_POINTS; i++) {
                const angle = (Math.PI * 2 * i) / BLOB_POINTS;
                const n = noise(
                    Math.cos(angle) * 2,
                    Math.sin(angle) * 2,
                    time * currentProfile.noiseSpeed * 0.5
                );
                const deform = n * currentProfile.noiseAmp * 0.6;
                const x = cx + Math.cos(angle) * (glowR + deform);
                const y = cy + Math.sin(angle) * (glowR + deform);
                i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.fillStyle = `rgba(${gc[0]}, ${gc[1]}, ${gc[2]}, ${alpha})`;
            ctx.fill();
        }

        // Main blob body
        ctx.beginPath();
        for (let i = 0; i <= BLOB_POINTS; i++) {
            const angle = (Math.PI * 2 * i) / BLOB_POINTS;
            const n = noise(
                Math.cos(angle) * 2,
                Math.sin(angle) * 2,
                time * currentProfile.noiseSpeed
            );
            const deform = n * currentProfile.noiseAmp;
            const x = cx + Math.cos(angle) * (r + deform);
            const y = cy + Math.sin(angle) * (r + deform);
            i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.closePath();

        // Radial gradient fill
        const bc = currentProfile.baseColor;
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r + 20);
        grad.addColorStop(0,   `rgba(${bc[0]}, ${bc[1]}, ${bc[2]}, 0.9)`);
        grad.addColorStop(0.6, `rgba(${bc[0]}, ${bc[1]}, ${bc[2]}, 0.4)`);
        grad.addColorStop(1,   `rgba(${bc[0]}, ${bc[1]}, ${bc[2]}, 0.05)`);
        ctx.fillStyle = grad;
        ctx.fill();

        // Bright inner core
        const coreGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r * 0.4);
        coreGrad.addColorStop(0, `rgba(255, 255, 255, 0.15)`);
        coreGrad.addColorStop(1, `rgba(255, 255, 255, 0)`);
        ctx.beginPath();
        ctx.arc(cx, cy, r * 0.4, 0, Math.PI * 2);
        ctx.fillStyle = coreGrad;
        ctx.fill();

        // HUD ring
        ctx.beginPath();
        ctx.arc(cx, cy, r + 35, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${bc[0]}, ${bc[1]}, ${bc[2]}, 0.08)`;
        ctx.lineWidth = 1;
        ctx.stroke();

        // Second ring with dash
        ctx.beginPath();
        ctx.setLineDash([4, 8]);
        ctx.arc(cx, cy, r + 50, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${bc[0]}, ${bc[1]}, ${bc[2]}, 0.05)`;
        ctx.stroke();
        ctx.setLineDash([]);
    }

    // ── Animation loop ──────────────────────────────────────────────
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Smoothly interpolate to target profile
        const t = 0.03; // transition speed
        currentProfile = {
            baseColor:    lerpColor(currentProfile.baseColor, targetProfile.baseColor, t),
            glowColor:    lerpColor(currentProfile.glowColor, targetProfile.glowColor, t),
            particleColor: lerpColor(currentProfile.particleColor, targetProfile.particleColor, t),
            noiseSpeed:   lerpValue(currentProfile.noiseSpeed, targetProfile.noiseSpeed, t),
            noiseAmp:     lerpValue(currentProfile.noiseAmp, targetProfile.noiseAmp, t),
            pulseSpeed:   lerpValue(currentProfile.pulseSpeed, targetProfile.pulseSpeed, t),
        };

        drawBlob();
        drawParticles();

        time++;
        requestAnimationFrame(animate);
    }

    // ── Public API ──────────────────────────────────────────────────
    return {
        init(canvasId) {
            canvas = document.getElementById(canvasId);
            ctx = canvas.getContext('2d');
            cx = canvas.width / 2;
            cy = canvas.height / 2;
            baseRadius = 70;
            initParticles();
            animate();
        },

        setState(state) {
            if (STATE_PROFILES[state]) {
                targetProfile = STATE_PROFILES[state];
            }
        },
    };
})();
