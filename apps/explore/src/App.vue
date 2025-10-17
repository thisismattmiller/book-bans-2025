<script setup>
import { ref, computed, onMounted } from 'vue'

const books = ref([])
const loading = ref(false)
const selectedSubjects = ref([])
const selectedStates = ref([])
const selectedDistricts = ref([])
const searchQuery = ref('')
const statesSortBy = ref('count')
const districtsSortBy = ref('count')
const subjectsSortBy = ref('count')
const currentPage = ref(1)
const itemsPerPage = 100
const selectedBook = ref(null)
const showLoadPrompt = ref(true)
const dataLoaded = ref(false)

async function loadData() {
  loading.value = true
  showLoadPrompt.value = false
  try {
    const response = await fetch('/data.json')
    books.value = await response.json()
    dataLoaded.value = true
    loading.value = false
  } catch (error) {
    console.error('Error loading data:', error)
    loading.value = false
  }
}

onMounted(() => {
  // Handle escape key to close modal
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      selectedBook.value = null
    }
  })
})

// Filtered books based on selected facets
const filteredBooks = computed(() => {
  const filtered = books.value.filter(book => {
    // Search query filter
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      const matchesSearch =
        book.title?.toLowerCase().includes(query) ||
        book.author?.toLowerCase().includes(query)
      if (!matchesSearch) return false
    }

    // Subject filter - must have ALL selected subjects
    if (selectedSubjects.value.length > 0) {
      if (!Array.isArray(book.subjects)) return false
      const hasAllSubjects = selectedSubjects.value.every(subject =>
        book.subjects.includes(subject)
      )
      if (!hasAllSubjects) return false
    }

    // State filter - must have bans in ALL selected states
    if (selectedStates.value.length > 0) {
      if (!Array.isArray(book.bans)) return false
      const hasAllStates = selectedStates.value.every(state =>
        book.bans.some(ban => (ban.state === 'Nation' ? 'DoDEA' : ban.state) === state)
      )
      if (!hasAllStates) return false
    }

    // District filter - must have bans in ALL selected districts
    if (selectedDistricts.value.length > 0) {
      if (!Array.isArray(book.bans)) return false
      const hasAllDistricts = selectedDistricts.value.every(district =>
        book.bans.some(ban => ban.district === district)
      )
      if (!hasAllDistricts) return false
    }

    return true
  })

  // Sort by ban count (most bans first)
  return filtered.sort((a, b) => {
    const aBans = Array.isArray(a.bans) ? a.bans.length : 0
    const bBans = Array.isArray(b.bans) ? b.bans.length : 0
    return bBans - aBans
  })
})

// Pagination
const totalPages = computed(() => Math.ceil(filteredBooks.value.length / itemsPerPage))

const paginatedBooks = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return filteredBooks.value.slice(start, end)
})

// Reset to page 1 when filters change
const resetPage = () => {
  currentPage.value = 1
}

// Facet counts based ONLY on the currently filtered books
// Count unique books, not occurrences
const subjectCounts = computed(() => {
  const counts = {}
  filteredBooks.value.forEach(book => {
    if (Array.isArray(book.subjects)) {
      // Use Set to count each book only once per subject
      const uniqueSubjects = new Set(book.subjects)
      uniqueSubjects.forEach(subject => {
        counts[subject] = (counts[subject] || 0) + 1
      })
    }
  })
  return counts
})

const stateCounts = computed(() => {
  const counts = {}
  filteredBooks.value.forEach(book => {
    if (Array.isArray(book.bans)) {
      // Use Set to count each book only once per state
      const uniqueStates = new Set(book.bans.map(ban => ban.state === 'Nation' ? 'DoDEA' : ban.state))
      uniqueStates.forEach(state => {
        counts[state] = (counts[state] || 0) + 1
      })
    }
  })
  return counts
})

const districtCounts = computed(() => {
  const counts = {}
  filteredBooks.value.forEach(book => {
    if (Array.isArray(book.bans)) {
      // Use Set to count each book only once per district
      const uniqueDistricts = new Set(book.bans.map(ban => ban.district))
      uniqueDistricts.forEach(district => {
        counts[district] = (counts[district] || 0) + 1
      })
    }
  })
  return counts
})

