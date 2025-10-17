import './style.css';
import * as d3 from 'd3';
import * as topojson from 'topojson-client';
import { createApp } from 'vue';
import InfoPanel from './InfoPanel.js';

// Create Vue app for the info panel
const vueApp = createApp(InfoPanel);
const vm = vueApp.mount('#vue-app');

// Store loaded data globally
let booksData = [];
window.booksData = booksData;

// Wait for user to click "Load Map" button
document.getElementById('load-map-btn').addEventListener('click', () => {
  // Hide welcome modal
  const welcomeModal = document.getElementById('welcome-modal');
  welcomeModal.classList.add('hidden');

  // Show loading spinner
  const spinner = document.getElementById('loading-spinner');
  spinner.classList.remove('hidden');

  // Load all data before initializing the map
  Promise.all([
    fetch('./counties-albers-10m.json').then(r => r.json()),
    fetch('./data.json').then(r => r.json())
  ])
    .then(([us, data]) => {
      booksData = data;
      window.booksData = data;

      // Hide loading spinner
      spinner.classList.add('hidden');

      return us;
    })
    .then(us => {
      // Initialize the map with the loaded data
      initializeMap(us);
    })
    .catch(error => {
      console.error('Error loading data:', error);
      spinner.innerHTML = '<p style="color: red;">Error loading data. Please refresh the page.</p>';
    });
});

