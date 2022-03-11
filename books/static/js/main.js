/**
 * Given a name that consist of 1 or more parts collapses all parts
 * except for the last. For example "Jon Doe" becomes "J. Doe".
 * @param {string} name 
 * @returns string
 */
function shortenName(name) {
  const parts = name.split(' ');
  for (let i = 0; i < parts.length - 1; i++) {
    if (parts[i].length === 1) continue;
    parts[i] = parts[i][0] + '.';
  }
  return parts.join(' ');
}

/**
 * Renders a search result (book or author) and returns DOM element.
 * @param {!Object} hit 
 * @returns {!HTMLElement}
 */
function renderHit(hit) {
  const hitAnchor = document.createElement('a');
  hitAnchor.classList.add('hit');
  const content = document.createElement('div');
  content.classList.add('content');
  hitAnchor.appendChild(content);
  if (hit['model'] === 'book') {
    content.textContent = hit['title'];
    const authors = hit['authors'].map(shortenName).join(', ');
    const authorsSpan = document.createElement('span');
    authorsSpan.textContent = authors;
    authorsSpan.classList.add('authors');
    content.appendChild(authorsSpan);
    hitAnchor.href = `/books/${hit['slug']}`;
  } else {
    content.textContent = hit['name'];
    hitAnchor.href = `/person/${hit['slug']}`;
  }
  return hitAnchor;
}

/**
 * Initializes dynamic search using Algolia.
 */
function initializeSearch() {
  const algoliaParams = document.querySelector('meta[name="algolia"]').dataset;
  const search = instantsearch({
    indexName: algoliaParams['index'],
    searchClient: algoliasearch(
      algoliaParams['appId'],
      algoliaParams['searchKey'],
    ),
  });

  const makeSearchBox = instantsearch.connectors.connectSearchBox(
    (renderOptions, isFirstRender) => {
      if (!isFirstRender) return;
      const { refine, clear } = renderOptions;
      const search = document.querySelector('#search');
      search.addEventListener('input', () => {
        // Search only when there are 3 or more characters to make it meaningful.
        if (search.value.length > 2) {
          refine(search.value);
        } else {
          clear();
        }
      });
    });
  const conf = instantsearch.widgets.configure({
    hitsPerPage: 4,
  });
  const makeHits = instantsearch.connectors.connectHits(
    ({ results }) => {
      const autocomplete = document.querySelector('#autocomplete');
      if (results == null || results.query === '') {
        autocomplete.classList.add('d-none');
        return;
      }
      autocomplete.innerHTML = '';
      for (const hit of results.hits) {
        autocomplete.appendChild(renderHit(hit));
      }
      autocomplete.classList.remove('d-none');
    }
  );
  search.addWidgets([makeSearchBox(), makeHits(), conf]);
  search.start();
  document.documentElement.addEventListener('click', () => {
    document.querySelector('#autocomplete').classList.add('d-none');
  });
}

window.addEventListener('load', () => {
  initializeSearch();
});