// Sorted facet lists - only show facets that have books (count > 0)
const allStates = computed(() => {
  const states = Object.keys(stateCounts.value).filter(state => stateCounts.value[state] > 0)
  if (statesSortBy.value === 'count') {
    return states.sort((a, b) => (stateCounts.value[b] || 0) - (stateCounts.value[a] || 0))
  }
  return states.sort()
})

const allDistricts = computed(() => {
  const districts = Object.keys(districtCounts.value).filter(district => districtCounts.value[district] > 0)
  if (districtsSortBy.value === 'count') {
    return districts.sort((a, b) => (districtCounts.value[b] || 0) - (districtCounts.value[a] || 0))
  }
  return districts.sort()
})

const allSubjects = computed(() => {
  const subjects = Object.keys(subjectCounts.value).filter(subject => subjectCounts.value[subject] > 0)
  if (subjectsSortBy.value === 'count') {
    return subjects.sort((a, b) => (subjectCounts.value[b] || 0) - (subjectCounts.value[a] || 0))
  }
  return subjects.sort()
})

const hasActiveFilters = computed(() => {
  return selectedSubjects.value.length > 0 ||
         selectedStates.value.length > 0 ||
         selectedDistricts.value.length > 0
})

function toggleSubject(subject) {
  const index = selectedSubjects.value.indexOf(subject)
  if (index > -1) {
    selectedSubjects.value.splice(index, 1)
  } else {
    selectedSubjects.value.push(subject)
  }
  resetPage()
}

function toggleState(state) {
  const index = selectedStates.value.indexOf(state)
  if (index > -1) {
    selectedStates.value.splice(index, 1)
  } else {
    selectedStates.value.push(state)
  }
  resetPage()
}

function toggleDistrict(district) {
  const index = selectedDistricts.value.indexOf(district)
  if (index > -1) {
    selectedDistricts.value.splice(index, 1)
  } else {
    selectedDistricts.value.push(district)
  }
  resetPage()
}

function removeSubject(subject) {
  const index = selectedSubjects.value.indexOf(subject)
  if (index > -1) {
    selectedSubjects.value.splice(index, 1)
  }
  resetPage()
}

function removeState(state) {
  const index = selectedStates.value.indexOf(state)
  if (index > -1) {
    selectedStates.value.splice(index, 1)
  }
  resetPage()
}

function removeDistrict(district) {
  const index = selectedDistricts.value.indexOf(district)
  if (index > -1) {
    selectedDistricts.value.splice(index, 1)
  }
  resetPage()
}

function clearFilters() {
  selectedSubjects.value = []
  selectedStates.value = []
  selectedDistricts.value = []
  searchQuery.value = ''
  resetPage()
}

function openBookModal(book) {
  selectedBook.value = book
}

function closeModal() {
  selectedBook.value = null
}
</script>

