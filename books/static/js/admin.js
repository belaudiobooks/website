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
            const error = document.createElement('p');
            error.classList.add('errornote');
            error.innerText = 'Text contains one of the following quotation marks: " “ ” " „ '
                + 'We should be using only « » Please fix the text.';

            // Add a button that tries to auto-fix the text.
            const fixButton = document.createElement('button');
            fixButton.innerText = 'Fix';
            fixButton.classList.add('button');
            fixButton.style = 'width: 50px; height: 25px; margin-left: 10px;';
            fixButton.addEventListener('click', (e) => {
                e.preventDefault();
                element.value = element.value
                    .replace(/"(.*)"/g, '«$1»')
                    .replace(/„(.*)“/g, '«$1»')
                    .replace(/“(.*)”/g, '«$1»');
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
    document.querySelector('.add-row').after(button);
}

function main() {
    autoDetectLinkType();
    showWarningOnWrongQuotes();
    addFindAppleBooksLinkButton();
}

window.addEventListener('load', main);