/**
 * Skill Swap Chains Visualizer
 * Renders circular multi-student directed exchanges with animated arrows,
 * avatars, skill transfer labels, and comprehensive logic explanation.
 */

class ChainsVisualizer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.chains = [];
    this.currentChainIndex = 0;
  }

  render(chains) {
    this.chains = chains || [];
    if (!this.container) return;

    if (!this.chains.length) {
      this.container.innerHTML = `
        <div style="text-align: center; padding: 48px 20px;">
          <div style="font-size: 2.5rem; margin-bottom: 12px; color: #64748B;">🔄</div>
          <h3 style="font-size: 1.2rem; color: #0F172A; margin-bottom: 8px;">No Circular Swap Chains Discovered</h3>
          <p style="color: #64748B; max-width: 480px; margin: 0 auto 20px; font-size: 0.9rem;">
            A chain requires at least 3 students with cyclical skill dependencies (A teaches B, B teaches C, C teaches A).
            Add more skills or explore direct 1-to-1 matchmaking!
          </p>
        </div>
      `;
      return;
    }

    this.currentChainIndex = 0;
    this.renderCurrentChain();
  }

  renderCurrentChain() {
    const chain = this.chains[this.currentChainIndex];
    if (!chain) return;

    const n = chain.steps.length;
    const width = 600;
    const height = 400;
    const cx = width / 2;
    const cy = height / 2;
    const radius = 135;

    // Calculate node coordinates around the circle
    const nodes = chain.steps.map((step, i) => {
      const angle = (2 * Math.PI * i) / n - Math.PI / 2;
      return {
        ...step,
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
        angle
      };
    });

    // Build SVG paths for directed circular arcs
    let svgEdges = '';
    for (let i = 0; i < n; i++) {
      const u = nodes[i];
      const v = nodes[(i + 1) % n];

      // Slight curvature
      const midAngle = (u.angle + v.angle) / 2 + (v.angle < u.angle ? Math.PI : 0);
      const arcRadius = radius * 0.92;
      const arcMidX = cx + arcRadius * Math.cos(midAngle);
      const arcMidY = cy + arcRadius * Math.sin(midAngle);

      const pathData = `M ${u.x} ${u.y} Q ${arcMidX} ${arcMidY} ${v.x} ${v.y}`;

      svgEdges += `
        <path d="${pathData}" fill="none" stroke="url(#chainGradient)" stroke-width="3" stroke-linecap="round" stroke-dasharray="6,4" class="animated-edge"/>
        
        <!-- Skill Badge along the arc -->
        <g transform="translate(${arcMidX}, ${arcMidY})">
          <rect x="-65" y="-14" width="130" height="28" rx="14" fill="#FFFFFF" stroke="#7C3AED" stroke-width="1.5" filter="drop-shadow(0 2px 4px rgba(0,0,0,0.08))"/>
          <text x="0" y="4" text-anchor="middle" fill="#6D28D9" font-size="11" font-weight="700">
            ${this.escapeHtml(u.teaches_skill)} →
          </text>
        </g>
      `;
    }

    // Build SVG nodes with avatars
    let svgNodes = '';
    nodes.forEach((node, i) => {
      const avatarUrl = node.avatar_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150';
      svgNodes += `
        <g class="chain-node-group" style="cursor: pointer;">
          <defs>
            <pattern id="avatar-pat-${i}" patternUnits="userSpaceOnUse" width="60" height="60" x="${node.x - 30}" y="${node.y - 30}">
              <image href="${avatarUrl}" x="0" y="0" width="60" height="60" preserveAspectRatio="xMidYMid slice" />
            </pattern>
          </defs>
          
          <!-- Outer Glow Circle -->
          <circle cx="${node.x}" cy="${node.y}" r="34" fill="none" stroke="#7C3AED" stroke-width="2.5" opacity="0.9"/>
          <!-- Avatar Circle -->
          <circle cx="${node.x}" cy="${node.y}" r="30" fill="url(#avatar-pat-${i})" stroke="#FFFFFF" stroke-width="2.5"/>
          
          <!-- Name Pill -->
          <g transform="translate(${node.x}, ${node.y + 44})">
            <rect x="-55" y="-11" width="110" height="22" rx="11" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1" filter="drop-shadow(0 1px 2px rgba(0,0,0,0.06))"/>
            <text x="0" y="4" text-anchor="middle" fill="#0F172A" font-size="11" font-weight="700">
              ${this.escapeHtml(node.name.split(' ')[0])}
            </text>
          </g>
        </g>
      `;
    });

    const selectorHtml = this.chains.length > 1 ? `
      <div style="display: flex; gap: 8px; align-items: center; justify-content: center; margin-bottom: 20px;">
        <span style="font-size: 0.8rem; color: #475569; font-weight: 600;">Discovered Chains:</span>
        ${this.chains.map((c, idx) => `
          <button class="btn btn-sm ${idx === this.currentChainIndex ? 'btn-primary' : 'btn-secondary'}" onclick="window.chainsVisualizer.switchChain(${idx})">
            Chain #${idx + 1} (${c.length}-Way)
          </button>
        `).join('')}
      </div>
    ` : '';

    this.container.innerHTML = `
      ${selectorHtml}

      <div style="text-align: center; margin-bottom: 16px;">
        <span style="display: inline-block; padding: 5px 14px; background: #F5F3FF; border: 1px solid #DDD6FE; border-radius: 9999px; color: #6D28D9; font-size: 0.8rem; font-weight: 700;">
          ✨ ${chain.length}-Student Closed Loop Exchange
        </span>
      </div>

      <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 18px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.04); position: relative;">
        <svg class="chain-graph-svg" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="chainGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#7C3AED" />
              <stop offset="50%" stop-color="#2563EB" />
              <stop offset="100%" stop-color="#0284C7" />
            </linearGradient>
            <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#0284C7" />
            </marker>
          </defs>

          ${svgEdges}
          ${svgNodes}
        </svg>

        <div style="margin-top: 16px; padding: 16px; background: #F8FAFC; border-radius: 12px; border: 1px solid #E2E8F0;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            <span style="color: #7C3AED; font-size: 1.1rem;">💡</span>
            <h4 style="font-size: 0.95rem; color: #0F172A; font-weight: 700;">How This Swap Chain Operates</h4>
          </div>
          <p style="font-size: 0.88rem; color: #334155; line-height: 1.6;">
            ${chain.explanation}
          </p>
        </div>
      </div>

      <div class="chain-steps-list">
        ${chain.steps.map((s, idx) => `
          <div class="chain-step-card" style="background: #FFFFFF; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div class="step-num">STAGE ${idx + 1} OF ${chain.length}</div>
            <div class="chain-step-title">${this.escapeHtml(s.name)}</div>
            <div style="font-size: 0.78rem; color: #64748B; margin-bottom: 8px;">${this.escapeHtml(s.course)}</div>
            <div class="chain-step-exchange">
              <div style="color: #047857; font-size: 0.82rem; font-weight: 500;">
                <strong style="color: #065F46;">Teaches:</strong> ${this.escapeHtml(s.teaches_skill)} → <strong style="color: #0F172A;">${this.escapeHtml(s.teaches_to_name)}</strong>
              </div>
              <div style="color: #1D4ED8; font-size: 0.82rem; font-weight: 500;">
                <strong style="color: #1E40AF;">Receives:</strong> ${this.escapeHtml(s.receives_skill)} ← <strong style="color: #0F172A;">${this.escapeHtml(s.receives_from_name)}</strong>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  switchChain(index) {
    this.currentChainIndex = index;
    this.renderCurrentChain();
  }

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}

// Attach globally
window.ChainsVisualizer = ChainsVisualizer;