<template>
  <div class="app">
    <!-- Load Data Prompt -->
    <div v-if="showLoadPrompt" class="load-prompt-overlay">
      <div class="load-prompt">
        <h2>Book Bans Explorer</h2>
        <p>Load the explorer?</p>
        <button @click="loadData" class="load-btn">Load Explorer</button>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading data...</div>

    <div v-else-if="dataLoaded" class="main-content">
      <aside class="facets">
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search by title or author..."
            class="search-input"
            @input="resetPage"
          />
        </div>

        <div class="facet-header">
          <h2>Filters</h2>
          <button @click="clearFilters" class="clear-btn">Clear</button>
        </div>

        <!-- Active Filters -->
        <div v-if="hasActiveFilters" class="active-filters">
          <h3>Active Filters</h3>
          <div class="active-filter-tags">
            <span
              v-for="subject in selectedSubjects"
              :key="'active-subject-' + subject"
              class="filter-tag"
            >
              {{ subject }}
              <button @click="removeSubject(subject)" class="remove-tag">×</button>
            </span>
            <span
              v-for="state in selectedStates"
              :key="'active-state-' + state"
              class="filter-tag"
            >
              {{ state }}
              <button @click="removeState(state)" class="remove-tag">×</button>
            </span>
            <span
              v-for="district in selectedDistricts"
              :key="'active-district-' + district"
              class="filter-tag"
            >
              {{ district }}
              <button @click="removeDistrict(district)" class="remove-tag">×</button>
            </span>
          </div>
        </div>

        <div class="facet-group">
          <div class="facet-title">
            <h3>Subjects</h3>
            <button
              @click="subjectsSortBy = subjectsSortBy === 'count' ? 'alpha' : 'count'"
              class="sort-btn"
            >
              {{ subjectsSortBy === 'count' ? 'A-Z' : '#' }}
            </button>
          </div>
          <div class="facet-list">
            <label
              v-for="subject in allSubjects"
              :key="subject"
              class="facet-item"
            >
              <input
                type="checkbox"
                :checked="selectedSubjects.includes(subject)"
                @change="toggleSubject(subject)"
              />
              <span>{{ subject }}</span>
              <span class="count">{{ subjectCounts[subject] || 0 }}</span>
            </label>
          </div>
        </div>

        <div class="facet-group">
          <div class="facet-title">
            <h3>States</h3>
            <button
              @click="statesSortBy = statesSortBy === 'count' ? 'alpha' : 'count'"
              class="sort-btn"
            >
              {{ statesSortBy === 'count' ? 'A-Z' : '#' }}
            </button>
          </div>
          <div class="facet-list">
            <label
              v-for="state in allStates"
              :key="state"
              class="facet-item"
            >
              <input
                type="checkbox"
                :checked="selectedStates.includes(state)"
                @change="toggleState(state)"
              />
              <span>{{ state }}</span>
              <span class="count">{{ stateCounts[state] || 0 }}</span>
            </label>
          </div>
        </div>

        <div class="facet-group">
          <div class="facet-title">
            <h3>Districts</h3>
            <button
              @click="districtsSortBy = districtsSortBy === 'count' ? 'alpha' : 'count'"
              class="sort-btn"
            >
              {{ districtsSortBy === 'count' ? 'A-Z' : '#' }}
            </button>
          </div>
          <div class="facet-list">
            <label
              v-for="district in allDistricts"
              :key="district"
              class="facet-item"
            >
              <input
                type="checkbox"
                :checked="selectedDistricts.includes(district)"
                @change="toggleDistrict(district)"
              />
              <span>{{ district }}</span>
              <span class="count">{{ districtCounts[district] || 0 }}</span>
            </label>
          </div>
        </div>
      </aside>

      <main class="books">
        <div class="books-header">
          <div class="results-info">
            {{ filteredBooks.length }} Books
            <span v-if="totalPages > 1">
              (Page {{ currentPage }} of {{ totalPages }})
            </span>
          </div>

          <div v-if="totalPages > 1" class="pagination">
            <button
              @click="currentPage--"
              :disabled="currentPage === 1"
              class="page-btn"
            >
              ‹ Prev
            </button>
            <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
            <button
              @click="currentPage++"
              :disabled="currentPage === totalPages"
              class="page-btn"
            >
              Next ›
            </button>
          </div>
        </div>

        <div class="book-list">
          <div
            v-for="book in paginatedBooks"
            :key="book.id"
            class="book-card"
            @click="openBookModal(book)"
          >
            <img
              :src="`/thumbnails/${book.id}.jpg`"
              :alt="book.title"
              class="book-thumbnail"
              @error="(e) => e.target.style.display = 'none'"
            />
            <div class="book-info">
              <h3>{{ book.title }}</h3>
              <p class="author">{{ book.author }}</p>
              <div v-if="Array.isArray(book.bans) && book.bans.length" class="ban-count">
                {{ book.bans.length }} ban{{ book.bans.length !== 1 ? 's' : '' }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="totalPages > 1" class="pagination bottom-pagination">
          <button
            @click="currentPage--"
            :disabled="currentPage === 1"
            class="page-btn"
          >
            ‹ Prev
          </button>
          <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
          <button
            @click="currentPage++"
            :disabled="currentPage === totalPages"
            class="page-btn"
          >
            Next ›
          </button>
        </div>
      </main>
    </div>

    <!-- Book Detail Modal -->
    <div v-if="selectedBook" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <button class="modal-close" @click="closeModal">×</button>

        <div class="modal-header">
          <img
            :src="`/thumbnails/${selectedBook.id}.jpg`"
            :alt="selectedBook.title"
            class="modal-thumbnail"
            @error="(e) => e.target.style.display = 'none'"
          />
          <div class="modal-title-info">
            <h2>{{ selectedBook.title }}</h2>
            <p class="modal-author">{{ selectedBook.author }}</p>
            <div class="modal-ids-row">
              <div class="modal-ids">
                <a v-if="selectedBook.isbn" :href="'https://www.google.com/books?vid=ISBN:' + selectedBook.isbn" target="_blank" class="modal-id-link">ISBN: {{ selectedBook.isbn }}</a>
                <a v-if="selectedBook.oclc" :href="'http://worldcat.org/oclc/' + selectedBook.oclc" target="_blank" class="modal-id-link">OCLC: {{ selectedBook.oclc }}</a>
                <a v-if="selectedBook.lccn" :href="'https://lccn.loc.gov/' + selectedBook.lccn" target="_blank" class="modal-id-link">LCCN: {{ selectedBook.lccn }}</a>
                <span v-if="selectedBook.pageCount" class="modal-page-count">Pages: {{ selectedBook.pageCount }}</span>
              </div>
            </div>
            <div v-if="Array.isArray(selectedBook.subjects) && selectedBook.subjects.length" class="modal-subjects-header">
              <div class="modal-subjects-grid">
                <span v-for="subject in selectedBook.subjects" :key="subject" class="modal-subject-item">
                  {{ subject }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-body">
          <div class="modal-two-columns">
            <div class="modal-column">
              <div class="modal-field">
                <strong>Description:</strong>
                <p>{{ selectedBook.description || 'No description available' }}</p>
              </div>
            </div>

            <div class="modal-column">
              <div v-if="Array.isArray(selectedBook.bans) && selectedBook.bans.length" class="modal-field">
                <strong>Bans ({{ selectedBook.bans.length }}):</strong>
                <div class="modal-bans">
                  <div v-for="(ban, idx) in selectedBook.bans" :key="idx" class="modal-ban-item">
                    <div class="ban-location">
                      <strong>{{ ban.state === 'Nation' ? 'DoDEA' : ban.state }}</strong> - {{ ban.district }}
                    </div>
                    <div class="ban-details">
                      <span class="ban-status">{{ ban.ban_status }}</span>
                      <span v-if="ban.date" class="ban-date">{{ ban.date }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  width: 100%;
  overflow: hidden;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: #f5f5f5;
  font-size: 14px;
}

.app {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
}

.loading {
  text-align: center;
  padding: 2rem;
  font-size: 1.2rem;
  color: #666;
}

/* Load Prompt */
.load-prompt-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.load-prompt {
  background: white;
  padding: 3rem;
  border-radius: 8px;
  text-align: center;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.load-prompt h2 {
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 2rem;
}

.load-prompt p {
  color: #555;
  margin-bottom: 2rem;
  font-size: 1.1rem;
}

.load-btn {
  padding: 0.75rem 2rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
}

.load-btn:hover {
  background: #2980b9;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.facets {
  width: 280px;
  flex-shrink: 0;
  background: white;
  border-right: 1px solid #ddd;
  overflow-y: auto;
  padding: 1rem;
}

.search-box {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e0e0e0;
}

.search-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  font-size: 0.9rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.facet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #e0e0e0;
}

.facet-header h2 {
  font-size: 1.1rem;
  color: #2c3e50;
}

.clear-btn {
  padding: 0.35rem 0.75rem;
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.8rem;
}

.clear-btn:hover {
  background: #c0392b;
}

.active-filters {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e0e0e0;
}

.active-filters h3 {
  font-size: 0.9rem;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.active-filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: #3498db;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.75rem;
  font-weight: 500;
}

.remove-tag {
  background: none;
  border: none;
  color: white;
  font-size: 1.2rem;
  line-height: 1;
  cursor: pointer;
  padding: 0;
  margin-left: 0.25rem;
}

.remove-tag:hover {
  color: #e74c3c;
}

.facet-group {
  margin-bottom: 1.25rem;
}

.facet-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.facet-title h3 {
  font-size: 0.95rem;
  color: #34495e;
  font-weight: 600;
}

.sort-btn {
  padding: 0.2rem 0.5rem;
  background: #ecf0f1;
  border: 1px solid #bdc3c7;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.75rem;
  color: #555;
  font-weight: 600;
}

.sort-btn:hover {
  background: #d5dbdb;
}

.facet-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  max-height: 250px;
  overflow-y: auto;
}

.facet-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.4rem;
  cursor: pointer;
  border-radius: 3px;
  transition: background 0.2s;
  font-size: 0.85rem;
}

