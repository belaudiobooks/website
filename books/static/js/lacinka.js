/**
 * @fileoverview JS file that powers https://audiobooks.by/articles/lacinka
 */

const Orthography = {
    OFFICIAL: 'OFFICIAL',
    CLASSICAL: 'CLASSICAL',
    LATIN: 'LATIN',
    LATIN_NO_DIACTRIC: 'LATIN_NO_DIACTRIC',
};

/** @const {!Map<!Orthography, !Array<!Orthography>>} */
const SUPPORTED_CONVERSIONS = new Map([
    [Orthography.OFFICIAL, [Orthography.LATIN, Orthography.CLASSICAL, Orthography.LATIN_NO_DIACTRIC]],
    [Orthography.CLASSICAL, [Orthography.LATIN, Orthography.LATIN_NO_DIACTRIC]],
    [Orthography.LATIN, [Orthography.LATIN_NO_DIACTRIC]],
]);

const ORTHOGRAPHIES_NAMES = (() => {
    const result = new Map();
    for (const ortho of Object.values(Orthography)) {
        const attributeName = 'data-ortho-' + ortho.toLowerCase().replace(/_/g, '-');
        result.set(ortho, document.currentScript.getAttribute(attributeName));
    }
    return result;
})();

function createOrthographyOption(ortho) {
    const option = document.createElement('option');
    option.value = ortho;
    option.textContent = ORTHOGRAPHIES_NAMES.get(ortho);
    return option;
}

function fillFromSelector() {
    const fromOrtho = document.querySelector('#orthography-from');
    const toOrtho = document.querySelector('#orthography-to');
    for (const ortho of SUPPORTED_CONVERSIONS.keys()) {
        const option = createOrthographyOption(ortho);
        if (ortho === Orthography.OFFICIAL) {
            option.selected = 'selected';
        }
        fromOrtho.appendChild(option);
    }
    fromOrtho.addEventListener('change', () => {
        const options = SUPPORTED_CONVERSIONS.get(fromOrtho.value).map(createOrthographyOption);
        options[0].selected = 'selected';
        toOrtho.replaceChildren(...options);
        convertAndUpdateText();
    });
    toOrtho.addEventListener('change', convertAndUpdateText);
    fromOrtho.dispatchEvent(new CustomEvent('change'));
}

async function convert(text, fromOrtho, toOrtho) {
    const result = await fetch('/api/convert_orthography?' + new URLSearchParams({
        'text': text,
        'from': fromOrtho,
        'to': toOrtho
    }));
    return await result.text();
}

async function convertAndUpdateText() {
    const textFrom = document.querySelector('#text-from');
    const textTo = document.querySelector('#text-to');
    const orthoFrom = document.querySelector('#orthography-from');
    const orthoTo = document.querySelector('#orthography-to');
    if (textFrom.value === '') {
        textTo.value = '';
    } else {
        textTo.value = await convert(
            textFrom.value,
            orthoFrom.value,
            orthoTo.value,
        );
    }
}

function handleInput() {
    let timeoutId = 0;
    document.querySelector('#text-from').addEventListener('input', () => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(convertAndUpdateText, 300);
    });
}

function handleNotifyErrorButton() {
    document.querySelector('#button-notify').addEventListener('click', () => {
        const textFrom = encodeURIComponent(document.querySelector('#text-from').value);
        const textTo = encodeURIComponent(document.querySelector('#text-to').value);
        const prefilledFormUrl =
            `https://docs.google.com/forms/d/e/1FAIpQLScIZHxrKhtDRORl91JgXkWFnMO2nw9reTWZgMS3ZPdnj6ZMWg/viewform?usp=pp_url&entry.866058195=${textFrom}&entry.1652077591=${textTo}`;
        window.open(prefilledFormUrl, '_blank');
    });
}

window.addEventListener('load', () => {
    fillFromSelector();
    handleInput();
    handleNotifyErrorButton();
});
