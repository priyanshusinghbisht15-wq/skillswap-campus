/**
 * SkillSwap Campus — Frontend Core Architecture & State Management
 * Clean Modern White Theme Edition
 */

class SkillSwapApp {
  constructor() {
    this.currentStudentId = 1; // Default: Asha Patel
    this.currentStudent = null;
    this.allStudents = [];
    this.heatmapChart = null;
    this.dashboardGapChart = null;
    
    this.init();
  }

  async init() {
    this.bindNavigation();
    this.bindModals();
    await this.loadAllStudents();
    await this.switchStudent(this.currentStudentId);
    
    // Auto-discover chains visualizer
    window.chainsVisualizer = new ChainsVisualizer('chainVisualizerContainer');
    this.loadSwapChains();
  }

  // --- Student & Global State ---
  async loadAllStudents() {
    try {
      const res = await fetch('/api/students');
      const data = await res.json();
      this.allStudents = data.students || [];

      // Populate Topbar Demo Switcher
      const select = document.getElementById('studentSwitcher');
      if (select) {
        select.innerHTML = this.allStudents.map(s => 
          `<option value="${s.id}">${s.name} (${s.year}, ${s.course.split(' ')[0]})</option>`
        ).join('');
        select.value = this.currentStudentId;

        select.addEventListener('change', (e) => {
          this.switchStudent(parseInt(e.target.value));
        });
      }
    } catch (err) {
      console.error('Failed loading students', err);
    }
  }

  async switchStudent(studentId) {
    this.currentStudentId = studentId;
    try {
      const res = await fetch(`/api/students/${studentId}`);
      this.currentStudent = await res.json();

      // Update Topbar UI
      document.getElementById('topbarUserName').textContent = this.currentStudent.name;
      document.getElementById('topbarUserLevel').textContent = `Lvl ${this.currentStudent.level} (${this.currentStudent.xp} XP)`;
      document.getElementById('topbarUserAvatar').src = this.currentStudent.avatar_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150';

      // Update current active tab view
      this.refreshCurrentView();
    } catch (err) {
      console.error('Failed switching student', err);
    }
  }

  refreshCurrentView() {
    const activeLink = document.querySelector('.nav-link.active');
    const viewName = activeLink ? activeLink.getAttribute('data-view') : 'dashboard';
    this.navigateTo(viewName);
  }