.facet-item:hover {
  background: #f8f9fa;
}

.facet-item input[type="checkbox"] {
  cursor: pointer;
  flex-shrink: 0;
}

.facet-item span {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.facet-item .count {
  flex: 0;
  color: #7f8c8d;
  font-size: 0.75rem;
  font-weight: 600;
  min-width: 2rem;
  text-align: right;
}

.books {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f5f5f5;
}

.books-header {
  padding: 1rem;
  background: white;
  border-bottom: 1px solid #ddd;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.results-info {
  font-size: 1rem;
  font-weight: 600;
  color: #2c3e50;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.page-btn {
  padding: 0.4rem 0.75rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.85rem;
}

.page-btn:hover:not(:disabled) {
  background: #2980b9;
}

.page-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.page-info {
  font-size: 0.9rem;
  color: #555;
}

.book-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 1rem;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  grid-auto-rows: min-content;
  gap: 1rem;
}

.bottom-pagination {
  padding: 1rem;
  background: white;
  border-top: 1px solid #ddd;
  display: flex;
  justify-content: center;
}

.book-card {
  background: white;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  transition: box-shadow 0.2s, transform 0.2s;
  cursor: pointer;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.book-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
  transform: translateY(-2px);
}

.book-thumbnail {
  width: 100%;
  height: 200px;
  object-fit: cover;
  background: #e0e0e0;
  display: block;
}

