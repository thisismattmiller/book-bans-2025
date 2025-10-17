import './style.css'

async function loadData() {
  const response = await fetch('/data.json');
  return await response.json();
}

function analyzeData(books) {
  const stateData = {};

  books.forEach(book => {
    if (!book.bans || !Array.isArray(book.bans)) return;
    if (!book.subjects || !Array.isArray(book.subjects)) return;

    book.bans.forEach(ban => {
      if (!ban.state || !ban.district) return;

      const state = ban.state;
      const district = ban.district;

      if (!stateData[state]) {
        stateData[state] = {
          districts: {},
          subjectCounts: {},
          totalBans: 0
        };
      }

      if (!stateData[state].districts[district]) {
        stateData[state].districts[district] = {
          subjectCounts: {},
          totalBans: 0
        };
      }

      // Count subjects for state
      book.subjects.forEach(subject => {
        if (subject) {
          stateData[state].subjectCounts[subject] = (stateData[state].subjectCounts[subject] || 0) + 1;
          stateData[state].districts[district].subjectCounts[subject] = (stateData[state].districts[district].subjectCounts[subject] || 0) + 1;
        }
      });

      stateData[state].totalBans++;
      stateData[state].districts[district].totalBans++;
    });
  });

  return stateData;
}

function getTopSubjects(subjectCounts, limit = 20) {
  return Object.entries(subjectCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit);
}

function createSubjectCard(subject, count) {
  return `
    <div class="subject-card">
      <div class="subject-name">${subject}</div>
      <div class="subject-count">${count}</div>
    </div>
  `;
}

function createDistrictSection(districtName, districtData) {
  const topSubjects = getTopSubjects(districtData.subjectCounts, 20);
  const districtId = `district-${districtName.replace(/\s+/g, '-')}`;

  // Split subjects: first 10 on left, last 10 on right
  const leftSubjects = topSubjects.slice(0, 10);
  const rightSubjects = topSubjects.slice(10, 20);

  return `
    <div class="district-section">
      <div class="district-header" onclick="toggleSection('${districtId}')">
        <span class="toggle-icon" id="${districtId}-icon">▶</span>
        <h3>${districtName}</h3>
        <div class="district-stats">
          ${districtData.totalBans} bans • ${topSubjects.length} top subjects
        </div>
      </div>
      <div class="subjects-grid collapsed" id="${districtId}">
        <div class="subjects-column">
          ${leftSubjects.map(([subject, count]) => createSubjectCard(subject, count)).join('')}
        </div>
        <div class="subjects-column">
          ${rightSubjects.map(([subject, count]) => createSubjectCard(subject, count)).join('')}
        </div>
      </div>
    </div>
  `;
}

function createStateSection(stateName, stateData) {
  const topSubjects = getTopSubjects(stateData.subjectCounts, 20);
  const displayName = stateName === "Nation" ? "Department of Defense Education Activity" : stateName;
  const stateId = `state-${stateName.replace(/\s+/g, '-')}`;
  const districts = Object.entries(stateData.districts).sort((a, b) => b[1].totalBans - a[1].totalBans);

  // Split subjects: first 10 on left, last 10 on right
  const leftSubjects = topSubjects.slice(0, 10);
  const rightSubjects = topSubjects.slice(10, 20);

  return `
    <div class="state-section">
      <div class="state-header" onclick="toggleSection('${stateId}')">
        <span class="toggle-icon" id="${stateId}-icon">▶</span>
        <h2>${displayName}</h2>
        <div class="state-stats">
          <span>📚 ${stateData.totalBans} total bans</span>
          <span>🏫 ${districts.length} districts</span>
          <span>📊 ${topSubjects.length} top subjects</span>
        </div>
      </div>
      <div class="collapsed" id="${stateId}">
        <div class="subjects-grid">
          <div class="subjects-column">
            ${leftSubjects.map(([subject, count]) => createSubjectCard(subject, count)).join('')}
          </div>
          <div class="subjects-column">
            ${rightSubjects.map(([subject, count]) => createSubjectCard(subject, count)).join('')}
          </div>
        </div>
        ${districts.map(([districtName, districtData]) =>
          createDistrictSection(districtName, districtData)
        ).join('')}
      </div>
    </div>
  `;
}

window.toggleSection = function(sectionId) {
  const content = document.getElementById(sectionId);
  const icon = document.getElementById(`${sectionId}-icon`);

  content.classList.toggle('collapsed');
  icon.classList.toggle('open');
}

async function init() {
  const app = document.getElementById('app');
  app.innerHTML = '<div class="loading">Loading data...</div>';

  try {
    const books = await loadData();
    const stateData = analyzeData(books);

    const sortedStates = Object.entries(stateData)
      .sort((a, b) => b[1].totalBans - a[1].totalBans);

    app.innerHTML = `
      <div class="container">
        ${sortedStates.map(([stateName, data]) =>
          createStateSection(stateName, data)
        ).join('')}
      </div>
    `;
  } catch (error) {
    app.innerHTML = `<div class="loading">Error loading data: ${error.message}</div>`;
  }
}

init();
