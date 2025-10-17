export default {
  data() {
    return {
      selectedItem: null,
      itemType: null,
      bannedBooks: [],
      selectedSubjects: [],
      selectedBanStatus: [],
      selectedPopularityLevels: [],
      selectedBook: null,
      showingDistrictSelection: false,
      districtChoices: []
    };
  },
  computed: {
    hasSelection() {
      return this.selectedItem !== null;
    },
    showFilters() {
      return this.bannedBooks.length > 5;
    },
    displayName() {
      if (!this.selectedItem) return '';
      if (this.itemType === 'district') {
        return this.selectedItem.District;
      }
      // For military bases, show base name with DoD in parentheses
      const baseName = this.selectedItem.formatted_name || this.selectedItem.name;
      return `${baseName} (Department of Defense Educational Activitity)`;
    },
    allSubjects() {
      const subjectCounts = {};
      this.bannedBooks.forEach(book => {
        if (book.subjects) {
          // Handle both array and string subjects
          const subjects = Array.isArray(book.subjects) ? book.subjects : [book.subjects];
          subjects.forEach(subject => {
            subjectCounts[subject] = (subjectCounts[subject] || 0) + 1;
          });
        }
      });
      // Sort by count descending, then alphabetically
      return Object.entries(subjectCounts)
        .sort((a, b) => {
          if (b[1] !== a[1]) return b[1] - a[1]; // Sort by count descending
          return a[0].localeCompare(b[0]); // Then alphabetically
        })
        .map(([subject, count]) => ({ subject, count }));
    },
    allBanStatuses() {
      const statusSet = new Set();
      this.bannedBooks.forEach(book => {
        book.bans.forEach(ban => {
          if (ban.ban_status) statusSet.add(ban.ban_status);
        });
      });
      return Array.from(statusSet).sort();
    },
    allPopularityLevels() {
      const popularityCounts = {};
      this.bannedBooks.forEach(book => {
        if (book.popularityLevel) {
          popularityCounts[book.popularityLevel] = (popularityCounts[book.popularityLevel] || 0) + 1;
        }
      });
      // Sort by predefined order: Very Popular, Popular, Medium, Less Popular
      const order = ['Very Popular', 'Popular', 'Medium', 'Less Popular'];
      return order
        .filter(level => popularityCounts[level])
        .map(level => ({ level, count: popularityCounts[level] }));
    },
    filteredBooks() {
      return this.bannedBooks.filter(book => {
        // Subject filter
        if (this.selectedSubjects.length > 0) {
          if (!book.subjects) return false;
          const subjects = Array.isArray(book.subjects) ? book.subjects : [book.subjects];
          const hasSubject = subjects.some(s => this.selectedSubjects.includes(s));
          if (!hasSubject) return false;
        }

        // Ban status filter
        if (this.selectedBanStatus.length > 0) {
          const hasBanStatus = book.bans && book.bans.some(b => this.selectedBanStatus.includes(b.ban_status));
          if (!hasBanStatus) return false;
        }

        // Popularity level filter
        if (this.selectedPopularityLevels.length > 0) {
          if (!this.selectedPopularityLevels.includes(book.popularityLevel)) return false;
        }

        return true;
      });
    }
  },
  methods: {
    setSelectedItem(item, type, books) {
      console.log('Vue: setSelectedItem called', { item, type, booksCount: books?.length });
      this.selectedItem = item;
      this.itemType = type;
      this.bannedBooks = books || [];
      this.selectedSubjects = [];
      this.selectedBanStatus = [];
      this.selectedPopularityLevels = [];
      this.selectedBook = null;
    },
    clearSelection() {
      this.selectedItem = null;
      this.itemType = null;
      this.bannedBooks = [];
      this.selectedSubjects = [];
      this.selectedBanStatus = [];
      this.selectedPopularityLevels = [];
      this.selectedBook = null;
    },
    selectBook(book) {
      this.selectedBook = book;
      // Scroll to top of info panel
      const infoPanel = document.getElementById('info-panel');
      if (infoPanel) {
        infoPanel.scrollTop = 0;
      }
    },
    backToList() {
      this.selectedBook = null;
    },
    closeOverlay() {
      // Trigger the close by simulating a click on empty map area
      const event = new Event('click');
      const svg = document.querySelector('#map');
      if (svg) {
        svg.dispatchEvent(event);
      }
    },
    toggleSubject(subject) {
      const index = this.selectedSubjects.indexOf(subject);
      if (index > -1) {
        this.selectedSubjects.splice(index, 1);
      } else {
        this.selectedSubjects.push(subject);
      }
    },
    toggleBanStatus(status) {
      const index = this.selectedBanStatus.indexOf(status);
      if (index > -1) {
        this.selectedBanStatus.splice(index, 1);
      } else {
        this.selectedBanStatus.push(status);
      }
    },
    togglePopularityLevel(level) {
      const index = this.selectedPopularityLevels.indexOf(level);
      if (index > -1) {
        this.selectedPopularityLevels.splice(index, 1);
      } else {
        this.selectedPopularityLevels.push(level);
      }
    },
    showDistrictSelection(districts, booksData) {
      // Calculate banned book counts for each district
      this.districtChoices = districts.map(({ name, data }) => {
        const districtName = data.District;
        const bannedCount = booksData.filter(book => {
          return book.bans && book.bans.some(ban => ban.district === districtName);
        }).length;
        return { name: districtName, count: bannedCount, data };
      });
      this.showingDistrictSelection = true;
      this.selectedItem = null;
      this.selectedBook = null;
    },
    selectDistrictFromList(districtData) {
      const districtName = districtData.data.District;
      const bannedBooksForDistrict = window.booksData.filter(book => {
        return book.bans && book.bans.some(ban => ban.district === districtName);
      });

      this.setSelectedItem(districtData.data, 'district', bannedBooksForDistrict);
      this.showingDistrictSelection = false;
    },
    getThumbnailUrl(bookId) {
      return `/thumbnails/${bookId}.jpg`;
    }
  },
  template: `
    <div class="info-content">
      <div v-if="showingDistrictSelection">
        <div class="list-header">
          <h2>Select a District</h2>
          <button @click="closeOverlay" class="close-button" title="Close">✕</button>
        </div>
        <div class="district-selection">
          <p class="selection-instruction">Multiple districts share this county. Select one to view banned books:</p>
          <div class="district-choices">
            <button
              v-for="district in districtChoices"
              :key="district.name"
              @click="selectDistrictFromList(district)"
              class="district-choice-button"
            >
              <div class="district-choice-name">{{ district.name }}</div>
              <div class="district-choice-count">{{ district.count }} banned book{{ district.count !== 1 ? 's' : '' }}</div>
            </button>
          </div>
        </div>
      </div>
      <div v-else-if="!hasSelection">
        <h2>Select a location</h2>
        <p>Click on a school district or military base to view banned books</p>
      </div>
      <div v-else>
        <!-- Book Detail View -->
        <div v-if="selectedBook" class="book-detail">
          <button @click="backToList" class="back-button">← Back to List</button>

          <div class="book-detail-header">
            <img
              :src="getThumbnailUrl(selectedBook.id)"
              :alt="selectedBook.title"
              class="book-detail-thumbnail"
              @error="$event.target.style.display='none'"
            />
            <div class="book-detail-title-section">
              <h2>{{ selectedBook.title }}</h2>
              <p class="book-detail-author">by {{ selectedBook.author }}</p>
            </div>
          </div>

          <div class="book-detail-content">
            <div v-if="selectedBook.description" class="detail-section">
              <h3>Description</h3>
              <p>{{ selectedBook.description }}</p>
            </div>

            <div class="detail-section">
              <h3>Book Information</h3>
              <div class="detail-grid">
                <div v-if="selectedBook.isbn" class="detail-item">
                  <strong>ISBN:</strong> <a :href="'https://www.google.com/books?vid=ISBN:' + selectedBook.isbn" target="_blank">{{ selectedBook.isbn }}</a>
                </div>
                <div v-if="selectedBook.popularityLevel" class="detail-item">
                  <strong>Popularity:</strong> {{ selectedBook.popularityLevel }}
                </div>
                <div v-if="selectedBook.pageCount" class="detail-item">
                  <strong>Pages:</strong> {{ selectedBook.pageCount }}
                </div>
                <div v-if="selectedBook.oclc" class="detail-item">
                  <strong>OCLC:</strong> <a :href="'http://worldcat.org/oclc/' + selectedBook.oclc" target="_blank">{{ selectedBook.oclc }}</a>
                </div>
                <div v-if="selectedBook.lccn" class="detail-item">
                  <strong>LCCN:</strong> <a :href="'https://lccn.loc.gov/' + selectedBook.lccn + '/'" target="_blank">{{ selectedBook.lccn }}</a>
                </div>
              </div>
            </div>

            <div v-if="selectedBook.subjects" class="detail-section">
              <h3>Subjects</h3>
              <div class="book-subjects">
                <span v-for="subject in (Array.isArray(selectedBook.subjects) ? selectedBook.subjects : [selectedBook.subjects])" :key="subject" class="subject-tag">
                  {{ subject }}
                </span>
              </div>
            </div>

            <div v-if="selectedBook.bans && selectedBook.bans.length" class="detail-section">
              <h3>Ban History ({{ selectedBook.bans.length }})</h3>
              <div class="bans-list">
                <div v-for="(ban, index) in selectedBook.bans" :key="index" class="ban-item">
                  <div class="ban-location">
                    <strong>{{ ban.district }}</strong>
                    <span v-if="ban.state" class="ban-state">{{ ban.state }}</span>
                  </div>
                  <div class="ban-details">
                    <span v-if="ban.date" class="ban-date">{{ ban.date }}</span>
                    <span v-if="ban.ban_status" class="ban-status">{{ ban.ban_status }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Book List View -->
        <div v-else>
          <div class="list-header">
            <div>
              <h2>{{ displayName }}</h2>
              <p class="book-count">{{ bannedBooks.length }} banned book{{ bannedBooks.length !== 1 ? 's' : '' }}</p>
            </div>
            <button @click="closeOverlay" class="close-button" title="Close">✕</button>
          </div>

          <div v-if="bannedBooks.length > 0" class="books-section">
            <!-- Filters (only show if more than 5 books) -->
            <div v-if="showFilters" class="filters">
            <!-- Ban Status Filter -->
            <details class="filter-group">
              <summary>Ban Status ({{ selectedBanStatus.length }})</summary>
              <div class="filter-options">
                <label v-for="status in allBanStatuses" :key="status" class="filter-option">
                  <input
                    type="checkbox"
                    :checked="selectedBanStatus.includes(status)"
                    @change="toggleBanStatus(status)"
                  />
                  <span class="filter-label">{{ status }}</span>
                </label>
              </div>
            </details>

            <!-- Popularity Level Filter -->
            <details class="filter-group">
              <summary>Popularity Level ({{ selectedPopularityLevels.length }})</summary>
              <p class="filter-help">Popularity is a rough gauge based on the number of institutions that hold the book and number of editions</p>
              <div class="filter-options">
                <label v-for="item in allPopularityLevels" :key="item.level" class="filter-option">
                  <input
                    type="checkbox"
                    :checked="selectedPopularityLevels.includes(item.level)"
                    @change="togglePopularityLevel(item.level)"
                  />
                  <span class="filter-label">{{ item.level }} <span class="filter-count">({{ item.count }})</span></span>
                </label>
              </div>
            </details>

            <!-- Subject Filter -->
            <details class="filter-group">
              <summary>Subjects ({{ selectedSubjects.length }})</summary>
              <div class="filter-options">
                <label v-for="item in allSubjects" :key="item.subject" class="filter-option">
                  <input
                    type="checkbox"
                    :checked="selectedSubjects.includes(item.subject)"
                    @change="toggleSubject(item.subject)"
                  />
                  <span class="filter-label">{{ item.subject }} <span class="filter-count">({{ item.count }})</span></span>
                </label>
              </div>
            </details>
            </div>

            <!-- Books List -->
            <div class="books-list">
              <div v-for="book in filteredBooks" :key="book.id" class="book-item" @click="selectBook(book)">
                <img
                  :src="getThumbnailUrl(book.id)"
                  :alt="book.title"
                  class="book-thumbnail"
                  @error="$event.target.style.display='none'"
                />
                <div class="book-info">
                  <h3 class="book-title">{{ book.title }}</h3>
                  <p class="book-author">{{ book.author }}</p>
                  <div class="book-subjects">
                    <span v-for="subject in (Array.isArray(book.subjects) ? book.subjects : (book.subjects ? [book.subjects] : [])).slice(0, 3)" :key="subject" class="subject-tag">
                      {{ subject }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <p v-if="filteredBooks.length === 0" class="no-results">
              No books match your filters. Try adjusting your filters.
            </p>
          </div>

          <div v-else>
            <p>No banned books found for this location.</p>
          </div>
        </div>
      </div>
    </div>
  `
};