.book-info {
  padding: 0.75rem;
  flex: 1;
}

.book-card h3 {
  color: #2c3e50;
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.author {
  color: #7f8c8d;
  font-size: 0.75rem;
  margin-bottom: 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ban-count {
  font-size: 0.75rem;
  color: #e74c3c;
  font-weight: 600;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 800px;
  max-height: 90vh;
  width: 100%;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.modal-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: transparent;
  color: #2c3e50;
  border: none;
  font-size: 2rem;
  line-height: 1;
  cursor: pointer;
  font-weight: bold;
  z-index: 1;
  padding: 0.25rem;
}

.modal-close:hover {
  color: #e74c3c;
}

.modal-header {
  display: flex;
  gap: 1.5rem;
  padding: 2rem;
  border-bottom: 1px solid #e0e0e0;
}

.modal-thumbnail {
  width: 150px;
  height: 225px;
  object-fit: cover;
  border-radius: 4px;
  background: #e0e0e0;
  flex-shrink: 0;
}

.modal-title-info {
  flex: 1;
}

.modal-title-info h2 {
  color: #2c3e50;
  font-size: 1.75rem;
  margin-bottom: 0.5rem;
}

.modal-author {
  color: #7f8c8d;
  font-size: 1.1rem;
  font-style: italic;
  margin-bottom: 0.75rem;
}

.modal-body {
  padding: 2rem;
}

.modal-two-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 1.5rem;
}

.modal-column {
  min-width: 0;
}

.modal-field {
  margin-bottom: 1.5rem;
}

.modal-field strong {
  color: #2c3e50;
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.modal-field p {
  color: #555;
  line-height: 1.6;
}

.modal-ids-row {
  margin-top: 0.5rem;
}

.modal-ids {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
}

.modal-id-link {
  color: #3498db;
  text-decoration: none;
  font-size: 0.9rem;
}

.modal-id-link:hover {
  text-decoration: underline;
  color: #2980b9;
}

.modal-page-count {
  color: #555;
  font-size: 0.9rem;
}

.modal-subjects-header {
  margin-top: 0.75rem;
}

.modal-subjects-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.35rem;
  font-size: 0.8rem;
}

.modal-subject-item {
  background: #ecf0f1;
  color: #2c3e50;
  padding: 0.3rem 0.5rem;
  border-radius: 3px;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.modal-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.modal-tag {
  background: #ecf0f1;
  color: #2c3e50;
  padding: 0.35rem 0.75rem;
  border-radius: 3px;
  font-size: 0.85rem;
}

.modal-bans {
  margin-top: 0.75rem;
}

.modal-ban-item {
  padding: 0.75rem;
  background: #f8f9fa;
  border-left: 3px solid #e74c3c;
  margin-bottom: 0.75rem;
  border-radius: 4px;
}

.ban-location {
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.ban-details {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
}

.ban-status {
  color: #e74c3c;
  font-weight: 600;
}

.ban-date {
  color: #7f8c8d;
}
</style>
