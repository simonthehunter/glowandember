/**
 * Glow and Ember — Minimal Holding Page Interactive Scripts
 * Master Brand Identity: Radiance & Warmth
 * Est. 2026
 */

(function () {
  'use strict';

  // --- 1. Ambient Warm Ember Sparks Canvas ---
  const canvas = document.getElementById('ambient-canvas');
  if (canvas && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];
    const particleCount = 24;

    function resize() {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    }

    window.addEventListener('resize', resize);
    resize();

    class EmberParticle {
      constructor() {
        this.reset(true);
      }

      reset(initial = false) {
        this.x = Math.random() * width;
        this.y = initial ? Math.random() * height : height + 10;
        this.size = Math.random() * 2.0 + 0.8;
        this.speedY = -(Math.random() * 0.4 + 0.15);
        this.speedX = (Math.random() - 0.5) * 0.3;
        this.maxOpacity = Math.random() * 0.45 + 0.15;
        this.opacity = initial ? Math.random() * this.maxOpacity : 0;
        this.fadeSpeed = Math.random() * 0.004 + 0.002;
        this.fadingIn = true;
        // Warm amber tones: #C17F44, #D49B5B
        const r = Math.floor(190 + Math.random() * 35);
        const g = Math.floor(125 + Math.random() * 30);
        const b = Math.floor(65 + Math.random() * 25);
        this.color = `${r}, ${g}, ${b}`;
        this.isSpark = Math.random() > 0.65;
      }

      update() {
        this.y += this.speedY;
        this.x += this.speedX;

        if (this.fadingIn) {
          this.opacity += this.fadeSpeed;
          if (this.opacity >= this.maxOpacity) {
            this.fadingIn = false;
          }
        } else {
          this.opacity -= this.fadeSpeed * 0.7;
          if (this.opacity <= 0) {
            this.reset(false);
          }
        }

        if (this.y < -10 || this.x < -10 || this.x > width + 10) {
          this.reset(false);
        }
      }

      draw() {
        ctx.save();
        ctx.fillStyle = `rgba(${this.color}, ${this.opacity})`;
        ctx.shadowBlur = 6;
        ctx.shadowColor = `rgba(193, 127, 68, ${this.opacity * 0.7})`;

        if (this.isSpark && this.size > 1.3) {
          // Subtle 4-pointed micro spark matching brand stars
          ctx.beginPath();
          const s = this.size * 1.4;
          ctx.moveTo(this.x, this.y - s);
          ctx.quadraticCurveTo(this.x, this.y, this.x + s, this.y);
          ctx.quadraticCurveTo(this.x, this.y, this.x, this.y + s);
          ctx.quadraticCurveTo(this.x, this.y, this.x - s, this.y);
          ctx.quadraticCurveTo(this.x, this.y, this.x, this.y - s);
          ctx.closePath();
          ctx.fill();
        } else {
          ctx.beginPath();
          ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.restore();
      }
    }

    for (let i = 0; i < particleCount; i++) {
      particles.push(new EmberParticle());
    }

    function animate() {
      ctx.clearRect(0, 0, width, height);
      for (let i = 0; i < particles.length; i++) {
        particles[i].update();
        particles[i].draw();
      }
      requestAnimationFrame(animate);
    }
    animate();
  }

  // --- 2. Private Register Form Handler ---
  const registerForm = document.getElementById('register-form');
  const emailInput = document.getElementById('guest-email');
  const confirmMsg = document.getElementById('confirmation-msg');

  // Ensure clean state on page load (do not lock out the form)
  try {
    localStorage.removeItem('glow_ember_registered');
    localStorage.removeItem('glow_ember_guest_email');
  } catch (e) {}

  if (registerForm) {
    registerForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const email = emailInput.value.trim();

      if (!email || !validateEmail(email)) {
        emailInput.focus();
        emailInput.style.color = '#B86B27';
        setTimeout(() => { emailInput.style.color = ''; }, 1500);
        return;
      }

      const submitBtn = document.getElementById('register-btn');
      if (submitBtn) {
        submitBtn.disabled = true;
        const btnSpan = submitBtn.querySelector('span');
        if (btnSpan) btnSpan.textContent = 'Reserving...';
      }

      // Send to FormSubmit via AJAX
      fetch('https://formsubmit.co/ajax/hello@glowandember.co.uk', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          email: email,
          _subject: 'Glow and Ember — New Invitation Request'
        })
      })
      .then(function () {
        registerForm.style.display = 'none';
        if (confirmMsg) confirmMsg.style.display = 'inline-flex';
      })
      .catch(function () {
        registerForm.style.display = 'none';
        if (confirmMsg) confirmMsg.style.display = 'inline-flex';
      });
    });
  }

  function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

})();
