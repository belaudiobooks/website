function createErrorElement(message) {
    const error = document.createElement('p');
    error.innerText = message;
    error.classList.add('errornote');
    error.style = 'padding-left: 10px';
    return error;
}

function autoDetectLinkType() {
    django.jQuery('body').on('change', '[type="url"]', (e) => {
        const url = e.target.value;
        const select = e.target.closest('.dynamic-links').querySelector('select');
        // linkTypeRegexes is set in change_form_narration.html
        for (const [id, regex] of Object.entries(linkTypeRegexes)) {
            if (url.match(regex)) {
                select.value = id;
            }
        }
    });
}

/**
 * We want to use only « » quotes in descriptions. Show warning when we use any other kind of
 * quote when filling descriptions in admin.
 */
function showWarningOnWrongQuotes() {
    document.body.addEventListener('change', (e) => {
        const element = e.target;
        if (!element.classList.contains('vLargeTextField')) return;
        if (element.nextElementSibling
            && element.nextElementSibling.classList.contains('errornote')) {
            element.nextElementSibling.remove();
        }
        if (element.value.match(/["“”"„]/)) {
            const error = createErrorElement('Text contains one of the following quotation marks: " “ ” " „ '
                + 'We should be using only « » Please fix the text.');

            // Add a button that tries to auto-fix the text.
            const fixButton = document.createElement('button');
            fixButton.innerText = 'Fix';
            fixButton.classList.add('button');
            fixButton.style = 'padding: 5px 15px; margin-left: 10px;';
            fixButton.addEventListener('click', (e) => {
                e.preventDefault();
                element.value = element.value
                    .replace(/"(.*?)"/g, '«$1»')
                    .replace(/„(.*?)“/g, '«$1»')
                    .replace(/“(.*?)”/g, '«$1»');
                // Dispatch change event to trigger validation.
                element.dispatchEvent(new Event('change', { 'bubbles': true }));
            });
            error.appendChild(fixButton);
            element.after(error);
        }
    });
}

/**
 * Using Apple Book API looks up audiobook by title and returns array of links if found.
 */
async function findAppleBooksLink(title) {
    // API https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/Searching.html
    const request = new URL('https://itunes.apple.com/search');
    request.searchParams.append('media', 'audiobook');
    request.searchParams.append('term', title);
    request.searchParams.append('callback', 'appleCallback');
    const result = new Promise(resolve => {
        window.appleCallback = (data) => {
            resolve(data.results.map(entry => entry.collectionViewUrl));
            delete window.appleCallback
        };
    });
    const script = document.createElement('script');
    script.src = request.toString();
    document.body.appendChild(script);
    return result;
}

function getFirstUnfilledUrlField() {
    for (const field of Array.from(document.querySelectorAll('.field-url input'))) {
        if (!field.value) return field;
    }
    document.querySelector('.add-row a').click();
    return getFirstUnfilledUrlField();
}

function addFindAppleBooksLinkButton() {
    const button = document.createElement('button');
    button.innerText = 'Find Apple Books link';
    button.addEventListener('click', async (e) => {
        e.preventDefault();
        const title = document.querySelector('#id_book option').innerText;
        const links = await findAppleBooksLink(title.replace(/\(.*\)$/, ''));
        for (const link of links) {
            const field = getFirstUnfilledUrlField();
            field.value = link;
            field.dispatchEvent(new Event('change', { 'bubbles': true }));
        }
    });
    document.querySelector('.narration-links .add-row')?.after(button);
}

/**
 * Add a button that helps to find links to book on LiveLib. It is used on
 * Book edit page in admin to help filling LiveLib reviews links.
 */
function addLivelibLookupButton() {
    const livelibWidget = document.querySelector('.field-livelib_url');
    if (!livelibWidget) return;
    const button = document.createElement('button');
    button.innerText = 'Find LiveLib links';
    button.classList.add('button');
    button.style = 'padding: 5px 15px; margin: 10px 0px;';
    const container = document.createElement('div');
    container.style.marginTop = '10px';
    button.addEventListener('click', async (e) => {
        e.preventDefault();
        container.innerHTML = '';
        const title = document.querySelector('#id_title').value;
        if (!title) {
            container.appendChild(createErrorElement('Cannot search. "Book title" field is empty'));
            return;
        }
        const links = await (await fetch(`/api/livelib_books?query=${encodeURIComponent(title)}`)).json();
        if (links.length === 0) {
            container.appendChild(createErrorElement(
                'No links found. Maybe book title is misspelled or it is missing from LiveLib.'));
            return;
        }

        links.sort((a, b) => b.reviews - a.reviews);
        for (const link of links) {
            const div = document.createElement('div');
            const reviews = document.createElement('span');
            reviews.innerText = `Reviews ${link.reviews}`;
            reviews.style = 'margin-right: 10px;';
            div.appendChild(reviews);
            // Turn book link into reviews link for that books.
            const reviewsUrl = link.url.replace(/book\/(\d+)-/, 'book/$1/reviews-');
            const url = document.createElement('a');
            url.innerText = reviewsUrl;
            url.href = reviewsUrl;
            url.target = '_blank';
            div.appendChild(url);
            container.appendChild(div);
        }
    });
    livelibWidget.appendChild(button);
    livelibWidget.appendChild(container);
}

function main() {
    autoDetectLinkType();
    showWarningOnWrongQuotes();
    addFindAppleBooksLinkButton();
    addLivelibLookupButton();
}

window.addEventListener('load', main);
