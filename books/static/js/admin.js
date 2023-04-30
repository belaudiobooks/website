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
            element.after(error);
        }
    });
}

function main() {
    autoDetectLinkType();
    showWarningOnWrongQuotes();
}

window.addEventListener('load', main);