function initializeMap(us) {
    // Create path generator for pre-projected TopoJSON (no projection needed)
    const path = d3.geoPath();

    // Create path generator with projection for GeoJSON school districts
    const projection = d3.geoAlbersUsa().scale(1300).translate([487.5, 305]);
    const pathWithProjection = d3.geoPath().projection(projection);

    // Select the SVG element
    const svg = d3.select('#map');

    // Create tooltip div
    const tooltip = d3.select('body')
      .append('div')
      .attr('class', 'map-tooltip')
      .style('opacity', 0);

    // Add SVG filter for glow effect
    const defs = svg.append('defs');

    // Standard glow for 100+ bans
    const filter = defs.append('filter')
      .attr('id', 'glow')
      .attr('x', '-50%')
      .attr('y', '-50%')
      .attr('width', '200%')
      .attr('height', '200%');

    filter.append('feGaussianBlur')
      .attr('stdDeviation', '3')
      .attr('result', 'coloredBlur');

    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    // Intense glow for 250+ bans
    const filterIntense = defs.append('filter')
      .attr('id', 'glow-intense')
      .attr('x', '-100%')
      .attr('y', '-100%')
      .attr('width', '300%')
      .attr('height', '300%');

    filterIntense.append('feGaussianBlur')
      .attr('stdDeviation', '6')
      .attr('result', 'coloredBlur');

    const feMergeIntense = filterIntense.append('feMerge');
    feMergeIntense.append('feMergeNode').attr('in', 'coloredBlur');
    feMergeIntense.append('feMergeNode').attr('in', 'SourceGraphic');

    // Extreme glow for 500+ bans
    const filterExtreme = defs.append('filter')
      .attr('id', 'glow-extreme')
      .attr('x', '-100%')
      .attr('y', '-100%')
      .attr('width', '300%')
      .attr('height', '300%');

    filterExtreme.append('feGaussianBlur')
      .attr('stdDeviation', '6')
      .attr('result', 'coloredBlur');

    const feMergeExtreme = filterExtreme.append('feMerge');
    feMergeExtreme.append('feMergeNode').attr('in', 'coloredBlur');
    feMergeExtreme.append('feMergeNode').attr('in', 'coloredBlur');
    feMergeExtreme.append('feMergeNode').attr('in', 'coloredBlur');
    feMergeExtreme.append('feMergeNode').attr('in', 'SourceGraphic');

    // Create a group for the map elements
    const g = svg.append('g')
      .attr('fill', 'none')
      .attr('stroke', '#000')
      .attr('stroke-linejoin', 'round')
      .attr('stroke-linecap', 'round');

    // Draw county borders (within states)
    g.append('path')
      .attr('stroke', '#ddd')
      .attr('stroke-width', 0.5)
      .attr('d', path(topojson.mesh(us, us.objects.counties, (a, b) => a !== b && (a.id / 1000 | 0) === (b.id / 1000 | 0))));

    // Draw state borders
    g.append('path')
      .attr('stroke-width', 0.5)
      .attr('d', path(topojson.mesh(us, us.objects.states, (a, b) => a !== b)));

    // Draw nation border
    g.append('path')
      .attr('d', path(topojson.feature(us, us.objects.nation)));

    // Load and draw school districts
    fetch('./school_districts.json')
      .then(response => response.json())
      .then(schoolDistricts => {
        // Create a group for school districts
        const districtsGroup = g.append('g')
          .attr('class', 'school-districts');

        // Group districts by County ID
        const countyGroups = {};
        Object.entries(schoolDistricts).forEach(([name, data]) => {
          if (data.county_geojson && data.nces_data && data.nces_data['County ID']) {
            const countyId = data.nces_data['County ID'];
            if (!countyGroups[countyId]) {
              countyGroups[countyId] = [];
            }
            countyGroups[countyId].push({ name, data });
          }
        });

        // Draw each school district's county
        Object.entries(schoolDistricts).forEach(([name, data]) => {
          if (data.county_geojson) {
            // Calculate banned books count for this district
            const districtName = data.District;
            const bannedCount = booksData.filter(book => {
              return book.bans && book.bans.some(ban => ban.district === districtName);
            }).length;

            // Get county ID and find all districts in this county
            const countyId = data.nces_data ? data.nces_data['County ID'] : null;
            const districtsInCounty = countyId ? countyGroups[countyId] : [{ name, data }];

            const districtPath = districtsGroup.append('path')
              .datum(data.county_geojson)
              .attr('d', pathWithProjection)
              .attr('fill', bannedCount <= 2 ? 'rgba(214, 48, 49, 0.15)' : bannedCount > 100 ? 'rgba(214, 48, 49, 0.5)' : 'rgba(214, 48, 49, 0.3)')
              .attr('stroke', bannedCount <= 2 ? '#f0a0a0' : '#d63031')
              .attr('stroke-width', 1.5)
              .attr('class', 'school-district')
              .attr('data-district-name', districtName)
              .attr('data-banned-count', bannedCount)
              .attr('data-county-id', countyId)
              .attr('filter', bannedCount > 500 ? 'url(#glow-extreme)' : bannedCount > 250 ? 'url(#glow-intense)' : bannedCount > 100 ? 'url(#glow)' : null)
              .style('cursor', 'pointer')
              .on('mouseover', function(event) {
                // Show all districts in this county in the tooltip
                if (districtsInCounty.length > 1) {
                  let tooltipHtml = '<div class="tooltip-title">Multiple Districts:</div>';
                  districtsInCounty.forEach(({ name, data }) => {
                    const districtName = data.District;
                    const bannedCount = booksData.filter(book => {
                      return book.bans && book.bans.some(ban => ban.district === districtName);
                    }).length;
                    tooltipHtml += `<div class="tooltip-district">${districtName}: ${bannedCount} book${bannedCount !== 1 ? 's' : ''}</div>`;
                  });
                  tooltip.html(tooltipHtml);
                } else {
                  const bannedCount = booksData.filter(book => {
                    return book.bans && book.bans.some(ban => ban.district === districtName);
                  }).length;
                  tooltip.html(`
                    <div class="tooltip-title">${districtName}</div>
                    <div class="tooltip-count">${bannedCount} banned book${bannedCount !== 1 ? 's' : ''}</div>
                  `);
                }

                tooltip.transition()
                  .duration(200)
                  .style('opacity', 1)
                  .style('left', (event.pageX + 10) + 'px')
                  .style('top', (event.pageY - 10) + 'px');
              })
              .on('mousemove', function(event) {
                tooltip
                  .style('left', (event.pageX + 10) + 'px')
                  .style('top', (event.pageY - 10) + 'px');
              })
              .on('mouseout', function() {
                tooltip.transition()
                  .duration(200)
                  .style('opacity', 0);
              })
              .on('click', function(event) {
                event.stopPropagation();

                // Check if there are multiple districts in this county
                if (districtsInCounty.length > 1) {
                  // Show district selection UI
                  vm.showDistrictSelection(districtsInCounty, booksData);

                  // Show the info panel
                  const app = document.getElementById('app');
                  const infoPanel = document.getElementById('info-panel');
                  app.classList.add('detail-mode');
                  infoPanel.classList.remove('hidden');
                  return;
                }

                // Remove selection from all items, but restore their original glow if they had it
                d3.selectAll('.school-district').each(function() {
                  const path = d3.select(this);
                  const bannedCount = parseInt(path.attr('data-banned-count'));

                  path.attr('fill', bannedCount <= 2 ? 'rgba(214, 48, 49, 0.15)' : bannedCount > 100 ? 'rgba(214, 48, 49, 0.5)' : 'rgba(214, 48, 49, 0.3)')
                    .attr('stroke', bannedCount <= 2 ? '#f0a0a0' : '#d63031')
                    .attr('filter', bannedCount > 500 ? 'url(#glow-extreme)' : bannedCount > 250 ? 'url(#glow-intense)' : bannedCount > 100 ? 'url(#glow)' : null);
                });
                d3.selectAll('.military-base')
                  .attr('fill', 'rgba(214, 48, 49, 0.3)')
                  .attr('stroke', '#d63031')
                  .attr('filter', null);

                // Highlight selected district with orange and glow
                d3.select(this)
                  .attr('fill', '#e17055')
                  .attr('stroke', '#e17055')
                  .attr('filter', 'url(#glow)');

                // Calculate centroid of the district
                const centroid = pathWithProjection.centroid(data.county_geojson);

                // Find all books banned in this district
                const districtName = data.District;
                console.log('Selected district:', districtName);
                console.log('Total books in dataset:', booksData.length);

                const bannedBooksForDistrict = booksData.filter(book => {
                  return book.bans && book.bans.some(ban => ban.district === districtName);
                });

                console.log('Banned books found:', bannedBooksForDistrict.length);

                // Update Vue component with selected district data
                vm.setSelectedItem(data, 'district', bannedBooksForDistrict);

                // Show the info panel
                const app = document.getElementById('app');
                const infoPanel = document.getElementById('info-panel');
                app.classList.add('detail-mode');
                infoPanel.classList.remove('hidden');

                // Wait for CSS transition to complete, then calculate new position
                setTimeout(() => {
                  const svgRect = svg.node().getBoundingClientRect();
                  const targetX = svgRect.width * 0.7; // 20% more to the right
                  const targetY = svgRect.height / 2;

                  // Validate centroid
                  if (!centroid || isNaN(centroid[0]) || isNaN(centroid[1])) {
                    console.warn('Invalid centroid, skipping zoom animation');
                    return;
                  }

                  // Calculate new transform to place centroid at target position
                  const newScale = 8;
                  const translateX = targetX - centroid[0] * newScale;
                  const translateY = targetY - centroid[1] * newScale;

                  // Validate transform calculations
                  if (isNaN(translateX) || isNaN(translateY)) {
                    console.warn('Invalid transform calculation, skipping zoom animation');
                    return;
                  }

                  const newTransform = d3.zoomIdentity
                    .translate(translateX, translateY)
                    .scale(newScale);

                  currentZoomIndex = zoomLevels.indexOf(newScale);

                  svg.transition()
                    .duration(500)
                    .call(zoom.transform, newTransform);
                }, 300);
              });
          }
        });

        console.log(`Rendered ${Object.keys(schoolDistricts).length} school districts`);
      })
      .catch(error => {
        console.error('Error loading school districts:', error);
      });

    // Load and draw military bases
    fetch('./mil_bases.json')
      .then(response => response.json())
      .then(milBases => {
        // Create a group for military bases
        const basesGroup = g.append('g')
          .attr('class', 'military-bases');

        // Draw each military base as a circle
        basesGroup.selectAll('circle')
          .data(milBases)
          .enter()
          .append('circle')
          .attr('cx', d => {
            const coords = projection([d.lng, d.lat]);
            return coords ? coords[0] : null;
          })
          .attr('cy', d => {
            const coords = projection([d.lng, d.lat]);
            return coords ? coords[1] : null;
          })
          .attr('r', 3)
          .attr('fill', 'rgba(214, 48, 49, 0.3)')
          .attr('stroke', '#d63031')
          .attr('stroke-width', 1)
          .attr('class', 'military-base')
          .style('cursor', 'pointer')
          .on('mouseover', function(event, d) {
            // Calculate banned books count for Department of Defense
            const bannedCount = booksData.filter(book => {
              return book.bans && book.bans.some(ban => ban.district === 'Department of Defense Educational Activitity');
            }).length;

            const baseName = d.formatted_name || d.name;
            tooltip.transition()
              .duration(200)
              .style('opacity', 1);
            tooltip.html(`
              <div class="tooltip-title">${baseName}</div>
              <div class="tooltip-subtitle">Department of Defense</div>
              <div class="tooltip-count">${bannedCount} banned book${bannedCount !== 1 ? 's' : ''}</div>
            `)
              .style('left', (event.pageX + 10) + 'px')
              .style('top', (event.pageY - 10) + 'px');
          })
          .on('mousemove', function(event) {
            tooltip
              .style('left', (event.pageX + 10) + 'px')
              .style('top', (event.pageY - 10) + 'px');
          })
          .on('mouseout', function() {
            tooltip.transition()
              .duration(200)
              .style('opacity', 0);
          })
          .on('click', function(event, d) {
            event.stopPropagation();

            // Remove selection from all items
            d3.selectAll('.school-district')
              .attr('fill', 'rgba(214, 48, 49, 0.3)')
              .attr('stroke', '#d63031')
              .attr('filter', null);
            d3.selectAll('.military-base')
              .attr('fill', 'rgba(214, 48, 49, 0.3)')
              .attr('stroke', '#d63031')
              .attr('filter', null);

            // Highlight selected base with orange and glow
            d3.select(this)
              .attr('fill', '#e17055')
              .attr('stroke', '#e17055')
              .attr('filter', 'url(#glow)');

            // Get the base coordinates
            const coords = projection([d.lng, d.lat]);

            // Find all books banned in Department of Defense (all military bases)
            const bannedBooksForMilitary = booksData.filter(book => {
              return book.bans && book.bans.some(ban => ban.district === 'Department of Defense Educational Activitity');
            });

            // Update Vue component with selected base data
            vm.setSelectedItem(d, 'base', bannedBooksForMilitary);

            // Show the info panel
            const app = document.getElementById('app');
            const infoPanel = document.getElementById('info-panel');
            app.classList.add('detail-mode');
            infoPanel.classList.remove('hidden');

            // Wait for CSS transition to complete, then calculate new position
            setTimeout(() => {
              const svgRect = svg.node().getBoundingClientRect();
              const targetX = svgRect.width * 0.7; // 20% more to the right
              const targetY = svgRect.height / 2;

              // Validate coords
              if (!coords || isNaN(coords[0]) || isNaN(coords[1])) {
                console.warn('Invalid coords, skipping zoom animation');
                return;
              }

              // Calculate new transform to place base at target position
              const newScale = 8;
              const translateX = targetX - coords[0] * newScale;
              const translateY = targetY - coords[1] * newScale;

              // Validate transform calculations
              if (isNaN(translateX) || isNaN(translateY)) {
                console.warn('Invalid transform calculation, skipping zoom animation');
                return;
              }

              const newTransform = d3.zoomIdentity
                .translate(translateX, translateY)
                .scale(newScale);

              currentZoomIndex = zoomLevels.indexOf(newScale);

              svg.transition()
                .duration(500)
                .call(zoom.transform, newTransform);
            }, 300);
          });

        console.log(`Rendered ${milBases.length} military bases`);
      })
      .catch(error => {
        console.error('Error loading military bases:', error);
      });

    // Zoom levels: 1x (default), 2.5x, 5x
    const zoomLevels = [1, 2.5, 5];
    let currentZoomIndex = 0;
    let currentTransform = d3.zoomIdentity;
    let accumulatedDelta = 0;
    const ZOOM_THRESHOLD = 100; // Accumulated delta needed to trigger zoom

    // Create zoom behavior with free-form panning
    const zoom = d3.zoom()
      .scaleExtent([1, 8])
      .on('zoom', (event) => {
        // Apply transform for both panning and zooming
        const transform = event.transform;

        // Validate transform values
        if (isNaN(transform.x) || isNaN(transform.y) || isNaN(transform.k)) {
          console.warn('Invalid transform detected, skipping');
          return;
        }

        currentTransform = transform;
        g.attr('transform', transform);
      });

    // Handle mouse wheel for discrete zoom levels
    svg.on('wheel', (event) => {
      event.preventDefault();

      // Accumulate delta values
      accumulatedDelta += event.deltaY;

      // Check if accumulated delta exceeds threshold
      if (Math.abs(accumulatedDelta) >= ZOOM_THRESHOLD) {
        // Determine zoom direction
        if (accumulatedDelta < 0) {
          // Zoom in
          if (currentZoomIndex < zoomLevels.length - 1) {
            currentZoomIndex++;
          }
        } else {
          // Zoom out
          if (currentZoomIndex > 0) {
            currentZoomIndex--;
          }
        }

        // Reset accumulated delta
        accumulatedDelta = 0;
      } else {
        // Not enough delta accumulated yet, skip zoom
        return;
      }

      // Get the new zoom level
      const newScale = zoomLevels[currentZoomIndex];

      // Calculate the mouse position relative to the SVG
      const [mouseX, mouseY] = d3.pointer(event, svg.node());

      // Validate mouse position
      if (isNaN(mouseX) || isNaN(mouseY)) {
        console.warn('Invalid mouse position, skipping zoom');
        return;
      }

      // Calculate the point in the map that's under the mouse
      const pointX = (mouseX - currentTransform.x) / currentTransform.k;
      const pointY = (mouseY - currentTransform.y) / currentTransform.k;

      // Validate calculated points
      if (isNaN(pointX) || isNaN(pointY)) {
        console.warn('Invalid point calculation, skipping zoom');
        return;
      }

      // Create new transform that keeps the point under the mouse
      const newTransform = d3.zoomIdentity
        .translate(mouseX, mouseY)
        .scale(newScale)
        .translate(-pointX, -pointY);

      // Apply the transform with transition
      svg.transition()
        .duration(300)
        .call(zoom.transform, newTransform);
    });

    // Enable zoom and pan
    svg.call(zoom);

    // Handle click on empty map area to close detail panel
    svg.on('click', (event) => {
      // Only close if clicking on the SVG itself, not on a child element
      if (event.target === svg.node() || event.target.tagName === 'path' && !event.target.classList.contains('school-district') && !event.target.classList.contains('military-base')) {
        // Clear Vue component selection
        vm.clearSelection();

        const app = document.getElementById('app');
        const infoPanel = document.getElementById('info-panel');
        app.classList.remove('detail-mode');
        infoPanel.classList.add('hidden');

        // Deselect all items and restore their original glow states
        d3.selectAll('.school-district').each(function() {
          const path = d3.select(this);
          const bannedCount = parseInt(path.attr('data-banned-count'));

          path.attr('fill', bannedCount <= 2 ? 'rgba(214, 48, 49, 0.15)' : bannedCount > 100 ? 'rgba(214, 48, 49, 0.5)' : 'rgba(214, 48, 49, 0.3)')
            .attr('stroke', bannedCount <= 2 ? '#f0a0a0' : '#d63031')
            .attr('filter', bannedCount > 500 ? 'url(#glow-extreme)' : bannedCount > 250 ? 'url(#glow-intense)' : bannedCount > 100 ? 'url(#glow)' : null);
        });
        d3.selectAll('.military-base')
          .attr('fill', 'rgba(214, 48, 49, 0.3)')
          .attr('stroke', '#d63031')
          .attr('filter', null);

        // Zoom back to default level
        currentZoomIndex = 0;
        svg.transition()
          .duration(500)
          .call(zoom.transform, d3.zoomIdentity);
      }
    });

    console.log('Map rendered successfully!');
    console.log(`Loaded ${booksData.length} books with ban data`);
}
