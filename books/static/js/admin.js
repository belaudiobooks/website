function autoDetectLinkType() {
    django.jQuery('.dynamic-links').on('change', '[type="url"]', (e) => {
        const url = e.target.value;
        // linkTypeRegexes is set in change_form_narration.html
        for (const [id, regex] of Object.entries(linkTypeRegexes)) {
            if (url.match(regex)) {
                e.delegateTarget.querySelector('select').value = id;
            }
        }
    });
}

window.addEventListener('load', autoDetectLinkType);