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

window.addEventListener('load', autoDetectLinkType);