  // --- Navigation Router ---
  bindNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const view = link.getAttribute('data-view');
        this.navigateTo(view);
      });
    });

    // Mobile menu toggle
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('appSidebar');
    if (mobileBtn && sidebar) {
      mobileBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
      });
    }

    // Reset Demo Button
    const resetBtn = document.getElementById('resetDemoBtn');
    if (resetBtn) {
      resetBtn.addEventListener('click', async () => {
        if (confirm('Reset campus database to clean deterministic demo data?')) {
          await fetch('/api/demo/reset', { method: 'POST' });
          alert('Demo data restored!');
          await this.loadAllStudents();
          await this.switchStudent(this.currentStudentId);
        }
      });
    }
  }

  navigateTo(viewName) {
    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(l => {
      l.classList.toggle('active', l.getAttribute('data-view') === viewName);
    });

    // Close mobile sidebar if open
    const sidebar = document.getElementById('appSidebar');
    if (sidebar) sidebar.classList.remove('open');

    // Switch visible view section
    document.querySelectorAll('.view-section').forEach(sec => {
      sec.classList.remove('active');
    });

    const activeSec = document.getElementById(`view-${viewName}`);
    if (activeSec) {
      activeSec.classList.add('active');
    }

    // Load view data
    switch (viewName) {
      case 'dashboard':
        this.loadDashboard();
        break;
      case 'profile':
        this.loadProfile();
        break;
      case 'matchmaking':
        this.loadMatchmaking();
        break;
      case 'chains':
        this.loadSwapChains();
        break;
      case 'sessions':
        this.loadSessions();
        break;
      case 'notes':
        this.loadAllNotes();
        break;
      case 'roadmaps':
        this.loadRoadmaps();
        break;
      case 'heatmap':
        this.loadHeatmap();
        break;
      case 'achievements':
        this.loadAchievements();
        break;
      case 'report':
        this.loadReport();
        break;
    }
  }

  // --- 1. Dashboard View ---
  async loadDashboard() {
    if (!this.currentStudent) return;
    const s = this.currentStudent;

    document.getElementById('dashWelcomeName').textContent = s.name.split(' ')[0];
    document.getElementById('dashStatSessions').textContent = (s.completed_teaching_sessions || 0) + (s.completed_learning_sessions || 0);
    document.getElementById('dashStatSkillsLearned').textContent = s.skills_wanted.length;
    document.getElementById('dashStatTeachingHours').textContent = ((s.completed_teaching_sessions || 0) * 1.0).toFixed(1) + 'h';
    document.getElementById('dashStatStreak').textContent = `${s.streak_weeks} wks`;

    // Mini Match recommendations
    try {
      const matchRes = await fetch(`/api/matchmaking/${s.id}`);
      const matchData = await matchRes.json();
      const topMatches = (matchData.matches || []).slice(0, 3);

      const recContainer = document.getElementById('dashRecommendedPartners');
      if (recContainer) {
        if (!topMatches.length) {
          recContainer.innerHTML = '<p style="color: #64748B; font-size: 0.85rem;">No partner matches found yet.</p>';
        } else {
          recContainer.innerHTML = topMatches.map(m => `
            <div class="partner-card" style="padding: 16px; margin-bottom: 12px;">
              <div class="partner-top">
                <img src="${m.partner.avatar_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150'}" class="partner-avatar" style="width: 44px; height: 44px;"/>
                <div class="partner-info">
                  <h3 style="font-size: 0.95rem;">${this.escapeHtml(m.partner.name)}</h3>
                  <p>${this.escapeHtml(m.partner.course)}</p>
                </div>
                <div style="margin-left: auto; text-align: right;">
                  <span style="font-weight: 800; color: #7C3AED; font-size: 1.15rem;">${m.match.overall_score}%</span>
                  <div style="font-size: 0.72rem; color: #64748B; font-weight: 600;">${m.match.match_tier}</div>
                </div>
              </div>
              <div style="font-size: 0.82rem; color: #475569; margin-top: 6px;">
                ${this.escapeHtml(m.match.breakdown.skill_compatibility.reason)}
              </div>
              <div style="display: flex; gap: 8px; margin-top: 10px;">
                <button class="btn btn-primary btn-sm" style="flex: 1;" onclick="window.app.openScheduleModal(${m.partner.id}, '${this.escapeHtml(m.partner.name)}')">
                  Schedule Swap
                </button>
                <button class="btn btn-secondary btn-sm" onclick="window.app.openFreeSlotModal(${s.id}, ${m.partner.id}, '${this.escapeHtml(m.partner.name)}')">
                  Free Slots
                </button>
              </div>
            </div>
          `).join('');
        }
      }
    } catch (e) {
      console.error(e);
    }

    // Upcoming sessions preview
    try {
      const sessRes = await fetch(`/api/sessions?student_id=${s.id}`);
      const sessData = await sessRes.json();
      const upcoming = (sessData.sessions || []).filter(x => x.status === 'accepted' || x.status === 'pending').slice(0, 3);

      const sessContainer = document.getElementById('dashUpcomingSessions');
      if (sessContainer) {
        if (!upcoming.length) {
          sessContainer.innerHTML = '<p style="color: #64748B; font-size: 0.85rem;">No upcoming sessions scheduled. Connect with a partner to start learning!</p>';
        } else {
          sessContainer.innerHTML = upcoming.map(sess => `
            <div class="session-item" style="padding: 12px 16px;">
              <div>
                <div style="font-weight: 700; font-size: 0.9rem; color: #0F172A;">
                  ${sess.skill_name} (${sess.session_format})
                </div>
                <div style="font-size: 0.78rem; color: #64748B;">
                  With ${sess.mentor_id === s.id ? sess.learner_name + ' (Learner)' : sess.mentor_name + ' (Mentor)'} • ${sess.scheduled_date} at ${sess.start_time}
                </div>
              </div>
              <span class="session-badge-status status-${sess.status}">${sess.status}</span>
            </div>
          `).join('');
        }
      }
    } catch (e) {
      console.error(e);
    }

    // Mini Campus Skill Gap Chart
    this.renderDashboardGapChart();
  }

  async renderDashboardGapChart() {
    try {
      const res = await fetch('/api/heatmap');
      const data = await res.json();
      const topGaps = (data.heatmap || []).slice(0, 4);

      const ctx = document.getElementById('dashGapChart');
      if (!ctx) return;

      if (this.dashboardGapChart) {
        this.dashboardGapChart.destroy();
      }

      this.dashboardGapChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: topGaps.map(g => g.name),
          datasets: [
            {
              label: 'Mentors Offering',
              data: topGaps.map(g => g.offered_count),
              backgroundColor: 'rgba(5, 150, 105, 0.85)',
              borderRadius: 4
            },
            {
              label: 'Students Seeking',
              data: topGaps.map(g => g.wanted_count),
              backgroundColor: 'rgba(124, 58, 237, 0.85)',
              borderRadius: 4
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom', labels: { color: '#334155', boxWidth: 12, font: { size: 11, weight: '600' } } }
          },
          scales: {
            x: { ticks: { color: '#64748B', font: { size: 11 } }, grid: { display: false } },
            y: { ticks: { color: '#64748B', font: { size: 11 }, stepSize: 1 }, grid: { color: '#F1F5F9' } }
          }
        }
      });
    } catch (e) {
      console.error(e);
    }
  }

  // --- 2. Profile View ---
  loadProfile() {
    if (!this.currentStudent) return;
    const s = this.currentStudent;

    document.getElementById('profileAvatarLarge').src = s.avatar_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150';
    document.getElementById('profileName').textContent = s.name;
    document.getElementById('profileCourseYear').textContent = `${s.course} • ${s.year}`;
    document.getElementById('profileBio').textContent = s.bio || 'No bio provided.';
    document.getElementById('profileEmail').textContent = s.email;
    document.getElementById('profileRatingAvg').textContent = s.rating_avg ? `${s.rating_avg} / 5.0 (${s.rating_count} reviews)` : 'No reviews yet';

    // Skills Offered
    const offeredContainer = document.getElementById('profileSkillsOffered');
    offeredContainer.innerHTML = (s.skills_offered || []).map(sk => `
      <div style="display: flex; align-items: center; justify-content: space-between; background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px; padding: 8px 14px; margin-bottom: 6px;">
        <span style="font-size: 0.85rem; color: #065F46; font-weight: 700;">${this.escapeHtml(sk.skill_name)}</span>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="font-size: 0.72rem; color: #047857; font-weight: 600;">${sk.proficiency}</span>
          <button style="background: none; border: none; color: #EF4444; cursor: pointer; font-size: 0.85rem; font-weight: bold;" onclick="window.app.deleteSkill(${sk.id})">✕</button>
        </div>
      </div>
    `).join('') || '<p style="color: #64748B; font-size: 0.85rem;">No skills offered listed.</p>';

    // Skills Wanted
    const wantedContainer = document.getElementById('profileSkillsWanted');
    wantedContainer.innerHTML = (s.skills_wanted || []).map(sk => `
      <div style="display: flex; align-items: center; justify-content: space-between; background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 8px 14px; margin-bottom: 6px;">
        <span style="font-size: 0.85rem; color: #1E40AF; font-weight: 700;">${this.escapeHtml(sk.skill_name)}</span>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="font-size: 0.72rem; color: #1D4ED8; font-weight: 600;">${sk.proficiency}</span>
          <button style="background: none; border: none; color: #EF4444; cursor: pointer; font-size: 0.85rem; font-weight: bold;" onclick="window.app.deleteSkill(${sk.id})">✕</button>
        </div>
      </div>
    `).join('') || '<p style="color: #64748B; font-size: 0.85rem;">No skills wanted listed.</p>';

    // Availability
    const availContainer = document.getElementById('profileAvailabilityList');
    availContainer.innerHTML = (s.availability || []).map(av => `
      <div style="display: inline-block; background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 6px 14px; margin: 4px; font-size: 0.82rem; color: #0F172A;">
        <strong style="color: #7C3AED;">${av.day_of_week}:</strong> ${av.start_time} - ${av.end_time}
      </div>
    `).join('') || '<p style="color: #64748B; font-size: 0.85rem;">No weekly availability entered.</p>';
  }

  openEditProfileModal() {
    const s = this.currentStudent;
    document.getElementById('editProfileName').value = s.name;
    document.getElementById('editProfileCourse').value = s.course;
    document.getElementById('editProfileYear').value = s.year;
    document.getElementById('editProfileBio').value = s.bio || '';
    document.getElementById('editProfileModal').classList.add('active');
  }

  async saveProfile(e) {
    e.preventDefault();
    const payload = {
      name: document.getElementById('editProfileName').value,
      course: document.getElementById('editProfileCourse').value,
      year: document.getElementById('editProfileYear').value,
      bio: document.getElementById('editProfileBio').value
    };

    await fetch(`/api/students/${this.currentStudentId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    document.getElementById('editProfileModal').classList.remove('active');
    await this.switchStudent(this.currentStudentId);
  }

  async addSkill(skillType) {
    const skillName = prompt(`Enter ${skillType === 'offer' ? 'teaching' : 'learning'} skill name:`);
    if (!skillName || !skillName.trim()) return;

    const prof = prompt('Proficiency level (Beginner, Intermediate, Advanced):', 'Intermediate') || 'Intermediate';

    await fetch(`/api/students/${this.currentStudentId}/skills`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        skill_name: skillName.trim(),
        skill_type: skillType,
        proficiency: prof
      })
    });

    await this.switchStudent(this.currentStudentId);
  }

  async deleteSkill(studentSkillId) {
    if (!confirm('Remove this skill from your profile?')) return;
    await fetch(`/api/students/${this.currentStudentId}/skills/${studentSkillId}`, {
      method: 'DELETE'
    });
    await this.switchStudent(this.currentStudentId);
  }

  // --- 3. Smart Matchmaking View ---
  async loadMatchmaking() {
    if (!this.currentStudent) return;
    const container = document.getElementById('matchmakingContainer');
    container.innerHTML = '<div style="text-align: center; padding: 40px; color: #64748B;">Calculating dynamic compatibility algorithms...</div>';

    try {
      const res = await fetch(`/api/matchmaking/${this.currentStudentId}`);
      const data = await res.json();
      const matches = data.matches || [];

      if (!matches.length) {
        container.innerHTML = '<p style="color: #64748B;">No candidate peers found on campus.</p>';
        return;
      }

      container.innerHTML = `
        <div style="background: #F5F3FF; border: 1px solid #DDD6FE; border-radius: 12px; padding: 14px 18px; margin-bottom: 24px; font-size: 0.88rem; color: #334155;">
          <strong style="color: #6D28D9;">Algorithmic Scoring Model:</strong> 
          Weighted by <strong>Two-way Skill Match (50%)</strong>, <strong>Experience Level (20%)</strong>, <strong>Shared Free Time (20%)</strong>, and <strong>Peer Rating (10%)</strong>.
        </div>

        <div class="partner-grid">
          ${matches.map((m, idx) => `
            <div class="partner-card ${m.match.is_two_way_swap ? 'two-way-badge' : ''}">
              <div class="partner-top">
                <img src="${m.partner.avatar_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150'}" class="partner-avatar"/>
                <div class="partner-info">
                  <h3>${this.escapeHtml(m.partner.name)}</h3>
                  <p>${this.escapeHtml(m.partner.course)} • ${m.partner.year}</p>
                  <div style="font-size: 0.78rem; color: #D97706; font-weight: 700; margin-top: 2px;">
                    ★ ${m.partner.rating_avg ? m.partner.rating_avg + ' / 5.0' : 'New Mentor'}
                  </div>
                </div>
              </div>

              <!-- Match Score Banner -->
              <div class="match-score-badge">
                <div>
                  <div class="score-number">${m.match.overall_score}%</div>
                  <div class="score-text">${m.match.match_tier}</div>
                </div>
                <button class="score-breakdown-btn" onclick="document.getElementById('breakdown-${idx}').classList.toggle('active')">
                  View Scoring Breakdown ▾
                </button>
              </div>

              <!-- Expandable Breakdown -->
              <div id="breakdown-${idx}" class="breakdown-drawer" style="display: none;">
                <div class="breakdown-item">
                  <div class="breakdown-header">
                    <span>Two-Way Skill Compatibility (${m.match.breakdown.skill_compatibility.weight})</span>
                    <strong style="color: #0F172A;">${m.match.breakdown.skill_compatibility.score}%</strong>
                  </div>
                  <div class="progress-track"><div class="progress-bar-fill" style="width: ${m.match.breakdown.skill_compatibility.score}%;"></div></div>
                  <span style="font-size: 0.72rem; color: #64748B;">${this.escapeHtml(m.match.breakdown.skill_compatibility.reason)}</span>
                </div>

                <div class="breakdown-item">
                  <div class="breakdown-header">
                    <span>Experience Level Alignment (${m.match.breakdown.experience_compatibility.weight})</span>
                    <strong style="color: #0F172A;">${m.match.breakdown.experience_compatibility.score}%</strong>
                  </div>
                  <div class="progress-track"><div class="progress-bar-fill" style="width: ${m.match.breakdown.experience_compatibility.score}%;"></div></div>
                  <span style="font-size: 0.72rem; color: #64748B;">${this.escapeHtml(m.match.breakdown.experience_compatibility.reason)}</span>
                </div>

                <div class="breakdown-item">
                  <div class="breakdown-header">
                    <span>Shared Free Time Overlap (${m.match.breakdown.shared_free_time.weight})</span>
                    <strong style="color: #0F172A;">${m.match.breakdown.shared_free_time.score}%</strong>
                  </div>
                  <div class="progress-track"><div class="progress-bar-fill" style="width: ${m.match.breakdown.shared_free_time.score}%;"></div></div>
                  <span style="font-size: 0.72rem; color: #64748B;">${this.escapeHtml(m.match.breakdown.shared_free_time.reason)}</span>
                </div>

                <div class="breakdown-item">
                  <div class="breakdown-header">
                    <span>Partner Peer Rating (${m.match.breakdown.partner_rating.weight})</span>
                    <strong style="color: #0F172A;">${m.match.breakdown.partner_rating.score}%</strong>
                  </div>
                  <div class="progress-track"><div class="progress-bar-fill" style="width: ${m.match.breakdown.partner_rating.score}%;"></div></div>
                  <span style="font-size: 0.72rem; color: #64748B;">${this.escapeHtml(m.match.breakdown.partner_rating.reason)}</span>
                </div>
              </div>

              <!-- Skills Offered & Wanted -->
              <div class="skill-tags-group">
                <span class="skill-tags-label">Teaches</span>
                <div class="tags-row">
                  ${m.partner.skills_offered.map(sk => `
                    <span class="skill-tag ${m.match.user_can_learn.includes(sk.skill_name) ? 'matched' : 'offer'}">
                      ${this.escapeHtml(sk.skill_name)}
                    </span>
                  `).join('')}
                </div>
              </div>

              <div class="skill-tags-group">
                <span class="skill-tags-label">Wants to Learn</span>
                <div class="tags-row">
                  ${m.partner.skills_wanted.map(sk => `
                    <span class="skill-tag ${m.match.partner_can_learn.includes(sk.skill_name) ? 'matched' : 'want'}">
                      ${this.escapeHtml(sk.skill_name)}
                    </span>
                  `).join('')}
                </div>
              </div>

              <!-- Actions -->
              <div style="display: flex; gap: 8px; margin-top: auto; padding-top: 8px;">
                <button class="btn btn-primary btn-sm" style="flex: 1;" onclick="window.app.openScheduleModal(${m.partner.id}, '${this.escapeHtml(m.partner.name)}')">
                  📅 Schedule Swap
                </button>
                <button class="btn btn-secondary btn-sm" onclick="window.app.openFreeSlotModal(${this.currentStudentId}, ${m.partner.id}, '${this.escapeHtml(m.partner.name)}')">
                  🕒 Free Slots
                </button>
              </div>
            </div>
          `).join('')}
        </div>
      `;

      // Enable toggling breakdown drawers
      document.querySelectorAll('.breakdown-drawer').forEach(d => {
        d.classList.remove('active');
      });
    } catch (err) {
      console.error(err);
      container.innerHTML = '<p style="color: #EF4444;">Failed calculating matchmaking scores.</p>';
    }
  }

  // --- 4. Skill Swap Chains (Signature Feature) ---
  async loadSwapChains() {
    const btn = document.getElementById('discoverChainsBtn');
    if (btn) btn.textContent = 'Discovering Cycles...';

    try {
      const res = await fetch('/api/swap-chains');
      const data = await res.json();
      if (window.chainsVisualizer) {
        window.chainsVisualizer.render(data.chains);
      }
    } catch (err) {
      console.error('Error fetching swap chains', err);
    } finally {
      if (btn) btn.textContent = '🔄 Discover Chains';
    }
  }

  // --- 5. Sessions View ---
  async loadSessions(filterStatus = '') {
    if (!this.currentStudent) return;
    const container = document.getElementById('sessionsListContainer');
    container.innerHTML = '<div style="color: #64748B; padding: 20px;">Loading sessions...</div>';

    try {
      const url = `/api/sessions?student_id=${this.currentStudentId}${filterStatus ? '&status=' + filterStatus : ''}`;
      const res = await fetch(url);
      const data = await res.json();
      const sessions = data.sessions || [];

      if (!sessions.length) {
        container.innerHTML = `
          <div style="text-align: center; padding: 48px; background: #FFFFFF; border-radius: 12px; border: 1px solid var(--border-subtle);">
            <p style="color: #64748B; margin-bottom: 12px;">No learning sessions found.</p>
            <button class="btn btn-primary" onclick="window.app.navigateTo('matchmaking')">Find a Peer to Swap With</button>
          </div>
        `;
        return;
      }

      container.innerHTML = sessions.map(sess => {
        const isMentor = sess.mentor_id === this.currentStudentId;
        const partnerName = isMentor ? sess.learner_name : sess.mentor_name;
        const roleLabel = isMentor ? 'Teaching (Mentor)' : 'Learning (Student)';

        return `
          <div class="session-item">
            <div class="session-meta">
              <div style="width: 44px; height: 44px; border-radius: 50%; background: ${isMentor ? '#ECFDF5' : '#EFF6FF'}; border: 1px solid ${isMentor ? '#A7F3D0' : '#BFDBFE'}; display: flex; align-items: center; justify-content: center; font-size: 1.25rem;">
                ${isMentor ? '👨‍🏫' : '🎒'}
              </div>
              <div>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <strong style="color: #0F172A; font-size: 1rem;">${this.escapeHtml(sess.skill_name)}</strong>
                  <span style="font-size: 0.72rem; padding: 2px 8px; border-radius: 4px; background: #F1F5F9; color: #475569; font-weight: 600;">${roleLabel}</span>
                  <span class="session-badge-status status-${sess.status}">${sess.status}</span>
                </div>
                <div style="font-size: 0.8rem; color: #64748B; margin-top: 4px;">
                  With <strong style="color: #334155;">${this.escapeHtml(partnerName)}</strong> • ${sess.scheduled_date} at ${sess.start_time} (${sess.duration_minutes} min) • ${sess.session_format}
                </div>
                ${sess.location_or_link ? `<div style="font-size: 0.75rem; color: #0284C7; font-weight: 500; margin-top: 2px;">📍 ${this.escapeHtml(sess.location_or_link)}</div>` : ''}
              </div>
            </div>

            <div class="session-actions">
              ${sess.status === 'pending' && isMentor ? `
                <button class="btn btn-outline-emerald btn-sm" onclick="window.app.updateSessionStatus(${sess.id}, 'accepted')">Accept</button>
              ` : ''}

              ${sess.status === 'accepted' ? `
                <button class="btn btn-outline-emerald btn-sm" onclick="window.app.updateSessionStatus(${sess.id}, 'completed')">Mark Completed</button>
              ` : ''}

              ${sess.status !== 'completed' && sess.status !== 'cancelled' ? `
                <button class="btn btn-outline-rose btn-sm" onclick="window.app.updateSessionStatus(${sess.id}, 'cancelled')">Cancel</button>
              ` : ''}

              <!-- Shared Notes Button -->
              <button class="btn btn-secondary btn-sm" onclick="window.app.openNotesModal(${sess.id}, '${this.escapeHtml(sess.skill_name)}')">
                📝 Notes ${sess.has_note ? '✓' : ''}
              </button>

              <!-- Completed Session Actions: Teach-Back & Rating -->
              ${sess.status === 'completed' ? `
                <button class="btn btn-secondary btn-sm" onclick="window.app.openTeachBackModal(${sess.id}, ${isMentor}, '${this.escapeHtml(partnerName)}')">
                  💡 Teach-Back ${sess.teach_back_confirmed ? '★' : ''}
                </button>
                <button class="btn btn-secondary btn-sm" onclick="window.app.openRatingModal(${sess.id}, '${this.escapeHtml(partnerName)}')">
                  ⭐ Rate
                </button>
              ` : ''}
            </div>
          </div>
        `;
      }).join('');
    } catch (err) {
      console.error(err);
      container.innerHTML = '<p style="color: #EF4444;">Failed loading sessions.</p>';
    }
  }

  async updateSessionStatus(sessionId, newStatus) {
    if (!confirm(`Are you sure you want to mark this session as ${newStatus}?`)) return;

    try {
      const res = await fetch(`/api/sessions/${sessionId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
      const data = await res.json();
      if (res.ok) {
        alert(data.message);
        this.loadSessions();
        await this.switchStudent(this.currentStudentId);
      } else {
        alert(data.error || 'Failed updating status');
      }
    } catch (err) {
      console.error(err);
    }
  }

  // --- 6. Shared Notes View ---
  async loadAllNotes() {
    if (!this.currentStudent) return;
    const container = document.getElementById('allNotesContainer');
    container.innerHTML = '<div style="color: #64748B;">Loading shared study notes...</div>';

    try {
      const res = await fetch(`/api/sessions?student_id=${this.currentStudentId}`);
      const data = await res.json();
      const sessions = (data.sessions || []).filter(s => s.has_note || s.status === 'completed');

      if (!sessions.length) {
        container.innerHTML = '<p style="color: #64748B;">No session notes created yet. Open any session to write learning outcomes and topics!</p>';
        return;
      }

      const noteCards = await Promise.all(sessions.map(async (sess) => {
        const noteRes = await fetch(`/api/sessions/${sess.id}/notes`);
        const noteData = await noteRes.json();
        const note = noteData.note;

        return `
          <div class="card" style="margin-bottom: 16px;">
            <div class="card-header">
              <div>
                <h3 class="card-title">${this.escapeHtml(sess.skill_name)} Session Notes</h3>
                <p style="font-size: 0.8rem; color: #64748B;">
                  ${sess.scheduled_date} • Mentor: <strong style="color: #334155;">${this.escapeHtml(sess.mentor_name)}</strong> | Learner: <strong style="color: #334155;">${this.escapeHtml(sess.learner_name)}</strong>
                </p>
              </div>
              <button class="btn btn-secondary btn-sm" onclick="window.app.openNotesModal(${sess.id}, '${this.escapeHtml(sess.skill_name)}')">Edit Notes</button>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px;">
              <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 14px; border-radius: 10px;">
                <div style="font-size: 0.75rem; color: #7C3AED; font-weight: 700; text-transform: uppercase;">Topics Covered</div>
                <div style="font-size: 0.88rem; color: #334155; margin-top: 6px; white-space: pre-line; line-height: 1.5;">${this.escapeHtml(note ? note.topics_covered : 'No topics recorded yet.')}</div>
              </div>
              <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 14px; border-radius: 10px;">
                <div style="font-size: 0.75rem; color: #059669; font-weight: 700; text-transform: uppercase;">Learning Outcomes</div>
                <div style="font-size: 0.88rem; color: #334155; margin-top: 6px; white-space: pre-line; line-height: 1.5;">${this.escapeHtml(note ? note.learning_outcomes : 'No outcomes recorded yet.')}</div>
              </div>
              <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 14px; border-radius: 10px;">
                <div style="font-size: 0.75rem; color: #0284C7; font-weight: 700; text-transform: uppercase;">Next Steps</div>
                <div style="font-size: 0.88rem; color: #334155; margin-top: 6px; white-space: pre-line; line-height: 1.5;">${this.escapeHtml(note ? note.next_steps : 'No next steps planned.')}</div>
              </div>
            </div>
          </div>
        `;
      }));

      container.innerHTML = noteCards.join('');
    } catch (err) {
      console.error(err);
    }
  }

  // --- 7. Learning Roadmaps View ---
  async loadRoadmaps() {
    const container = document.getElementById('roadmapsContainer');
    container.innerHTML = '<div style="color: #64748B;">Loading learning pathways...</div>';

    try {
      const res = await fetch('/api/roadmaps');
      const data = await res.json();
      const roadmaps = data.roadmaps || [];

      container.innerHTML = roadmaps.map(r => `
        <div class="roadmap-card">
          <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
            <div>
              <span style="font-size: 0.75rem; text-transform: uppercase; color: #7C3AED; font-weight: 700;">${this.escapeHtml(r.category)}</span>
              <h2 style="font-size: 1.3rem; color: #0F172A; margin-top: 2px;">${this.escapeHtml(r.title)}</h2>
            </div>
            <span style="font-size: 0.8rem; background: #F5F3FF; color: #6D28D9; border: 1px solid #DDD6FE; font-weight: 600; padding: 4px 12px; border-radius: 9999px;">
              ${r.stages.length} Milestones
            </span>
          </div>
          <p style="color: #475569; font-size: 0.88rem; margin: 8px 0 16px;">${this.escapeHtml(r.description)}</p>

          <div class="roadmap-stages">
            ${r.stages.map(st => `
              <div class="stage-card">
                <div class="stage-info">
                  <div class="stage-num-badge">${st.stage}</div>
                  <div>
                    <strong style="color: #0F172A; font-size: 0.95rem;">${this.escapeHtml(st.title)}</strong>
                    <div style="font-size: 0.8rem; color: #0284C7; font-weight: 600;">Target Skill: ${this.escapeHtml(st.skill_name)}</div>
                    <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">${this.escapeHtml(st.description)}</div>
                  </div>
                </div>

                <div style="display: flex; align-items: center; gap: 10px;">
                  <div style="text-align: right;">
                    <div style="font-size: 0.72rem; color: #64748B;">Campus Mentors</div>
                    <div style="font-size: 0.82rem; font-weight: 700; color: #059669;">
                      ${st.mentors.length ? `${st.mentors.length} Available` : 'Looking for mentor'}
                    </div>
                  </div>
                  ${st.mentors.length ? `
                    <button class="btn btn-primary btn-sm" onclick="window.app.openScheduleModal(${st.mentors[0].id}, '${this.escapeHtml(st.mentors[0].name)}')">
                      Find Mentor
                    </button>
                  ` : `
                    <button class="btn btn-secondary btn-sm" disabled style="opacity: 0.6;">No Mentor Yet</button>
                  `}
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `).join('');
    } catch (err) {
      console.error(err);
    }
  }

  // --- 8. Campus Skill Heatmap View ---
  async loadHeatmap() {
    try {
      const res = await fetch('/api/heatmap');
      const data = await res.json();
      const items = data.heatmap || [];

      // Render Ranked Shortage Table
      const tableBody = document.getElementById('heatmapTableBody');
      if (tableBody) {
        tableBody.innerHTML = items.map(item => `
          <tr style="border-bottom: 1px solid var(--border-subtle);">
            <td style="padding: 12px; font-weight: 700; color: #0F172A;">${this.escapeHtml(item.name)}</td>
            <td style="padding: 12px; color: #475569;">${this.escapeHtml(item.category)}</td>
            <td style="padding: 12px; color: #059669; font-weight: 700;">${item.offered_count} students</td>
            <td style="padding: 12px; color: #7C3AED; font-weight: 700;">${item.wanted_count} students</td>
            <td style="padding: 12px;">
              <span style="font-weight: 800; color: ${item.gap < 0 ? '#E11D48' : '#059669'};">
                ${item.gap > 0 ? '+' : ''}${item.gap}
              </span>
            </td>
            <td style="padding: 12px;">
              <span style="padding: 3px 9px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; background: ${item.gap < -1 ? '#FFF1F2; color: #BE123C; border: 1px solid #FECDD3;' : '#ECFDF5; color: #047857; border: 1px solid #A7F3D0;'}">
                ${item.status}
              </span>
            </td>
          </tr>
        `).join('');
      }

      // Render Chart.js Horizontal Bar Chart
      const ctx = document.getElementById('heatmapMainChart');
      if (ctx) {
        if (this.heatmapChart) {
          this.heatmapChart.destroy();
        }

        this.heatmapChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: items.map(i => i.name),
            datasets: [
              {
                label: 'Skills Offered (Supply)',
                data: items.map(i => i.offered_count),
                backgroundColor: 'rgba(5, 150, 105, 0.85)',
                borderColor: '#059669',
                borderWidth: 1,
                borderRadius: 6
              },
              {
                label: 'Skills Wanted (Demand)',
                data: items.map(i => i.wanted_count),
                backgroundColor: 'rgba(124, 58, 237, 0.85)',
                borderColor: '#7C3AED',
                borderWidth: 1,
                borderRadius: 6
              }
            ]
          },
          options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { labels: { color: '#334155', font: { size: 12, weight: '600' } } },
              tooltip: {
                callbacks: {
                  afterLabel: (ctx) => {
                    const item = items[ctx.dataIndex];
                    return `Supply-Demand Gap: ${item.gap} (${item.status})`;
                  }
                }
              }
            },
            scales: {
              x: {
                ticks: { color: '#64748B', stepSize: 1 },
                grid: { color: '#F1F5F9' }
              },
              y: {
                ticks: { color: '#0F172A', font: { size: 11, weight: '600' } },
                grid: { display: false }
              }
            }
          }
        });
      }
    } catch (err) {
      console.error(err);
    }
  }

  // --- 9. Achievements & Gamification View ---
  async loadAchievements() {
    if (!this.currentStudent) return;
    try {
      const res = await fetch(`/api/students/${this.currentStudentId}/achievements`);
      const data = await res.json();
      const s = data.student;

      document.getElementById('achieveLevelNumber').textContent = s.level;
      document.getElementById('achieveCurrentXP').textContent = `${s.xp} XP`;
      document.getElementById('achieveNextLevelXP').textContent = `${s.next_level_xp} XP Goal`;
      document.getElementById('achieveProgressBar').style.width = `${s.progress_pct}%`;
      document.getElementById('achieveStreak').textContent = `${s.streak_weeks} Weeks`;

      const grid = document.getElementById('badgesGridContainer');
      grid.innerHTML = (data.badges || []).map(b => `
        <div class="badge-item ${b.earned ? '' : 'locked'}">
          <div class="badge-icon-box">
            ${this.getBadgeIcon(b.badge.icon)}
          </div>
          <div>
            <div class="badge-title">${this.escapeHtml(b.badge.name)}</div>
            <div class="badge-desc">${this.escapeHtml(b.badge.description)}</div>
            <div class="badge-xp-tag">+${b.badge.xp_reward} XP</div>
            ${b.earned ? `<div style="font-size: 0.72rem; color: #059669; font-weight: 600; margin-top: 4px;">Unlocked ${b.awarded_at ? b.awarded_at.split('T')[0] : 'Recently'}</div>` : '<div style="font-size: 0.72rem; color: #94A3B8; margin-top: 4px;">Locked</div>'}
          </div>
        </div>
      `).join('');
    } catch (err) {
      console.error(err);
    }
  }

  getBadgeIcon(iconName) {
    const icons = {
      'zap': '⚡',
      'award': '🏆',
      'book-open': '📖',
      'flame': '🔥',
      'check-circle-2': '🎓'
    };
    return icons[iconName] || '🌟';
  }

  // --- 10. Learning Report View ---
  async loadReport() {
    if (!this.currentStudent) return;
    try {
      const res = await fetch(`/api/students/${this.currentStudentId}/report`);
      const report = await res.json();

      document.getElementById('repStudentName').textContent = report.student.name;
      document.getElementById('repCourseYear').textContent = `${report.student.course} • ${report.student.year}`;
      document.getElementById('repGeneratedAt').textContent = report.generated_at;

      document.getElementById('repTeachingHours').textContent = `${report.summary.teaching_hours} hrs`;
      document.getElementById('repLearningHours').textContent = `${report.summary.learning_hours} hrs`;
      document.getElementById('repTotalSessions').textContent = report.summary.total_completed_sessions;
      document.getElementById('repRating').textContent = report.summary.average_rating ? `${report.summary.average_rating} / 5.0` : 'N/A';
      document.getElementById('repLevel').textContent = `Level ${report.summary.level} (${report.summary.xp} XP)`;

      // Completed Sessions Table
      const sessTable = document.getElementById('repSessionsTable');
      const allCompleted = (report.mentored_sessions || []).concat(report.learned_sessions || []);
      if (!allCompleted.length) {
        sessTable.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 12px; color: #64748B;">No completed sessions on record.</td></tr>';
      } else {
        sessTable.innerHTML = allCompleted.map(s => `
          <tr style="border-bottom: 1px solid var(--border-subtle);">
            <td style="padding: 10px; color: #0F172A; font-weight: 600;">${this.escapeHtml(s.skill_name)}</td>
            <td style="padding: 10px; color: #475569;">${s.mentor_id === report.student.id ? 'Mentor' : 'Learner'}</td>
            <td style="padding: 10px; color: #475569;">${s.mentor_id === report.student.id ? s.learner_name : s.mentor_name}</td>
            <td style="padding: 10px; color: #64748B;">${s.scheduled_date}</td>
          </tr>
        `).join('');
      }

      // Badges
      const badgesContainer = document.getElementById('repBadgesContainer');
      badgesContainer.innerHTML = (report.badges || []).map(b => `
        <span style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; background: #F5F3FF; border: 1px solid #DDD6FE; border-radius: 9999px; font-size: 0.8rem; color: #6D28D9; font-weight: 600; margin: 4px;">
          ${this.getBadgeIcon(b.icon)} ${this.escapeHtml(b.name)}
        </span>
      `).join('') || '<span style="color: #64748B; font-size: 0.8rem;">No badges earned yet.</span>';

      // Save report data for export
      this.currentReportData = report;
    } catch (err) {
      console.error(err);
    }
  }

  exportReportJSON() {
    if (!this.currentReportData) return;
    const blob = new Blob([JSON.stringify(this.currentReportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `SkillSwap_Report_${this.currentStudent.name.replace(/\s+/g, '_')}.json`;
    a.click();
  }

  exportReportText() {
    if (!this.currentReportData) return;
    const r = this.currentReportData;
    const text = `
=====================================================
SKILLSWAP CAMPUS — OFFICIAL LEARNING REPORT
=====================================================
Student Name:     ${r.student.name}
Course & Year:    ${r.student.course} (${r.student.year})
Email:            ${r.student.email}
Generated At:     ${r.generated_at}

-----------------------------------------------------
PERFORMANCE SUMMARY
-----------------------------------------------------
- Total Completed Sessions: ${r.summary.total_completed_sessions}
- Teaching Contribution:    ${r.summary.teaching_hours} Hours
- Learning Investment:      ${r.summary.learning_hours} Hours
- Peer Mentor Rating:       ${r.summary.average_rating ? r.summary.average_rating + ' / 5.0' : 'N/A'}
- Experience & Rank:        Level ${r.summary.level} (${r.summary.xp} XP)
- Active Streak:            ${r.summary.streak_weeks} Weeks

-----------------------------------------------------
SKILLS OFFERED (TEACHING)
-----------------------------------------------------
${r.skills_offered.map(s => `* ${s.skill_name} [${s.proficiency}]`).join('\n')}

-----------------------------------------------------
SKILLS SOUGHT (LEARNING)
-----------------------------------------------------
${r.skills_wanted.map(s => `* ${s.skill_name} [${s.proficiency}]`).join('\n')}

-----------------------------------------------------
EARNED CAMPUS BADGES
-----------------------------------------------------
${r.badges.map(b => `[x] ${b.name} — ${b.description}`).join('\n')}

=====================================================
SkillSwap Campus — "Your skills are someone else's next breakthrough."
=====================================================
    `.trim();

    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `SkillSwap_Report_${this.currentStudent.name.replace(/\s+/g, '_')}.txt`;
    a.click();
  }

  // --- Modals Controller ---
  bindModals() {
    // Schedule modal close
    document.querySelectorAll('.modal-close-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
      });
    });

    // Schedule form submission
    const scheduleForm = document.getElementById('scheduleSessionForm');
    if (scheduleForm) {
      scheduleForm.addEventListener('submit', (e) => this.submitScheduleSession(e));
    }

    // Notes form submission
    const notesForm = document.getElementById('sharedNotesForm');
    if (notesForm) {
      notesForm.addEventListener('submit', (e) => this.submitNotes(e));
    }

    // Rating star clicks
    const starContainer = document.getElementById('starRatingSelector');
    if (starContainer) {
      starContainer.querySelectorAll('span').forEach(star => {
        star.addEventListener('click', () => {
          const rating = parseInt(star.getAttribute('data-star'));
          this.selectedRatingStars = rating;
          starContainer.querySelectorAll('span').forEach(s => {
            s.classList.toggle('selected', parseInt(s.getAttribute('data-star')) <= rating);
          });
        });
      });
    }

    // Rating form submission
    const ratingForm = document.getElementById('submitRatingForm');
    if (ratingForm) {
      ratingForm.addEventListener('submit', (e) => this.submitRating(e));
    }

    // Teach-back form submission
    const teachBackForm = document.getElementById('teachBackForm');
    if (teachBackForm) {
      teachBackForm.addEventListener('submit', (e) => this.submitTeachBack(e));
    }

    // Edit profile form
    const editProfileForm = document.getElementById('editProfileForm');
    if (editProfileForm) {
      editProfileForm.addEventListener('submit', (e) => this.saveProfile(e));
    }
  }

  // Schedule Modal
  openScheduleModal(partnerId, partnerName) {
    document.getElementById('schedPartnerId').value = partnerId;
    document.getElementById('schedPartnerName').textContent = partnerName;

    // Populate partner offered skills into select dropdown
    const partner = this.allStudents.find(s => s.id === partnerId);
    const skillSelect = document.getElementById('schedSkillSelect');
    if (partner && partner.skills_offered && partner.skills_offered.length) {
      skillSelect.innerHTML = partner.skills_offered.map(sk => 
        `<option value="${sk.skill_id}">${sk.skill_name} (${sk.proficiency})</option>`
      ).join('');
    } else {
      skillSelect.innerHTML = '<option value="1">General Knowledge Swap</option>';
    }

    // Pre-fill tomorrow's date
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    document.getElementById('schedDate').value = tomorrow.toISOString().split('T')[0];
    document.getElementById('schedTime').value = '15:00';

    document.getElementById('scheduleModal').classList.add('active');
  }

  async submitScheduleSession(e) {
    e.preventDefault();
    const partnerId = parseInt(document.getElementById('schedPartnerId').value);
    const skillId = parseInt(document.getElementById('schedSkillSelect').value);
    const scheduledDate = document.getElementById('schedDate').value;
    const startTime = document.getElementById('schedTime').value;
    const duration = parseInt(document.getElementById('schedDuration').value);
    const format = document.getElementById('schedFormat').value;
    const location = document.getElementById('schedLocation').value;

    const payload = {
      mentor_id: partnerId,
      learner_id: this.currentStudentId,
      skill_id: skillId,
      scheduled_date: scheduledDate,
      start_time: startTime,
      duration_minutes: duration,
      session_format: format,
      location_or_link: location
    };

    try {
      const res = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (res.ok) {
        alert('Learning session successfully scheduled!');
        document.getElementById('scheduleModal').classList.remove('active');
        this.navigateTo('sessions');
      } else {
        alert(data.error || 'Failed scheduling session');
      }
    } catch (err) {
      console.error(err);
      alert('Error scheduling session');
    }
  }

  // Free Slot Modal
  async openFreeSlotModal(studentAId, studentBId, partnerName) {
    const modal = document.getElementById('freeSlotModal');
    const content = document.getElementById('freeSlotModalContent');
    document.getElementById('freeSlotPartnerName').textContent = partnerName;
    content.innerHTML = '<div style="color: #64748B; padding: 20px;">Comparing weekly calendar intervals...</div>';
    modal.classList.add('active');

    try {
      const res = await fetch(`/api/free-slots?student_a=${studentAId}&student_b=${studentBId}`);
      const data = await res.json();

      if (!data.overlapping_slots || !data.overlapping_slots.length) {
        content.innerHTML = `
          <div style="text-align: center; padding: 20px;">
            <p style="color: #EF4444; font-weight: 700;">No direct weekly overlap found.</p>
            <p style="color: #64748B; font-size: 0.85rem; margin-top: 6px;">
              You can still propose a custom slot using the session planner or update your availability in My Profile.
            </p>
          </div>
        `;
      } else {
        content.innerHTML = `
          <div style="margin-bottom: 12px; color: #059669; font-weight: 700; font-size: 0.9rem;">
            ✓ Found ${data.total_overlap_minutes} minutes of shared free time weekly!
          </div>
          <div style="display: flex; flex-direction: column; gap: 8px;">
            ${data.overlapping_slots.map(slot => `
              <div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px; padding: 10px 14px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                  <strong style="color: #065F46;">${slot.day_of_week}</strong>
                  <div style="font-size: 0.8rem; color: #047857; font-weight: 600;">${slot.start_time} - ${slot.end_time} (${slot.duration_minutes} min window)</div>
                </div>
                <button class="btn btn-primary btn-sm" onclick="window.app.scheduleUsingSlot(${studentBId}, '${this.escapeHtml(partnerName)}', '${slot.start_time}')">
                  Select Slot
                </button>
              </div>
            `).join('')}
          </div>
        `;
      }
    } catch (err) {
      console.error(err);
      content.innerHTML = '<p style="color: #EF4444;">Failed comparing availability.</p>';
    }
  }

  scheduleUsingSlot(partnerId, partnerName, startTime) {
    document.getElementById('freeSlotModal').classList.remove('active');
    this.openScheduleModal(partnerId, partnerName);
    document.getElementById('schedTime').value = startTime;
  }

  // Notes Modal
  async openNotesModal(sessionId, skillName) {
    document.getElementById('notesSessionId').value = sessionId;
    document.getElementById('notesSkillName').textContent = skillName;

    try {
      const res = await fetch(`/api/sessions/${sessionId}/notes`);
      const data = await res.json();
      const note = data.note;

      document.getElementById('noteTopics').value = note ? note.topics_covered : '';
      document.getElementById('noteOutcomes').value = note ? note.learning_outcomes : '';
      document.getElementById('noteNextSteps').value = note ? note.next_steps : '';

      document.getElementById('notesModal').classList.add('active');
    } catch (err) {
      console.error(err);
    }
  }

  async submitNotes(e) {
    e.preventDefault();
    const sessionId = document.getElementById('notesSessionId').value;
    const payload = {
      topics_covered: document.getElementById('noteTopics').value,
      learning_outcomes: document.getElementById('noteOutcomes').value,
      next_steps: document.getElementById('noteNextSteps').value
    };

    await fetch(`/api/sessions/${sessionId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    document.getElementById('notesModal').classList.remove('active');
    alert('Shared session notes saved!');
    this.refreshCurrentView();
  }

  // Rating Modal
  openRatingModal(sessionId, partnerName) {
    document.getElementById('rateSessionId').value = sessionId;
    document.getElementById('ratePartnerName').textContent = partnerName;
    document.getElementById('rateComment').value = '';
    this.selectedRatingStars = 5;

    // Reset stars to 5
    const starContainer = document.getElementById('starRatingSelector');
    starContainer.querySelectorAll('span').forEach(s => s.classList.add('selected'));

    document.getElementById('ratingModal').classList.add('active');
  }

  async submitRating(e) {
    e.preventDefault();
    const sessionId = document.getElementById('rateSessionId').value;
    const payload = {
      reviewer_id: this.currentStudentId,
      stars: this.selectedRatingStars || 5,
      comment: document.getElementById('rateComment').value
    };

    try {
      const res = await fetch(`/api/sessions/${sessionId}/rate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (res.ok) {
        alert('Thank you! Rating submitted and mentor awarded XP!');
        document.getElementById('ratingModal').classList.remove('active');
        await this.switchStudent(this.currentStudentId);
      } else {
        alert(data.error || 'Failed submitting rating');
      }
    } catch (err) {
      console.error(err);
    }
  }

  // Teach-Back Modal
  async openTeachBackModal(sessionId, isMentor, partnerName) {
    document.getElementById('tbSessionId').value = sessionId;
    document.getElementById('tbPartnerName').textContent = partnerName;

    const res = await fetch(`/api/sessions/${sessionId}/teach-back`);
    const data = await res.json();
    const tb = data.teach_back;

    const learnerSection = document.getElementById('tbLearnerSection');
    const mentorSection = document.getElementById('tbMentorSection');

    if (isMentor) {
      // Mentor view: reviewing submissions
      learnerSection.style.display = 'none';
      mentorSection.style.display = 'block';

      if (tb) {
        document.getElementById('tbSubmittedTakeaways').textContent = tb.takeaways;
        document.getElementById('tbMentorFeedback').value = tb.feedback || '';
        document.getElementById('tbConfirmBtn').disabled = tb.teacher_confirmed;
        document.getElementById('tbConfirmBtn').textContent = tb.teacher_confirmed ? 'Takeaways Already Verified ✓' : 'Verify Takeaways & Award Badge';
      } else {
        document.getElementById('tbSubmittedTakeaways').textContent = 'Learner has not yet submitted their takeaways for this session.';
        document.getElementById('tbConfirmBtn').disabled = true;
      }
    } else {
      // Learner view: submitting key takeaways
      learnerSection.style.display = 'block';
      mentorSection.style.display = 'none';

      document.getElementById('tbTakeawaysInput').value = tb ? tb.takeaways : '';
      document.getElementById('tbStatusText').textContent = tb 
        ? (tb.teacher_confirmed ? 'Status: Confirmed by Mentor! Verified Scholar badge awarded.' : 'Status: Submitted, waiting for mentor review.') 
        : 'Status: Not yet submitted.';
    }

    document.getElementById('teachBackModal').classList.add('active');
  }

  async submitTeachBack(e) {
    e.preventDefault();
    const sessionId = document.getElementById('tbSessionId').value;
    const takeaways = document.getElementById('tbTakeawaysInput').value;

    const res = await fetch(`/api/sessions/${sessionId}/teach-back`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        learner_id: this.currentStudentId,
        takeaways: takeaways
      })
    });

    if (res.ok) {
      alert('Takeaways submitted for your mentor to review!');
      document.getElementById('teachBackModal').classList.remove('active');
      this.refreshCurrentView();
    }
  }

  async confirmTeachBackMentor() {
    const sessionId = document.getElementById('tbSessionId').value;
    const feedback = document.getElementById('tbMentorFeedback').value;

    const res = await fetch(`/api/sessions/${sessionId}/teach-back/confirm`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feedback })
    });

    if (res.ok) {
      alert('Takeaways verified! Verified Scholar badge awarded to learner!');
      document.getElementById('teachBackModal').classList.remove('active');
      this.refreshCurrentView();
    }
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

// Bootstrap
window.addEventListener('DOMContentLoaded', () => {
  window.app = new SkillSwapApp();
});
